# AIMPOS-Spark Visual — API image (FastAPI monolith).
# Build context is the repo root so the local packages/ can be installed
# alongside the api source:
#   docker build -f api/Dockerfile -t aimpos-api .
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /srv

# Install the local packages first so the api's aimpos-core / aimpos-config
# dependencies resolve from the workspace (they are not published to PyPI).
COPY packages/aimpos-core ./packages/aimpos-core
COPY packages/aimpos-config ./packages/aimpos-config
RUN pip install ./packages/aimpos-core ./packages/aimpos-config

# Install the api and its third-party dependencies.
COPY api ./api
RUN pip install ./api

# Run as a non-root user.
RUN useradd --create-home --uid 10001 appuser
USER appuser

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
