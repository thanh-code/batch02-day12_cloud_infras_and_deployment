# ============================================================
# ADVANCED Dockerfile - Multi-stage build
#
# Build from this folder:
#   docker build -t agent-production .
# ============================================================

FROM python:3.11-slim AS builder

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --timeout 120 --retries 10 --user -r requirements.txt


FROM python:3.11-slim AS runtime

RUN groupadd -r appuser && useradd -r -g appuser -d /home/appuser -m appuser

WORKDIR /app

COPY --from=builder /root/.local /home/appuser/.local
COPY main.py .
COPY utils/ ./utils/

RUN chown -R appuser:appuser /app /home/appuser

USER appuser

ENV PATH=/home/appuser/.local/bin:$PATH
ENV HOME=/home/appuser
ENV PYTHONPATH=/home/appuser/.local/lib/python3.11/site-packages:/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
