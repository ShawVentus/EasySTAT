# EasySTAT 迁移与部署指南

这份文档旨在指导将 EasySTAT 系统（包含核心逻辑、后端 API 和前端界面）部署到新的无头（Serverless/Headless）或独立服务器环境。

## 1. 系统要求 (System Requirements)

在开始部署之前，请确保目标环境满足以下要求：

- **Operating System**: Linux (Recommended), macOS, or Windows
- **Python**: Version 3.10 或更高版本 (但低于 3.14)
- **Node.js**: Version 18+ (推荐使用 LTS 版本)
- **npm**: 通常随 Node.js 安装
- **Git**: 用于代码拉取
- **Internet Access**: 用于下载依赖包 (PyPI, npm)

## 2. 项目结构概览 (Project Structure)

本项目是一个 Monorepo 结构，主要包含三个部分：

- `EasySTAT/`: **核心业务逻辑**。包含基于 CrewAI 的多智能体系统、金融数据分析工具 (AkShare) 等。
- `easystat-webui/backend/`: **后端服务**。基于 FastAPI，提供 REST API 和 SSE 实时流服务，用于调用核心逻辑并返回结果。
- `easystat-webui/frontend/`: **前端界面**。基于 React + Vite + TypeScript，提供用户交互界面。

## 3. 安装步骤 (Installation Steps)

请按照顺序执行以下安装步骤。

### 第一步：安装核心依赖 (EasySTAT Core)

首先配置核心模块及其依赖。

1.  进入核心目录：

    ```bash
    cd EasySTAT
    ```

2.  安装核心依赖（建议在虚拟环境如 conda 或 venv 中进行）：

    ```bash
    # 如果有 pyproject.toml 支持的安装方式
    pip install .

    # 或者直接安装 pyproject.toml 中列出的主要依赖
    pip install "crewai[tools]==1.7.2" "akshare>=1.13.0" "tenacity>=8.2.0" "joblib>=1.3.0"
    ```

    _注意：请根据实际情况创建 `.env` 文件配置 API Key（如 OpenAI, Serper 等）到 `EasySTAT/.env` 或系统环境变量中。_

### 第二步：安装后端服务 (Backend)

1.  进入后端目录：

    ```bash
    cd ../easystat-webui/backend
    ```

2.  安装后端依赖：

    ```bash
    pip install -r requirements.txt
    ```

3.  配置环境变量：
    复制 `.env.example` 为 `.env` 并根据需要修改：
    ```bash
    cp .env.example .env
    ```
    确保 `.env` 中的配置指向正确的路径或服务端口。

### 第三步：安装前端依赖 (Frontend)

1.  进入前端目录：

    ```bash
    cd ../frontend
    ```

2.  （可选）使用淘宝镜像加速 npm：

    ```bash
    npm config set registry https://registry.npmmirror.com
    ```

3.  安装依赖：

    ```bash
    npm install
    # 或者使用 pnpm (如果已安装)
    # pnpm install
    ```

4.  构建生产环境代码（如果是部署到生产环境）：
    ```bash
    npm run build
    ```
    构建产物将位于 `dist/` 目录下。

## 4. 快速启动 (Quick Start)

我们提供了一个一键启动脚本，可以同时启动后端 (Port 8000) 和前端 (Port 50001)，并监听所有网络接口 (0.0.0.0)，以便从外部访问。

在项目根目录下执行：

```bash
bash start.sh
```

服务启动后，请访问：**http://<服务器 IP>:50001**

## 5. 手动启动服务 (Manual Start)

如果您需要分别调试，可以使用以下命令：

### 启动后端 (Backend)

在 `easystat-webui/backend` 目录下：

```bash
# 开发模式 (带有热重载，监听所有接口)
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

后端服务将在 `http://0.0.0.0:8000` (或服务器 IP) 上启动。

### 启动前端 (Frontend)

在 `easystat-webui/frontend` 目录下：

```bash
# 指定端口并监听所有接口
npm run dev -- --port 50001 --host 0.0.0.0
```

**或者构建后运行**：
Nginx 配置示例 (简化版):

```nginx
server {
    listen 50001;
    server_name your_domain.com;

    location / {
        root /path/to/easystat-webui/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # 代理 API 请求到后端
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 6. 验证部署 (Verification)

1.  访问前端地址（如 `http://localhost:50001`）。
2.  确保页面加载正常，无报错。
3.  尝试发起一个简单的任务（如“查询某股票数据”），观察后端日志是否有响应，以及前端是否能实时收到 SSE 推送的消息。
