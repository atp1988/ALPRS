# Plate Stream — License Plate Recognition Service

![Python](https://img.shields.io/badge/Python-3.10-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-green) ![YOLOv5](https://img.shields.io/badge/YOLOv5-Detection-red) ![CRNN](https://img.shields.io/badge/CRNN-Recognition-orange) ![Docker](https://img.shields.io/badge/Docker-Compose-blue)

Real-time Persian license plate recognition service that processes live RTSP camera streams. Detects license plates using YOLOv5 and reads Persian characters using a CRNN model, returning structured results via REST API.

## Features

- **Real-time RTSP processing** — continuous license plate reading from IP camera streams
- **YOLOv5 plate detection** — fast and accurate plate localization in complex environments
- **Persian CRNN reader** — character-level recognition model trained on Persian/Arabic plate characters
- **Box detection** — identifies plate character box regions for precise cropping
- **Multi-camera API** — manage multiple concurrent camera streams via REST endpoints
- **Docker deployment** — fully containerized with configurable service stack

## Tech Stack

| Component | Technology |
|---|---|
| Plate Detector | YOLOv5 (custom trained) |
| Character Reader | CRNN (PyTorch) |
| API Server | FastAPI + Uvicorn |
| Containerization | Docker Compose |
| Camera Capture | OpenCV |

## Architecture

```
IP Camera (RTSP)
      │
      ▼
 Stream Capture (OpenCV)
      │  raw frames
      ▼
 YOLOv5 Plate Detector
      │  plate bounding box
      ▼
 Box Extractor (boxes.py)
      │  character region crops
      ▼
 CRNN Recognition Model
      │  plate text (e.g. "12ب34567")
      ▼
 FastAPI Response  →  Client
```

## Prerequisites

- Docker & Docker Compose
- YOLOv5 plate detection weights in `app/weights/`
- CRNN character recognition model in `app/weights/`

## Installation & Setup

```bash
# 1. Clone the repository
git clone https://github.com/sadra-ai25/plate-stream.git
cd plate-stream

# 2. Place model weights
mkdir -p app/weights
cp /path/to/plate_detector.pt app/weights/
cp /path/to/crnn_model.pt    app/weights/

# 3. Start services
docker compose up -d --build
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service health check |
| `POST` | `/start_stream` | Start processing an RTSP stream |
| `POST` | `/stop_stream` | Stop a running stream |
| `GET` | `/latest` | Get the most recently read plate |
| `GET` | `/history` | Get recent plate readings |
| `POST` | `/predict` | Run single-image plate recognition |

### Example: Start a Stream

```bash
curl -X POST http://localhost:8000/start_stream \
  -H "Content-Type: application/json" \
  -d '{
    "camera_id": "gate1",
    "rtsp_url": "rtsp://username:password@192.168.1.100:554/"
  }'
```

### Example: Single Image Predict

```bash
curl -X POST http://localhost:8000/predict \
  -F "file=@/path/to/frame.jpg"
```

**Response:**

```json
{
  "plate_text": "12ب34567",
  "confidence": 0.94,
  "bbox": [120, 340, 280, 390],
  "timestamp": "2024-01-15T09:32:11"
}
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first.

## License

MIT
