# Dockerfile (place at repo root)
FROM python:3.11-slim

WORKDIR /usr/src/app

# System deps - required for some Python packages and psycopg2 build if needed
RUN apt-get update && \
    apt-get install -y build-essential gcc libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first (cache)
COPY requirements.txt .

# Upgrade pip and install requirements
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Expose port
EXPOSE 8000

# Use uvicorn to serve the FastAPI app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
