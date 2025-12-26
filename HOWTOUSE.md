# EasySTAT 操作指南

欢迎使用优化后的 EasySTAT 金融分析系统！本项目已通过并发采集、数据总线协议及自动化任务编排，实现了性能与稳定性的全面提升。

## 🚀 快速启动

### 1. 启动后端 (FastAPI)

```bash
cd /Users/mac/dev/personal/br_competition/easystat-webui/backend
conda activate br
python -m uvicorn main:app --reload --port 8000
```

### 2. 启动前端 (React + Vite)

```bash
cd /Users/mac/dev/personal/br_competition/easystat-webui/frontend
npm run dev
```

---

## ⚙️ 性能配置 (.env)

您可以通过修改根目录下的 `.env` 文件来调整系统性能：

- `MAX_MACRO_CONCURRENT`: 宏观数据采集的最大并发数（建议 3-5）。
- `MAX_STOCK_CONCURRENT`: 股票 K 线采集的最大并发数（建议 5-10）。
- `AKSHARE_CACHE_PATH`: 本地缓存路径，建议使用绝对路径以提高稳定性。

---

## 📊 数据管理

### 1. 数据总线 (DataBus)

系统采用统一的数据总线协议，所有采集工具（Crawler, OHLCV, Macro）都会将大数据存入 `data/shared` 目录，并仅在工具间传递轻量级的 `data_ref` 引用。这有效避免了 LLM 上下文溢出和数据截断问题。

### 2. 自动存盘报告

每次执行完成后，系统会自动在 `result/` 目录下生成一份带时间戳的 Markdown 分析报告，例如：
`result/report_20251226_002010.md`

---

## 🧪 验证与测试

如果您需要手动验证核心逻辑，可以使用以下脚本：

- **全链路验证**: `tests/12.26_0010_Phase7_Logic_Optimization/test_flow.py`
- **宏观并发验证**: `tests/12.26_0015_Phase7_Macro_Optimization/test_macro.py`

---

## 🛠️ 常见问题

- **导入错误**: 请确保已激活 `conda br` 环境。
- **采集失败**: 检查网络连接或 API 限制。系统已内置自动重试与降级机制，单个指标失败不会中断整体流程。
