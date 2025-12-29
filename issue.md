# EasySTAT 部署与修复日志 (Deployment & Refactoring Log)

本文档详细记录了将 EasySTAT 项目从零部署到新环境（Conda `es`）的全过程，以及期间进行的架构重构和 Bug 修复。

## 1. 自动化环境构建 (Environment Setup)

### 1.1 Conda 环境脚本 (`setup_env.sh`)

为解决依赖安装繁琐的问题，创建了自动化部署脚本。

- **功能**:
  - 自动检测并创建 Conda 虚拟环境 `es` (Python 3.10)。
  - 自动安装 `EasySTAT/pyproject.toml` 中的核心依赖（CrewAI, AKShare 等）。
  - 自动安装后端 (`backend/requirements.txt`) 和前端 (`package.json`) 依赖。
  - 处理了 `requirements.txt` 中因文档字符串导致的安装错误。

### 1.2 启动脚本优化 (`start.sh`)

- **改进点**:
  - **自动环境激活**: 启动前自动激活 `es` 环境，无需用户手动操作。
  - **端口冲突检测**: 启动前检查 8000 和 50001 端口占用情况。
  - **外部访问支持**: 强制将后端 (`uvicorn`) 和前端 (`vite`) 绑定到 `0.0.0.0`，确保局域网或公网可访问。

## 2. 核心架构重构 (Core Architecture Refactoring)

### 2.1 消除绝对路径 (Path Refactoring)

原项目大量使用了硬编码的绝对路径（如 `/Users/mac/dev/...`），导致无法在其他机器或 Docker 中运行。

- **修改内容**:
  - **`.env` 文件**: 将 `config.env` 和 `backend/.env` 中的所有绝对路径修改为相对路径（如 `../../EasySTAT`）。
  - **`config.py`**: 增加了动态路径解析逻辑。利用 `os.path.abspath(__file__)` 自动定位项目根目录，无论项目部署在哪里，都能正确找到资源。
  - **修复逻辑缺陷**: 修正了 `config.py` 中 `_backend_dir` 计算时多了一层 `dirname` 的 Bug，确保能正确导航到 `EasySTAT` 目录。
  - **`executor.py`**: 优化了 `sys.path` 注入逻辑，确保在执行 CrewAI 时能正确加载 `EasySTAT/src` 模块。

### 2.2 跨域与网络配置 (CORS & Network)

- **问题**: 前端 (50001) 无法调用后端 (8000) 接口。
- **解决方案**:
  - 后端 `.env` 新增 `CORS_ORIGINS=["*"]`。
  - `config.py` 和 `main.py` 更新代码，支持读取环境变量并允许所有来源 (`*`) 的跨域请求。

## 3. 关键 Bug 修复 (Critical Bug Fixes)

### 3.1 移除脆弱的外部爬虫依赖 (Refactoring CrawlerTool)

- **问题**: 运行时报错 `ModuleNotFoundError: "crawler"` 或无法导入 `financial_crew`。
- **根源**:
  - 代码依赖一个项目外部的兄弟目录 `OpenRepo/Financial_Program`，这在独立部署时不仅文件缺失，且路径解析极易出错。
  - 原有的动态路径注入逻辑 (`sys.path.append`) 脆弱且难以维护。
- **解决方案 (Refactor)**:
  - **重写 `CrawlerTool`**: 彻底移除了对外部 `crawler` 模块的引用。
  - **集成标准库**: 改用 **AKShare** 标准库直接获取资金流数据。
    - 个股资金流: `ak.stock_fund_flow_individual(symbol="即时")`
    - 板块资金流: `ak.stock_sector_fund_flow_rank(indicator="今日")`
  - **成效**: 仅仅修改约 30 行代码，彻底解决了模块丢失问题，并显著提升了数据采集的稳定性和代码的可移植性。

## 4. 最终状态 (Final Status)

- **服务状态**: 后端与前端均能正常启动并通信。
- **功能验证**: 输入“分析茅台股票”，全流程（搜索 -> 资金流采集 -> K 线获取 -> 宏观数据 -> 指标计算）均已跑通。
- **可移植性**: 项目现在是自包含的 (Self-contained)，可以直接打包成 Docker 镜像或分发给其他用户，无需配置复杂的外部路径。
