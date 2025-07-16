FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies including ffmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
# COPY requirements.txt .
COPY pyproject.toml .
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Copy application code
COPY src/ ./src/

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Create necessary directories
RUN mkdir -p /app/input /app/output /app/credentials

# Clean up unnecessary files
RUN rm -rf /root/.cache/pip/* && \
    rm -rf /tmp/*

# Set entrypoint
ENTRYPOINT ["./entrypoint.sh"]

# Default command
CMD ["python", "-m", "src.main"]