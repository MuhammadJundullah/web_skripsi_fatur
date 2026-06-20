from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

DATABASE_URL = "sqlite:///./database.db"

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def create_db_and_tables():
    # Import all models here before calling create_all
    # so that they are registered on the metadata
    from . import models
    print("--- Creating database and tables ---")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    if "detection_jobs" in inspector.get_table_names():
        existing_columns = {column["name"] for column in inspector.get_columns("detection_jobs")}
        with engine.begin() as connection:
            if "healthy_detection_count" not in existing_columns:
                connection.execute(text(
                    "ALTER TABLE detection_jobs ADD COLUMN healthy_detection_count INTEGER DEFAULT 0"
                ))
            if "unhealthy_detection_count" not in existing_columns:
                connection.execute(text(
                    "ALTER TABLE detection_jobs ADD COLUMN unhealthy_detection_count INTEGER DEFAULT 0"
                ))
            if "total_frames" not in existing_columns:
                connection.execute(text(
                    "ALTER TABLE detection_jobs ADD COLUMN total_frames INTEGER DEFAULT 0"
                ))
            if "processed_frames" not in existing_columns:
                connection.execute(text(
                    "ALTER TABLE detection_jobs ADD COLUMN processed_frames INTEGER DEFAULT 0"
                ))
            if "progress_percent" not in existing_columns:
                connection.execute(text(
                    "ALTER TABLE detection_jobs ADD COLUMN progress_percent INTEGER DEFAULT 0"
                ))
