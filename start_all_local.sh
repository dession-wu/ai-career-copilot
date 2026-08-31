#!/bin/zsh
# 本地联调：同一进程组内启动 backend(8000) 与 frontend(3001)
BACKEND_DIR="/Users/wuye.ori/Desktop/joyCode/ai-career-copilot/backend"
FRONTEND_DIR="/Users/wuye.ori/Desktop/joyCode/ai-career-copilot/frontend"

cd "$BACKEND_DIR"
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACK_PID=$!
echo "backend started, pid=$BACK_PID"

cd "$FRONTEND_DIR"
source ~/.nvm/nvm.sh
npm run start &
FRONT_PID=$!
echo "frontend started, pid=$FRONT_PID"

trap 'kill $BACK_PID $FRONT_PID 2>/dev/null' EXIT
wait