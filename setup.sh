#!/bin/bash
# Quick Setup Script for Insurance Fraud Detection with Gemini AI
# For Linux/Mac users

echo "============================================"
echo "Insurance Fraud Detection - Quick Setup"
echo "With Google Gemini AI Integration"
echo "============================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
GRAY='\033[0;37m'
NC='\033[0m' # No Color

# Step 1: Check Python
echo -e "${YELLOW}[1/5] Checking Python installation...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "  ${GREEN}✓ $PYTHON_VERSION found${NC}"
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version)
    echo -e "  ${GREEN}✓ $PYTHON_VERSION found${NC}"
    PYTHON_CMD="python"
else
    echo -e "  ${RED}✗ Python not found. Please install Python 3.8+${NC}"
    exit 1
fi

# Step 2: Install dependencies
echo ""
echo -e "${YELLOW}[2/5] Installing dependencies...${NC}"
echo -e "  ${GRAY}This may take a few minutes...${NC}"

if $PYTHON_CMD -m pip install -r requirements.txt --quiet; then
    echo -e "  ${GREEN}✓ All dependencies installed${NC}"
else
    echo -e "  ${RED}✗ Error installing dependencies${NC}"
    echo -e "  ${YELLOW}Try manually: pip install -r requirements.txt${NC}"
    exit 1
fi

# Step 3: Check for .env file
echo ""
echo -e "${YELLOW}[3/5] Checking environment configuration...${NC}"

if [ -f ".env" ]; then
    echo -e "  ${GREEN}✓ .env file exists${NC}"
else
    echo -e "  ${GRAY}Creating .env from template...${NC}"
    cp .env.example .env
    echo -e "  ${GREEN}✓ .env file created${NC}"
    echo ""
    echo -e "  ${YELLOW}⚠ IMPORTANT: Edit .env and add your Gemini API key!${NC}"
    echo -e "  ${CYAN}1. Get API key: https://makersuite.google.com/app/apikey${NC}"
    echo -e "  ${CYAN}2. Open .env file and set: GEMINI_API_KEY=your-key-here${NC}"
    echo ""
fi

# Step 4: Initialize database
echo ""
echo -e "${YELLOW}[4/5] Initializing database...${NC}"

if $PYTHON_CMD init_db.py; then
    echo -e "  ${GREEN}✓ Database initialized${NC}"
else
    echo -e "  ${YELLOW}! Database initialization skipped (may already exist)${NC}"
fi

# Step 5: Test Gemini connection
echo ""
echo -e "${YELLOW}[5/5] Testing Gemini integration...${NC}"
echo ""

$PYTHON_CMD test_gemini.py || echo -e "  ${YELLOW}! Gemini test completed with warnings${NC}"

# Summary
echo ""
echo -e "${CYAN}============================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${CYAN}============================================${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo ""
echo -e "${NC}1. Configure Gemini API (if not done):${NC}"
echo -e "   ${GRAY}- Get key: https://makersuite.google.com/app/apikey${NC}"
echo -e "   ${GRAY}- Edit .env and set GEMINI_API_KEY=your-key${NC}"
echo ""
echo -e "${NC}2. Start the application:${NC}"
echo -e "   ${CYAN}$PYTHON_CMD -m uvicorn app.main:app --reload${NC}"
echo ""
echo -e "${NC}3. Open in browser:${NC}"
echo -e "   ${CYAN}http://localhost:8000/docs${NC}"
echo ""
echo -e "${NC}4. Test the frontend:${NC}"
echo -e "   ${CYAN}Open: frontend/insurer.html${NC}"
echo ""
echo -e "${YELLOW}Documentation:${NC}"
echo -e "   ${GRAY}- GEMINI_INTEGRATION_COMPLETE.md - Quick overview${NC}"
echo -e "   ${GRAY}- GEMINI_SETUP.md - Detailed setup guide${NC}"
echo -e "   ${GRAY}- README.md - Full documentation${NC}"
echo ""
echo -e "${CYAN}============================================${NC}"
