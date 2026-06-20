from sqlalchemy import Column, Integer, String, DateTime, func
from .database import Base

class DetectionJob(Base):
    __tablename__ = "detection_jobs"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String, unique=True, index=True, nullable=True)
    filename = Column(String, nullable=False, unique=True) # Randomized internal filename
    original_filename = Column(String, nullable=False) # User's original filename
    status = Column(String, default="PENDING")
    upload_time = Column(DateTime, server_default=func.now())
    output_path = Column(String, nullable=True)
    completion_time = Column(DateTime, nullable=True)
    healthy_detection_count = Column(Integer, default=0)
    unhealthy_detection_count = Column(Integer, default=0)
    total_frames = Column(Integer, default=0)
    processed_frames = Column(Integer, default=0)
    progress_percent = Column(Integer, default=0)

class Setting(Base):
    __tablename__ = "settings"

    key = Column(String, primary_key=True, index=True)
    value = Column(String, nullable=False)
