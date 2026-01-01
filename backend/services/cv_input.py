"""
CV Input Service - Hand tracking for steering, head tracking for looking around.
Uses OpenCV for hand/face detection (works with Python 3.14).
Better UI with visual feedback for VR-style control.
"""
import cv2
import json
import asyncio
import websockets
import sys
import numpy as np
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.settings import settings
from backend.utils.logger import logger
from backend.models import SteeringMessage

# Use OpenCV for detection (works everywhere)
print("✅ Using OpenCV for hand and face tracking")
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Webcam
cap = None

# WebSocket target
WS_URI = settings.cv_websocket_uri_resolved

def detect_hand_simple(frame):
    """
    Simple hand detection using color-based tracking.
    Looks for skin-colored regions in lower portion of frame.
    
    Returns:
        (x, y, w, h) bounding box or None
    """
    # Convert to HSV for better color detection
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # Define skin color range (HSV)
    lower_skin = np.array([0, 20, 70], dtype=np.uint8)
    upper_skin = np.array([20, 255, 255], dtype=np.uint8)
    
    # Create mask for skin color
    mask = cv2.inRange(hsv, lower_skin, upper_skin)
    
    # Apply morphological operations to clean up mask
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    
    # Find contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours:
        # Get largest contour (likely hand)
        largest_contour = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest_contour) > 5000:  # Minimum area threshold
            x, y, w, h = cv2.boundingRect(largest_contour)
            return (x, y, w, h)
    return None

def calculate_steering_from_hand(hand_bbox, image_width):
    """
    Calculate steering from hand position (left/right in frame).
    
    Args:
        hand_bbox: Hand bounding box (x, y, w, h)
        image_width: Image width in pixels
        
    Returns:
        Steering value in range [-1, 1]
    """
    if hand_bbox is None:
        return 0.0
    
    # Get hand center
    hand_center_x = hand_bbox[0] + hand_bbox[2] / 2
    
    # Calculate offset from image center
    image_center_x = image_width / 2
    offset = (hand_center_x - image_center_x) / image_center_x
    
    # Normalize to [-1, 1] range with sensitivity
    steering = max(-1.0, min(1.0, offset * 1.8))
    
    return steering

def calculate_head_rotation(face_bbox, image_width):
    """
    Calculate head rotation for looking around (limited range).
    Uses face position to estimate head yaw.
    
    Args:
        face_bbox: Face bounding box (x, y, w, h)
        image_width: Image width in pixels
        
    Returns:
        Head rotation in range [-0.5, 0.5] (limited for VR feel)
    """
    if face_bbox is None:
        return 0.0
    
    # Get face center
    face_center_x = face_bbox[0] + face_bbox[2] / 2
    
    # Calculate offset from image center
    image_center_x = image_width / 2
    offset = (face_center_x - image_center_x) / image_center_x
    
    # Normalize to limited range [-0.5, 0.5] for VR feel
    max_rotation = 0.5
    rotation = max(-max_rotation, min(max_rotation, offset * 0.6))
    
    return rotation

async def send_steering():
    """Main function to capture video, track hands/face, and send data."""
    global cap
    
    print("\n" + "="*70)
    print("🚀 VR RACING CONTROL - Hand Steering + Head Look")
    print("="*70)
    
    # Initialize webcam
    print(f"\n📹 Opening webcam index {settings.webcam_index}...")
    cap = cv2.VideoCapture(settings.webcam_index)
    if not cap.isOpened():
        print(f"\n❌ ❌ ❌ CAMERA PERMISSION REQUIRED ❌ ❌ ❌")
        print(f"\nCould not open webcam at index {settings.webcam_index}")
        print("\n🔧 FIX:")
        print("   1. Open System Settings > Privacy & Security > Camera")
        print("   2. Enable camera for Terminal (or Python)")
        logger.error(f"Could not open webcam at index {settings.webcam_index}")
        return
    print("✅ Webcam opened!")
    
    # Set webcam resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    print("✅ Resolution set to 1280x720")
    
    print(f"\n🔌 Connecting to server...")
    logger.info(f"Webcam opened at index {settings.webcam_index}")
    
    frame_count = 0
    hand_detection_count = 0
    face_detection_count = 0
    
    try:
        print("⏳ Connecting to server (will continue even if server is down)...")
        ws_connected = False
        ws = None
        try:
            ws = await asyncio.wait_for(websockets.connect(WS_URI), timeout=3.0)
            print("✅ CONNECTED TO SERVER!")
            ws_connected = True
        except (asyncio.TimeoutError, ConnectionRefusedError, OSError) as e:
            print(f"⚠️  Server not available: {type(e).__name__}")
            print("   Running in local mode (no WebSocket)")
            ws = None
            ws_connected = False
        except Exception as e:
            print(f"⚠️  Connection error: {e}")
            print("   Continuing in local mode (no WebSocket)")
            ws = None
            ws_connected = False
        
        print("\n" + "="*70)
        print("📹 WEBCAM WINDOW SHOULD OPEN NOW")
        print("="*70)
        print("🎮 CONTROLS:")
        print("   - Move HAND left/right → Steering")
        print("   - Turn HEAD left/right → Look around (limited range)")
        print("   - Press 'q' to quit")
        print("="*70)
        print("[CV DEBUG] Frame | Hand | Steering | Head | Rotation")
        print("-" * 70)
        logger.info("Starting hand and face tracking...")
        
        window_created = False  # Track if window was created
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[CV] ⚠️  Failed to read frame from webcam")
                continue

            frame_count += 1
            
            # Flip frame horizontally for mirror effect
            frame = cv2.flip(frame, 1)
            image_height, image_width, _ = frame.shape
            
            steering = 0.0
            head_rotation = 0.0
            hand_detected = False
            face_detected = False
            hand_bbox = None
            face_bbox = None
            
            try:
                # Detect hand (in lower portion of frame)
                lower_region = frame[image_height//2:, :]
                hand_bbox_lower = detect_hand_simple(lower_region)
                if hand_bbox_lower is not None:
                    # Adjust coordinates to full frame
                    x, y, w, h = hand_bbox_lower
                    hand_bbox = (x, y + image_height//2, w, h)
                    hand_detected = True
                    hand_detection_count += 1
                    steering = calculate_steering_from_hand(hand_bbox, image_width)
            except Exception as e:
                # Hand detection failed, continue without hand
                pass
            
            # Detect face
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            if len(faces) > 0:
                face_detected = True
                face_detection_count += 1
                face_bbox = faces[0]  # Use first face (numpy array)
                head_rotation = calculate_head_rotation(face_bbox, image_width)
            else:
                face_bbox = None
            
            # Draw center line
            cv2.line(frame, (image_width // 2, 0), (image_width // 2, image_height), (255, 255, 255), 2)
            
            # Draw hand detection
            if hand_bbox is not None:
                x, y, w, h = hand_bbox
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 3)
                cv2.circle(frame, (x + w//2, y + h//2), 10, (0, 255, 0), -1)
                cv2.putText(frame, "HAND", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Draw face detection
            if face_bbox is not None:
                x, y, w, h = face_bbox
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 255), 3)
                # Draw eye line
                eye_y = y + int(h * 0.4)
                cv2.line(frame, (x, eye_y), (x + w, eye_y), (255, 0, 255), 2)
                cv2.putText(frame, "FACE", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)
            
            # Draw steering bar at top (larger, more visible)
            bar_width = 600
            bar_height = 50
            bar_x = (image_width - bar_width) // 2
            bar_y = 20
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (20, 20, 20), -1)
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (255, 255, 255), 3)
            
            # Steering indicator
            center_x = bar_x + bar_width // 2
            indicator_x = int(center_x + steering * (bar_width // 2 - 20))
            color = (0, 255, 0) if abs(steering) < 0.1 else ((255, 0, 0) if steering < 0 else (0, 0, 255))
            cv2.rectangle(frame, (indicator_x - 20, bar_y), (indicator_x + 20, bar_y + bar_height), color, -1)
            cv2.putText(frame, "STEERING", (bar_x + 20, bar_y + 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            
            # Head rotation indicator (below steering bar)
            head_bar_y = bar_y + bar_height + 15
            head_bar_width = 400
            head_bar_x = (image_width - head_bar_width) // 2
            cv2.rectangle(frame, (head_bar_x, head_bar_y), (head_bar_x + head_bar_width, head_bar_y + 40), (20, 20, 20), -1)
            cv2.rectangle(frame, (head_bar_x, head_bar_y), (head_bar_x + head_bar_width, head_bar_y + 40), (200, 200, 200), 2)
            head_indicator_x = int(head_bar_x + head_bar_width // 2 + head_rotation * (head_bar_width // 2))
            cv2.rectangle(frame, (head_indicator_x - 15, head_bar_y), (head_indicator_x + 15, head_bar_y + 40), (0, 255, 255), -1)
            cv2.putText(frame, "HEAD LOOK", (head_bar_x + 15, head_bar_y + 28), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Status text (larger, more visible)
            status_y = head_bar_y + 70
            if hand_detected:
                cv2.putText(frame, f"HAND: Steering={steering:.2f}", (15, status_y), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 3)
            else:
                cv2.putText(frame, "NO HAND - Show hand in lower half", (15, status_y), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 3)
            
            if face_detected:
                cv2.putText(frame, f"HEAD: Rotation={head_rotation:.2f}", (15, status_y + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 255), 3)
            else:
                cv2.putText(frame, "NO FACE DETECTED", (15, status_y + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (100, 100, 100), 3)
            
            # Print debug info every 10 frames
            if frame_count % 10 == 0:
                hand_status = "✓" if hand_detected else "✗"
                face_status = "✓" if face_detected else "✗"
                print(f"[{frame_count:5d}] Hand:{hand_status} | Steering:{steering:+.2f} | Head:{face_status} | Rotation:{head_rotation:+.2f}")
            
            # Send data to server
            if (hand_detected or face_detected) and ws_connected:
                try:
                    message = {
                        "source": "webcam",
                        "steering": float(steering) if hand_detected else 0.0,
                        "head_rotation": float(head_rotation) if face_detected else 0.0
                    }
                    await ws.send(json.dumps(message))
                except:
                    ws_connected = False
                    print("\n⚠️  WebSocket disconnected, continuing in local mode")
            
            # Show frame - MUST be called every frame
            window_name = "VR Racing Control - Hand Steering + Head Look"
            cv2.imshow(window_name, frame)
            
            # Check window creation on first frame
            if not window_created and frame_count == 1:
                try:
                    prop = cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE)
                    if prop >= 0:
                        window_created = True
                        print(f"✅ Window opened! Size: {image_width}x{image_height}")
                        print("💡 Press 'q' to quit")
                except:
                    pass
            
            # Print first frame info
            if frame_count == 1:
                print(f"✅ First frame captured! Size: {image_width}x{image_height}")
            
            # Quit on 'q' or ESC - waitKey MUST be called for window to update
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:
                print("\n🛑 Quitting...")
                break
                    
    except KeyboardInterrupt:
        print("\n\n🛑 Interrupted by user (Ctrl+C)")
    except Exception as e:
        if "Connection" in str(type(e).__name__):
            print(f"\n⚠️  Connection issue (continuing in local mode): {e}")
        else:
            print(f"\n\n❌ Error: {e}")
            print(f"   Processed {frame_count} frames before error")
            import traceback
            traceback.print_exc()
            logger.error(f"Error in CV input: {e}", exc_info=True)
    finally:
        print(f"\n📊 Statistics:")
        print(f"   Total frames: {frame_count}")
        print(f"   Hand detections: {hand_detection_count}")
        print(f"   Face detections: {face_detection_count}")
        if frame_count > 0:
            print(f"   Hand detection rate: {hand_detection_count/frame_count*100:.1f}%")
            print(f"   Face detection rate: {face_detection_count/frame_count*100:.1f}%")
        print("\n🧹 Cleaning up...")
        if cap is not None:
            cap.release()
        cv2.destroyAllWindows()
        logger.info("Cleaned up resources")
        print("✅ Done")

if __name__ == "__main__":
    asyncio.run(send_steering())
