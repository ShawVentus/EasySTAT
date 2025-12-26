# AKShare 中文使用指南

## 📌 概述

[AKShare](https://github.com/akfamily/akshare) 是一个基于 Python 的**开源财经数据接口库**，旨在简化金融数据的获取过程。它提供了 **800+ 个数据接口**，覆盖股票、期货、期权、基金、外汇、债券、指数、加密货币等多种金融产品的基本面数据、实时行情和历史数据。

> **核心理念：Write less, get more!**
> 一行代码即可获取所需金融数据。

### 主要特点

- ✅ **易用性**：一行代码获取数据
- ✅ **扩展性**：易于与其他应用集成
- ✅ **全面性**：覆盖中国及全球主要金融市场
- ✅ **实时更新**：持续维护和更新数据接口
- ✅ **跨语言支持**：通过 HTTP API 支持非 Python 语言调用

---

## 📊 可获取的数据类型

### 1. 股票数据

| 数据类别     | 接口示例                  | 说明                     |
| ------------ | ------------------------- | ------------------------ |
| A 股实时行情 | `stock_zh_a_spot_em`      | 东财 A 股实时行情数据    |
| A 股历史行情 | `stock_zh_a_hist`         | A 股日/周/月频率历史数据 |
| A 股分时数据 | `stock_zh_a_minute`       | A 股分时历史行情数据     |
| 港股行情     | `stock_hk_spot_em`        | 港股实时行情             |
| 美股行情     | `stock_us_daily`          | 美股历史数据(含复权)     |
| 科创板       | `stock_zh_kcb_daily`      | 科创板历史行情数据       |
| 北交所       | `stock_bj_a_spot_em`      | 北交所实时行情           |
| 股票指数     | `stock_zh_index_daily_em` | 股票指数历史行情         |

### 2. 期货数据

| 数据类别     | 接口示例               | 说明               |
| ------------ | ---------------------- | ------------------ |
| 国内期货实时 | `futures_zh_spot`      | 国内期货实时行情   |
| 外盘期货     | `futures_foreign_hist` | 外盘期货历史行情   |
| 期货持仓     | `get_rank_sum_daily`   | 前 20 会员持仓排名 |
| 期货库存     | `futures_inventory_em` | 商品期货库存数据   |
| 期货交割     | `futures_delivery_dce` | 交割统计数据       |

### 3. 期权数据

| 数据类别     | 接口示例                     | 说明                 |
| ------------ | ---------------------------- | -------------------- |
| 金融期权     | `option_finance_board`       | 金融期权数据         |
| 商品期权     | `option_hist_dce`            | 大连商品期权历史数据 |
| 上交所期权   | `option_sse_spot_price_sina` | 上交所期权实时行情   |
| 期权希腊字母 | `option_sse_greeks_sina`     | 期权希腊字母计算     |

### 4. 基金数据

| 数据类别   | 接口示例                   | 说明                 |
| ---------- | -------------------------- | -------------------- |
| 开放式基金 | `fund_open_fund_daily_em`  | 开放式基金实时数据   |
| ETF 基金   | `fund_etf_fund_daily_em`   | 场内交易基金实时数据 |
| 货币基金   | `fund_money_fund_daily_em` | 货币型基金实时数据   |
| 基金净值   | `fund_etf_hist_em`         | 基金历史净值         |
| 基金排行   | `fund_open_fund_rank_em`   | 开放式基金排行       |
| 基金经理   | `fund_manager_em`          | 基金经理信息         |

### 5. 债券数据

| 数据类别   | 接口示例                  | 说明             |
| ---------- | ------------------------- | ---------------- |
| 沪深债券   | `bond_zh_hs_daily`        | 沪深债券历史行情 |
| 可转债     | `bond_zh_cov`             | 可转债数据一览表 |
| 国债收益率 | `bond_zh_us_rate`         | 中美国债收益率   |
| 债券发行   | `macro_china_bond_public` | 中国债券发行统计 |

### 6. 外汇数据

| 数据类别   | 接口示例            | 说明               |
| ---------- | ------------------- | ------------------ |
| 人民币汇率 | `fx_spot_quote`     | 人民币外汇即期报价 |
| 外币对报价 | `fx_pair_quote`     | 外币对即期报价     |
| 货币换算   | `currency_convert`  | 实时货币换算       |
| 中行牌价   | `currency_boc_sina` | 中行人民币牌价历史 |

### 7. 宏观经济数据

| 数据类别   | 接口示例                   | 说明               |
| ---------- | -------------------------- | ------------------ |
| 中国 GDP   | `macro_china_gdp`          | 中国 GDP 数据      |
| 中国 CPI   | `macro_china_cpi`          | 中国消费价格指数   |
| 中国 PMI   | `macro_china_pmi`          | 中国采购经理人指数 |
| 美国非农   | `macro_usa_non_farm`       | 美国非农就业人数   |
| 美国 CPI   | `macro_usa_cpi_monthly`    | 美国 CPI 月率      |
| 欧元区利率 | `macro_euro_interest_rate` | 欧洲央行决议报告   |

### 8. 加密货币数据

| 数据类别   | 接口示例                     | 说明             |
| ---------- | ---------------------------- | ---------------- |
| 实时行情   | `crypto_js_spot`             | 加密货币实时行情 |
| 比特币持仓 | `crypto_bitcoin_hold_report` | 比特币持仓报告   |
| CME 成交量 | `crypto_bitcoin_cme`         | CME 比特币成交量 |

### 9. 特色数据

| 数据类别 | 接口示例                      | 说明           |
| -------- | ----------------------------- | -------------- |
| 龙虎榜   | `stock_lhb_detail_daily_sina` | A 股龙虎榜数据 |
| 涨停板   | `stock_zt_pool_em`            | 涨停股池       |
| 资金流向 | `stock_individual_fund_flow`  | 个股资金流向   |
| 机构调研 | `stock_jgdy_detail_em`        | 机构调研详情   |
| 融资融券 | `stock_margin_sse`            | 融资融券汇总   |
| 千股千评 | `stock_comment_em`            | 股市关注度评论 |
| 电影票房 | `movie_boxoffice_realtime`    | 电影实时票房   |
| 新闻联播 | `news_cctv`                   | 新闻联播文字稿 |

---

## 🛠️ 安装与配置

### 系统要求

- **Python 版本**：3.8+ (推荐 3.11.x) 64 位
- **操作系统**：支持 Windows、macOS、Linux（均需 64 位）
- **苹果芯片**：原生支持 M 系列芯片
- **树莓派**：支持树莓派 4B (64 位系统)

### 安装方法

#### 方法一：pip 安装（推荐）

```bash
# 通用安装
pip install akshare --upgrade

# 国内镜像安装（推荐）
pip install akshare --upgrade -i https://pypi.tuna.tsinghua.edu.cn/simple
```

#### 方法二：Anaconda 安装

```bash
# 创建虚拟环境
conda create -n akshare_env python=3.11

# 激活环境
conda activate akshare_env

# 安装 AKShare
pip install akshare --upgrade --user -i https://pypi.tuna.tsinghua.edu.cn/simple
```

#### 方法三：Docker 安装

```bash
# 拉取镜像
docker pull registry.cn-shanghai.aliyuncs.com/akfamily/aktools:jupyter

# 运行容器
docker run -it registry.cn-shanghai.aliyuncs.com/akfamily/aktools:jupyter python

# 测试
import akshare as ak
print(ak.__version__)
```

### 升级 AKShare

由于接口更新频繁，建议使用前先升级：

```bash
pip install akshare --upgrade -i https://pypi.org/simple
```

---

## 📖 使用教程

### 基础用法

```python
import akshare as ak

# 查看版本
print(ak.__version__)

# 获取 A 股历史行情数据
stock_df = ak.stock_zh_a_hist(
    symbol="000001",      # 股票代码
    period="daily",       # 周期：daily/weekly/monthly
    start_date="20230101",# 开始日期
    end_date="20231231",  # 结束日期
    adjust=""             # 复权：""不复权/"qfq"前复权/"hfq"后复权
)
print(stock_df)
```

输出示例：

```
         日期     开盘     收盘     最高     最低       成交量        成交额   振幅  涨跌幅   涨跌额  换手率
0  2023-01-03  12.92  13.15  13.20  12.88  1063893  1388687878  2.49  1.86  0.24  0.62
1  2023-01-04  13.20  13.24  13.36  13.11  1073554  1416985071  1.90  0.68  0.09  0.62
...
```

### 常用接口示例

#### 1. 获取实时行情

```python
import akshare as ak

# A 股实时行情
df = ak.stock_zh_a_spot_em()
print(df.head())

# 港股实时行情
df_hk = ak.stock_hk_spot_em()
print(df_hk.head())

# 期货实时行情
df_futures = ak.futures_zh_spot()
print(df_futures.head())
```

#### 2. 获取指数数据

```python
import akshare as ak

# 获取上证指数历史数据
index_df = ak.stock_zh_index_daily_em(symbol="sh000001")
print(index_df.head())

# 获取中证指数成份股
cons_df = ak.index_stock_cons_csindex(symbol="000300")
print(cons_df.head())
```

#### 3. 获取基金数据

```python
import akshare as ak

# 开放式基金实时数据
fund_df = ak.fund_open_fund_daily_em()
print(fund_df.head())

# ETF 历史净值
etf_df = ak.fund_etf_hist_em(symbol="159919", period="daily")
print(etf_df.head())
```

#### 4. 获取宏观经济数据

```python
import akshare as ak

# 中国 GDP 数据
gdp_df = ak.macro_china_gdp()
print(gdp_df.head())

# 美国非农就业数据
nonfarm_df = ak.macro_usa_non_farm()
print(nonfarm_df.head())

# 中国 LPR 利率
lpr_df = ak.macro_china_lpr()
print(lpr_df.head())
```

#### 5. 获取交易日历

```python
import akshare as ak

# 获取交易日历
trade_date_df = ak.tool_trade_date_hist()
print(trade_date_df.head())
```

### 数据可视化示例

```python
import akshare as ak
import mplfinance as mpf  # pip install mplfinance

# 获取美股数据
stock_us_df = ak.stock_us_daily(symbol="AAPL", adjust="qfq")
stock_us_df = stock_us_df.set_index(["date"])
stock_us_df = stock_us_df["2024-01-01": "2024-03-01"]

# 绘制 K 线图
mpf.plot(
    stock_us_df,
    type="candle",       # 蜡烛图
    mav=(5, 10, 20),     # 均线
    volume=True,         # 显示成交量
    show_nontrading=False
)
```

---

## 🔗 集成到其他应用

### 方法一：Python 直接调用

AKShare 作为 Python 库，可直接在任何 Python 项目中导入使用：

```python
import akshare as ak

def get_stock_data(symbol, start_date, end_date):
    """获取股票历史数据的封装函数"""
    return ak.stock_zh_a_hist(
        symbol=symbol,
        period="daily",
        start_date=start_date,
        end_date=end_date,
        adjust="qfq"
    )

# 在你的应用中调用
data = get_stock_data("000001", "20230101", "20231231")
```

### 方法二：HTTP API 服务（推荐跨语言集成）

通过 **AKTools** 可将 AKShare 部署为 HTTP API 服务，支持任何编程语言调用：

#### 安装 AKTools

```bash
pip install aktools
```

#### 启动 HTTP 服务

```bash
python -m aktools
```

服务默认运行在 `http://127.0.0.1:8080`

#### API 调用示例

**Python 调用：**

```python
import requests

# 调用 API 获取股票数据
params = {
    "symbol": "000001",
    "period": "daily",
    "start_date": "20230101",
    "end_date": "20231231"
}
response = requests.get("http://127.0.0.1:8080/api/stock_zh_a_hist", params=params)
data = response.json()
print(data)
```

**JavaScript/Node.js 调用：**

```javascript
const axios = require("axios");

async function getStockData() {
  const response = await axios.get(
    "http://127.0.0.1:8080/api/stock_zh_a_hist",
    {
      params: {
        symbol: "000001",
        period: "daily",
        start_date: "20230101",
        end_date: "20231231",
      },
    }
  );
  console.log(response.data);
}
```

**cURL 调用：**

```bash
curl "http://127.0.0.1:8080/api/stock_zh_a_hist?symbol=000001&period=daily&start_date=20230101&end_date=20231231"
```

### 方法三：R 语言调用

```r
library(reticulate)
use_python("/path/to/your/python")

ak <- import("akshare")
stock_df <- ak$stock_zh_a_hist(symbol="000001", period="daily")
head(stock_df)
```

### 方法四：MATLAB 调用

```matlab
% 配置 Python 环境
pyenv(Version="C:\path\to\python.exe");

% 调用 AKShare
py.akshare.stock_zh_a_hist("000001", "daily", "20230101", "20231231", "")
```

---

## 🤖 作为 AI Tool 使用

AKShare 非常适合作为 AI 应用的数据获取工具：

### Tool 设计示例

```python
from typing import Optional
import akshare as ak
import pandas as pd

class AKShareTool:
    """AKShare 数据获取工具类"""

    def get_stock_history(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        period: str = "daily",
        adjust: str = "qfq"
    ) -> pd.DataFrame:
        """
        获取 A 股历史行情数据

        Args:
            symbol: 股票代码，如 "000001"
            start_date: 开始日期，格式 "YYYYMMDD"
            end_date: 结束日期，格式 "YYYYMMDD"
            period: 周期，可选 "daily"/"weekly"/"monthly"
            adjust: 复权类型，""不复权/"qfq"前复权/"hfq"后复权

        Returns:
            包含 OHLCV 数据的 DataFrame
        """
        return ak.stock_zh_a_hist(
            symbol=symbol,
            period=period,
            start_date=start_date,
            end_date=end_date,
            adjust=adjust
        )

    def get_realtime_quote(self, symbol: Optional[str] = None) -> pd.DataFrame:
        """
        获取 A 股实时行情

        Args:
            symbol: 可选，指定股票代码过滤

        Returns:
            实时行情 DataFrame
        """
        df = ak.stock_zh_a_spot_em()
        if symbol:
            df = df[df['代码'] == symbol]
        return df

    def get_macro_data(self, indicator: str) -> pd.DataFrame:
        """
        获取宏观经济数据

        Args:
            indicator: 指标名称，支持：
                - "gdp": 中国 GDP
                - "cpi": 中国 CPI
                - "pmi": 中国 PMI
                - "lpr": LPR 利率
                - "m2": M2 货币供应

        Returns:
            宏观数据 DataFrame
        """
        indicator_map = {
            "gdp": ak.macro_china_gdp,
            "cpi": ak.macro_china_cpi,
            "pmi": ak.macro_china_pmi,
            "lpr": ak.macro_china_lpr,
            "m2": ak.macro_china_m2_yearly
        }
        if indicator not in indicator_map:
            raise ValueError(f"不支持的指标: {indicator}")
        return indicator_map[indicator]()

    def search_fund(self, keyword: str = "") -> pd.DataFrame:
        """
        搜索基金信息

        Args:
            keyword: 搜索关键词

        Returns:
            基金列表 DataFrame
        """
        df = ak.fund_name_em()
        if keyword:
            df = df[df['基金简称'].str.contains(keyword, na=False)]
        return df


# 使用示例
tool = AKShareTool()

# 获取平安银行历史数据
stock_data = tool.get_stock_history("000001", "20230101", "20231231")

# 获取中国 GDP 数据
gdp_data = tool.get_macro_data("gdp")

# 搜索沪深300相关基金
fund_data = tool.search_fund("沪深300")
```

### LangChain Tool 集成

```python
from langchain.tools import tool
import akshare as ak

@tool
def get_stock_price(symbol: str, days: int = 30) -> str:
    """
    获取指定股票最近 N 天的收盘价数据。

    Args:
        symbol: A 股股票代码，如 "000001" 表示平安银行
        days: 获取最近多少天的数据，默认 30 天

    Returns:
        股票价格数据的描述性文本
    """
    import pandas as pd
    from datetime import datetime, timedelta

    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=days*2)).strftime("%Y%m%d")

    df = ak.stock_zh_a_hist(
        symbol=symbol,
        period="daily",
        start_date=start_date,
        end_date=end_date,
        adjust="qfq"
    ).tail(days)

    latest = df.iloc[-1]
    return f"股票 {symbol} 最近 {days} 天: 最新收盘价 {latest['收盘']}元, 涨跌幅 {latest['涨跌幅']}%"


@tool
def get_market_overview() -> str:
    """
    获取 A 股市场整体概况，包括涨跌家数、成交额等。

    Returns:
        市场概况描述
    """
    df = ak.stock_zh_a_spot_em()

    total = len(df)
    up_count = len(df[df['涨跌幅'] > 0])
    down_count = len(df[df['涨跌幅'] < 0])
    flat_count = total - up_count - down_count
    total_amount = df['成交额'].sum() / 1e8  # 转换为亿元

    return f"A 股市场共 {total} 只股票: 上涨 {up_count} 只, 下跌 {down_count} 只, 平盘 {flat_count} 只, 总成交额 {total_amount:.2f} 亿元"
```

---

## 📚 接口查询方法

### 方法一：查看文档

官方文档：https://akshare.akfamily.xyz/

### 方法二：代码内查询

```python
import akshare as ak

# 查看所有可用接口
print(dir(ak))

# 查看某个接口的帮助文档
help(ak.stock_zh_a_hist)

# 查看接口参数
import inspect
sig = inspect.signature(ak.stock_zh_a_hist)
print(sig)
```

### 方法三：搜索接口

```python
import akshare as ak

# 搜索包含特定关键词的接口
keyword = "stock"
interfaces = [name for name in dir(ak) if keyword in name.lower()]
print(interfaces)
```

---

## ⚠️ 注意事项

1. **数据用途**：AKShare 提供的数据仅供学术研究使用，不构成任何投资建议
2. **网络依赖**：数据实时采集自网络，需要稳定的网络连接
3. **版本更新**：因目标网站变化，部分接口可能需要更新，请保持 AKShare 最新版本
4. **限流策略**：频繁调用可能触发目标网站的限流，建议适当控制调用频率
5. **文件命名**：程序运行时，文件名、文件夹名不能命名为 `akshare`

---

## 🔗 相关资源

- **GitHub 仓库**：https://github.com/akfamily/akshare
- **官方文档**：https://akshare.akfamily.xyz/
- **AKTools HTTP API**：https://aktools.akfamily.xyz/
- **PyPI**：https://pypi.org/project/akshare/

---

## 📄 许可证

AKShare 采用 MIT 许可证开源。

---

_最后更新：2024-12-24_
