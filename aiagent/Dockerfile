# First stage: Build dependencies
FROM python:3.9-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir --prefix=/install -r requirements.txt

# Final stage: Minimized runtime image
FROM python:3.9-slim
WORKDIR /app
COPY --from=builder /install /usr/local
COPY src /app

# Precompile Python files for better startup speed
RUN python -m compileall .

COPY refund_model.pkl /app

# Set environment variables
ENV PYTHONUNBUFFERED=1

CMD ["python", "2.py"]
