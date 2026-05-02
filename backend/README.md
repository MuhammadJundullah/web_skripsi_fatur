# Backend Documentation

This document provides instructions for building a single Docker image locally and pushing it to Docker Hub. The image already includes the API and Celery worker via `supervisord`.

## Prerequisites

- Docker installed on your machine.
- A Docker Hub account.

## Build the Docker image (local)

Open a terminal in the `backend` directory and run:

```bash
docker build -t <dockerhub-username>/<image-name>:<tag> .
```

Example:

```bash
docker build -t myuser/vannamei-backend:1.0.0 .
```

## Run the Docker image (local)

The container listens on port `7860` by default.

```bash
docker run --rm -p 7860:7860 \
  -e REDIS_URL="<redis-url>" \
  -e BACKEND_BASE_URL="http://localhost:7860" \
  <dockerhub-username>/<image-name>:<tag>
```

If you previously saw an error like `ImportError: libGL.so.1`, rebuild the image from the updated Dockerfile. The runtime image now installs the native libraries needed by the backend CV stack.

## Push the image to Docker Hub

```bash
docker login
docker push <dockerhub-username>/<image-name>:<tag>
```

## Hugging Face Dockerfile (uses Docker Hub image)

Use this in your Hugging Face Space repo:

```dockerfile
FROM <dockerhub-username>/<image-name>:<tag>
```

## Running the Backend without Docker

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Run app with uvicorn:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 7860
```
