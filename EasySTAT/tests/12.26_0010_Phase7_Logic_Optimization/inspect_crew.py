import sys
import os
from financial_crew.crew import FinancialCrew

# 动态添加路径
sys.path.append(os.path.join("/Users/mac/dev/personal/br_competition/EasySTAT", "src"))

def inspect_crew():
    print("正在初始化 FinancialCrew...")
    crew_instance = FinancialCrew().crew()
    print("\n[Crew 结构检查]")
    print(f"任务总数: {len(crew_instance.tasks)}")
    
    for i, task in enumerate(crew_instance.tasks):
        agent_role = task.agent.role if task.agent else "None"
        print(f"任务 {i+1}: {task.description[:50].strip()}...")
        print(f"  - 执行者 (Agent Role): {agent_role}")
        
        # 处理 context，crewai 内部可能使用 _NotSpecified
        if task.context and not hasattr(task.context, '__iter__'):
             print(f"  - 上下文依赖: 无")
        elif task.context:
            context_names = [t.description[:20].strip() for t in task.context]
            print(f"  - 上下文依赖: {context_names}")
        else:
            print(f"  - 上下文依赖: 无")
        print("-" * 30)

if __name__ == "__main__":
    inspect_crew()
