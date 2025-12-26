import sys
import os
from financial_crew.crew import FinancialCrew

# 动态添加路径
sys.path.append(os.path.join("/Users/mac/dev/personal/br_competition/EasySTAT", "src"))

def debug_config():
    crew_instance = FinancialCrew()
    print(f"tasks_config 类型: {type(crew_instance.tasks_config)}")
    print(f"tasks_config 内容: {crew_instance.tasks_config}")
    
    if isinstance(crew_instance.tasks_config, dict):
        print("search_stock_code_task 配置:")
        print(crew_instance.tasks_config.get('search_stock_code_task'))
    else:
        print("错误：tasks_config 不是字典！")

if __name__ == "__main__":
    debug_config()
