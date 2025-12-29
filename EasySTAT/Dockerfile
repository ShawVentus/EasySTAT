# ==========================================
# EasySTAT Docker 镜像 - 多阶段构建
# ==========================================
# 说明：此 Dockerfile 需要从 br_competition 根目录构建
# 构建命令：docker build -f EasySTAT/Dockerfile -t easystat:latest .

# ---------- 阶段 1: 前端构建 ----------
FROM node:18-alpine AS frontend-builder

WORKDIR /build

# 复制 package.json 优先（利用 Docker 缓存）
COPY easystat-webui/frontend/package*.json ./
RUN npm ci --registry=https://registry.npmmirror.com

# 复制前端源码并构建
COPY easystat-webui/frontend/ ./
RUN npm run build

# ---------- 阶段 2: 后端运行时 ----------
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖（编译某些 Python 包需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装
COPY EasySTAT/requirements.docker.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制 EasySTAT 核心项目
COPY EasySTAT/ ./EasySTAT/

# 使用 .env.docker 作为容器内的 .env
COPY EasySTAT/.env.docker ./EasySTAT/.env

# 直接复制原有 crawler 目录（不做任何修改）
COPY OpenRepo/Financial_Program/backend/crawler/ ./crawler/

# 复制 WebUI 后端
COPY easystat-webui/backend/ ./easystat-webui/backend/

# 使用 Docker 版本的 .env
COPY easystat-webui/backend/.env.docker ./easystat-webui/backend/.env

# 复制前端构建产物到后端 static 目录
COPY --from=frontend-builder /build/dist ./easystat-webui/backend/static

# 复制启动脚本
COPY EasySTAT/start.sh ./
RUN chmod +x start.sh

# 创建数据目录
RUN mkdir -p /app/EasySTAT/data/shared \
    /app/EasySTAT/data/cache \
    /app/EasySTAT/result \
    /app/EasySTAT/logs

# 设置工作目录
WORKDIR /app/easystat-webui/backend

# 暴露端口
EXPOSE 50001

# 启动命令
CMD ["/app/start.sh"]
