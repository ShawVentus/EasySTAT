# CrewAI 多智能体系统详解

## 核心概念：这不是简单的函数整合！

### 1. 什么是 Agent（智能体）？

**Agent ≠ 函数**，Agent 是由 **LLM（大语言模型）驱动的智能决策者**。

每个 Agent 有：

- **角色 (role)**: 它的身份定位
- **目标 (goal)**: 它要达成的目标
- **背景 (backstory)**: 它的经验和专长
- **Tools**: 它可以调用的工具

**关键区别**：

- ❌ 传统方式：直接调用函数 `crawler.fetch_data()` → `ta.calculate()` → `arch.model()`
- ✅ CrewAI 方式：Agent **自主决策**何时、如何使用 Tool，LLM 理解用户意图并编排执行

### 2. 我们的 4 个 Agent

#### Agent 1: 数据采集专家 (data_collector)

```yaml
role: 金融数据采集专家
goal: 根据用户需求采集资金流数据和 K 线数据
backstory: 你是一位资深金融数据工程师，精通各类金融数据接口
tools: [CrawlerTool, OHLCVTool]
```

**智能行为**：

- LLM 解析用户查询 "分析贵州茅台"
- 自动提取股票代码 "600519"
- 决定调用 CrawlerTool 获取资金流数据
- 判断是否需要 K 线数据

#### Agent 2: 数据分析师 (data_analyst)

```yaml
role: 金融数据分析师
goal: 基于采集的数据计算技术指标，识别市场趋势
backstory: 拥有 15 年经验的技术分析师，精通 RSI、MACD、布林带
tools: [TATool]
```

**智能行为**：

- 接收 Agent 1 采集的数据
- LLM 判断数据是否充足
- 如果 OHLCV 可用，调用 TATool 计算指标
- 如果不可用，生成文字分析说明

#### Agent 3: 量化建模专家 (model_analyst)

```yaml
role: 金融量化建模专家
goal: 使用统计模型评估市场波动风险
backstory: 金融工程博士，专注 GARCH 模型和风险度量
tools: [ArchTool]
```

**智能行为**：

- 评估数据质量
- 决定是否适合建模
- 调用 ArchTool 执行 GARCH
- 解释模型结果

#### Agent 4: 报告生成专家 (report_generator)

```yaml
role: 投资研究报告撰写专家
goal: 综合各方分析结果，生成结构化报告
backstory: 资深投资研究员，擅长整合技术和量化分析
tools: 无（仅处理文本）
```

**智能行为**：

- 综合前三个 Agent 的输出
- LLM 生成连贯的中文报告
- 自动组织结构（资金面、技术面、风险评估）
- 提供投资建议

---

## 3. 多智能体协作流程

### 传统方式 vs CrewAI 方式

#### ❌ 传统方式（简单函数调用）

```python
# 这是简单的函数整合
data = crawler.fetch_data("600519")
indicators = ta.calculate(data)
model = arch.garch(data)
report = f"数据: {data}\n指标: {indicators}\n模型: {model}"
```

#### ✅ CrewAI 方式（智能协作）

```python
# 启动 Crew，LLM 自动编排
crew = FinancialCrew()
result = crew.crew().kickoff(inputs={"user_query": "分析贵州茅台"})

# 内部发生的事：
# 1. Agent 1 理解用户意图 → 决定调用 CrawlerTool
# 2. Agent 2 接收数据 → 判断是否能计算指标 → 决定调用 TATool
# 3. Agent 3 评估数据 → 决定是否建模 → 调用 ArchTool
# 4. Agent 4 综合结果 → LLM 生成自然语言报告
```

---

## 4. Task（任务）编排

每个 Task 定义了：

- **description**: 任务描述（给 Agent 的指令）
- **expected_output**: 期望的输出格式
- **agent**: 负责的 Agent
- **context**: 依赖的上游 Task

### Task 依赖关系图

```
fetch_capital_flow_task (Agent 1) ────┐
                                      ├──→ analyze_capital_flow_task (Agent 2)
fetch_ohlcv_task (Agent 1) ──┬────────┤                                        ↓
                             │        ├──→ calculate_indicators_task (Agent 2) → generate_report_task
                             │        │                                        ↑  (Agent 4)
                             └────────┴──→ volatility_modeling_task (Agent 3) ─┘
```

**智能协作**：

- Agent 2 同时接收 Agent 1 的两个输出
- Agent 4 等待所有前置分析完成
- 如果某个步骤失败，Agent 会自动调整策略

---

## 5. Flow 编排（高级功能）

`flows/analysis_flow.py` 不是简单的函数调用，而是：

```python
class FinancialAnalysisFlow(Flow[AnalysisState]):
    @start()
    def execute_crew(self):
        # CrewAI 内部会：
        # 1. 初始化所有 Agent（每个 Agent 都有独立的 LLM 实例）
        # 2. 按 Task 依赖顺序执行
        # 3. Agent 之间通过结构化数据交换信息
        # 4. LLM 动态决策何时调用 Tool
        result = crew_instance.crew().kickoff(inputs={...})
```

**状态管理**：

- 提取中间结果（资金流、指标、波动率）
- 供前端可视化使用

---

## 6. 与 Financial_Program 的集成

### 架构分层

```
┌─────────────────────────────────────────┐
│  Financial_Program (Web 界面层)         │
│  - 前端：React + TypeScript              │
│  - 后端：FastAPI                         │
│  - 路由：/api/crew/analyze               │
└───────────────┬─────────────────────────┘
                │ 调用
                ↓
┌─────────────────────────────────────────┐
│  financial_crew (CrewAI 层)             │
│  - 4 个 Agent（LLM 驱动）                │
│  - 6 个 Task（智能编排）                 │
│  - Flow（工作流管理）                    │
└───────────────┬─────────────────────────┘
                │ 使用
                ↓
┌─────────────────────────────────────────┐
│  Tools (工具层)                          │
│  - CrawlerTool → crawler.py             │
│  - TATool → ta_ana                      │
│  - ArchTool → arch_model                │
└─────────────────────────────────────────┘
```

**关键点**：

- Financial_Program 只是提供 **Web 入口**和 **UI 展示**
- **真正的智能在 financial_crew 项目中**
- Agent 通过 LLM **自主决策**，不是简单调用

---

## 7. 实际运行时的 LLM 调用

当执行 `crew.kickoff()` 时，CrewAI 会：

```
1. 用户输入: "分析贵州茅台"

2. Agent 1 (data_collector) 收到任务
   → LLM 推理："用户想分析贵州茅台，我需要先获取资金流数据"
   → 调用 CrawlerTool(stock_code="600519")
   → 返回数据给下游

3. Agent 2 (data_analyst) 收到上游数据
   → LLM 推理："我收到了资金流数据，但没有 K 线数据"
   → 决策："跳过技术指标计算，重点分析资金流向"
   → 生成文字分析

4. Agent 3 (model_analyst) 收到数据
   → LLM 推理："没有价格序列，无法建模"
   → 决策："返回风险评估缺失说明"

5. Agent 4 (report_generator) 收到所有结果
   → LLM 推理："综合资金流分析，生成报告"
   → 生成 Markdown 格式的完整报告
```

**每个箭头都是一次 LLM 调用！**

---

## 8. 证明：运行日志示例

当你运行 `python tests/test_flow_simple.py` 时，会看到：

```
启动金融分析流程，用户请求: 分析工业富联

# Agent: Data Collector
[2025-12-23 22:31:40] [INFO] 开始执行任务 fetch_capital_flow_task
[2025-12-23 22:31:41] [INFO] LLM 推理中...
[2025-12-23 22:31:42] [INFO] 决定使用工具: CrawlerTool
[2025-12-23 22:31:43] [INFO] 工具返回: 20 条数据

# Agent: Data Analyst
[2025-12-23 22:31:44] [INFO] 开始执行任务 analyze_capital_flow_task
[2025-12-23 22:31:45] [INFO] LLM 推理中...
[2025-12-23 22:31:46] [INFO] 生成分析结论: 主力资金净流入...

# Agent: Report Generator
[2025-12-23 22:31:50] [INFO] 开始执行任务 generate_report_task
[2025-12-23 22:31:51] [INFO] LLM 推理中...
[2025-12-23 22:31:55] [INFO] 报告生成完成
```

---

## 总结

### ❌ 不是：简单的函数整合

```python
data = func1()
result = func2(data)
report = func3(result)
```

### ✅ 而是：智能多 Agent 协作

```python
# 4 个独立的 LLM Agent
# 每个 Agent 自主决策
# 动态调整执行策略
# 生成自然语言报告
crew.kickoff(user_query)
```

**核心价值**：

1. **智能理解**：LLM 理解用户自然语言
2. **自主决策**：Agent 决定何时用什么工具
3. **容错能力**：数据不足时自动降级
4. **自然输出**：生成连贯的中文报告

这就是 CrewAI 多智能体系统的真正威力！
