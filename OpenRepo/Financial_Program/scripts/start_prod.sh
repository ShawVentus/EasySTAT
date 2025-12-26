#!/bin/bash
# ========================================
# Financial_Program 远程服务器生产启动脚本
# ========================================
# 功能说明：
#   在远程无头服务器上启动完整的生产服务。
#   后端以 nohup 方式后台运行。
#
# 使用方法：
#   chmod +x scripts/start_prod.sh
#   ./scripts/start_prod.sh
#
# 前提条件：
#   1. 已安装 Docker
#   2. 已安装 Miniconda 并创建 br 环境
#   3. 已配置 backend/.env 文件
#   4. 已构建前端静态文件 (npm run build)
# ========================================

set -e  # 遇到错误立即退出

echo "========================================="
echo "Financial_Program 生产环境启动"
echo "========================================="

# 获取脚本所在目录的父目录（项目根目录）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"
echo "[1/5] 项目目录: $PROJECT_DIR"

# 检查 .env 文件
if [ ! -f "backend/.env" ]; then
    echo "[错误] backend/.env 文件不存在！"
    echo "[提示] 请先配置: cp .env.example backend/.env && vim backend/.env"
    exit 1
fi

# 启动 Docker 服务
echo "[2/5] 启动 MySQL 和 Redis Docker 容器..."
docker compose -f docker-compose.dev.yml up -d

# 等待 MySQL 就绪
echo "[3/5] 等待 MySQL 启动就绪..."
sleep 15

# 检查服务状态
echo "[检查] Docker 容器状态:"
docker compose -f docker-compose.dev.yml ps

# 检查是否有旧进程在运行
echo "[4/5] 检查后端进程..."
if pgrep -f "python run.py" > /dev/null; then
    echo "[警告] 发现后端进程正在运行，正在停止..."
    pkill -f "python run.py" || true
    sleep 2
fi

# 激活 conda 环境并启动后端
echo "[5/5] 启动后端服务（后台运行）..."
source ~/miniconda3/bin/activate br 2>/dev/null || source ~/anaconda3/bin/activate br 2>/dev/null || {
    echo "[错误] 无法激活 conda br 环境"
    exit 1
}

cd "$PROJECT_DIR/backend"

# 确保日志目录存在
mkdir -p /var/log 2>/dev/null || mkdir -p "$PROJECT_DIR/logs"
LOG_FILE="${PROJECT_DIR}/logs/backend.log"

# 后台启动
nohup python run.py > "$LOG_FILE" 2>&1 &
BACKEND_PID=$!

echo ""
echo "========================================="
echo "生产环境启动完成！"
echo "========================================="
echo "后端 PID: $BACKEND_PID"
echo "后端日志: $LOG_FILE"
echo ""
echo "服务地址："
echo "  后端 API: http://<服务器IP>:8000/docs"
echo "  MySQL: localhost:3306"
echo "  Redis: localhost:6379"
echo ""
echo "常用命令："
echo "  查看日志: tail -f $LOG_FILE"
echo "  停止后端: pkill -f 'python run.py'"
echo "  停止 Docker: docker compose -f docker-compose.dev.yml down"
echo "========================================="
