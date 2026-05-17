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
| `GET` | `/plate` | Service health check — returns `{"Just": "Fine!"}` |
| `POST` | `/plate` | Run plate recognition on a base64-encoded image |

> Default route is `/plate` (configurable via `APP_ROOT` env var). Service runs on port `3002` by default (`PORT_NUMBER` env var).

### Example: Recognize Plate from Base64 Image

```bash
curl -X POST http://localhost:3002/plate \
  -H "Content-Type: application/json" \
  -d '{"image": "<base64-encoded-frame>"}'
```

**Response:**

```json
{
  "plate_text": "12ب34567",
  "confidence": 0.94,
  "bbox": [120, 340, 280, 390]
}
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first.

## License

MIT
