# 多智能体金融分析平台

基于 CrewAI 框架的多智能体金融分析系统，集成资金流采集、技术指标分析和波动率建模功能。

## 🎯 项目特色

- **多智能体协作**：4 个专业 Agent（数据采集、数据分析、建模分析、报告生成）协同工作
- **智能编排**：基于 CrewAI Flow 的事件驱动工作流
- **模块化设计**：工具层层封装，易于扩展
- **Web 界面**：React + FastAPI 前后端分离架构
- **实时分析**：支持资金流实时采集和技术指标计算

## 📦 系统架构

```
br_competition/financial_crew/          # CrewAI 项目
├── src/financial_crew/
│   ├── tools/                          # 工具集
│   │   ├── crawler_tool.py             # 资金流采集
│   │   ├── ohlcv_tool.py               # K线数据（预留）
│   │   ├── ta_tool.py                  # 技术指标计算
│   │   └── arch_tool.py                # 波动率建模
│   ├── flows/                          # Flow 编排
│   │   └── analysis_flow.py
│   ├── config/                         # 配置文件
│   │   ├── agents.yaml                 # Agent 定义
│   │   └── tasks.yaml                  # Task 定义
│   └── crew.py                         # Crew 主入口
└── tests/                              # 测试脚本

Financial_Program/                      # 前后端项目
├── backend/
│   └── api/crew_api.py                 # CrewAI API 接口
└── frontend/
    └── src/pages/
        ├── DataAnalysis.tsx            # 数据分析页面
        └── ModelAnalysis.tsx           # 建模分析页面
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 激活 conda 环境
conda activate br

# 安装 Python 依赖
pip install crewai ta arch pydantic python-dotenv fastapi uvicorn

# 安装前端依赖
cd /Users/mac/dev/personal/easystat/OpenRepo/金融/Financial_Program/frontend
npm install
```

### 2. 配置环境变量

编辑 `financial_crew/.env`：

```env
# LLM 配置
OPENAI_API_KEY=your-api-key
OPENAI_API_BASE=https://openapi.dp.tech/openapi/v1
OPENAI_MODEL_NAME=qwen-plus

# 路径配置（已自动设置，无需修改）
FINANCIAL_CREW_SRC_PATH=/path/to/financial_crew/src
TA_ANA_PATH=/path/to/ta_ana
ARCH_MODEL_PATH=/path/to/arch_model
FINANCIAL_PROGRAM_BACKEND_PATH=/path/to/Financial_Program/backend
```

### 3. 启动后端

```bash
cd /Users/mac/dev/personal/easystat/OpenRepo/金融/Financial_Program/backend
conda activate br
python run.py
```

后端启动在 `http://localhost:8000`

### 4. 启动前端

```bash
cd /Users/mac/dev/personal/easystat/OpenRepo/金融/Financial_Program/frontend
npm run dev
```

前端启动在 `http://localhost:5173`

### 5. 使用系统

1. 打开浏览器访问 `http://localhost:5173`
2. 点击顶部菜单的 "数据分析" 或 "建模分析"
3. 输入分析目标，例如："分析贵州茅台的资金流和技术指标"
4. 等待多智能体团队协作完成分析
5. 查看结构化报告和数据可视化

## 🧪 测试功能

### 工具单元测试

```bash
cd financial_crew

# 测试资金流采集
python tests/test_crawler_tool.py

# 测试技术指标计算
python tests/test_ta_tool.py

# 测试波动率建模
python tests/test_arch_tool.py

# 测试 Flow 端到端
python tests/test_flow_simple.py
```

### API 测试

```bash
# 测试 CrewAI API
curl -X POST http://localhost:8000/api/crew/analyze \
  -H "Content-Type: application/json" \
  -d '{"query": "分析工业富联"}'
```

## 📖 核心功能

### 1. 数据采集

- **CrawlerTool**：采集东方财富资金流数据
  - 个股资金流（主力/散户净流入）
  - 板块资金流
  - 支持多时间周期（今日/3 日/5 日/10 日）

### 2. 技术分析

- **TATool**：计算常用技术指标
  - RSI（相对强弱指标）
  - MACD（指数平滑异同移动平均线）
  - 布林带（Bollinger Bands）
  - ATR（平均真实波幅）

### 3. 波动率建模

- **ArchTool**：GARCH(1,1) 波动率建模
  - 条件波动率预测
  - 模型参数估计（omega, alpha, beta）
  - 对数似然值

### 4. 智能报告生成

- 综合资金流、技术面、风险评估
- Markdown 格式结构化报告
- 自动提取投资建议

## 🛠️ API 接口

### POST /api/crew/analyze

触发多智能体分析

**请求体：**

```json
{
  "query": "分析贵州茅台"
}
```

**响应：**

```json
{
  "success": true,
  "report": "综合分析报告...",
  "data": {
    "capital_flow": [...],
    "technical_indicators": {...},
    "volatility_data": {...}
  }
}
```

## ⚙️ Agent 说明

1. **Data Collector（数据采集专家）**

   - 采集资金流数据
   - 获取 K 线数据（预留）

2. **Data Analyst（数据分析师）**

   - 计算技术指标
   - 分析资金流向

3. **Model Analyst（量化建模专家）**

   - GARCH 波动率建模
   - 风险评估

4. **Report Generator（投研报告专家）**
   - 综合多源信息
   - 生成结构化报告

## 🔧 故障排查

### 问题 1：CrewAI 导入失败

```bash
pip install crewai
```

### 问题 2：LLM API Key 无效

检查 `.env` 文件中的 `OPENAI_API_KEY` 是否正确

### 问题 3：前端无法连接后端

确保后端已启动在 `http://localhost:8000`

### 问题 4：OHLCV 数据未实现

这是预留接口，当前系统会优雅降级，仅使用资金流数据。如需启用：

1. 在 `ohlcv_tool.py` 中实现数据获取逻辑
2. 集成 AKShare 或其他数据源

## 📝 开发说明

### 扩展新的 Tool

1. 在 `src/financial_crew/tools/` 创建新文件
2. 继承 `BaseTool` 并实现 `_run` 方法
3. 在 `crew.py` 中绑定到相应 Agent

### 添加新的 Agent

1. 在 `config/agents.yaml` 中定义
2. 在 `crew.py` 中添加 `@agent` 装饰的方法

### 修改 Flow 逻辑

编辑 `flows/analysis_flow.py`，使用 `@start()` 和 `@listen()` 装饰器

## 📄 许可证

本项目仅供学习和研究使用。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**项目维护者**: 金融综设小组  
**最后更新**: 2025-12-23
