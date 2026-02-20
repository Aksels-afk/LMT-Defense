# LMT Defence - Dockerfile

FROM python:3.14-slim

WORKDIR /app

# Install dependencies globally
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (includes schema.sql)
COPY app/ ./app/

# Expose FastAPI port
EXPOSE 8000

# Initialize database and start server
# Note: DB initialization happens on first run if DB doesn't exist
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
