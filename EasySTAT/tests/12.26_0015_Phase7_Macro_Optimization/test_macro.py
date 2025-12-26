import sys
import os
import time
import json

# ==========================================
# 测试参数配置 (前置化)
# ==========================================
INDICATORS = ["gdp", "cpi", "ppi", "invalid_one", "pmi"] # 包含一个无效指标测试降级
LIMIT = 5
TEST_NAME = "12.26_0015_Phase7_Macro_Optimization"
PROJECT_ROOT = "/Users/mac/dev/personal/br_competition/EasySTAT"
RESULT_DIR = os.path.join(PROJECT_ROOT, "tests", TEST_NAME, "result")

# 动态添加路径
sys.path.append(os.path.join(PROJECT_ROOT, "src"))

from financial_crew.tools.macro_tool import MacroTool

def run_macro_test():
    """
    运行宏观采集并发验证测试
    
    主要验证：
    1. 是否支持 List[str] 输入
    2. 并发执行是否生效 (通过耗时观察)
    3. 异常指标是否能被优雅跳过 (invalid_one)
    """
    print(f"开始测试: {TEST_NAME}")
    print(f"待采集指标: {INDICATORS}")
    
    tool = MacroTool()
    
    start_time = time.time()
    
    # 执行采集
    print("\n[测试] 正在启动并发采集...")
    result_json = tool._run(indicator=INDICATORS, limit=LIMIT)
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\n[测试] 采集完成！总耗时: {duration:.2f} 秒")
    
    # 结果分析
    results = json.loads(result_json)
    
    output_file = os.path.join(RESULT_DIR, "macro_test_result.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        
    print(f"[测试] 结果已保存至: {output_file}")
    
    # 验证降级
    if "invalid_one" in results:
        status = results["invalid_one"].get("status")
        print(f"[验证] 无效指标 'invalid_one' 状态: {status} (预期为 failed)")
    
    # 验证成功指标
    success_count = sum(1 for k, v in results.items() if v.get("status") == "success")
    print(f"[验证] 成功采集指标数: {success_count} / {len(INDICATORS)-1}")

if __name__ == "__main__":
    # 确保结果目录存在
    if not os.path.exists(RESULT_DIR):
        os.makedirs(RESULT_DIR)
        
    run_macro_test()
