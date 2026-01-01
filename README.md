# Headless VR Racing Control Backend

Backend service that receives steering input from webcam (face tilt) and phone (tilt/joystick) via WebSocket, then outputs a unified steering value.

## MVP Features

- **WebSocket Server** (`/ws`) - Accepts steering input from multiple sources
- **Webcam Input** - Face tracking via MediaPipe FaceMesh (head tilt)
- **Phone Input** - Tilt or joystick control via browser
- **Steering Merge** - Combines multiple inputs into unified steering value
- **Headless** - No UI required, just backend service

## Quick Start

### 1. Install Dependencies
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Start Server
```bash
cd /Users/ryleymao/Racing-CV
cd backend && source venv/bin/activate && cd ..
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Start Webcam Input
```bash
cd /Users/ryleymao/Racing-CV
cd backend && source venv/bin/activate && cd ..
python3 run_cv.py
```

**OR directly:**
```bash
python3 -m backend.services.cv_input
```

**What you'll see:**
- Webcam window opens (1280x720)
- Green face mesh overlay
- Yellow line between eyes (shows tilt)
- Steering bar at top
- Real-time steering values in console

Tilt your head left/right to see steering change!

### 4. Open Phone Client
On your phone browser: `http://YOUR_IP:8000`
- Use joystick or enable tilt control
- Steering values are sent to server

## API Endpoints

- `GET /` - Phone client HTML
- `GET /health` - Health check with current steering
- `GET /api/steering` - Get merged steering from all sources
- `GET /api/stats` - Connection statistics
- `GET /api/docs` - API documentation

## WebSocket Protocol

**Endpoint:** `/ws`

**Send:**
```json
{"source": "webcam", "steering": 0.3}
{"source": "phone", "steering": -0.2}
```

**Get merged steering:**
```bash
curl http://localhost:8000/api/steering
```

## Project Structure

```
backend/
├── main.py              # FastAPI server
├── services/
│   ├── cv_input.py      # Webcam face tracking
│   └── phone_input.py   # Phone input (test client)
├── utils/
│   └── steering_merge.py # Merge steering inputs
└── settings.py          # Configuration
```

## Tech Stack

- Python 3.14
- FastAPI
- MediaPipe (FaceMesh)
- OpenCV
- WebSockets