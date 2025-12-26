from pydantic import BaseModel
from typing import List, Optional

class FlowDataSchema(BaseModel):
    """资金流数据结构（对应 crawler.py 输出）"""
    code: str                    # 股票代码
    name: str                    # 股票名称
    latest_price: float          # 最新价
    change_percentage: float     # 涨跌幅
    main_flow_net_amount: float  # 主力净流入
    main_flow_net_percentage: float # 主力净流入占比
    crawl_time: str              # 采集时间

class TechnicalIndicatorsSchema(BaseModel):
    """技术指标结构（对应 ta_ana 输出）"""
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    bollinger_hband: Optional[float] = None
    bollinger_lband: Optional[float] = None
    atr: Optional[float] = None

class VolatilityModelSchema(BaseModel):
    """波动率模型结构（对应 arch_model 输出）"""
    conditional_volatility: Optional[float] = None
    garch_params: Optional[dict] = None
    log_likelihood: Optional[float] = None
    summary: Optional[str] = None
