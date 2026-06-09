# Use a stable python base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system utilities needed for building packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy python dependencies
COPY requirements.txt .

# Install dependencies without local caching to minimize image size
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend source files
COPY . .

# Preload Hugging Face model weights during the build phase
RUN python preload_model.py

# Expose backend port
EXPOSE 8000

# Start FastAPI server via Uvicorn
CMD ["python", "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
