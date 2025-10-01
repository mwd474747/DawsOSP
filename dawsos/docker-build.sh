#!/bin/bash

# DawsOS Docker Build Script

echo "======================================"
echo "Building DawsOS Docker Container"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}Warning: .env file not found${NC}"
    echo "Creating .env from .env.docker template..."
    cp .env.docker .env
    echo -e "${YELLOW}Please edit .env and add your API keys${NC}"
    exit 1
fi

# Create necessary directories
echo "Creating storage directories..."
mkdir -p storage/backups storage/agent_memory storage/sessions storage/patterns storage/workflows
mkdir -p logs

# Build Docker image
echo "Building Docker image..."
docker build -t dawsos:latest .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Docker image built successfully${NC}"
else
    echo -e "${RED}❌ Docker build failed${NC}"
    exit 1
fi

# Optional: Build with docker-compose
read -p "Do you want to build with docker-compose (includes Redis & PostgreSQL)? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Building with docker-compose..."
    docker-compose build

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Docker-compose build successful${NC}"
    else
        echo -e "${RED}❌ Docker-compose build failed${NC}"
        exit 1
    fi
fi

echo ""
echo "======================================"
echo "Build Complete!"
echo "======================================"
echo ""
echo "To run DawsOS:"
echo ""
echo "1. Simple Docker run:"
echo "   ./docker-run.sh"
echo ""
echo "2. With docker-compose (includes database):"
echo "   docker-compose up -d"
echo ""
echo "3. Manual Docker run:"
echo "   docker run -d -p 8501:8501 --env-file .env -v ./storage:/app/storage dawsos:latest"
echo ""
echo "Access DawsOS at: http://localhost:8501"