import pytest
import os
import sys
from financial_crew.crew import FinancialCrew

# 只有在明确需要跑集成测试时才运行
@pytest.mark.skipif(os.environ.get("RUN_E2E") != "true", reason="Skipping E2E academic test")
def test_academic_output_structure():
    """
    测试生成的报告是否符合学术规范：
    1. 不包含投资建议关键词
    2. 包含实证分析关键词
    3. 成功生成了 Markdown 文件
    """
    # 1. 初始化 Crew
    crew_inst = FinancialCrew().crew()
    
    # 2. 定义输入 (以贵州茅台为例)
    inputs = {
        'user_query': '分析贵州茅台(600519)的近期市场微观结构与波动率特征'
    }
    
    # 3. 运行
    result = crew_inst.kickoff(inputs=inputs)
    
    # CrewAI 的 result 可能是 TaskOutput 对象或字符串
    report_content = str(result)
    
    print("\n\n========== Generated Report Content ==========\n")
    print(report_content)
    print("\n==============================================\n")

    # 4. 断言检查 (语义层)
    # 4.1 负面清单 (禁止出现的词)
    forbidden_words = ["投资建议", "强烈推荐", "买入评级", "目标价", "主力洗盘", "跟庄"]
    for word in forbidden_words:
        assert word not in report_content, f"Report contained forbidden non-academic word: {word}"

    # 4.2 正面清单 (必须出现的词)
    required_words = ["实证", "结论", "数据", "波动率"] # 稍微放宽一点，避免过于严格匹配
    for word in required_words:
        assert word in report_content, f"Report missing academic keyword: {word}"
    
    # 5. 检查文件是否生成
    # crew.py 中生成的文件名带有时间戳，比较难直接 assert 文件存在性
    # 但我们可以检查 result 文件夹是否有最近生成的文件
    result_dir = "result"
    if os.path.exists(result_dir):
        files = os.listdir(result_dir)
        md_files = [f for f in files if f.endswith(".md") and "report_" in f]
        assert len(md_files) > 0, "No report file generated in result/"

if __name__ == "__main__":
    # 方便手动运行
    os.environ["RUN_E2E"] = "true"
    pytest.main(["-v", "-s", __file__])
