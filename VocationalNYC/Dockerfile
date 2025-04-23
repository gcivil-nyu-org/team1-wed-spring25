    # ---- Stage 1: Build ----
    FROM python:3.12.9-slim AS builder
    
    ARG SECRET_KEY
    ARG AWS_ACCESS_KEY_ID
    ARG AWS_SECRET_ACCESS_KEY
    ENV SECRET_KEY=$SECRET_KEY
    ENV AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID
    ENV AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY
    ENV PYTHONDONTWRITEBYTECODE=1 \
        PYTHONUNBUFFERED=1 \
        PYTHONPATH=/vocationalnyc \
        SECRET_KEY="2kr32wckkxtv&_r+p7!)o+1(jtupvk#z^uzp#y$h-=#3*7p5zr"
    
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
        PYTHONUNBUFFERED=1 \
        PYTHONPATH=/vocationalnyc
    
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
    