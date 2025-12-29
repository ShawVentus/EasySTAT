# EasySTAT 跨服务器迁移部署指南

本指南详细说明了如何将 EasySTAT 项目从开发环境迁移并部署到新的 Linux/macOS 服务器。

## 1. 环境准备 (Prerequisites)

在目标服务器上，请确保安装以下基础软件：

- **Git**: 用于拉取代码
- **Miniconda / Anaconda**: 强烈推荐用于管理 Python 环境
- **Node.js (v18+)**: 用于前端构建
- **npm / yarn**: Node 包管理工具

## 2. 代码获取

## 3. 自动化安装 (Automated Installation)

**推荐使用一键安装脚本**，它会自动创建 Conda 环境 (`es`) 并安装所有前后端依赖。

```bash
chmod +x setup_env.sh
./setup_env.sh
```

该脚本会自动执行以下操作：

1. 检查 Conda 是否安装。
2. 创建名为 `es` 的 Python 3.10 环境。
3. 安装 CrewAI、AKShare、FastAPI 等核心 Python 库。
4. 安装前端 Node.js 依赖。

---

## 4. 核心配置 (Configuration)

### 4.1 环境变量 (.env)

项目已重构为**默认使用相对路径**，通常**无需**手动修改路径配置即可运行。

1. **EasySTAT/.env** (LLM 与核心配置)

   - 复制模板：`cp EasySTAT/.env.example EasySTAT/.env` (如已有则跳过)
   - **必填项**: 只需要配置 LLM API Key，例如 `OPENAI_API_KEY`、`OPENAI_API_BASE` 等。
   - **路径项**: 已默认为相对路径（如 `./src`），无需修改，除非您有特殊需求。
   - **已废弃**: `FINANCIAL_PROGRAM_BACKEND_PATH` (不再需要外部爬虫依赖)。

2. **easystat-webui/backend/.env** (后端配置)
   - 复制模板：`cp easystat-webui/backend/.env.example easystat-webui/backend/.env`
   - **跨域 (CORS)**: 默认为 `CORS_ORIGINS=["*"]`，允许所有来源访问。
   - **项目路径**: 默认为 `EASYSTAT_PROJECT_PATH=../../EasySTAT`，无需修改。

---

## 5. 一键启动 (Startup)

安装完成后，直接运行启动脚本：

```bash
chmod +x start.sh
./start.sh
```

脚本功能：

- 自动激活 `es` Conda 环境。
- 自动检查端口 (8000, 50001) 是否被占用。
- 启动后端 API 服务 (绑定 `0.0.0.0:8000`)。
- 启动前端 Web 服务 (绑定 `0.0.0.0:50001`)。

成功启动后，您可以通过浏览器访问：

- **前端页面**: `http://<服务器IP>:50001`
- **后端文档**: `http://<服务器IP>:8000/docs`

---

## 6. 常见问题排查

1.  **ModuleNotFoundError (e.g., 'financial_crew')**:

    - 请确保是通过 `./start.sh` 启动的，因为它会自动激活正确的 Conda 环境并设置 `PYTHONPATH`。
    - 如果手动启动，请务必先 `conda activate es`。

2.  **端口冲突**:

    - 如果 50001 端口被占用，启动脚本会提示警告。您可以修改前端 `vite.config.ts` 中的端口配置。

3.  **数据采集失败**:
    - 确保 `EasySTAT/.env` 中的 `OPENAI_API_KEY` 有效且余额充足。
    - 资金流数据现已使用 `akshare` 接口，无需配置外部爬虫路径。
