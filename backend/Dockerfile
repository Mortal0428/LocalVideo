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
