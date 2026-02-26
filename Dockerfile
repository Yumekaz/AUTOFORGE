# AUTOFORGE - Pipeline container
# Multi-stage build for smaller runtime image

# ============================================================================
# Stage 1: Build environment with all development tools
# ============================================================================
FROM ubuntu:22.04 AS builder

ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    g++ \
    clang \
    clang-tidy \
    cppcheck \
    cmake \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# ============================================================================
# Stage 2: Runtime environment (smaller)
# ============================================================================
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    g++ \
    clang-tidy \
    cppcheck \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.10/dist-packages /usr/local/lib/python3.10/dist-packages

WORKDIR /autoforge

# Copy application code
COPY . .

# Create output directory
RUN mkdir -p /autoforge/output

# Runtime environment variables
ENV PYTHONPATH=/autoforge/src
ENV GOOGLE_API_KEY=""
ENV OPENAI_API_KEY=""
ENV PYTHONIOENCODING="utf-8"
ENV PYTHONUTF8="1"

# Expose key data volumes
VOLUME ["/autoforge/output", "/autoforge/input"]

# Default command
ENTRYPOINT ["python3", "main.py"]
CMD ["--help"]

# Example:
#   docker build -t autoforge:v1.0 .
#   docker run --rm -v $(pwd)/output:/autoforge/output autoforge:v1.0 --demo bms --mock
