#!/bin/bash
# ==========================================
# EasySTAT Docker 容器启动脚本
# ==========================================
set -e

echo "=== EasySTAT Docker 容器启动 ==="

# 设置 Python 路径
export PYTHONPATH="/app/EasySTAT/src:/app/crawler:$PYTHONPATH"

# 加载 EasySTAT 环境变量
if [ -f /app/EasySTAT/.env ]; then
    echo "加载环境变量: /app/EasySTAT/.env"
    set -a
    source /app/EasySTAT/.env
    set +a
fi

# 打印环境信息
echo "Python 路径: $PYTHONPATH"
echo "数据目录: $DATA_BUS_PATH"
echo "结果目录: $REPORT_OUTPUT_DIR"

echo "启动 EasySTAT WebUI 服务 (Port 50001)..."
cd /app/easystat-webui/backend
exec python -m uvicorn main:app --host 0.0.0.0 --port 50001
