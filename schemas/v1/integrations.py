from pydantic import BaseModel


class IntegrationField(BaseModel):
    key: str
    label: str
    value: str        # masked for sensitive fields, full value for non-sensitive
    is_set: bool      # whether any effective value (env or DB) exists
    is_overridden: bool  # True when stored in DB (custom), False when from .env
    env_has_value: bool  # True when .env has a non-empty default
    sensitive: bool   # if True, value is masked and input uses password type
    placeholder: str
    hint: str = ""


class IntegrationGroup(BaseModel):
    id: str           # "discord" | "twilio" | "groq" | "alpaca"
    name: str
    description: str
    status: str       # "configured" | "partial" | "not_configured"
    restart_required: bool
    use_env_default: bool   # True when no DB overrides exist for this group
    env_configured: bool     # True when .env has all required values for this group
    fields: list[IntegrationField]


class IntegrationsResponse(BaseModel):
    groups: list[IntegrationGroup]


class IntegrationUpdateRequest(BaseModel):
    key: str
    value: str


class IntegrationUpdateResponse(BaseModel):
    key: str
    integrations: IntegrationsResponse


class IntegrationGroupUpdateRequest(BaseModel):
    use_env_default: bool


class IntegrationGroupUpdateResponse(BaseModel):
    group_id: str
    integrations: IntegrationsResponse
