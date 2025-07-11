from pydantic import BaseModel, Field
from datetime import datetime, time, date,timedelta
from typing import List, Optional
from uuid import uuid4
from enum import Enum

class PriorityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class Task(BaseModel):
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    
    # Task details
    name: str
    description: str
    dateofassignment: datetime
    duration: timedelta
    image_url: Optional[str] = None
    document_url: Optional[str] = None
    
   #this is regarding whether task is completed or not
    completed_status: bool = False
    #This field regarding the actual status of task changed to :
    # changed to : By nawaz 24/6/2025 
    descriptive_task_status:  Optional[str] =""
    priority: PriorityLevel
    requirements: Optional[List[str]] = None

   
    manager_id: str
    employee_id: str
    project_id: str
    
    accepted_status: bool = False
    reject_reason:Optional[str]

    created_at: datetime = Field(default_factory=datetime.now)
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
            time: lambda v: v.isoformat()
        }
        populate_by_name = True

        



