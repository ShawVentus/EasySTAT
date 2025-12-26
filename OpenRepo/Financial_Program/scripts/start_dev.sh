#!/bin/bash
# ========================================
# Financial_Program 本地开发启动脚本
# ========================================
# 功能说明：
#   启动 MySQL 和 Redis Docker 容器，然后启动后端服务。
#
# 使用方法：
#   chmod +x scripts/start_dev.sh
#   ./scripts/start_dev.sh
#
# 前提条件：
#   1. 已安装 Docker 和 Docker Compose
#   2. 已创建 conda br 环境
#   3. 已配置 backend/.env 文件
# ========================================

set -e  # 遇到错误立即退出

echo "========================================="
echo "Financial_Program 本地开发启动"
echo "========================================="

# 获取脚本所在目录的父目录（项目根目录）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"
echo "[1/4] 项目目录: $PROJECT_DIR"

# 检查 .env 文件
if [ ! -f "backend/.env" ]; then
    echo "[警告] backend/.env 文件不存在，正在从模板创建..."
    cp .env.example backend/.env
    echo "[提示] 请编辑 backend/.env 文件，配置 LLM_API_KEY 等参数"
fi

# 启动 Docker 服务
echo "[2/4] 启动 MySQL 和 Redis Docker 容器..."
docker compose -f docker-compose.dev.yml up -d

# 等待 MySQL 就绪
echo "[3/4] 等待 MySQL 启动就绪..."
sleep 10

# 检查服务状态
echo "[检查] Docker 容器状态:"
docker compose -f docker-compose.dev.yml ps

# 启动后端
echo "[4/4] 启动后端服务..."
echo ""
echo "请在新终端中运行以下命令启动后端："
echo "  cd $PROJECT_DIR/backend"
echo "  conda activate br"
echo "  python run.py"
echo ""
echo "请在另一个终端中运行以下命令启动前端："
echo "  cd $PROJECT_DIR/frontend"
echo "  npm install  # 首次运行"
echo "  npm run dev"
echo ""
echo "========================================="
echo "服务地址："
echo "  前端: http://localhost:5173"
echo "  后端 API: http://localhost:8000/docs"
echo "  MySQL: localhost:3306"
echo "  Redis: localhost:6379"
echo "========================================="
