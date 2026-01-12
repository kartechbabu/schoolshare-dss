# DSS App v2 - Dockerfile for Digital Ocean deployment
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for geopandas + curl for health check
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY app.py .
COPY .streamlit/ ./.streamlit/

# Create data directories (will be mounted or populated at runtime)
RUN mkdir -p data/processed data/raw data/census

# Set environment variables
ENV DSS_BASE_PATH=/app
ENV DSS_DATA_PATH=/app/data
ENV DSS_CENSUS_PATH=/app/data/census
ENV DSS_PROCESSED_PATH=/app/data/processed
ENV PYTHONPATH=/app/src

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
