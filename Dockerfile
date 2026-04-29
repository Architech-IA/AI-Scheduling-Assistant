# ============================================================
# STAGE 1: Dependencias
# ============================================================
FROM python:3.11-slim AS builder

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt --target /opt/deps

# ============================================================
# STAGE 2: Imagen final
# ============================================================
FROM python:3.11-slim

RUN groupadd -r app && useradd -r -g app -d /app -s /bin/bash app

WORKDIR /app

COPY --from=builder /opt/deps /opt/deps
COPY . .

RUN mkdir -p logs data && chown -R app:app logs data

ENV PYTHONPATH=/opt/deps:/app
ENV PATH=/opt/deps/bin:$PATH

EXPOSE 8000

USER app

CMD ["python3", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
