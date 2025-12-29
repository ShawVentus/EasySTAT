# EasySTAT Docker 部署指南

## 系统要求

- Docker 20.10+
- 至少 4GB 可用内存
- 网络能访问：
  - `registry.npmmirror.com`（npm 包下载）
  - `pypi.tuna.tsinghua.edu.cn`（Python 包下载）
  - `openapi.dp.tech`（LLM API）

---

## 快速开始

### 1. 构建镜像

```bash
# 进入项目根目录（包含 EasySTAT、easystat-webui、OpenRepo 三个子目录）
cd /path/to/br_competition

# 构建 Docker 镜像
docker build -f EasySTAT/Dockerfile -t easystat:latest .
```

构建时间约 5-10 分钟，取决于网络速度。

### 2. 运行容器

```bash
docker run -d \
  --name easystat \
  -p 50001:50001 \
  easystat:latest
```

### 3. 验证服务

```bash
# 检查容器状态
docker ps

# 检查健康接口
curl http://localhost:50001/

# 查看日志
docker logs -f easystat
```

### 4. 访问服务

打开浏览器访问：`http://localhost:50001`

---

## 一键启动指令

```bash
docker run -d --name easystat -p 50001:50001 easystat:latest
```

---

## 常用命令

| 操作     | 命令                                 |
| -------- | ------------------------------------ |
| 查看日志 | `docker logs -f easystat`            |
| 停止容器 | `docker stop easystat`               |
| 启动容器 | `docker start easystat`              |
| 删除容器 | `docker rm easystat`                 |
| 进入容器 | `docker exec -it easystat /bin/bash` |

---

## 数据持久化（可选）

如需保留分析结果，可挂载数据目录：

```bash
docker run -d \
  --name easystat \
  -p 50001:50001 \
  -v $(pwd)/data:/app/EasySTAT/data \
  -v $(pwd)/result:/app/EasySTAT/result \
  -v $(pwd)/logs:/app/EasySTAT/logs \
  easystat:latest
```

---

## 故障排查

### 问题 1：构建失败 - npm 依赖下载超时

**解决方案**：检查网络，或手动设置 npm 镜像：

```bash
npm config set registry https://registry.npmmirror.com
```

### 问题 2：容器启动后无法访问

**检查步骤**：

1. `docker ps` 确认容器运行中
2. `docker logs easystat` 查看错误日志
3. 确认端口 50001 未被占用

### 问题 3：CrewAI 分析失败

**可能原因**：LLM API 无法访问
**检查命令**：

```bash
docker exec easystat curl -I https://openapi.dp.tech/openapi/v1
```
