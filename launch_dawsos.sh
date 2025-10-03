#!/bin/bash

# DawsOS Docker Launcher
# Quick script to start DawsOS with Docker

set -e

echo "🚀 DawsOS Docker Launcher"
echo "========================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    echo "Please install Docker Desktop from https://www.docker.com/products/docker-desktop"
    exit 1
fi

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo -e "${YELLOW}⚠️  Docker daemon is not running${NC}"
    echo "Starting Docker Desktop..."
    open -a Docker

    echo "Waiting for Docker to start..."
    counter=0
    max_attempts=30

    while ! docker info &> /dev/null; do
        sleep 2
        counter=$((counter+1))
        echo -n "."

        if [ $counter -eq $max_attempts ]; then
            echo -e "\n${RED}❌ Docker failed to start after 60 seconds${NC}"
            echo "Please start Docker Desktop manually and try again"
            exit 1
        fi
    done

    echo -e "\n${GREEN}✅ Docker is running${NC}"
fi

# Navigate to dawsos directory
cd "$(dirname "$0")/dawsos" || exit 1

echo ""
echo "📍 Working directory: $(pwd)"
echo ""

# Check for .env file
if [ ! -f .env ]; then
    echo -e "${RED}❌ .env file not found${NC}"
    echo "Please create a .env file with your API keys"
    exit 1
else
    echo -e "${GREEN}✅ .env file found${NC}"
fi

# Check for requirements.txt
if [ ! -f requirements.txt ]; then
    echo -e "${RED}❌ requirements.txt not found${NC}"
    exit 1
else
    echo -e "${GREEN}✅ requirements.txt found${NC}"
fi

echo ""
echo "🏗️  Building Docker image..."
echo ""

# Build the image
if docker build -t dawsos:latest . --quiet; then
    echo -e "${GREEN}✅ Docker image built successfully${NC}"
else
    echo -e "${RED}❌ Docker build failed${NC}"
    echo "Check the error messages above"
    exit 1
fi

echo ""
echo "🚢 Launching DawsOS container..."
echo ""

# Stop existing container if running
if docker ps -a --format '{{.Names}}' | grep -q '^dawsos$'; then
    echo "Stopping existing container..."
    docker stop dawsos &> /dev/null || true
    docker rm dawsos &> /dev/null || true
fi

# Run the container
docker run -d \
  --name dawsos \
  -p 8501:8501 \
  --env-file .env \
  -v "$(pwd)/storage:/app/storage" \
  -v "$(pwd)/logs:/app/logs" \
  --restart unless-stopped \
  dawsos:latest

echo ""
echo "⏳ Waiting for application to start..."
sleep 5

# Check if container is running
if docker ps --format '{{.Names}}' | grep -q '^dawsos$'; then
    echo -e "${GREEN}✅ Container is running${NC}"

    # Wait for health check
    echo "Checking application health..."
    counter=0
    max_attempts=15

    while [ $counter -lt $max_attempts ]; do
        if curl -f http://localhost:8501/_stcore/health &> /dev/null; then
            echo -e "${GREEN}✅ Application is healthy${NC}"
            break
        fi
        sleep 2
        counter=$((counter+1))
        echo -n "."
    done

    echo ""
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${GREEN}🎉 DawsOS is now running!${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "📍 Access the application at: http://localhost:8501"
    echo ""
    echo "Useful commands:"
    echo "  • View logs:    docker logs -f dawsos"
    echo "  • Stop app:     docker stop dawsos"
    echo "  • Restart app:  docker restart dawsos"
    echo "  • Container sh: docker exec -it dawsos /bin/bash"
    echo ""
    echo "Opening browser..."
    sleep 2
    open http://localhost:8501

    echo ""
    echo "Following logs (Ctrl+C to exit)..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    docker logs -f dawsos

else
    echo -e "${RED}❌ Container failed to start${NC}"
    echo ""
    echo "Checking logs..."
    docker logs dawsos
    exit 1
fi
