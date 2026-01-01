#!/bin/bash

# Fix MediaPipe installation issue

echo "🔧 Fixing MediaPipe installation..."
echo ""

cd backend
source venv/bin/activate

echo "📦 Uninstalling old MediaPipe..."
pip uninstall mediapipe -y

echo "📥 Installing MediaPipe..."
pip install mediapipe

echo ""
echo "✅ MediaPipe reinstalled!"
echo ""
echo "🧪 Testing import..."
python3 -c "import mediapipe as mp; print('✅ MediaPipe OK'); print(f'Has solutions: {hasattr(mp, \"solutions\")}')"

echo ""
echo "✅ Done! Try running: python3 run_cv.py"

