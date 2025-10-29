#!/bin/bash

# DawsOS Launch Script
# Purpose: Start the complete application stack for testing
# Usage: ./launch.sh

set -e

echo "🚀 DawsOS Launch Script"
echo "========================"
echo ""

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

echo "✅ Docker is running"

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✅ Created .env file from .env.example"
    else
        echo "⚠️  No .env.example found. Using default values."
    fi
fi

# Stop any existing containers
echo "🧹 Cleaning up existing containers..."
docker compose down --remove-orphans >/dev/null 2>&1 || true

# Build and start the core services
echo "🔨 Building and starting core services..."
docker compose up -d postgres redis

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 10

# Start backend
echo "🔧 Starting backend API..."
docker compose up -d backend

# Wait for backend to be ready
echo "⏳ Waiting for backend to be ready..."
sleep 15

# Start UI
echo "🎨 Starting UI..."
docker compose up -d dawsos-ui

# Wait for UI to be ready
echo "⏳ Waiting for UI to be ready..."
sleep 10

# Check service health
echo "🔍 Checking service health..."
echo ""

# Check backend health
if curl -f http://localhost:8000/health >/dev/null 2>&1; then
    echo "✅ Backend API: http://localhost:8000"
else
    echo "❌ Backend API: Not responding"
fi

# Check UI health
if curl -f http://localhost:3000/api/health >/dev/null 2>&1; then
    echo "✅ UI: http://localhost:3000"
else
    echo "❌ UI: Not responding"
fi

echo ""
echo "🎯 DawsOS is ready for testing!"
echo ""
echo "📱 Access the application:"
echo "   UI: http://localhost:3000"
echo "   API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "🔐 Demo credentials:"
echo "   Email: michael@dawsos.com"
echo "   Password: mozzuq-byfqyQ-5tefvu"
echo ""
echo "🛑 To stop: docker compose down"
echo ""
