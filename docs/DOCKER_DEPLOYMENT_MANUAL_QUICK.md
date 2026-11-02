# CinemaAgent Docker 极速交付实操指引（简洁版）

> 面向对象：一线实施运维工程师  
> 预计耗时：5 ~ 10 分钟快速点亮服务  
> 架构原则：全容器化编排、OpenList 资产包无缝继承、开箱即用

---

## 一、交付物料说明（开发已准备好）

在部署前，请准备以下核心物料：
1. **项目源码仓库**：`git clone https://gitee.com/cyr003/local-vedio.git`（切换至 `dev` 分支）
   - 工程中已内置开箱即用的 `docker-compose.yml`、`frontend/Dockerfile`、`frontend/nginx.conf`、`backend/Dockerfile`、`cinema-ollama` 容器编排与 `.env.production.example`。
2. **OpenList 网盘数据包**：`openlist_data.tar.gz`（内含已在本地配置调试好的联通沃盘/夸克云盘账号凭据与数据，**无需运维在服务器上重新绑定网盘！**）
3. **本地大模型权重（可选）**：
   - **方式 A（云端免部署，推荐）**：无需模型文件，直接在 `.env` 配置商用 API（如小米 MiMo 或 DeepSeek），服务器零显存开销。
   - **方式 B（离线私有化部署）**：若服务器支持联网，启动容器后一行命令自动 pull；若为纯离线内网，将开发提供的 `ollama_models.tar.gz` 解压至 `/opt/cinema-agent/ollama`。

---

## 二、5 分钟快速部署流水线（纯命令可直接复制）

### 步骤 1：创建服务器工作目录并解压数据资产
登录 Linux 宿主机执行：

```bash
# 1. 递归创建业务持久化目录 (含数据库、网盘、存储与大模型目录)
sudo mkdir -p /opt/cinema-agent/mysql/data
sudo mkdir -p /opt/cinema-agent/openlist/data
sudo mkdir -p /opt/cinema-agent/ollama
sudo mkdir -p /opt/cinema-agent/backend/storage/uploads
sudo mkdir -p /opt/cinema-agent/backend/storage/hls
sudo mkdir -p /opt/cinema-agent/backend/storage/chroma

# 2. 将开发的 openlist_data.tar.gz 拷贝至服务器并解压到 openlist/data
# (假设你已将压缩包上传到 /tmp/openlist_data.tar.gz)
sudo tar -zxvf /tmp/openlist_data.tar.gz -C /opt/cinema-agent/openlist/data/

# 3. 关键校验：确保解压后的文件直接位于 data 目录下，绝不可嵌套多一层 data/
ls -l /opt/cinema-agent/openlist/data/config.json
ls -l /opt/cinema-agent/openlist/data/data.db

# 4. 修正权限 (AList/OpenList 官方镜像默认以 UID 1000 运行)
sudo chown -R 1000:1000 /opt/cinema-agent/openlist/data
sudo chmod -R 755 /opt/cinema-agent/openlist/data
```

---

### 步骤 2：克隆代码仓库并配置环境变量

```bash
# 1. 拉取工程代码并切换到 dev 分支
git clone https://gitee.com/cyr003/local-vedio.git /opt/cinema-agent/repo
cd /opt/cinema-agent/repo
git checkout dev

# 2. 从内置模板复制生产环境变量
cp .env.production.example .env

# 3. 检查或编辑 .env 配置文件 (默认已配置好本地 Ollama 容器与 MySQL 互联)
cat << 'EOF' > .env
# 基础服务配置
MYSQL_ROOT_PASSWORD=Cyx.chen27
MYSQL_DATABASE=video_platform_db
OPENLIST_USERNAME=admin
OPENLIST_PASSWORD=123456

# 大模型配置 (默认走本地私有化容器 cinema-ollama)
ACTIVE_PROVIDER=ollama
OLLAMA_BASE_URL=http://cinema-ollama:11434
DEFAULT_LLM_MODEL=deepseek-r1:1.5b
DEFAULT_EMBEDDING_MODEL=qwen3-embedding:0.6b

# 云端备用 (若切换 ACTIVE_PROVIDER=mimo 则生效)
MIMO_BASE_URL=https://api.xiaomimimo.com/v1
MIMO_API_KEY=
EOF
```

---

### 步骤 3：一键构建并启动全栈容器组

在 `/opt/cinema-agent/repo` 目录下直接执行：

```bash
# 构建镜像并后台拉起容器组 (包含 frontend、backend、mysql、openlist、ollama)
docker compose build
docker compose up -d

# 检查服务健康状态
docker compose ps
```

预期正常输出如下（5 个容器全部处于 `Up` 或 `healthy` 状态）：
```text
NAME                IMAGE                  COMMAND                  SERVICE             STATUS
cinema-backend      repo-cinema-backend    "uvicorn main:app --…"   cinema-backend      Up
cinema-frontend     repo-cinema-frontend   "/docker-entrypoint.…"   cinema-frontend     Up (healthy)
cinema-mysql        mysql:8.0              "docker-entrypoint.s…"   cinema-mysql        Up (healthy)
cinema-openlist     xhofe/alist:v3.42.0    "/entrypoint.sh"         cinema-openlist     Up (healthy)
cinema-ollama       ollama/ollama:latest   "/bin/ollama serve"      cinema-ollama       Up
```

---

### 步骤 4：本地大模型权重初始化（仅当使用本地 Ollama 时）

若目标服务器可以联网，直接在容器中拉取所需轻量模型（下载极快，约 1.5GB）：
```bash
docker exec -it cinema-ollama ollama pull deepseek-r1:1.5b
docker exec -it cinema-ollama ollama pull qwen3-embedding:0.6b
```

若目标服务器为纯离线无外网环境：
在启动前将开发导出的 `ollama_models.tar.gz` 解压至宿主机挂载目录即可：
```bash
sudo tar -zxvf /tmp/ollama_models.tar.gz -C /opt/cinema-agent/ollama/
```

---

## 三、快速验收与健康检查

| 检查项 | 验证方式 | 预期结果与默认凭据 |
| :--- | :--- | :--- |
| **前端门户访问** | 浏览器打开 `http://服务器公网IP` | 正常展示短剧影院大厅与暗黑拟态界面 |
| **管理后台登录** | 浏览器打开 `http://服务器公网IP/#/login` | 使用初始管理员账号：`admin`，默认密码：`admin123` |
| **后端 API 健康** | 执行 `curl http://127.0.0.1/api/v1/system/health` | 返回 `{"status": "ok"}` 状态码 200 |
| **OpenList 状态** | 浏览器打开 `http://服务器公网IP:5244` | 使用默认账号 `admin`/`123456` 登录，能看到“夸克/联通沃盘”且状态为“工作中” |
| **短剧切片播放** | 打开播放器播放任意短剧 | 视频秒开加载，时间轴 RAG 问答与弹幕正常滚动 |

---

## 四、常用日常运维操作速查

```bash
# 查看所有服务的实时日志
docker compose logs -f

# 仅查看后端业务接口与智能体日志
docker compose logs -f cinema-backend

# 仅查看 OpenList 云盘挂载日志
docker compose logs -f cinema-openlist

# 重启全套系统
docker compose restart

# 平滑停止全套服务 (不丢失持久化数据)
docker compose down
```
