#!/bin/bash
# EasySTAT 环境快速搭建脚本

echo "=== EasySTAT 环境搭建开始 ==="

# 1. 检查 Conda
if ! command -v conda &> /dev/null; then
    echo "错误: 未检测到 Conda。请先安装 Anaconda 或 Miniconda。"
    exit 1
fi

# 2. 创建或更新 Conda 环境 'es'
ENV_NAME="es"
echo "正在检查环境 '$ENV_NAME' ..."

if conda info --envs | grep -q "$ENV_NAME"; then
    echo "环境 '$ENV_NAME' 已存在，跳过创建。"
else
    echo "正在创建环境 '$ENV_NAME' (Python 3.10)..."
    conda create -n "$ENV_NAME" python=3.10 -y
fi

# 3. 激活环境
# 注意：在脚本中激活 conda 需要 source conda.sh
CONDA_BASE=$(conda info --base)
source "$CONDA_BASE/etc/profile.d/conda.sh"
conda activate "$ENV_NAME"

echo "当前激活环境: $(python --version)"

# 4. 安装 Python 依赖
echo "=== 安装 Python 依赖 ==="

# 4.1 安装核心依赖 (EasySTAT)
echo "正在安装 CrewAI 核心依赖..."
# 此时位于项目根目录，但 pyproject.toml 在 EasySTAT 目录下
# 如果你想直接安装 toml 中定义的依赖，可以使用 pip install . (前提是目录下有 pyproject.toml)
# 根据先前文件结构，pyproject.toml 在 EasySTAT 目录下
cd EasySTAT || { echo "错误: 找不到 EasySTAT 目录"; exit 1; }
pip install "crewai[tools]==1.7.2"
pip install "akshare>=1.13.0"
pip install "tenacity>=8.2.0"
pip install "joblib>=1.3.0"
# 或者如果 pyproject.toml 配置完备，也可以 pip install -e .
cd ..

# 4.2 安装后端依赖
echo "正在安装后端 Web 依赖..."
cd easystat-webui/backend || { echo "错误: 找不到 backend 目录"; exit 1; }
pip install -r requirements.txt
cd ../..

# 5. 安装前端依赖
echo "=== 安装前端依赖 ==="
if ! command -v npm &> /dev/null; then
    echo "警告: 未检测到 npm，跳过前端依赖安装。"
else
    cd easystat-webui/frontend || { echo "错误: 找不到 frontend 目录"; exit 1; }
    echo "执行 npm install..."
    npm install
    cd ../..
fi

echo "=== 环境搭建完成 ==="
echo "请运行 ./start.sh 启动服务"
