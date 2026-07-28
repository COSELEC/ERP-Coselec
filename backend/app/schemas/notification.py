from datetime import datetime

from pydantic import BaseModel, ConfigDict

class NotificationCreate(BaseModel):
    user_id: int
    message: str
    type: str
    reference_id: int | None = None

class NotificationResponse(BaseModel):
    id: int
    user_id: int
    message: str
    type: str
    is_read: bool
    created_at: datetime
    reference_id: int | None = None

    model_config = ConfigDict(
        from_attributes=True
    )
