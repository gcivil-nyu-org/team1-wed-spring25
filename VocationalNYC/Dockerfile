    # ---- Stage 1: Build ----
    FROM python:3.12.9-slim AS builder

    ENV PYTHONDONTWRITEBYTECODE=1 \
        PYTHONUNBUFFERED=1
    
    RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        && rm -rf /var/lib/apt/lists/*
    
    WORKDIR /vocationalnyc
    
    COPY requirements.txt .
    RUN pip install --upgrade pip && \
        pip install --no-cache-dir -r requirements.txt
    
    COPY . .
    
    RUN python manage.py collectstatic --noinput
    
    # ---- Stage 2: Runtime ----
    FROM python:3.12.9-slim
    
    ENV PYTHONDONTWRITEBYTECODE=1 \
        PYTHONUNBUFFERED=1
    
    RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
        && rm -rf /var/lib/apt/lists/*
    
    WORKDIR /vocationalnyc
    
    COPY --from=builder /usr/local /usr/local
    COPY --from=builder /vocationalnyc /vocationalnyc
    
    COPY entrypoint.sh /entrypoint.sh
    RUN chmod +x /entrypoint.sh
    
    RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
    USER appuser
    
    EXPOSE 5000
    
    ENTRYPOINT ["/entrypoint.sh"]
    