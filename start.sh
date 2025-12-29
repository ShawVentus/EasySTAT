#!/bin/bash
# EasySTAT 一键启动脚本

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== 启动 EasySTAT 服务 ===${NC}"

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 检查端口占用
check_port() {
    local port=$1
    if lsof -i :$port > /dev/null; then
        echo -e "${BLUE}警告: 端口 $port 似乎已被占用，这可能导致启动失败。${NC}"
        # 可选：这里可以添加自动 kill 逻辑，但为了安全起见先仅提示
    fi
}

check_port 8000
check_port 50001

# 尝试激活 Conda 环境 'es'
source "$(conda info --base)/etc/profile.d/conda.sh" 2>/dev/null
if conda env list | grep -q "es"; then
    echo -e "${GREEN}正在激活 Conda 环境 'es'...${NC}"
    conda activate es
else
    echo -e "${BLUE}警告: 未找到环境 'es'，将使用当前环境: $CONDA_DEFAULT_ENV${NC}"
    echo "建议运行 ./setup_env.sh 进行自动配置"
fi

# 1. 启动后端（内部端口 8000）
echo -e "${GREEN}[Backend] 正在启动 FastAPI 服务 (Port 8000)...${NC}"
cd easystat-webui/backend || { echo "找不到后端目录"; exit 1; }
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
PID_BACKEND=$!
echo "Backend PID: $PID_BACKEND"
cd "$SCRIPT_DIR"

# 等待后端端口就绪 (简单探测)
echo "等待后端启动..."
sleep 3

# 2. 启动前端（暴露端口 50001）
echo -e "${GREEN}[Frontend] 正在启动 React 前端 (Port 50001)...${NC}"
cd easystat-webui/frontend || { echo "找不到前端目录"; exit 1; }
# 确保绑定到 0.0.0.0 允许外部访问
npm run dev -- --port 50001 --host 0.0.0.0 &
PID_FRONTEND=$!
echo "Frontend PID: $PID_FRONTEND"
cd "$SCRIPT_DIR"

echo -e "${BLUE}=== 服务已启动 ===${NC}"
echo -e "后端 API: http://localhost:8000"
echo -e "前端页面: http://localhost:50001  (或 http://服务器IP:50001)"
echo -e "${BLUE}按 Ctrl+C 停止所有服务${NC}"

# 捕获退出信号，清理子进程
trap "kill $PID_BACKEND $PID_FRONTEND 2>/dev/null; exit" SIGINT SIGTERM

# 等待子进程
wait
