FROM node:20-slim AS node-builder

WORKDIR /build

COPY package.json package-lock.json ./
RUN npm ci

COPY vite.config.js tsconfig*.json ./
COPY engine/web/react/ engine/web/react/
RUN npm run build

FROM python:3.12-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

COPY requirements.txt ./
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install --no-compile --requirement requirements.txt \
    && find /opt/venv -type d \( -name __pycache__ -o -name test -o -name tests \) -prune -exec rm -rf '{}' + \
    && find /opt/venv -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete \
    && rm -rf /opt/venv/lib/python3.12/site-packages/lightrag/api \
        /opt/venv/lib/python3.12/site-packages/lightrag/tools \
        /opt/venv/lib/python3.12/site-packages/pip \
        /opt/venv/lib/python3.12/site-packages/pip-* \
        /opt/venv/lib/python3.12/site-packages/pkg_resources \
        /opt/venv/lib/python3.12/site-packages/setuptools \
        /opt/venv/lib/python3.12/site-packages/setuptools-* \
        /opt/venv/bin/lightrag-server \
        /opt/venv/bin/pip \
        /opt/venv/bin/pip3 \
        /opt/venv/bin/pip3.12

FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/opt/venv/bin:${PATH}"

RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --no-create-home --home /nonexistent --shell /usr/sbin/nologin app

RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY --chown=root:root . /app
COPY --from=node-builder /build/engine/web/static/js /app/engine/web/static/js

RUN mkdir -p /app/.data \
    && chown -R app:app /app/.data \
    && chmod 0750 /app/.data

USER app:app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/', timeout=3).read()" || exit 1

CMD ["python", "/app/sg", "web", "--host", "0.0.0.0"]
