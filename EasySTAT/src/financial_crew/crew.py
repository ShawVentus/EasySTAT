import os
from datetime import datetime
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from financial_crew.tools.crawler_tool import CrawlerTool
from financial_crew.tools.ohlcv_tool import OHLCVTool
from financial_crew.tools.ta_tool import TATool
from financial_crew.tools.data_reader_tool import DataReaderTool
from financial_crew.tools.arch_tool import ArchTool
from financial_crew.tools.macro_tool import MacroTool
from financial_crew.tools.stock_search_tool import StockSearchTool

@CrewBase
class FinancialCrew():
    """金融分析多智能体团队"""
    
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def data_collector(self) -> Agent:
        """数据采集智能体"""
        return Agent(
            config=self.agents_config['data_collector'],
            tools=[CrawlerTool(), OHLCVTool(), MacroTool(), StockSearchTool()],
            verbose=True
        )

    @agent
    def data_analyst(self) -> Agent:
        """数据分析智能体"""
        return Agent(
            config=self.agents_config['data_analyst'],
            tools=[TATool(), DataReaderTool()],
            verbose=True
        )

    @agent
    def model_analyst(self) -> Agent:
        """量化建模智能体"""
        return Agent(
            config=self.agents_config['model_analyst'],
            tools=[ArchTool()],
            verbose=True
        )

    @agent
    def report_generator(self) -> Agent:
        """报告生成智能体"""
        return Agent(
            config=self.agents_config['report_generator'],
            tools=[DataReaderTool()], # 赋予报告专家读取数据的能力，防止幻觉
            verbose=True
        )

    def __init__(self):
        """初始化任务缓存"""
        self._tasks_cache = {}

    def _create_task(self, task_key: str, **kwargs) -> Task:
        """
        辅助方法：手动解析任务配置并关联智能体（带缓存）
        """
        # 如果已经创建过该任务（无特殊 kwargs 的情况），直接返回缓存
        cache_key = task_key if not kwargs else f"{task_key}_{hash(str(kwargs))}"
        if cache_key in self._tasks_cache:
            return self._tasks_cache[cache_key]

        config = self.tasks_config[task_key].copy()
        agent_raw = config.pop('agent')
        
        # 自动处理 context 映射
        if 'context' in config and 'context' not in kwargs:
            context_keys = config.pop('context')
            context_tasks = []
            for k in context_keys:
                if isinstance(k, str):
                    if hasattr(self, k):
                        # 递归获取（会通过缓存保证唯一性）
                        context_tasks.append(getattr(self, k)())
                    else:
                        print(f"[FinancialCrew] 警告: 任务上下文 '{k}' 未在类中定义，已跳过。")
            kwargs['context'] = context_tasks
        
        # 解析智能体对象
        if isinstance(agent_raw, str):
            if hasattr(self, agent_raw):
                agent_obj = getattr(self, agent_raw)()
            else:
                raise AttributeError(f"智能体 '{agent_raw}' 未在类中定义，请检查 agents.yaml 和 crew.py")
        else:
            agent_obj = agent_raw
        
        task = Task(
            **config,
            agent=agent_obj,
            **kwargs
        )
        
        # 存入缓存
        self._tasks_cache[cache_key] = task
        return task

    @task
    def search_stock_code_task(self) -> Task:
        """股票代码查询任务"""
        return self._create_task('search_stock_code_task')

    @task
    def fetch_capital_flow_task(self) -> Task:
        """资金流采集任务"""
        return self._create_task('fetch_capital_flow_task')

    @task
    def fetch_ohlcv_task(self) -> Task:
        """K线采集任务"""
        return self._create_task('fetch_ohlcv_task')
    
    @task
    def fetch_macro_data_task(self) -> Task:
        """宏观数据采集任务"""
        return self._create_task('fetch_macro_data_task')

    @task
    def calculate_indicators_task(self) -> Task:
        """技术指标计算任务"""
        return self._create_task('calculate_indicators_task')

    @task
    def analyze_capital_flow_task(self) -> Task:
        """资金流分析任务"""
        return self._create_task('analyze_capital_flow_task')

    @task
    def volatility_modeling_task(self) -> Task:
        """波动率建模任务"""
        return self._create_task('volatility_modeling_task')

    @task
    def generate_report_task(self) -> Task:
        """投资报告生成任务"""
        # 动态生成带时间戳的文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"result/report_{timestamp}.md"
        
        return self._create_task('generate_report_task', output_file=output_path)

    @crew
    def crew(self) -> Crew:
        """创建金融分析 Crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
