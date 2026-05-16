# SWAT API — 短线致胜 AI 交易智能体
# Dockerfile — Python 3.11 Slim + FastAPI + Uvicorn

FROM python:3.11-slim

LABEL maintainer="SWAT Team" \
      description="短线致胜 AI 交易智能体 API 服务" \
      version="2.0.0"

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    SWAT_API_DEBUG=false \
    SWAT_API_RATE_LIMIT=10

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 创建工作目录
WORKDIR /app

# 先复制依赖文件，利用Docker缓存层
COPY requirements.txt ./

# 安装Python依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir \
        fastapi>=0.109.0 \
        uvicorn[standard]>=0.27.0 \
        aiohttp>=3.9.0 \
        aiocache>=0.12.0 \
        pydantic-settings>=2.1.0

# 复制应用代码
COPY api/ ./api/
COPY short_win_ai_trader/ ./short_win_ai_trader/
COPY tests/ ./tests/
COPY README.md ./

# 创建缓存目录
RUN mkdir -p /app/cache

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
