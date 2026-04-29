# ============================================================
# STAGE 1: Dependencias
# ============================================================
FROM python:3.11-slim AS builder

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --user -r requirements.txt

# ============================================================
# STAGE 2: Imagen final
# ============================================================
FROM python:3.11-slim

RUN groupadd -r app && useradd -r -g app -d /app -s /bin/bash app

WORKDIR /app

COPY --from=builder /root/.local /root/.local
COPY . .

RUN mkdir -p logs data && chown -R app:app logs data

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app

EXPOSE 8000

USER app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
