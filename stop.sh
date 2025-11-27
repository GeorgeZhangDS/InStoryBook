#!/bin/bash

# InStoryBook - Stop all services with one command
# Usage: ./stop.sh

set -e

echo "🛑 Stopping InStoryBook services..."

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Color output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. Stop frontend service
echo -e "${YELLOW}🎨 Stopping frontend service...${NC}"
if [ -f logs/frontend.pid ]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        kill $FRONTEND_PID 2>/dev/null || true
        echo -e "${GREEN}✅ Frontend service stopped (PID: $FRONTEND_PID)${NC}"
    else
        echo -e "${YELLOW}⚠️  Frontend process not found${NC}"
    fi
    rm -f logs/frontend.pid
else
    # Try to find and stop by port
    FRONTEND_PID=$(lsof -ti:5173 2>/dev/null || true)
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
        echo -e "${GREEN}✅ Frontend service stopped (found by port)${NC}"
    else
        echo -e "${YELLOW}⚠️  Frontend service not running${NC}"
    fi
fi

# 2. Stop backend service
echo -e "${YELLOW}🔧 Stopping backend service...${NC}"
if [ -f logs/backend.pid ]; then
    BACKEND_PID=$(cat logs/backend.pid)
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        kill $BACKEND_PID 2>/dev/null || true
        echo -e "${GREEN}✅ Backend service stopped (PID: $BACKEND_PID)${NC}"
    else
        echo -e "${YELLOW}⚠️  Backend process not found${NC}"
    fi
    rm -f logs/backend.pid
else
    # Try to find and stop by port
    BACKEND_PID=$(lsof -ti:8000 2>/dev/null || true)
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        echo -e "${GREEN}✅ Backend service stopped (found by port)${NC}"
    else
        echo -e "${YELLOW}⚠️  Backend service not running${NC}"
    fi
fi

# 3. Stop Redis (optional, data preserved)
echo -e "${YELLOW}📦 Stopping Redis...${NC}"
read -p "Stop Redis container? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker-compose stop redis 2>/dev/null || true
    echo -e "${GREEN}✅ Redis stopped${NC}"
else
    echo -e "${YELLOW}ℹ️  Redis container kept running (data preserved)${NC}"
fi

echo ""
echo -e "${GREEN}✅ All services stopped!${NC}"

