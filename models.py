from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Driver(BaseModel):
    id: str
    name: str
    phone: str
    current_location: Optional[str] = None
    is_loaded: bool = False
    truck_capacity: int = 40000
    created_at: Optional[datetime] = None

class Load(BaseModel):
    id: str
    load_number: str
    pickup_location: str
    delivery_location: str
    weight: int
    status: str = "available"
    assigned_driver_id: Optional[str] = None
    created_at: Optional[datetime] = None

class CallLog(BaseModel):
    id: str
    driver_id: str
    call_sid: Optional[str] = None
    is_loaded: Optional[bool] = None
    reason_not_loaded: Optional[str] = None
    current_location: Optional[str] = None
    call_duration: Optional[int] = None
    created_at: Optional[datetime] = None

class DriverStatus(BaseModel):
    id: str
    driver_id: str
    is_loaded: bool
    location: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

class MakeCallRequest(BaseModel):
    driver_id: str

class CallWebhook(BaseModel):
    type: str
    call: dict
    message: Optional[dict] = None

class UpdateDriverStatusRequest(BaseModel):
    is_loaded: bool
    location: str
    reason_not_loaded: Optional[str] = None