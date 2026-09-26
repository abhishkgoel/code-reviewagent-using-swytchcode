# DevPilot Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Swytchcode CLI
RUN curl -fsSL https://raw.githubusercontent.com/swytchcodehq/swytchcode-cli/main/install.sh | bash || true

# Copy backend requirements
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy source code and demo repo
COPY . /app

EXPOSE 8000

ENV PORT=8000
ENV HOST=0.0.0.0
ENV PYTHONPATH=/app

CMD ["uvicorn", "backend.app.server:app", "--host", "0.0.0.0", "--port", "8000"]
