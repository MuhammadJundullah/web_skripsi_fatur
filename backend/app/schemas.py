from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

# Base schema for a Job
class JobBase(BaseModel):
    filename: str

# Schema for reading a Job from the API
class Job(JobBase):
    id: int
    original_filename: str
    task_id: Optional[str] = None
    status: str
    upload_time: datetime
    output_path: Optional[str] = None
    completion_time: Optional[datetime] = None
    healthy_detection_count: int = 0
    unhealthy_detection_count: int = 0

    class Config:
        from_attributes = True # orm_mode = True

# Base schema for a Setting
class SettingBase(BaseModel):
    key: str
    value: str

# Schema for reading a Setting from the API
class Setting(SettingBase):
    class Config:
        from_attributes = True # orm_mode = True

# --- New Schemas for Image Detection ---

class BoundingBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float

class Detection(BaseModel):
    class_name: str # Renamed from 'class' to avoid keyword clash
    confidence: float
    bbox: BoundingBox

class DetectionSummary(BaseModel):
    total_count: int
    healthy_count: int
    diseased_count: int
    healthy_percentage: float
    diseased_percentage: float
    healthy_class_name: str
    overall_status: str
    recommendation: str
    needs_immediate_harvest: bool

class ImageDetectionResponse(BaseModel):
    imageUrl: str
    detections: List[Detection]
    summary: DetectionSummary
