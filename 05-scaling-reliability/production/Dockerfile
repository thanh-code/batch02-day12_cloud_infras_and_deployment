# ============================================================
# Stateless scaling demo Dockerfile
#
# Build from this folder:
#   docker build -t stateless-agent .
# ============================================================

FROM python:3.11-slim AS builder

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --timeout 120 --retries 10 --user -r requirements.txt


FROM python:3.11-slim AS runtime

RUN groupadd -r agent && useradd -r -g agent -d /home/agent -m agent

WORKDIR /app

COPY --from=builder /root/.local /home/agent/.local
COPY app.py .
COPY utils/ ./utils/

RUN chown -R agent:agent /app /home/agent

USER agent

ENV PATH=/home/agent/.local/bin:$PATH
ENV HOME=/home/agent
ENV PYTHONPATH=/home/agent/.local/lib/python3.11/site-packages:/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
