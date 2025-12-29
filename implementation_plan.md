# EasySTAT 环境迁移与部署实施计划

## 目标 (Goal)

将 EasySTAT 项目迁移至名为 `es` 的 Conda 虚拟环境，消除代码中的绝对路径依赖，配置全开放的 CORS 策略，并提供稳健的一键启动脚本，为后续打包 Docker 镜像及服务器部署做好准备。

## 用户审核 (User Review Required)

> [!IMPORTANT] > **路径重构策略**: 我将把所有 `.env` 中的路径修改为相对于项目根目录的路径（例如 `./data/shared`）。后端代码将通过 `os.path.abspath` 动态计算绝对路径，以确保在任何目录下（包括 Docker 容器内）都能正常运行。

> [!WARNING] > **CORS 安全性**: 将 `Access-Control-Allow-Origin` 设置为 `*` (允许所有来源)。这在生产环境中虽然方便调试，但存在安全风险。鉴于这是为了后续部署为独立服务，且通常会有网关/防火墙由于前置，此配置是可接受的。

## 拟定变更 (Proposed Changes)

### 1. 配置文件与路径重构 (Config & Path Refactoring)

#### [MODIFY] [EasySTAT/.env](file:///Users/mac/dev/personal/es1/br_competition/EasySTAT/.env)

- 将 `FINANCIAL_CREW_SRC_PATH`, `TA_ANA_PATH` 等绝对路径修改为相对路径。

#### [MODIFY] [easystat-webui/backend/.env](file:///Users/mac/dev/personal/es1/br_competition/easystat-webui/backend/.env)

- 同样将路径修改为相对路径。
- 增加 `CORS_ORIGINS=["*"]` 配置项。

#### [MODIFY] [easystat-webui/backend/core/config.py](file:///Users/mac/dev/personal/es1/br_competition/easystat-webui/backend/core/config.py)

- 增加逻辑：自动检测环境变量中的相对路径，并基于项目根目录转换为绝对路径（防止子进程/CWD 切换导致的路径错误）。
- 更新 `CORS_ORIGINS` 读取逻辑，支持从环境变量读取通配符配置。

#### [MODIFY] [crawler_tool.py](file:///Users/mac/dev/personal/es1/br_competition/EasySTAT/src/financial_crew/tools/crawler_tool.py)

- 确保工具加载路径时支持相对路径解析。

### 2. Conda 环境构建 (Environment Setup)

#### [NEW] [setup_env.sh](file:///Users/mac/dev/personal/es1/br_competition/setup_env.sh)

- 脚本功能：
  1. 检查 `conda` 是否可用。
  2. 创建名为 `es` 的虚拟环境 (Python 3.10+)。
  3. 激活环境并安装 `EasySTAT/pyproject.toml` 和 `backend/requirements.txt` 中的所有依赖。
  4. 检查并安装 Node.js 依赖 (`npm install`)。

### 3. 一键启动脚本优化 (Startup Script Optimization)

#### [MODIFY] [start.sh](file:///Users/mac/dev/personal/es1/br_competition/start.sh)

- 增加环境激活逻辑：启动前尝试激活 `es` 环境。
- 端口检查：启动前检查 8000 和 50001 端口是否被占用。
- 路径修正：确保脚本无论在哪里执行，都会切换到项目根目录，保证相对路径正确性。
- **允许外部访问**: 确保 `main.py` 和 `vite` 启动参数均绑定 `0.0.0.0`。

## 验证计划 (Verification Plan)

### 自动化验证

1. **环境构建测试**: 运行 `./setup_env.sh`，确认环境 `es` 创建成功且依赖安装无误。
2. **CORS 测试**: 使用 `curl -v -H "Origin: http://example.com" http://localhost:8000` 验证是否返回 `Access-Control-Allow-Origin: *`。

### 手动验证 (Manual Verification)

1. **启动测试**: 运行 `./start.sh`，观察后端和前端是否正常启动，无报错。
2. **功能测试**: 打开浏览器访问 `http://localhost:50001`，发起一个简单的查询（如“查询茅台”），确认前后端通信正常，且 CrewAI 能根据相对路径找到数据文件。
