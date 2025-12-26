# EasySTAT 跨服务器迁移部署指南

本指南详细说明了如何将 EasySTAT 项目从开发环境迁移并部署到新的 Linux/macOS 服务器。

## 1. 环境准备 (Prerequisites)

在目标服务器上，请确保安装以下基础软件：

- **Git**: 用于拉取代码
- **Miniconda / Anaconda**: 强烈推荐用于管理 Python 环境
- **Node.js (v18+)**: 用于前端构建
- **npm / yarn**: Node 包管理工具

## 2. 代码获取

```bash
# 1. 拉取代码到目标目录
git clone <你的GitHub仓库地址> EasySTAT_Project
cd EasySTAT_Project
```

## 3.后端与核心环境配置 (Backend Setup)

建议使用 Conda 创建隔离环境：

```bash
# 1. 创建并激活环境
# 提示：如果使用 bash，请确保 conda init 已初始化
conda create -n easystat python=3.10 -y
conda activate easystat

# 2. 安装核心逻辑依赖
cd EasySTAT
# 安装 CrewAI 及其工具
pip install "crewai[tools]==1.7.2"
# 安装其他核心库
pip install "akshare>=1.13.0" "tenacity>=8.2.0" "joblib>=1.3.0" "pymysql"
# 如果使用了 pandas, numpy 等，通常会被自动依赖安装

# 3. 配置核心环境变量 (关键一步！)
# 注意：.env 文件通常不随 git 提交，需要手动创建
cp .env.example .env 2>/dev/null || touch .env
# 编辑 .env 文件，务必修改以下绝对路径为服务器上的实际路径
nano .env
```

**EasySTAT/.env 配置重点：**
请检查并修改以下路径（务必将 `/Users/mac/dev/personal/br_competition` 替换为服务器实际路径）：

- `FINANCIAL_CREW_SRC_PATH`: `<项目根目录>/EasySTAT/src`
- `TA_ANA_PATH`: `<项目根目录>/OpenRepo/ta_ana`
- `ARCH_MODEL_PATH`: `<项目根目录>/OpenRepo/arch_model`
- `FINANCIAL_PROGRAM_BACKEND_PATH`: `<项目根目录>/OpenRepo/Financial_Program/backend`
- `AKSHARE_CACHE_PATH`: `<项目根目录>/EasySTAT/data/cache`
- `DATA_BUS_PATH`: 建议使用相对路径 `./data/shared`
- `OPENAI_API_KEY` 等 LLM 配置：填入有效的 API Key

```bash
# 4. 安装后端 Web 服务依赖
cd ../easystat-webui/backend
pip install -r requirements.txt

# 5. 配置后端环境变量
cp .env.example .env
nano .env
```

**backend/.env 配置重点：**

- 确保 `EASYSTAT_PROJECT_PATH` 等路径正确（如果是相对路径 `../../EasySTAT` 则通常无需修改）。

## 4. 前端环境配置 (Frontend Setup)

```bash
cd ../frontend

# 1. 安装依赖
npm install

# 2. (正式部署无需此步，仅开发需要)
# 如果只是想跑起来看效果，可以直接用 dev 模式（start.sh 默认使用 dev 模式）
```

## 5. 一键启动

回到项目根目录：

```bash
cd ../..
chmod +x start.sh
./start.sh
```

- **后端** 将启动在 `http://0.0.0.0:8000`
- **前端** 将启动在 `http://0.0.0.0:50001`

确保服务器防火墙已放行 **8000** 和 **50001** 端口。

## 6. 常见问题排查

1.  **路径错误**：如果报错 "File not found"，请第一时间检查 `EasySTAT/.env` 和 `easystat-webui/backend/.env` 中的绝对路径是否已更新为当前服务器路径。
2.  **依赖缺失**：如果报错 "Module not found"，请在 conda 环境下重新 pip install 对应模块。
3.  **端口冲突**：如果 8000 或 50001 被占用，请修改 `start.sh` 和对应的 `.env` (前端 vite config) 配置。
