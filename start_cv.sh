#!/bin/bash
cd /Users/ryleymao/Racing-CV
/Users/ryleymao/Racing-CV/backend/venv/bin/python3 -c "
import sys
sys.path.insert(0, '.')
from backend.services.cv_input import send_steering
import asyncio
asyncio.run(send_steering())
"

