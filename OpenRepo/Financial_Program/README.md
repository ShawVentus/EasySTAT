# Financial_Program - 金融数据智能分析平台

一个集金融数据采集、AI 分析、可视化展示于一体的全栈解决方案。支持自动采集东方财富资金流数据，使用大语言模型进行智能分析并生成投资建议。

## 功能特性

- 📊 **自动数据采集**：定时采集个股/板块资金流数据
- 🤖 **AI 智能分析**：支持通义千问、Deepseek 等 OpenAI 兼容 API
- 💾 **本地存储**：报告存储到本地文件夹，无需 MinIO
- 🌐 **远程访问**：支持无头服务器部署，通过浏览器远程访问

---

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- MySQL 8.0+
- Redis 6.0+

---

## 本地开发部署

> 以下所有命令均在项目根目录下执行

### 1. 克隆项目

```bash
git clone <repository-url>
cd Financial_Program
```

### 2. 安装 MySQL 和 Redis

**macOS (Homebrew)**：

```bash
brew install mysql redis
brew services start mysql
brew services start redis
```

创建数据库：

```bash
mysql -u root -e "CREATE DATABASE IF NOT EXISTS financial_web_crawler CHARACTER SET utf8mb4;"
```

**Ubuntu/Debian**：

```bash
sudo apt update
sudo apt install -y mysql-server redis-server
sudo systemctl start mysql redis-server
```

创建数据库：

```bash
sudo mysql -e "CREATE DATABASE IF NOT EXISTS financial_web_crawler CHARACTER SET utf8mb4;"
```

### 3. 配置环境变量

```bash
cp .env.example backend/.env
```

编辑 `backend/.env`，配置以下必要项：

```ini
# LLM API 配置（通义千问示例）
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_API_KEY=sk-你的API密钥
LLM_MODEL=qwen-plus

# MySQL 配置（Homebrew 默认无密码）
MYSQL_HOST=127.0.0.1
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DATABASE=financial_web_crawler
```

### 4. 安装后端依赖

```bash
conda create -n br python=3.10 -y
conda activate br
pip install -r backend/requirements.txt
```

### 5. 启动后端

```bash
cd backend
python run.py
```

输出示例：

```
[Storage] 使用本地文件夹存储
数据库连接成功！
INFO: Uvicorn running on http://0.0.0.0:8000
```

### 6. 启动前端（新开终端）

```bash
cd frontend
npm install
npm run dev
```

### 7. 访问应用

- **前端界面**：http://localhost:5173
- **API 文档**：http://localhost:8000/docs

---

## 无头服务器部署

适用于远程 Linux 服务器，通过浏览器从本地电脑访问。

> 以下假设项目目录为 `/opt/Financial_Program`，请根据实际情况替换

### 1. 服务器环境准备

```bash
sudo apt update
sudo apt install -y mysql-server redis-server nodejs npm
```

安装 Miniconda：

```bash
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh -b
source ~/.bashrc
conda create -n br python=3.10 -y
```

### 2. 上传代码

```bash
scp -r Financial_Program/ user@server:/opt/
```

### 3. 配置数据库

```bash
sudo systemctl start mysql redis-server
sudo mysql -e "CREATE DATABASE IF NOT EXISTS financial_web_crawler CHARACTER SET utf8mb4;"
```

### 4. 配置环境变量

```bash
cd /opt/Financial_Program
cp .env.example backend/.env
vim backend/.env
```

### 5. 安装依赖

```bash
conda activate br
pip install -r backend/requirements.txt

cd frontend
npm install
```

### 6. 构建前端静态文件

```bash
cd frontend
npm run build
```

### 7. 启动后端服务

```bash
mkdir -p logs
cd backend
conda activate br
```

后台运行：

```bash
nohup python run.py > ../logs/backend.log 2>&1 &
```

### 8. 配置 Nginx

```bash
sudo apt install -y nginx
```

创建配置文件 `/etc/nginx/sites-available/financial`：

```nginx
server {
    listen 80;
    server_name _;

    # 前端静态文件（请替换为实际项目路径）
    location / {
        root /opt/Financial_Program/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # 后端 API 代理
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # 报告文件（请替换为实际项目路径）
    location /reports {
        alias /opt/Financial_Program/data/reports;
    }
}
```

启用配置：

```bash
sudo ln -s /etc/nginx/sites-available/financial /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

### 9. 开放防火墙

```bash
sudo ufw allow 80/tcp
```

### 10. 访问应用

在本地浏览器访问：`http://服务器IP地址`

---

## 使用 systemd 管理服务（推荐）

创建服务文件 `/etc/systemd/system/financial-backend.service`：

```ini
[Unit]
Description=Financial Program Backend
After=mysql.service redis.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/Financial_Program/backend
Environment="PATH=/root/miniconda3/envs/br/bin:/usr/bin"
ExecStart=/root/miniconda3/envs/br/bin/python run.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

> **注意**：请将 `/opt/Financial_Program` 和 `/root/miniconda3` 替换为实际路径

启用服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable financial-backend
sudo systemctl start financial-backend
```

查看状态：

```bash
sudo systemctl status financial-backend
sudo journalctl -u financial-backend -f
```

---

## 配置说明

### LLM 配置示例

| 服务     | LLM_BASE_URL                                        | LLM_MODEL       |
| -------- | --------------------------------------------------- | --------------- |
| 通义千问 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-plus`     |
| Deepseek | `https://api.deepseek.com`                          | `deepseek-chat` |
| OpenAI   | `https://api.openai.com/v1`                         | `gpt-4`         |

### 存储配置

```ini
# 本地存储（默认）
STORAGE_TYPE=local
LOCAL_STORAGE_DIR=./data/reports

# MinIO 对象存储
STORAGE_TYPE=minio
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
```

---

## 常用命令

```bash
# 启动/停止 MySQL 和 Redis (Homebrew)
brew services start mysql redis
brew services stop mysql redis

# 查看后端日志
tail -f logs/backend.log

# 停止后端进程
pkill -f "python run.py"

# 重启 Nginx
sudo systemctl restart nginx
```

---

## 项目结构

```
Financial_Program/
├── backend/                 # 后端 FastAPI
│   ├── ai/                  # AI 分析模块
│   │   ├── llm_agent.py     # 通用 LLM 客户端
│   │   ├── deepseek.py      # 兼容别名
│   │   └── report.py        # 报告生成
│   ├── api/                 # API 接口
│   ├── crawler/             # 数据采集
│   ├── storage/             # 存储模块
│   ├── services/            # 业务服务
│   ├── run.py               # 入口文件
│   └── requirements.txt     # Python 依赖
├── frontend/                # 前端 React
│   ├── src/
│   ├── vite.config.js       # Vite 配置
│   └── package.json
├── logs/                    # 日志目录
├── data/reports/            # 报告存储目录
├── .env.example             # 环境变量模板
├── docker-compose.dev.yml   # Docker 开发配置
└── scripts/                 # 启动脚本
```

---

## 许可证

MIT License
