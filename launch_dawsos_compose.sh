#!/bin/bash

# DawsOS Docker Compose Launcher
# Starts DawsOS with full stack (Redis + PostgreSQL optional)

set -e

echo "🚀 DawsOS Docker Compose Launcher"
echo "================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    exit 1
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed${NC}"
    exit 1
fi

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo -e "${YELLOW}⚠️  Starting Docker Desktop...${NC}"
    open -a Docker

    echo "Waiting for Docker to start..."
    counter=0
    while ! docker info &> /dev/null; do
        sleep 2
        counter=$((counter+1))
        echo -n "."
        if [ $counter -eq 30 ]; then
            echo -e "\n${RED}❌ Docker failed to start${NC}"
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

# Check for required files
echo "🔍 Checking configuration files..."
echo ""

if [ ! -f .env ]; then
    echo -e "${RED}❌ .env file not found${NC}"
    exit 1
else
    echo -e "${GREEN}✅${NC} .env file found"
fi

if [ ! -f docker-compose.yml ]; then
    echo -e "${RED}❌ docker-compose.yml not found${NC}"
    exit 1
else
    echo -e "${GREEN}✅${NC} docker-compose.yml found"
fi

if [ ! -f Dockerfile ]; then
    echo -e "${RED}❌ Dockerfile not found${NC}"
    exit 1
else
    echo -e "${GREEN}✅${NC} Dockerfile found"
fi

if [ ! -f requirements.txt ]; then
    echo -e "${RED}❌ requirements.txt not found${NC}"
    exit 1
else
    echo -e "${GREEN}✅${NC} requirements.txt found"
fi

echo ""
echo "🎛️  Select deployment mode:"
echo ""
echo "  1) DawsOS only (Lightweight)"
echo "  2) DawsOS + Redis (Recommended)"
echo "  3) Full stack (DawsOS + Redis + PostgreSQL)"
echo ""
read -p "Enter choice [1-3] (default: 1): " choice
choice=${choice:-1}

echo ""

case $choice in
    1)
        echo -e "${BLUE}🚀 Launching DawsOS only...${NC}"
        SERVICES="dawsos"
        ;;
    2)
        echo -e "${BLUE}🚀 Launching DawsOS + Redis...${NC}"
        SERVICES="dawsos redis"
        ;;
    3)
        echo -e "${BLUE}🚀 Launching full stack...${NC}"
        SERVICES=""
        ;;
    *)
        echo -e "${RED}❌ Invalid choice${NC}"
        exit 1
        ;;
esac

echo ""
echo "🏗️  Building images..."
echo ""

# Build
if [ -z "$SERVICES" ]; then
    docker-compose build
else
    docker-compose build $SERVICES
fi

echo ""
echo "🚢 Starting containers..."
echo ""

# Start services
if [ -z "$SERVICES" ]; then
    docker-compose up -d
else
    docker-compose up -d $SERVICES
fi

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check status
echo ""
echo "📊 Container status:"
echo ""
docker-compose ps

echo ""
echo "🏥 Health check..."
counter=0
while [ $counter -lt 15 ]; do
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
echo "📍 Access: http://localhost:8501"
echo ""
echo "Services running:"
docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "Useful commands:"
echo "  • View logs:     docker-compose logs -f dawsos"
echo "  • Stop all:      docker-compose down"
echo "  • Restart app:   docker-compose restart dawsos"
echo "  • Container sh:  docker exec -it dawsos /bin/bash"
echo ""

read -p "Open browser? [Y/n]: " open_browser
if [[ ! $open_browser =~ ^[Nn]$ ]]; then
    echo "Opening browser..."
    open http://localhost:8501
fi

echo ""
read -p "Follow logs? [Y/n]: " follow_logs
if [[ ! $follow_logs =~ ^[Nn]$ ]]; then
    echo ""
    echo "Following logs (Ctrl+C to exit)..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    docker-compose logs -f dawsos
fi
