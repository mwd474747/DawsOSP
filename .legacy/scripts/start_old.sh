#!/bin/bash
# DawsOS Quick Start Script
# Purpose: Fast development startup with hot reload
# Updated: 2025-10-28

set -e  # Exit on error

echo "🚀 DawsOS - Quick Start"
echo "======================"
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

echo "📋 Starting DawsOS in development mode..."
echo ""

# Start only essential services for development
echo "🐘 Starting database services..."
docker compose up -d postgres redis

echo "⏳ Waiting for database to be ready..."
sleep 10

echo "🔧 Starting backend API..."
docker compose up -d backend

echo "⏳ Waiting for backend to be ready..."
sleep 15

echo "🎨 Starting Next.js UI in development mode..."
echo "  Note: Next.js will run with hot reload on localhost:3000"
echo ""

# Start Next.js in development mode (not containerized for hot reload)
cd dawsos-ui
echo "📦 Installing dependencies..."
npm install

echo "🚀 Starting Next.js development server..."
echo "  UI will be available at: http://localhost:3000"
echo "  Backend API: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Start Next.js with hot reload
npm run dev