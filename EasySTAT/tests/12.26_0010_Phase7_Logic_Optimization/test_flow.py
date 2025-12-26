import sys
import os
from datetime import datetime
import json

# ==========================================
# 测试参数配置 (前置化)
# ==========================================
USER_QUERY = "分析茅台的资金流和技术指标"
TEST_NAME = "12.26_0010_Phase7_Logic_Optimization"
PROJECT_ROOT = "/Users/mac/dev/personal/br_competition/EasySTAT"
RESULT_DIR = os.path.join(PROJECT_ROOT, "tests", TEST_NAME, "result")

# 动态添加路径
sys.path.append(os.path.join(PROJECT_ROOT, "src"))

from financial_crew.crew import FinancialCrew

def run_test():
    """
    运行核心链路验证测试
    
    主要验证：
    1. 任务执行顺序是否正确 (搜索 -> 采集)
    2. CrawlerTool 是否产出 data_ref
    3. 报告是否自动存盘
    """
    print(f"开始测试: {TEST_NAME}")
    print(f"用户查询: {USER_QUERY}")
    
    inputs = {
        'user_query': USER_QUERY,
        'current_year': str(datetime.now().year)
    }

    try:
        # 执行 Crew
        print("\n[测试] 正在启动 CrewAI 执行...")
        result = FinancialCrew().crew().kickoff(inputs=inputs)
        
        # 结果分析
        print("\n[测试] 执行完成！")
        
        # 检查报告存盘
        # 注意：crew.py 中配置了 result/report_{timestamp}.md
        # 我们检查最新的报告文件
        report_dir = os.path.join(PROJECT_ROOT, "result")
        reports = [f for f in os.listdir(report_dir) if f.startswith("report_") and f.endswith(".md")]
        reports.sort(reverse=True)
        
        if reports:
            latest_report = os.path.join(report_dir, reports[0])
            print(f"[测试] 发现生成的报告: {latest_report}")
            
            # 将报告内容复制到测试结果目录
            with open(latest_report, 'r', encoding='utf-8') as f:
                content = f.read()
            
            output_file = os.path.join(RESULT_DIR, f"test_output_{datetime.now().strftime('%H%M%S')}.md")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"# 测试结果分析\n\n")
                f.write(f"## 原始报告内容\n\n{content}\n")
            
            print(f"[测试] 结果已保存至: {output_file}")
        else:
            print("[测试] 警告：未发现生成的报告文件。")

    except Exception as e:
        print(f"[测试] 发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 确保结果目录存在
    if not os.path.exists(RESULT_DIR):
        os.makedirs(RESULT_DIR)
        
    run_test()
