# Global ARG for Python version
ARG PYTHON_VERSION=3.10

# Step 0: compile-frontend(not included in final image)  
FROM node:22-bookworm-slim AS compile-frontend

# You can override these if your structure differs
ARG FRONTEND_DIR=frontend
ARG FRONTEND_OUT=dist

# /app is the ultimate working directory
# with manage.py in /app/manage.py 
# and .
WORKDIR /app/${FRONTEND_DIR}

# Install deps with cache-friendly order
# (copy lockfiles first for better layer caching)
COPY ${FRONTEND_DIR}/package*.json ./

RUN set -eux; \
    if [ -f package-lock.json ]; then npm ci; \
    else echo "No package-lock.json; running npm install"; npm install; fi

# Copy frontend source and build
COPY ${FRONTEND_DIR}/ ./
RUN npm run build

# Stage 1: Python dependencies builder
FROM python:${PYTHON_VERSION}-slim-bookworm AS python-builder

# Re-declare ARGs in this stage
# ARG TORCH_VERSION=2.1.2+cu121
# ARG TORCHAUDIO_VERSION=2.1.2+cu121
ARG FASTER_WHISPER_VERSION=1.0.3

# 设置pip清华源和HuggingFace镜像
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple/ \
    && pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn
    
ENV HF_ENDPOINT=https://hf-mirror.com

WORKDIR /app
COPY backend/requirements.txt .

# Install dependencies to system directory
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir \
        faster-whisper==${FASTER_WHISPER_VERSION} \
    && pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
# FROM python:${PYTHON_VERSION}-slim-bookworm AS runtime
FROM nvidia/cuda:12.3.2-cudnn9-runtime-ubuntu22.04 AS runtime

# 设置清华源 (Ubuntu)
RUN sed -i 's@archive.ubuntu.com@mirrors.tuna.tsinghua.edu.cn@g' /etc/apt/sources.list \
    && sed -i 's@security.ubuntu.com@mirrors.tuna.tsinghua.edu.cn@g' /etc/apt/sources.list

# Install only runtime dependencies (no dev packages)
# 根据是否存在 package-lock.json 来决定用 npm ci 还是 npm install。
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Python packages from builder (system-wide installation)
COPY --from=python-builder /usr/local /usr/local

# Copy frontend build from compile-frontend stage
COPY --from=compile-frontend /app/frontend/dist /app/static

# Copy backend code only
COPY backend/ .

# Create user and directories
RUN useradd --create-home --uid 1000 vidgo \
    && mkdir -p /app/media /app/models \
    && chown -R vidgo:vidgo /app

USER vidgo
# default port at 8000
EXPOSE 8000

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=vid_go.settings \
    HF_ENDPOINT=https://hf-mirror.com \
    HUGGINGFACE_HUB_CACHE=/app/models/.cache/huggingface

VOLUME ["/app/media", "/app/models"]

# Use gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120", "vid_go.wsgi:application"]