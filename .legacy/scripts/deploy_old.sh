#!/bin/bash
# DawsOS Unified Deployment Script
# Purpose: Docker-based deployment for complete DawsOS stack
# Updated: 2025-10-28

set -e  # Exit on error

echo "🚀 DawsOS - Unified Docker Deployment"
echo "====================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: docker-compose.yml not found. Please run this script from the DawsOS root directory."
    exit 1
fi

# Parse command line arguments
MODE=${1:-"dev"}
CLEAN=${2:-"false"}

echo "📋 Deployment Configuration:"
echo "  Mode: $MODE"
echo "  Clean Build: $CLEAN"
echo ""

# Clean up if requested
if [ "$CLEAN" = "true" ]; then
    echo "🧹 Cleaning up existing containers and images..."
    docker compose down --volumes --remove-orphans
    docker system prune -f
    echo "✅ Cleanup completed"
    echo ""
fi

# Select docker-compose file based on mode
COMPOSE_FILE="docker-compose.yml"
if [ "$MODE" = "prod" ]; then
    COMPOSE_FILE="docker-compose.prod.yml"
elif [ "$MODE" = "test" ]; then
    COMPOSE_FILE="docker-compose.test.yml"
elif [ "$MODE" = "observability" ]; then
    COMPOSE_FILE="docker-compose.observability.yml"
fi

echo "📦 Building and starting services..."
echo "  Using: $COMPOSE_FILE"
echo ""

# Build and start services
if [ "$CLEAN" = "true" ]; then
    docker compose -f $COMPOSE_FILE up -d --build --force-recreate
else
    docker compose -f $COMPOSE_FILE up -d --build
fi

echo ""
echo "⏳ Waiting for services to be ready..."

# Wait for services to be healthy
docker compose -f $COMPOSE_FILE ps

echo ""
echo "🔍 Service Status:"
echo "  Backend API: http://localhost:8000"
echo "  Next.js UI: http://localhost:3000"
echo "  Database: localhost:5432"
echo "  Redis: localhost:6379"

if [ "$MODE" = "observability" ]; then
    echo "  Prometheus: http://localhost:9090"
    echo "  Grafana: http://localhost:3001"
    echo "  Jaeger: http://localhost:16686"
fi

echo ""
echo "✅ DawsOS deployment completed successfully!"
echo ""
echo "📚 Useful commands:"
echo "  View logs: docker compose logs -f"
echo "  Stop services: docker compose down"
echo "  Restart: docker compose restart"
echo "  Clean restart: ./deploy.sh $MODE true"