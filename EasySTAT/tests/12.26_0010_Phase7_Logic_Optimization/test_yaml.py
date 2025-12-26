import yaml
import pprint

def test_yaml():
    path = "/Users/mac/dev/personal/br_competition/EasySTAT/src/financial_crew/config/tasks.yaml"
    with open(path, 'r', encoding='utf-8') as f:
        try:
            data = yaml.safe_load(f)
            print("YAML 解析成功！")
            pprint.pprint(data)
        except Exception as e:
            print(f"YAML 解析失败: {e}")

if __name__ == "__main__":
    test_yaml()
