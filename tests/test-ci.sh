#!/bin/bash
# Local CI test script - runs all checks from .github/workflows/ci.yml
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track what we need to cleanup
REDIS_STARTED=false
DOCKER_CONTAINER_STARTED=false

cleanup() {
    echo -e "\n${YELLOW}=== Cleanup ===${NC}"
    if [ "$REDIS_STARTED" = true ]; then
        echo "Stopping Redis..."
        docker stop redis-ci 2>/dev/null || true
        docker rm redis-ci 2>/dev/null || true
    fi
    if [ "$DOCKER_CONTAINER_STARTED" = true ]; then
        echo "Stopping test container..."
        docker stop test-container 2>/dev/null || true
    fi
}

trap cleanup EXIT

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Local CI Test Runner${NC}"
echo -e "${GREEN}========================================${NC}\n"

# Change to project root
cd "$(dirname "$0")/.."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    uv venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
echo -e "\n${YELLOW}=== Installing Dependencies ===${NC}"
uv pip install -e ".[dev]"

# Job 1: Lint
echo -e "\n${GREEN}=== Job 1: Lint ===${NC}"
echo "Running ruff linter..."
ruff check src tests
echo "Running ruff formatter check..."
ruff format --check src tests
echo -e "${GREEN}✓ Lint passed${NC}"

# Job 2: Test
echo -e "\n${GREEN}=== Job 2: Test ===${NC}"

# Check if Redis is already running on port 6379
REDIS_PORT=6379
if nc -z localhost 6379 2>/dev/null || docker ps --format '{{.Names}}' | grep -qE '^redis(-ci)?$'; then
    echo -e "${YELLOW}Redis already running on port 6379, using it...${NC}"
    REDIS_STARTED=false
else
    # Start Redis
    echo "Starting Redis..."
    # Clean up any stopped redis-ci container
    docker rm redis-ci 2>/dev/null || true
    docker run -d --name redis-ci -p 6379:6379 redis:7-alpine
    REDIS_STARTED=true

    # Wait for Redis to be ready
    echo "Waiting for Redis to be ready..."
    for i in {1..30}; do
        if docker exec redis-ci redis-cli ping 2>/dev/null | grep -q PONG; then
            echo "Redis is ready!"
            break
        fi
        sleep 1
    done
fi

# Run tests
echo "Running pytest with coverage..."
REDIS_URL=redis://localhost:${REDIS_PORT}/0 pytest tests/ -v --cov=src/weather_proxy --cov-report=xml --cov-report=term-missing

echo -e "${GREEN}✓ Tests passed${NC}"

# Stop Redis if we started it (cleanup will handle if script fails)
if [ "$REDIS_STARTED" = true ]; then
    docker stop redis-ci && docker rm redis-ci
    REDIS_STARTED=false
fi

# Job 3: Build Docker Image
echo -e "\n${GREEN}=== Job 3: Build Docker Image ===${NC}"
echo "Building Docker image..."
docker build -t weather-proxy-test .

echo "Testing Docker image..."
docker run --rm -d --name test-container -p 8000:8000 weather-proxy-test
DOCKER_CONTAINER_STARTED=true
sleep 5

echo "Testing health endpoint..."
if curl -f http://localhost:8000/health; then
    echo -e "\n${GREEN}✓ Health check passed${NC}"
else
    echo -e "\n${RED}✗ Health check failed${NC}"
    exit 1
fi

docker stop test-container
DOCKER_CONTAINER_STARTED=false
echo -e "${GREEN}✓ Docker build passed${NC}"

# Job 4: Security Scan (optional)
echo -e "\n${GREEN}=== Job 4: Security Scan ===${NC}"
echo "Running Trivy vulnerability scanner..."
if command -v trivy &> /dev/null; then
    trivy fs . --severity HIGH,CRITICAL || true
elif docker info &> /dev/null; then
    docker run --rm -v "$(pwd)":/app aquasec/trivy:latest fs /app --severity HIGH,CRITICAL || true
else
    echo -e "${YELLOW}Trivy not available, skipping security scan${NC}"
fi
echo -e "${GREEN}✓ Security scan completed${NC}"

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  All CI checks passed! ✓${NC}"
echo -e "${GREEN}========================================${NC}"
