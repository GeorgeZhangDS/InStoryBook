#!/bin/bash

# InStoryBook - Start all services with one command
# Usage: ./start.sh

set -e

echo "🚀 Starting InStoryBook services..."

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Color output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Start Redis (Docker)
echo -e "${YELLOW}📦 Starting Redis...${NC}"
if ! docker ps | grep -q instorybook-redis; then
    docker-compose up -d redis
    echo -e "${GREEN}✅ Redis started${NC}"
else
    echo -e "${GREEN}✅ Redis already running${NC}"
fi

# Wait for Redis to be ready
sleep 2
if docker exec instorybook-redis redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Redis connection OK${NC}"
else
    echo -e "${YELLOW}⚠️  Redis connection check failed, continuing...${NC}"
fi

# 2. Start backend service
echo -e "${YELLOW}🔧 Starting backend service...${NC}"
cd backend

# Check if backend is already running
if lsof -ti:8000 > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Backend service already running (port 8000)${NC}"
else
    # Start backend (run in background, output to log file)
    nohup uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > ../logs/backend.pid
    echo -e "${GREEN}✅ Backend service started (PID: $BACKEND_PID)${NC}"
    
    # Wait for backend to start
    sleep 3
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend health check passed${NC}"
    else
        echo -e "${YELLOW}⚠️  Backend starting up, health check pending...${NC}"
    fi
fi

cd ..

# 3. Start frontend service
echo -e "${YELLOW}🎨 Starting frontend service...${NC}"
cd frontend

# Check if frontend is already running
if lsof -ti:5173 > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Frontend service already running (port 5173)${NC}"
else
    # Start frontend (run in background, output to log file)
    nohup npm run dev > ../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > ../logs/frontend.pid
    echo -e "${GREEN}✅ Frontend service started (PID: $FRONTEND_PID)${NC}"
    
    # Wait for frontend to start
    sleep 3
fi

cd ..

echo ""
echo -e "${GREEN}🎉 All services started!${NC}"
echo ""
echo "📋 Service status:"
echo "  - Redis:     http://localhost:6379"
echo "  - Backend:   http://localhost:8000"
echo "  - API Docs:  http://localhost:8000/docs"
echo "  - Frontend:  http://localhost:5173"
echo ""
echo "📝 Log files:"
echo "  - Backend:   logs/backend.log"
echo "  - Frontend:  logs/frontend.log"
echo ""
echo "🛑 Stop services: run ./stop.sh"

