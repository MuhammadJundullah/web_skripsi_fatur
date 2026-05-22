from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, WebSocket
from fastapi.responses import StreamingResponse, Response, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import os
import io
import asyncio
import uuid
import datetime

# CV and ML imports
from ultralytics import YOLO
import cv2
import numpy as np
from PIL import Image
import psutil

from . import crud, models, schemas, tasks, dependencies, database

load_dotenv()

# Create all database tables on startup
database.create_db_and_tables()

app = FastAPI(title="Vannamei Shrimp Disease Detection API")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Directory and Model Loading ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.join(BASE_DIR, "..", "uploads")
OUTPUTS_DIR = os.path.join(BASE_DIR, "..", "outputs")
WEIGHT_PATH = os.path.join(BASE_DIR, "..", "weight/yolov8n.pt")
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(OUTPUTS_DIR, exist_ok=True)

# Mount the outputs directory to serve images
# This makes files in OUTPUTS_DIR accessible via the /outputs URL path
app.mount("/outputs", StaticFiles(directory=OUTPUTS_DIR), name="outputs")

# Define the base URL for the backend API
# This is crucial for generating absolute URLs for images
BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:8000")

try:
    model = YOLO(WEIGHT_PATH)
    print(f"YOLO model loaded successfully from {WEIGHT_PATH}")
except Exception as e:
    print(f"Error loading YOLO model: {e}")
    model = None

# --- Helper to get confidence setting ---
def get_model_confidence(db: Session) -> float:
    conf_setting = crud.get_setting(db, key="model_confidence")
    if conf_setting:
        try:
            return float(conf_setting.value)
        except (ValueError, TypeError):
            return 0.25 
    return 0.25 


HEALTHY_CLASS_NAME = "Udang Vanamei Sehat"
NORMALIZED_HEALTHY_CLASS_NAME = HEALTHY_CLASS_NAME.strip().lower()


def is_healthy_class(class_name: str) -> bool:
    return class_name.strip().lower() == NORMALIZED_HEALTHY_CLASS_NAME


def build_detection_summary(total_detected: int, healthy_count: int, diseased_count: int) -> schemas.DetectionSummary:
    healthy_percentage = (healthy_count / total_detected * 100) if total_detected > 0 else 0.0
    diseased_percentage = (diseased_count / total_detected * 100) if total_detected > 0 else 0.0

    if diseased_count > 0:
        overall_status = "warning"
        recommendation = "Terdeteksi udang selain sehat. Udang harus segera dipanen."
        needs_immediate_harvest = True
    elif healthy_count > 0:
        overall_status = "healthy"
        recommendation = "Seluruh udang yang terdeteksi berada dalam kondisi sehat."
        needs_immediate_harvest = False
    else:
        overall_status = "no_detection"
        recommendation = "Belum ada udang yang terdeteksi."
        needs_immediate_harvest = False

    return schemas.DetectionSummary(
        total_count=total_detected,
        healthy_count=healthy_count,
        diseased_count=diseased_count,
        healthy_percentage=healthy_percentage,
        diseased_percentage=diseased_percentage,
        healthy_class_name=HEALTHY_CLASS_NAME,
        overall_status=overall_status,
        recommendation=recommendation,
        needs_immediate_harvest=needs_immediate_harvest
    )

# --- API Endpoints ---

@app.post("/detect/video", response_model=schemas.Job)
async def detect_video_endpoint(file: UploadFile = File(...), db: Session = Depends(dependencies.get_db)):
    print(f"--- Received video upload request for file: {file.filename} ---")
    try:
        original_filename = os.path.basename(file.filename)
        _, extension = os.path.splitext(original_filename)
        random_filename = f"{uuid.uuid4()}{extension}"
        video_path = os.path.join(UPLOADS_DIR, random_filename)

        with open(video_path, "wb") as buffer:
            buffer.write(await file.read())
        print(f"Video saved to: {video_path}")

        # Get current model confidence from DB
        confidence = get_model_confidence(db)

        job = crud.create_detection_job(db=db, filename=random_filename, original_filename=original_filename)
        task = tasks.process_video_task.delay(job.id, confidence=confidence)
        crud.update_job_task_id(db=db, job_id=job.id, task_id=task.id)

        print(f"--- Task created with Celery ID: {task.id} for Job ID: {job.id} with conf: {confidence} ---")
        return job
    except Exception as e:
        print(f"Error in detect_video endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred while processing the video: {e}")

# --- Image Detection Endpoint ---
@app.post("/detect/image", response_model=schemas.ImageDetectionResponse)
async def detect_image_endpoint(file: UploadFile = File(...), db: Session = Depends(dependencies.get_db)):
    if not model:
        raise HTTPException(status_code=500, detail="YOLO model not loaded.")
    
    try:
        confidence = get_model_confidence(db)
        contents = await file.read()
        
        # Use Pillow to open image and convert to RGB
        image_pil = Image.open(io.BytesIO(contents)).convert("RGB")
        
        # Perform inference
        results = model(image_pil, conf=confidence, iou=0.45, verbose=False) # verbose=False to reduce console output
        
        # Process results
        detections_data = []
        healthy_count = 0
        diseased_count = 0
        
        # YOLOv8 results object structure: results[0] contains detections for the first image
        if results and results[0].boxes:
            for box in results[0].boxes:
                class_id = int(box.cls[0])
                class_name = model.names[class_id]
                confidence_score = float(box.conf[0])
                
                # Get bounding box coordinates
                x1, y1, x2, y2 = map(float, box.xyxy[0].tolist())
                
                # Kelas yang memuat kata seperti "sehat"/"normal"/"healthy"
                # diperlakukan sebagai udang sehat. Sisanya dianggap indikasi penyakit.
                if is_healthy_class(class_name):
                    healthy_count += 1
                else:
                    diseased_count += 1
                
                detections_data.append(schemas.Detection(
                    class_name=class_name,
                    confidence=confidence_score,
                    bbox=schemas.BoundingBox(x1=x1, y1=y1, x2=x2, y2=y2)
                ))

            total_detected = len(detections_data)
            summary = build_detection_summary(total_detected, healthy_count, diseased_count)
        else:
            summary = build_detection_summary(0, 0, 0)
            detections_data = []

        # Draw bounding boxes on the image
        annotated_image_np = results[0].plot(conf=True, boxes=True) # plot returns numpy array BGR
        annotated_image_pil = Image.fromarray(annotated_image_np[..., ::-1]) # Convert BGR to RGB for PIL

        # Save the processed image
        img_extension = "jpeg"
        img_filename = f"{uuid.uuid4()}.{img_extension}"
        img_save_path = os.path.join(OUTPUTS_DIR, img_filename)
        annotated_image_pil.save(img_save_path, format='JPEG')
        
        # Construct the ABSOLUTE URL for the saved image
        # This ensures the frontend can access it regardless of its origin
        image_url = f"{BACKEND_BASE_URL}/outputs/{img_filename}"

        # Prepare the response
        response_data = schemas.ImageDetectionResponse(
            imageUrl=image_url,
            detections=detections_data,
            summary=summary
        )
        
        return JSONResponse(content=response_data.model_dump())

    except HTTPException as e:
        raise e # Re-raise HTTP exceptions
    except Exception as e:
        print(f"Error in detect_image endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred while processing the image: {e}")

# --- Settings Endpoints ---

@app.get("/settings/{key}", response_model=schemas.Setting)
async def get_setting_endpoint(key: str, db: Session = Depends(dependencies.get_db)): # Corrected function name
    db_setting = crud.get_setting(db, key=key)
    if db_setting is None:
        # If a setting is not found, create it with a default
        default_value = "0.25" if key == "model_confidence" else ""
        if default_value:
            return crud.update_setting(db=db, key=key, value=default_value)
        raise HTTPException(status_code=404, detail="Setting not found")
    return db_setting

@app.post("/settings", response_model=schemas.Setting)
async def update_setting_endpoint(setting: schemas.SettingBase, db: Session = Depends(dependencies.get_db)):
    return crud.update_setting(db=db, key=setting.key, value=setting.value)

@app.get("/history", response_model=List[schemas.Job])
async def get_history_endpoint(skip: int = 0, limit: int = 100, db: Session = Depends(dependencies.get_db)):
    jobs = crud.get_jobs(db, skip=skip, limit=limit)
    return jobs

@app.delete("/history/{job_id}", status_code=200)
async def delete_job_endpoint(job_id: int, db: Session = Depends(dependencies.get_db)):
    job = crud.get_job(db, job_id=job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    try:
        original_file_path = os.path.join(UPLOADS_DIR, job.filename)
        if os.path.exists(original_file_path):
            os.remove(original_file_path)
        if job.output_path and os.path.exists(job.output_path):
            os.remove(job.output_path)
    except OSError as e:
        print(f"Error deleting files for job {job_id}: {e}")
    crud.delete_job(db, job_id=job_id)
    return {"message": f"Job {job_id} and associated files deleted successfully."}

@app.post("/retry/{job_id}", response_model=schemas.Job)
async def retry_job_endpoint(job_id: int, db: Session = Depends(dependencies.get_db)):
    job = crud.get_job(db, job_id=job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    if job.status != "FAILURE":
        raise HTTPException(status_code=400, detail=f"Job status is {job.status}, not 'FAILURE'. Cannot retry.")
    confidence = get_model_confidence(db)
    crud.set_job_status(db, job_id=job.id, status="PENDING")
    new_task = tasks.process_video_task.delay(job.id, confidence=confidence)
    updated_job = crud.update_job_task_id(db=db, job_id=job.id, task_id=new_task.id)
    print(f"--- Retrying job {job.id} with new Celery task ID: {new_task.id} ---")
    return updated_job

@app.get("/download/{job_id}")
async def download_video_endpoint(job_id: int, db: Session = Depends(dependencies.get_db)):
    job = crud.get_job(db, job_id=job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    if job.status != "SUCCESS" or not job.output_path or not os.path.exists(job.output_path):
        raise HTTPException(status_code=404, detail="Processed video not found or job not completed successfully.")
    async def videofile_iterator(file_path: str, chunk_size: int = 1024 * 1024):
        with open(file_path, mode="rb") as file_like:
            while chunk := file_like.read(chunk_size):
                yield chunk
    headers = {'Content-Disposition': f'attachment; filename="{job.original_filename}"'}
    return StreamingResponse(videofile_iterator(job.output_path), media_type="video/mp4", headers=headers)

# --- WebSocket and Monitoring ---
def get_system_resources_data():
    cpu_percent = psutil.cpu_percent(interval=None)
    virtual_memory = psutil.virtual_memory()
    disk_usage = psutil.disk_usage('/')
    net_io_counters = psutil.net_io_counters()
    return {
        "cpu_percent": cpu_percent,
        "memory": {"total": virtual_memory.total, "available": virtual_memory.available, "percent": virtual_memory.percent, "used": virtual_memory.used, "free": virtual_memory.free},
        "disk": {"total": disk_usage.total, "used": disk_usage.used, "free": disk_usage.free, "percent": disk_usage.percent},
        "network": {"bytes_sent": net_io_counters.bytes_sent, "bytes_recv": net_io_counters.bytes_recv},
        "timestamp": psutil.boot_time()
    }

@app.websocket("/ws/stream/realtime")
async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(dependencies.get_db)):
    await websocket.accept()
    if not model:
        await websocket.send_json({"error": "YOLO model not loaded."})
        await websocket.close()
        return
    
    confidence = get_model_confidence(db)

    async def send_monitor_stats_task():
        while True:
            try:
                stats = get_system_resources_data()
                await websocket.send_json({"type": "monitor_stats", "data": stats})
                await asyncio.sleep(2)
            except (asyncio.CancelledError, ConnectionResetError):
                break
            except Exception as e:
                print(f"Error in monitor stats task: {e}")
                break

    async def process_video_frames_task():
        while True:
            try:
                data = await websocket.receive_bytes()
                nparr = np.frombuffer(data, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if frame is None: continue
                results = model(frame, verbose=False, conf=confidence, iou=0.45)
                healthy_count = 0
                diseased_count = 0
                if results and results[0].boxes:
                    for box in results[0].boxes:
                        class_id = int(box.cls[0])
                        class_name = model.names[class_id]
                        if is_healthy_class(class_name):
                            healthy_count += 1
                        else:
                            diseased_count += 1
                summary = build_detection_summary(healthy_count + diseased_count, healthy_count, diseased_count)
                await websocket.send_json({"type": "detection_summary", "data": summary.model_dump()})
                annotated_frame = results[0].plot(conf=True, boxes=True)
                ret, buffer = cv2.imencode('.jpg', annotated_frame)
                if ret: await websocket.send_bytes(buffer.tobytes())
            except (asyncio.CancelledError, ConnectionResetError):
                break
            except Exception as e:
                print(f"Error in video frames task: {e}")
                break

    monitor_task = asyncio.create_task(send_monitor_stats_task())
    video_task = asyncio.create_task(process_video_frames_task())
    try:
        await asyncio.gather(monitor_task, video_task)
    finally:
        monitor_task.cancel()
        video_task.cancel()
        try: await websocket.close()
        except RuntimeError: pass
