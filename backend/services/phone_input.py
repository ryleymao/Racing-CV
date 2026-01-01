"""
Phone Input Service - Industry Standard
Receives tilt/joystick input from phone via WebSocket.
Uses websockets library for WebSocket client.
JSON encoding: json
"""
import asyncio
import websockets
import json
import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.settings import settings
from backend.utils.logger import logger

# WebSocket target
WS_URI = settings.cv_websocket_uri_resolved

async def send_phone_input(steering: float):
    """
    Send steering input from phone to WebSocket server.
    Industry standard: websockets library, JSON encoding.
    
    Args:
        steering: Steering value in range [-1, 1]
    """
    try:
        async with websockets.connect(WS_URI) as ws:
            logger.info("Phone input connected to WebSocket server")
            
            # Industry standard: JSON {"steering": float}
            message = {
                "source": "phone",
                "steering": float(steering)
            }
            
            await ws.send(json.dumps(message))
            logger.info(f"Sent phone steering: {steering}")
            
    except Exception as e:
        logger.error(f"Error sending phone input: {e}")


# This is mainly for testing - actual phone input comes from browser
if __name__ == "__main__":
    # Test with a sample steering value
    test_steering = 0.5
    logger.info(f"Testing phone input with steering: {test_steering}")
    asyncio.run(send_phone_input(test_steering))
