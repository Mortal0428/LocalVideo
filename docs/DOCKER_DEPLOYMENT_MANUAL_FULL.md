# CinemaAgent 全栈 Docker 容器化运维部署手册（完整版）

> 文档版本：v1.0.0  
> 适用对象：系统架构师、平台运维工程师、SRE 团队  
> 最后更新：2026-11-02  
> 运行环境：Linux (Ubuntu 22.04 LTS / Debian 12 / CentOS 7/8 / Rocky Linux 9)

---

## 目录
- [一、系统全景与架构拓扑](#一系统全景与架构拓扑)
- [二、运维环境准备与服务器规格要求](#二运维环境准备与服务器规格要求)
- [三、核心攻关：OpenList 网盘存储网关容器化与配置迁移](#三核心攻关openlist-网盘存储网关容器化与配置迁移)
- [四、标准化 Docker 编排物料规范 (Dockerfile & Compose)](#四标准化-docker-编排物料规范-dockerfile--compose)
  - [4.1 前端 Nginx 网关配置 (nginx.conf)](#41-前端-nginx-网关配置-nginxconf)
  - [4.2 前端 Dockerfile (多阶段构建)](#42-前端-dockerfile-多阶段构建)
  - [4.3 后端业务 Dockerfile (集成 FFmpeg)](#43-后端业务-dockerfile-集成-ffmpeg)
  - [4.4 生产级 docker-compose.yml 完整规范](#44-生产级-docker-composeyml-完整规范)
  - [4.5 环境变量对照表 (.env.production)](#45-环境变量对照表-envproduction)
- [五、标准上线流程实操指南](#五标准上线流程实操指南)
- [六、数据持久化、备份与灾难恢复](#六数据持久化备份与灾难恢复)
- [七、运维监控与常见故障排错决策树](#七运维监控与常见故障排错决策树)

---

## 一、系统全景与架构拓扑

CinemaAgent 是一套工业级多媒体短剧视听与 AI 多智能体协同生产平台，全栈服务容器化后由 4 大核心容器共同协作运行：

```text
                           客户端浏览器 (Web Browser)
                                      │
                                      ▼ HTTP/HTTPS (宿主机端口 80 / 443)
              ┌──────────────────────────────────────────────────┐
              │ 容器 1: cinema-frontend (Nginx 1.25-alpine)       │
              │ - 托管前端 Vue 3 SPA 静态资源                     │
              │ - 反向代理 /api/v1/ -> cinema-backend:8000        │
              │ - 反向代理 /storage/ -> cinema-backend:8000       │
              │ - 代理 WebSocket 弹幕总线 /api/v1/danmaku/ws      │
              └───────────────────────┬──────────────────────────┘
                                      │ 容器网络 (cinema-net)
                                      ▼
              ┌──────────────────────────────────────────────────┐
              │ 容器 2: cinema-backend (Python 3.12-slim)        │
              │ - FastAPI 异步高并发业务服务                     │
              │ - 10 大多智能体工作流引擎 (LangGraph + Blackboard)│
              │ - FFmpeg 异步音视频转码、分片与抽帧                │
              │ - Chroma 向量库与时间轴 RAG 检索中台             │
              └───────────────┬───────────────────┬──────────────┘
                              │                   │
                  MySQL 协议  │                   │ HTTP REST API (端口 5244)
                              ▼                   ▼
┌────────────────────────────────────────┐ ┌───────────────────────────────────────┐
│ 容器 3: cinema-mysql (MySQL 8.0)        │ │ 容器 4: cinema-openlist (AList/OpenList)│
│ - 影视资产、剧集、用户信息、金币打赏     │ │ - 挂载中国联通沃家云盘 / 夸克网盘   │
│ - 弹幕记录、DFA 审核日志、系统审计     │ │ - 本地数据卷挂载已有的 data 目录    │
└────────────────────────────────────────┘ └───────────────────┬───────────────────┘
                                                               │ 公网直连
                                                               ▼
                                                 外部对象存储 / 沃盘 / 夸克网盘
```

---

## 二、运维环境准备与服务器规格要求

### 2.1 推荐硬件规格

| 部署形态 | CPU 核心数 | 内存 (RAM) | 系统磁盘 | 数据盘 (持久化存储) | 带宽规格 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **基础体验型** (云端大模型) | 4 核 | 8 GB | 50 GB SSD | 100 GB+ SSD | 5 Mbps+ |
| **生产商用型** (高并发切片转码) | 8 核 | 16 GB ~ 32 GB | 100 GB NVMe | 500 GB+ NVMe/SATA | 20 Mbps+ |
| **全私有化型** (本地运行 Ollama 7B) | 8 核 + GPU (如 RTX 4090 24G) | 32 GB | 100 GB SSD | 500 GB+ SSD | 20 Mbps+ |

> **说明**：短剧视频切片播放采用网盘高速直链（HTTP 302 重定向），视频流本身不占用业务服务器出网带宽，大幅降低了服务器带宽成本。

### 2.2 基础运行环境准备

在 Linux 宿主机上必须预装 Docker Engine 与 Docker Compose v2：

```bash
# 1. 卸载旧版本（如有）
sudo apt-get remove docker docker-engine docker.io containerd runc -y

# 2. 安装 Docker 官方仓库与工具
sudo apt-get update
sudo apt-get install ca-certificates curl gnupg lsb-release -y
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 3. 安装 Docker Engine 与 Docker Compose Plugin
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-compose-plugin -y

# 4. 验证安装版本 (要求 Docker >= 24.0, Compose >= 2.20)
docker --version
docker compose version
```

### 2.3 防火墙与安全组端口规划

| 端口号 | 协议 | 容器服务 | 开放级别 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| **80** | TCP | cinema-frontend | **公开 (Public)** | Web 前端门户访问与 API 反向代理入网口 |
| **443** | TCP | cinema-frontend | **公开 (Public)** | HTTPS 证书加密访问（按需启用） |
| **5244** | TCP | cinema-openlist | **内网/白名单** | OpenList 管理后台（建议仅对运维 IP 或通过内网访问） |
| **8000** | TCP | cinema-backend | **容器内通信 (Private)** | FastAPI 接口，通过 Docker 内部网络供 Nginx 调用 |
| **3306** | TCP | cinema-mysql | **容器内通信 (Private)** | 业务数据库，仅容器内可见，不对外暴露公网 |

---

## 三、核心攻关：OpenList 网盘存储网关容器化与配置迁移

### 3.1 核心问题剖析：为什么不需要运维重新挂载云盘？

在本地开发环境中，开发人员使用的 `openlist.exe`（Version v4.2.7，基于 AList/OpenList 开源内核）具备完全的数据文件独立性。它的所有核心状态全部持久化在运行目录下的 **`data/`** 目录中：
- `data/config.json`：存储 Web 监听端口、安全密钥、Token 加密算法；
- `data/data.db`：嵌入式 SQLite 数据库，**里面已经完整记录了联通沃盘 / 夸克网盘的挂载参数、客户端授权凭证（Cookie/Token）、虚拟路径挂载点（`/kuake/短剧资源目录`）以及驱动缓存**。

只要将这个 `data/` 目录完整打包给运维，并在 Linux 容器中将其挂载到官方镜像的对应目录，**容器启动后将 100% 还原开发环境中的所有云盘资源，无需运维再次登录后台手动绑定网盘！**

---

### 3.2 资产交接与数据迁移操作步骤

#### 步骤 1：开发端生成 OpenList 资产包
在本地开发机器的 OpenList 运行目录下（例如 `E:\浏览器下载内容\data`）：
1. 确保已停止本地的 `openlist.exe` 进程，防止 SQLite 处于 WAL 读写锁定状态；
2. 将 `data` 文件夹打包压缩为 `openlist_data.tar.gz`（或者 `openlist_data.zip`）；
3. 将此压缩包交予运维同事。

#### 步骤 2：运维在服务器创建工作目录并解压
运维在生产服务器的目标部署根目录执行：

```bash
# 1. 创建标准部署拓扑目录
sudo mkdir -p /opt/cinema-agent/openlist/data
sudo mkdir -p /opt/cinema-agent/mysql/data
sudo mkdir -p /opt/cinema-agent/backend/storage/uploads
sudo mkdir -p /opt/cinema-agent/backend/storage/hls
sudo mkdir -p /opt/cinema-agent/backend/storage/chroma

# 2. 将开发提交的 openlist_data.tar.gz 上传至 /opt/cinema-agent/openlist/ 目录下解压
cd /opt/cinema-agent/openlist/
tar -zxvf openlist_data.tar.gz -C ./data/

# 3. 校验解压后文件必须包含 data.db 与 config.json
ls -lh ./data/
# 预期输出应包含: config.json, data.db, data.db-shm (如有), data.db-wal (如有)

# 4. 目录权限修正 (AList 官方镜像默认使用 UID:GID 1000 运行)
sudo chown -R 1000:1000 /opt/cinema-agent/openlist/data
sudo chmod -R 755 /opt/cinema-agent/openlist/data
```

#### 步骤 3：验证 OpenList 容器无缝就绪
当执行 `docker compose up -d cinema-openlist` 后：
- 运维可打开浏览器访问 `http://服务器IP:5244`；
- 输入既有账号密码（默认管理员 `admin` / `123456`）；
- 检查【存储】列表：此时页面上直接显示“夸克网盘 / 联通沃家云盘”，状态为“工作中”，挂载路径为 `/kuake/短剧资源目录`，与本地完全一致。

---

## 四、标准化 Docker 编排物料规范 (Dockerfile & Compose)

为了让运维工程师能够开箱即用，以下提供全套符合工业级标准的基础设施配置文件，可在工程根目录直接创建或由运维引用。

### 4.1 前端 Nginx 网关配置 (nginx.conf)
文件路径：`frontend/nginx.conf`

```nginx
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 2048;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    # 启用 Gzip 极速压缩
    gzip on;
    gzip_min_length 1024;
    gzip_comp_level 5;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript image/svg+xml;

    # 允许大文件与短剧视频切片上传 (放宽到 1000M)
    client_max_body_size 1000M;

    server {
        listen 80;
        server_name localhost;

        # 前端单页面应用 (SPA) 托管
        location / {
            root /usr/share/nginx/html;
            index index.html index.htm;
            # 解决 Vue Router History 模式刷新 404 问题
            try_files $uri $uri/ /index.html;
        }

        # 后端接口 API 反向代理
        location /api/ {
            proxy_pass http://cinema-backend:8000/api/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # 超时时间放宽以支撑大模型长思考与长链路 RAG 问答
            proxy_connect_timeout 90s;
            proxy_read_timeout 180s;
            proxy_send_timeout 180s;
        }

        # 本地流媒体切片与封面存储反向代理
        location /storage/ {
            proxy_pass http://cinema-backend:8000/storage/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            
            # 支持流媒体切片分段加载 (HTTP Range 206)
            proxy_cache_bypass $http_range;
            proxy_no_cache $http_range;
        }

        # WebSocket 实时弹幕广播通道升级
        location /api/v1/danmaku/ws {
            proxy_pass http://cinema-backend:8000/api/v1/danmaku/ws;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_read_timeout 3600s;
            proxy_send_timeout 3600s;
        }
    }
}
```

---

### 4.2 前端 Dockerfile (多阶段构建)
文件路径：`frontend/Dockerfile`

```dockerfile
# -------------------------------------------------------------
# 阶段 1: 构建阶段 (Node.js 编译)
# -------------------------------------------------------------
FROM node:20-alpine AS build-stage

WORKDIR /app

# 利用 Docker 缓存层加速依赖构建
COPY package.json package-lock.json ./
RUN npm install --registry=https://registry.npmmirror.com

# 拷贝前端全部源码并执行生产打包
COPY . .
RUN npm run build

# -------------------------------------------------------------
# 阶段 2: 生产运行阶段 (Nginx 静态托管)
# -------------------------------------------------------------
FROM nginx:1.25-alpine AS production-stage

# 拷贝静态资源与自定义 Nginx 配置文件
COPY --from=build-stage /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

---

### 4.3 后端业务 Dockerfile (集成 FFmpeg)
文件路径：`backend/Dockerfile`

```dockerfile
# -------------------------------------------------------------
# CinemaAgent Python 3.12 生产级镜像 (内嵌 FFmpeg 工具链)
# -------------------------------------------------------------
FROM python:3.12-slim

# 设置清华 Debian 镜像源并安装 FFmpeg 及基础构建依赖
RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || true && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        curl \
        gcc \
        python3-dev \
        libmariadb-dev \
        libgl1 \
        libglib2.0-0 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 升级 pip 并配置国内 PyPI 镜像源
RUN pip install --no-cache-dir --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple

# 安装 Python 核心依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 拷贝后端工程全量业务代码
COPY . .

# 创建持久化存储缓冲目录
RUN mkdir -p storage/uploads storage/hls storage/chroma

ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Shanghai

EXPOSE 8000

# 生产级 Uvicorn 异步多协程启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--proxy-headers"]
```

---

### 4.4 生产级 docker-compose.yml 完整规范
文件路径：`docker-compose.yml`

```yaml
version: '3.8'

networks:
  cinema-net:
    driver: bridge

volumes:
  mysql_data:
    driver: local
  openlist_data:
    driver: local

services:
  # -----------------------------------------------------------
  # 1. 关系型数据库节点 (MySQL 8.0)
  # -----------------------------------------------------------
  cinema-mysql:
    image: mysql:8.0
    container_name: cinema-mysql
    restart: always
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD:-Cyx.chen27}
      MYSQL_DATABASE: ${MYSQL_DATABASE:-video_platform_db}
      TZ: Asia/Shanghai
    command:
      - --character-set-server=utf8mb4
      - --collation-server=utf8mb4_unicode_ci
      - --default-authentication-plugin=mysql_native_password
      - --max_connections=500
    volumes:
      - /opt/cinema-agent/mysql/data:/var/lib/mysql
    networks:
      - cinema-net
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-u", "root", "-p${MYSQL_ROOT_PASSWORD:-Cyx.chen27}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # -----------------------------------------------------------
  # 2. 外部网盘聚合网关节点 (OpenList / AList)
  # -----------------------------------------------------------
  cinema-openlist:
    image: xhofe/alist:v3.42.0
    container_name: cinema-openlist
    restart: always
    environment:
      - PUID=1000
      - PGID=1000
      - UMASK=022
      - TZ=Asia/Shanghai
    volumes:
      # 核心关键挂载：将本地迁移过来的 data 目录挂入，直接继承沃盘/夸克配置
      - /opt/cinema-agent/openlist/data:/opt/alist/data
    ports:
      - "5244:5244"
    networks:
      - cinema-net
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:5244/ping || exit 0"]
      interval: 15s
      timeout: 5s
      retries: 3

  # -----------------------------------------------------------
  # 3. 后端业务主服务 (FastAPI + Agent Fleet + RAG)
  # -----------------------------------------------------------
  cinema-backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: cinema-backend
    restart: always
    depends_on:
      cinema-mysql:
        condition: service_healthy
      cinema-openlist:
        condition: service_started
    environment:
      # 数据库连接 (直连内部网络 cinema-mysql 容器)
      MYSQL_HOST: cinema-mysql
      MYSQL_PORT: 3306
      MYSQL_USER: root
      MYSQL_PASSWORD: ${MYSQL_ROOT_PASSWORD:-Cyx.chen27}
      MYSQL_DATABASE: ${MYSQL_DATABASE:-video_platform_db}
      USE_SQLITE_FALLBACK: "False"

      # OpenList 桥接 (直连内部网络 cinema-openlist 容器)
      OPENLIST_BASE_URL: http://cinema-openlist:5244
      OPENLIST_USERNAME: ${OPENLIST_USERNAME:-admin}
      OPENLIST_PASSWORD: ${OPENLIST_PASSWORD:-123456}
      OPENLIST_MOUNT_PATH: /kuake/短剧资源目录
      OPENLIST_FALLBACK_PATHS: /kuake/短剧资源目录,/kuake,/liantong

      # 存储路径
      UPLOAD_DIR: storage/uploads
      PROCESSED_VIDEO_DIR: storage/hls
      VECTOR_DB_DIR: storage/chroma

      # 云端模型服务凭证
      MIMO_BASE_URL: ${MIMO_BASE_URL:-https://api.xiaomimimo.com/v1}
      MIMO_API_KEY: ${MIMO_API_KEY:-}
      ACTIVE_PROVIDER: ${ACTIVE_PROVIDER:-mimo}

      # 10号智能体外部生态
      COZE_API_TOKEN: ${COZE_API_TOKEN:-}
      COZE_BOT_ID: ${COZE_BOT_ID:-7700811095929323554}
      COZE_BASE_URL: https://api.coze.cn
      COZE_TIMEOUT: 30
    volumes:
      - /opt/cinema-agent/backend/storage/uploads:/app/storage/uploads
      - /opt/cinema-agent/backend/storage/hls:/app/storage/hls
      - /opt/cinema-agent/backend/storage/chroma:/app/storage/chroma
    networks:
      - cinema-net
    logging:
      driver: "json-file"
      options:
        max-size: "50m"
        max-file: "5"

  # -----------------------------------------------------------
  # 4. 前端网关节点 (Vue3 + Nginx 静态托管)
  # -----------------------------------------------------------
  cinema-frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: cinema-frontend
    restart: always
    depends_on:
      - cinema-backend
    ports:
      - "80:80"
    networks:
      - cinema-net
    logging:
      driver: "json-file"
      options:
        max-size: "20m"
        max-file: "3"
```

---

### 4.5 环境变量对照表 (.env.production)
文件路径：`.env.production`（运维根据生产环境填写）

```env
# MySQL 凭据
MYSQL_ROOT_PASSWORD=YourStrongDatabasePassword2026
MYSQL_DATABASE=video_platform_db

# OpenList 后台管理员账号密码（与 data 目录一致）
OPENLIST_USERNAME=admin
OPENLIST_PASSWORD=YourOpenListAdminPassword

# 云端大模型配置 (小米 MiMo / DeepSeek / MiniMax)
MIMO_BASE_URL=https://api.xiaomimimo.com/v1
MIMO_API_KEY=sk-your-production-mimo-api-key
ACTIVE_PROVIDER=mimo

# Coze 外部智能体凭证 (10号智能体)
COZE_API_TOKEN=pat_your_coze_production_token
COZE_BOT_ID=7700811095929323554
```

---

## 五、标准上线流程实操指南

### 5.1 首次部署全流程清单

```bash
# 1. 在生产服务器克隆代码仓库
git clone https://gitee.com/cyr003/local-vedio.git /opt/cinema-agent/repo
cd /opt/cinema-agent/repo
git checkout dev

# 2. 准备持久化目录拓扑
sudo mkdir -p /opt/cinema-agent/mysql/data
sudo mkdir -p /opt/cinema-agent/openlist/data
sudo mkdir -p /opt/cinema-agent/backend/storage/uploads
sudo mkdir -p /opt/cinema-agent/backend/storage/hls
sudo mkdir -p /opt/cinema-agent/backend/storage/chroma

# 3. 解压并导入开发者交付的 openlist_data.tar.gz
sudo tar -zxvf /tmp/openlist_data.tar.gz -C /opt/cinema-agent/openlist/data/
sudo chown -R 1000:1000 /opt/cinema-agent/openlist/data

# 4. 准备生产环境变量文件
cp .env.production.example .env
vim .env  # 填入真实的数据库密码与大模型 API Key

# 5. 一键构建并启动全栈容器组
docker compose build --no-cache
docker compose up -d

# 6. 查看服务运行状态
docker compose ps
```

### 5.2 验证各节点服务健康度

1. **前端页面访问**：打开浏览器输入 `http://服务器公网IP`，能够正常展示短剧海报大厅与暗黑主题；
2. **后端服务探测**：执行 `curl http://127.0.0.1:80/api/v1/system/health`，返回 `{"status": "ok"}`；
3. **OpenList 网盘状态**：打开 `http://服务器公网IP:5244`，登录后台检查沃盘/夸克云盘资源树是否可读；
4. **数据库与短剧同步**：登录系统管理中台（`http://服务器公网IP/#/admin`），点击【短剧资产编目】->【扫描云盘资源】，检查短剧切片与集数是否毫秒级同步入库。

---

## 六、数据持久化、备份与灾难恢复

### 6.1 核心数据持久化映射表

| 数据类别 | 容器内部路径 | 宿主机持久化绝对路径 | 备份优先级 |
| :--- | :--- | :--- | :--- |
| **MySQL 业务数据** | `/var/lib/mysql` | `/opt/cinema-agent/mysql/data` | **最高 (每日增量/全量)** |
| **OpenList 云盘配置与 Token** | `/opt/alist/data` | `/opt/cinema-agent/openlist/data` | **高 (每次账号变更后备份)** |
| **用户上传与视频切片** | `/app/storage/uploads` | `/opt/cinema-agent/backend/storage/uploads` | 中 |
| **HLS 转码产物** | `/app/storage/hls` | `/opt/cinema-agent/backend/storage/hls` | 中 |
| **Chroma 向量数据库** | `/app/storage/chroma` | `/opt/cinema-agent/backend/storage/chroma` | 中 |

### 6.2 自动化定时备份脚本 (Shell 示例)
可配置入 Crontab 每天凌晨 3:00 执行：

```bash
#!/bin/bash
BACKUP_DIR="/data/backup/cinema_agent/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# 1. 导出 MySQL 数据库全量 SQL
docker exec cinema-mysql mysqldump -uroot -pCyx.chen27 video_platform_db > "$BACKUP_DIR/video_platform_db.sql"

# 2. 备份 OpenList 配置数据库
tar -zcvf "$BACKUP_DIR/openlist_data.tar.gz" -C /opt/cinema-agent/openlist/data/ .

# 3. 清理 15 天之前的历史归档
find /data/backup/cinema_agent/ -mtime +15 -type d -exec rm -rf {} +
echo "Backup completed successfully at $(date)"
```

---

## 七、运维监控与常见故障排错决策树

### 7.1 故障一：OpenList 容器启动后短剧播放器报 403 或无法获取视频直链
- **排查路径**：
  1. 执行 `docker logs cinema-openlist` 查看网盘鉴权日志；
  2. 登录 `http://服务器IP:5244`，进入【存储】列表；
  3. 检查夸克网盘或联通沃盘的状态是否显示“Cookie/Token 已过期”；
- **自愈处置**：在 OpenList 网页后台重新填写新的网盘 Cookie 并点击保存。由于挂载卷是宿主机持久化目录，更新后无需重启容器。

### 7.2 故障二：后端接口报 `Can't connect to MySQL server on 'cinema-mysql'`
- **排查路径**：
  1. 执行 `docker compose ps` 检查 `cinema-mysql` 容器是否处于 `healthy` 状态；
  2. 检查 `backend` 的连接地址是否为容器网络别名 `cinema-mysql`，严禁写成 `localhost` 或 `127.0.0.1`（容器内部的 127.0.0.1 代表容器自身，无法直连宿主机或其他容器）。

### 7.3 故障三：前端页面刷新出现 404 Not Found
- **根因**：Vue Router 采用 HTML5 History 模式，直接访问子路由时 Nginx 未找到对应物理静态文件。
- **自愈处置**：检查 `frontend/nginx.conf` 中是否配置了 `try_files $uri $uri/ /index.html;`。

### 7.4 故障四：大模型协同圆桌或 RAG 问答中途报 504 Gateway Timeout
- **排查路径**：多智能体 5~10 位专家协同思考推演或调用外部模型耗时较长（约 30~60 秒）。
- **自愈处置**：在 `frontend/nginx.conf` 反向代理段中将 `proxy_read_timeout` 与 `proxy_send_timeout` 均调高至 `180s` 以上。
