# AIMPOS-Spark Visual — Temporal worker stub (Sprint 1).
# Full workflow registration lands in US-07 (Sprint 2).
# Build context is the repo root for parity with api/.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /srv

COPY packages/aimpos-core ./packages/aimpos-core
COPY packages/aimpos-config ./packages/aimpos-config
RUN pip install ./packages/aimpos-core ./packages/aimpos-config

COPY configs ./configs
COPY worker ./worker
ENV AIMPOS_CONFIG_ROOT=/srv/configs
RUN pip install ./worker

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg espeak-ng \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --uid 10002 worker
USER worker

CMD ["python", "-m", "app.main"]
