#!/bin/bash
# EasySTAT 一键启动脚本

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== 启动 EasySTAT 无头系统迁移版 ===${NC}"

# 检查 Conda 环境 (可选)
if [[ -n "$CONDA_DEFAULT_ENV" ]]; then
    echo -e "${BLUE}当前 Conda 环境: $CONDA_DEFAULT_ENV${NC}"
fi

# 1. 启动后端
echo -e "${GREEN}[Backend] 正在启动 FastAPI 服务 (Port 8000)...${NC}"
cd easystat-webui/backend || { echo "找不到后端目录"; exit 1; }
# 使用 nohup 或直接后台运行
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
PID_BACKEND=$!
echo "Backend PID: $PID_BACKEND"
cd ../..

# 等待几秒确保后端开始启动
sleep 2

# 2. 启动前端
echo -e "${GREEN}[Frontend] 正在启动 React 前端 (Port 50001)...${NC}"
cd easystat-webui/frontend || { echo "找不到前端目录"; exit 1; }
# 传递 --port 50001 --host 0.0.0.0 参数给 Vite
npm run dev -- --port 50001 --host 0.0.0.0 &
PID_FRONTEND=$!
echo "Frontend PID: $PID_FRONTEND"
cd ../..

echo -e "${BLUE}=== 服务已启动 ===${NC}"
echo -e "后端 API: http://localhost:8000"
echo -e "前端页面: http://localhost:50001"
echo -e "${BLUE}按 Ctrl+C 停止所有服务${NC}"

# 捕获退出信号，清理子进程
trap "kill $PID_BACKEND $PID_FRONTEND; exit" SIGINT SIGTERM

# 等待子进程
wait
