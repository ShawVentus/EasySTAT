#!/bin/bash

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== 启动 EasySTAT WebUI 服务 ===${NC}"

# 检查 Conda 环境
if [[ "$CONDA_DEFAULT_ENV" != "br" ]]; then
    echo -e "${BLUE}提示: 建议在 'br' Conda 环境下运行此脚本${NC}"
    # 不强制退出，因为用户可能手动配置了环境
fi

# 启动后端
echo -e "${GREEN}[Backend] 正在启动 FastAPI 服务 (Port 8000)...${NC}"
cd backend
python -m uvicorn main:app --reload --port 8000 &
PID_BACKEND=$!
cd ..

# 等待几秒确保后端开始启动
sleep 2

# 启动前端
echo -e "${GREEN}[Frontend] 正在启动 React 开发服务器...${NC}"
cd frontend
npm run dev &
PID_FRONTEND=$!
cd ..

echo -e "${BLUE}=== 服务已启动 ===${NC}"
echo -e "后端 API: http://localhost:8000"
echo -e "前端页面: http://localhost:5173"
echo -e "${BLUE}按 Ctrl+C 停止所有服务${NC}"

# 捕获退出信号，清理子进程
trap "kill $PID_BACKEND $PID_FRONTEND; exit" SIGINT SIGTERM

# 等待子进程
wait
