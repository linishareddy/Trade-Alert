from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from schemas.v1.integrations import (
    IntegrationField, IntegrationGroup, IntegrationsResponse,
    IntegrationUpdateRequest, IntegrationUpdateResponse,
    IntegrationGroupUpdateRequest, IntegrationGroupUpdateResponse,
)
from services.v1.config.runtime_settings import runtime, EDITABLE
from services.v1.integrations.reload import apply_integration_reload

router = APIRouter()

# ── Keys that belong to integrations (subset of EDITABLE) ────────────────────

INTEGRATION_KEYS = {
    "discord_token", "discord_channels",
    "twilio_sid", "twilio_token", "twilio_from", "whatsapp_to",
    "groq_key",
    "alpaca_key", "alpaca_secret",
}

GROUP_FIELD_KEYS: dict[str, list[str]] = {
    "discord": ["discord_token", "discord_channels"],
    "twilio": ["twilio_sid", "twilio_token", "twilio_from", "whatsapp_to"],
    "groq": ["groq_key"],
    "alpaca": ["alpaca_key", "alpaca_secret"],
}


def _mask(value: str) -> str:
    """Mask all but the last 4 characters of a secret value."""
    if not value:
        return ""
    if len(value) <= 4:
        return "••••"
    return "••••••••" + value[-4:]


def _field(
    key: str,
    label: str,
    placeholder: str,
    sensitive: bool = True,
    hint: str = "",
) -> IntegrationField:
    raw = str(runtime.get(key) or "")
    env_raw = str(runtime.env_get(key) or "")
    return IntegrationField(
        key=key,
        label=label,
        value=_mask(raw) if sensitive else raw,
        is_set=bool(raw),
        is_overridden=runtime.is_overridden(key),
        env_has_value=bool(env_raw),
        sensitive=sensitive,
        placeholder=placeholder,
        hint=hint,
    )


def _status(fields: list[IntegrationField]) -> str:
    n_set = sum(1 for f in fields if f.is_set)
    if n_set == len(fields):
        return "configured"
    if n_set > 0:
        return "partial"
    return "not_configured"


def _group_meta(fields: list[IntegrationField]) -> tuple[bool, bool]:
    use_env_default = not any(f.is_overridden for f in fields)
    env_configured = all(f.env_has_value for f in fields)
    return use_env_default, env_configured


def _build_integrations() -> IntegrationsResponse:
    discord_fields = [
        _field("discord_token",   "User Token",   "MTU...",          sensitive=True,  hint="Your Discord user token (not a bot token)"),
        _field("discord_channels","Channel IDs",  "123456,789012",   sensitive=False, hint="Comma-separated channel IDs to monitor"),
    ]

    twilio_fields = [
        _field("twilio_sid",   "Account SID", "AC...",           sensitive=True,  hint="From twilio.com/console"),
        _field("twilio_token", "Auth Token",  "••••••••",        sensitive=True,  hint="From twilio.com/console"),
        _field("twilio_from",  "From Number", "+14155238886",    sensitive=False, hint="Twilio WhatsApp sandbox or production number"),
        _field("whatsapp_to",  "Your Number", "+919876543210",   sensitive=False, hint="Your personal WhatsApp number with country code"),
    ]

    groq_fields = [
        _field("groq_key", "API Key", "gsk_...", sensitive=True, hint="From console.groq.com/keys"),
    ]

    alpaca_fields = [
        _field("alpaca_key",    "API Key",    "PK...",    sensitive=True, hint="From alpaca.markets/paper-account"),
        _field("alpaca_secret", "API Secret", "••••••••", sensitive=True, hint="From alpaca.markets/paper-account"),
    ]

    groups_spec = [
        ("discord", "Discord", "Monitors channels for trading signals", False, discord_fields),
        ("twilio", "WhatsApp", "Trade alerts via WhatsApp (Twilio)", False, twilio_fields),
        ("groq", "AI Parsing", "Fallback parser for unrecognised signals (Groq)", False, groq_fields),
        ("alpaca", "Alpaca", "Paper trading broker — executes bracket orders", False, alpaca_fields),
    ]

    groups: list[IntegrationGroup] = []
    for gid, name, desc, restart, fields in groups_spec:
        use_env, env_ok = _group_meta(fields)
        groups.append(IntegrationGroup(
            id=gid,
            name=name,
            description=desc,
            status=_status(fields),
            restart_required=restart,
            use_env_default=use_env,
            env_configured=env_ok,
            fields=fields,
        ))

    return IntegrationsResponse(groups=groups)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/integrations", response_model=IntegrationsResponse)
def get_integrations() -> IntegrationsResponse:
    """Return all integration groups with masked credential values."""
    return _build_integrations()


@router.patch("/integrations", response_model=IntegrationUpdateResponse)
async def update_integration(
    req: IntegrationUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> IntegrationUpdateResponse:
    """Save a single integration credential to the DB. Takes effect immediately."""
    if req.key not in INTEGRATION_KEYS:
        raise HTTPException(
            status_code=400,
            detail=f"'{req.key}' is not an integration key. Valid keys: {sorted(INTEGRATION_KEYS)}",
        )
    if req.key not in EDITABLE:
        raise HTTPException(status_code=400, detail=f"'{req.key}' is not editable at runtime")

    await runtime.set(req.key, req.value, db)
    apply_integration_reload({req.key})
    return IntegrationUpdateResponse(key=req.key, integrations=_build_integrations())


@router.delete("/integrations/{key}", response_model=IntegrationUpdateResponse)
async def reset_integration(
    key: str,
    db: AsyncSession = Depends(get_db),
) -> IntegrationUpdateResponse:
    """Remove DB override for a credential — value reverts to .env."""
    if key not in INTEGRATION_KEYS:
        raise HTTPException(status_code=400, detail=f"'{key}' is not an integration key")
    await runtime.reset(key, db)
    apply_integration_reload({key})
    return IntegrationUpdateResponse(key=key, integrations=_build_integrations())


@router.patch("/integrations/groups/{group_id}", response_model=IntegrationGroupUpdateResponse)
async def update_integration_group(
    group_id: str,
    req: IntegrationGroupUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> IntegrationGroupUpdateResponse:
    """When use_env_default=true, remove all DB overrides for the group (revert to .env)."""
    if group_id not in GROUP_FIELD_KEYS:
        raise HTTPException(status_code=404, detail=f"Unknown integration group '{group_id}'")

    changed: set[str] = set()
    if req.use_env_default:
        for key in GROUP_FIELD_KEYS[group_id]:
            if runtime.is_overridden(key):
                await runtime.reset(key, db)
                changed.add(key)

    if changed:
        apply_integration_reload(changed)

    return IntegrationGroupUpdateResponse(group_id=group_id, integrations=_build_integrations())


@router.post("/integrations/test/whatsapp")
async def test_whatsapp() -> dict:
    """Send a test WhatsApp message to verify Twilio credentials."""
    from services.v1.notifications.whatsapp_service import notify_test
    ok = await notify_test()
    if ok:
        return {"ok": True, "message": "Test message sent — check your WhatsApp"}
    return {"ok": False, "message": "Failed to send — check Twilio credentials and WhatsApp toggle"}
