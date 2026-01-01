#!/usr/bin/env python3
"""
Simple runner script for CV input.
Run this from project root: python3 run_cv.py
"""
import sys
import os
from pathlib import Path

# Check if we're using venv Python
venv_python = Path(__file__).parent / "backend" / "venv" / "bin" / "python3"
using_venv = sys.executable == str(venv_python) or 'venv' in sys.executable

if not using_venv and venv_python.exists():
    print("⚠️  Not using venv Python!")
    print(f"   Current: {sys.executable}")
    print(f"   Should use: {venv_python}")
    print(f"\n💡 Run: {venv_python} run_cv.py")
    print("   Or activate venv first: source backend/venv/bin/activate")
    sys.exit(1)

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Check if we can import
try:
    from backend.services.cv_input import send_steering
    import asyncio
    print("✅ Imports OK")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("\n💡 Make sure you:")
    print("   1. Activate virtual environment: cd backend && source venv/bin/activate")
    print("   2. Install dependencies: pip install -r requirements.txt")
    sys.exit(1)

# Check if server is running
try:
    import urllib.request
    urllib.request.urlopen('http://localhost:8000/health', timeout=2)
    print("✅ Server is running")
except:
    print("⚠️  Server doesn't seem to be running on port 8000")
    print("   Start it with: uvicorn backend.main:app --host 0.0.0.0 --port 8000")
    print("   Continuing anyway...\n")

# Run
if __name__ == "__main__":
    print("\n🚀 Starting Face Tracking CV Input...\n")
    try:
        asyncio.run(send_steering())
    except KeyboardInterrupt:
        print("\n\n✅ Shutdown complete")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

