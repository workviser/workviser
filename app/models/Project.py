from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List, Optional
from uuid import UUID

class Project(BaseModel):
    id: UUID
    name: str
    description: str
    dateofassignement: datetime
    duration: str
    image_url: Optional[str] = None
    document_url: Optional[str] = None
    status: bool
    created_at: datetime

    employee_ids: List[str]
    manager_ids: List[str]

    client_name: str
    client_email: EmailStr

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }
