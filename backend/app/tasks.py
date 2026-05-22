from .celery_utils import celery_app
from . import crud
from .database import SessionLocal
from ultralytics import YOLO
import os
import cv2

HEALTHY_CLASS_NAME = "Udang Vanamei Sehat"
NORMALIZED_HEALTHY_CLASS_NAME = HEALTHY_CLASS_NAME.strip().lower()


def is_healthy_class(class_name: str) -> bool:
    return class_name.strip().lower() == NORMALIZED_HEALTHY_CLASS_NAME


# Define base directory for uploads and outputs
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.join(BASE_DIR, "..", "uploads")
OUTPUTS_DIR = os.path.join(BASE_DIR, "..", "outputs")
WEIGHT_PATH = os.path.join(BASE_DIR, "..", "weight/yolov8n.pt")

# Load the model once when the worker starts
try:
    model = YOLO(WEIGHT_PATH)
except Exception as e:
    print(f"Error loading YOLO model in worker: {e}")
    model = None

@celery_app.task
def process_video_task(job_id: int, confidence: float = 0.1):
    """
    Celery task to process a video, using CRUD functions to update state.
    """
    db = SessionLocal()
    try:
        job = crud.get_job(db, job_id)
        if not job:
            print(f"Error: Job with ID {job_id} not found.")
            return

        crud.set_job_status(db, job_id, "PROCESSING")

        if not model:
            raise ValueError("YOLO model not loaded in worker.")

        video_path = os.path.join(UPLOADS_DIR, job.filename)
        output_path = os.path.join(OUTPUTS_DIR, f"output_{job.filename}")

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise IOError(f"Could not open video file {video_path}")

        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        healthy_detection_count = 0
        unhealthy_detection_count = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            results = model(frame, verbose=False, conf=confidence)
            if results and results[0].boxes:
                for box in results[0].boxes:
                    class_id = int(box.cls[0])
                    class_name = model.names[class_id]
                    if is_healthy_class(class_name):
                        healthy_detection_count += 1
                    else:
                        unhealthy_detection_count += 1
            annotated_frame = results[0].plot()
            out.write(annotated_frame)

        cap.release()
        out.release()

        crud.complete_job(
            db,
            job_id,
            "SUCCESS",
            output_path,
            healthy_detection_count=healthy_detection_count,
            unhealthy_detection_count=unhealthy_detection_count
        )
        print(f"--- Video Processing Task SUCCESS for job {job_id} ---")

        # Clean up the original uploaded file
        try:
            os.remove(video_path)
            print(f"Successfully deleted original file: {video_path}")
        except OSError as e:
            print(f"Error deleting original file {video_path}: {e}")

    except Exception as e:
        print(f"Error during video processing task for job {job_id}: {e}")
        crud.complete_job(db, job_id, "FAILURE", healthy_detection_count=0, unhealthy_detection_count=0)
    finally:
        db.close()
