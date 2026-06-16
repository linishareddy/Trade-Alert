from pydantic import BaseModel


class RawAlertIn(BaseModel):
    """Schema for the self-bot to POST a raw Discord message."""
    message_id: str
    channel_id: str
    author: str
    content: str
    embeds: list[dict] = []
    timestamp: str
    is_edit: bool = False


class IngestResponse(BaseModel):
    """Response after accepting a raw alert."""
    accepted: bool
    signal_id: str | None = None
    action: str | None = None
