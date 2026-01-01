"""
FastAPI Server for Headless VR Racing Control Backend
Industry Standard:
- Language: Python 3.14
- Web framework: FastAPI
- WebSocket handling: fastapi.WebSocket
- Async handling: asyncio
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import json
import asyncio
from datetime import datetime

from backend.settings import settings
from backend.models import SteeringMessage, ErrorResponse
from backend.services.connection_manager import ConnectionManager
from backend.utils.logger import logger
from backend.utils.steering_merge import SteeringMerger

# Initialize FastAPI app
app = FastAPI(
    title="Headless VR Racing Control Backend",
    description="Backend service that merges steering inputs from webcam and phone",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS Configuration - follows least privilege principle
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "OPTIONS"],  # Only allow necessary methods
    allow_headers=["*"],
)

# Initialize connection manager for input sources only
connection_manager = ConnectionManager(
    max_game_clients=0,  # No game clients needed for headless MVP
    max_cv_clients=10  # Allow multiple input sources
)

# Initialize steering merger
steering_merger = SteeringMerger(
    weights={"webcam": 0.5, "phone": 0.5},  # Equal weights by default
    smoothing_window=5,
    smoothing_enabled=True
)

logger.info("Headless VR Racing Control Backend starting", extra={
    "server_host": settings.server_host,
    "server_port": settings.server_port,
})


@app.websocket(settings.ws_cv_endpoint)
async def input_websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for input sources (webcam, phone, etc.).
    Accepts messages with {"source": "webcam|phone", "steering": float}
    Merges inputs and broadcasts unified steering.
    """
    await websocket.accept()
    
    # Check connection limit (allow multiple input sources)
    connected = await connection_manager.connect_cv_client(websocket)
    if not connected:
        logger.warning("Input client connection rejected: limit reached")
        await websocket.close(code=1008, reason="Input client limit reached")
        return
    
    stats = connection_manager.get_stats()
    logger.info("Input client connected", extra={"stats": stats.model_dump()})
    
    try:
        while True:
            # Receive steering data
            data = await websocket.receive_text()
            
            try:
                # Parse JSON message
                msg = json.loads(data)
                source = msg.get("source", "unknown")
                steering = msg.get("steering", 0.0)
                
                # Validate steering value
                if not isinstance(steering, (int, float)):
                    continue
                
                steering = max(-1.0, min(1.0, float(steering)))
                
                # Update steering merger with source
                steering_merger.update_source(source, steering)
                
                # Get merged steering value
                merged_steering = steering_merger.get_merged_steering()
                
                # Update connection manager with merged value
                await connection_manager.update_steering(merged_steering)
                
                # Log source info
                source_info = steering_merger.get_source_info()
                logger.debug(f"Steering updated: {source_info} -> merged: {merged_steering:.3f}")
                
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON from input client: {e}", extra={
                    "raw_data": data[:100]
                })
                continue
            except Exception as e:
                logger.warning(f"Error processing input message: {e}", extra={
                    "raw_data": data[:100]
                })
                continue
                
    except WebSocketDisconnect:
        logger.info("Input client disconnected")
    except Exception as e:
        logger.error(f"Error in input websocket: {e}", exc_info=True)
    finally:
        await connection_manager.disconnect_cv_client(websocket)
        stats = connection_manager.get_stats()
        logger.info("Input client cleaned up", extra={"stats": stats.model_dump()})




@app.get("/")
async def read_root():
    """Serve the phone client HTML file."""
    phone_client_path = settings.project_root / "frontend" / "js" / "phone_client.html"
    if not phone_client_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Phone client file not found"
        )
    return FileResponse(str(phone_client_path))


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "steering": {
            "merged": steering_merger.get_merged_steering(),
            "sources": steering_merger.get_source_info()
        },
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/stats")
async def get_stats():
    """Get connection statistics (for monitoring/debugging)."""
    return {
        "input_clients": connection_manager.get_stats().cv_clients,
        "max_input_clients": connection_manager.get_stats().max_cv_clients
    }

@app.get("/api/steering")
async def get_steering_info():
    """Get current steering information from all sources."""
    return {
        "merged_steering": steering_merger.get_merged_steering(),
        "sources": steering_merger.get_source_info(),
        "source_count": steering_merger.get_source_count()
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return HTTPException(
        status_code=500,
        detail=ErrorResponse(
            error="Internal server error",
            detail=str(exc) if settings.log_level == "DEBUG" else None
        ).model_dump()
    )