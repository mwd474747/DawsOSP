#!/bin/bash

# DawsOS Status Script
# Purpose: Check if all services are running
# Usage: ./status.sh

echo "🔍 DawsOS Service Status"
echo "========================"
echo ""

# Check backend
echo "Backend API (port 8000):"
if curl -s http://localhost:8000/health >/dev/null 2>&1; then
    echo "✅ Running - http://localhost:8000"
    echo "   API Docs: http://localhost:8000/docs"
else
    echo "❌ Not running"
fi

echo ""

# Check UI
echo "UI (port 3000):"
if curl -s http://localhost:3000/api/health >/dev/null 2>&1; then
    echo "✅ Running - http://localhost:3000"
    echo "   Login: http://localhost:3000/login"
    echo "   Home: http://localhost:3000"
else
    echo "❌ Not running"
fi

echo ""

# Check database
echo "Database (PostgreSQL):"
if docker ps | grep dawsos-postgres >/dev/null 2>&1; then
    echo "✅ Running in Docker"
else
    echo "⚠️  Not running (backend may use local DB)"
fi

echo ""

# Check Redis
echo "Cache (Redis):"
if docker ps | grep dawsos-redis >/dev/null 2>&1; then
    echo "✅ Running in Docker"
else
    echo "⚠️  Not running (backend may use local cache)"
fi

echo ""
echo "🎯 Ready for testing!"
echo ""
echo "Demo credentials:"
echo "  Email: michael@dawsos.com"
echo "  Password: mozzuq-byfqyQ-5tefvu"
echo ""
