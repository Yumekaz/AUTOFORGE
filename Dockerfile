# AUTOFORGE - Production Docker Container
# Multi-stage build for optimized size

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

# Set environment variables
ENV PYTHONPATH=/autoforge/src
ENV GOOGLE_API_KEY=""
ENV OPENAI_API_KEY=""

# Expose output volume
VOLUME ["/autoforge/output", "/autoforge/input"]

# Default command
ENTRYPOINT ["python3", "main.py"]
CMD ["--help"]

# ============================================================================
# Usage Examples:
# ============================================================================
# Build:
#   docker build -t autoforge:v1.0 .
#
# Run with demo:
#   docker run --rm -e GOOGLE_API_KEY=$GOOGLE_API_KEY \
#     -v $(pwd)/output:/autoforge/output \
#     autoforge:v1.0 --demo bms
#
# Run with custom requirement:
#   docker run --rm -e GOOGLE_API_KEY=$GOOGLE_API_KEY \
#     -v $(pwd)/input:/autoforge/input \
#     -v $(pwd)/output:/autoforge/output \
#     autoforge:v1.0 --requirement /autoforge/input/my_service.yaml
#
# Run with mock LLM (no API key):
#   docker run --rm \
#     -v $(pwd)/output:/autoforge/output \
#     autoforge:v1.0 --demo bms --mock
# ============================================================================
