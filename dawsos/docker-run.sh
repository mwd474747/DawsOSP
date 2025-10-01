#!/bin/bash

# DawsOS Docker Run Script

echo "======================================"
echo "Starting DawsOS Docker Container"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Container name
CONTAINER_NAME="dawsos"
IMAGE_NAME="dawsos:latest"
PORT="8501"

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found${NC}"
    echo "Please create .env from .env.docker and add your API keys"
    exit 1
fi

# Check if image exists
if [[ "$(docker images -q ${IMAGE_NAME} 2> /dev/null)" == "" ]]; then
    echo -e "${YELLOW}Docker image not found. Building...${NC}"
    ./docker-build.sh
    if [ $? -ne 0 ]; then
        echo -e "${RED}Build failed${NC}"
        exit 1
    fi
fi

# Stop existing container if running
if [ "$(docker ps -q -f name=${CONTAINER_NAME})" ]; then
    echo "Stopping existing container..."
    docker stop ${CONTAINER_NAME}
fi

# Remove existing container if exists
if [ "$(docker ps -aq -f name=${CONTAINER_NAME})" ]; then
    echo "Removing existing container..."
    docker rm ${CONTAINER_NAME}
fi

# Run container
echo "Starting DawsOS container..."
docker run -d \
    --name ${CONTAINER_NAME} \
    -p ${PORT}:8501 \
    --env-file .env \
    -v $(pwd)/storage:/app/storage \
    -v $(pwd)/logs:/app/logs \
    --restart unless-stopped \
    ${IMAGE_NAME}

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ DawsOS container started successfully${NC}"

    # Wait for container to be healthy
    echo "Waiting for DawsOS to be ready..."
    for i in {1..30}; do
        if curl -f http://localhost:${PORT}/_stcore/health >/dev/null 2>&1; then
            echo -e "${GREEN}✅ DawsOS is ready!${NC}"
            break
        fi
        echo -n "."
        sleep 1
    done

    echo ""
    echo "======================================"
    echo "DawsOS is running!"
    echo "======================================"
    echo ""
    echo "Access at: http://localhost:${PORT}"
    echo ""
    echo "Commands:"
    echo "  View logs:    docker logs -f ${CONTAINER_NAME}"
    echo "  Stop:         docker stop ${CONTAINER_NAME}"
    echo "  Restart:      docker restart ${CONTAINER_NAME}"
    echo "  Shell access: docker exec -it ${CONTAINER_NAME} /bin/bash"
    echo ""
else
    echo -e "${RED}❌ Failed to start container${NC}"
    echo "Check logs with: docker logs ${CONTAINER_NAME}"
    exit 1
fi