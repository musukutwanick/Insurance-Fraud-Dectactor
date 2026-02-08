# Quick Setup Script for Insurance Fraud Detection with Gemini AI
# This script helps you set up the application quickly

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Insurance Fraud Detection - Quick Setup" -ForegroundColor Cyan
Write-Host "With Google Gemini AI Integration" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check Python
Write-Host "[1/5] Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  ✓ $pythonVersion found" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Python not found. Please install Python 3.8+" -ForegroundColor Red
    exit 1
}

# Step 2: Install dependencies
Write-Host ""
Write-Host "[2/5] Installing dependencies..." -ForegroundColor Yellow
Write-Host "  This may take a few minutes..." -ForegroundColor Gray

try {
    pip install -r requirements.txt --quiet
    Write-Host "  ✓ All dependencies installed" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Error installing dependencies" -ForegroundColor Red
    Write-Host "  Try manually: pip install -r requirements.txt" -ForegroundColor Yellow
    exit 1
}

# Step 3: Check for .env file
Write-Host ""
Write-Host "[3/5] Checking environment configuration..." -ForegroundColor Yellow

if (Test-Path ".env") {
    Write-Host "  ✓ .env file exists" -ForegroundColor Green
} else {
    Write-Host "  Creating .env from template..." -ForegroundColor Gray
    Copy-Item ".env.example" ".env"
    Write-Host "  ✓ .env file created" -ForegroundColor Green
    Write-Host ""
    Write-Host "  ⚠ IMPORTANT: Edit .env and add your Gemini API key!" -ForegroundColor Yellow
    Write-Host "  1. Get API key: https://makersuite.google.com/app/apikey" -ForegroundColor Cyan
    Write-Host "  2. Open .env file and set: GEMINI_API_KEY=your-key-here" -ForegroundColor Cyan
    Write-Host ""
}

# Step 4: Initialize database
Write-Host ""
Write-Host "[4/5] Initializing database..." -ForegroundColor Yellow

try {
    python init_db.py
    Write-Host "  ✓ Database initialized" -ForegroundColor Green
} catch {
    Write-Host "  ! Database initialization skipped (may already exist)" -ForegroundColor Yellow
}

# Step 5: Test Gemini connection
Write-Host ""
Write-Host "[5/5] Testing Gemini integration..." -ForegroundColor Yellow
Write-Host ""

try {
    python test_gemini.py
} catch {
    Write-Host "  ! Gemini test completed with warnings" -ForegroundColor Yellow
}

# Summary
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Configure Gemini API (if not done):" -ForegroundColor White
Write-Host "   - Get key: https://makersuite.google.com/app/apikey" -ForegroundColor Gray
Write-Host "   - Edit .env and set GEMINI_API_KEY=your-key" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Start the application:" -ForegroundColor White
Write-Host "   python -m uvicorn app.main:app --reload" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. Open in browser:" -ForegroundColor White
Write-Host "   http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "4. Test the frontend:" -ForegroundColor White
Write-Host "   Open: frontend/insurer.html" -ForegroundColor Cyan
Write-Host ""
Write-Host "Documentation:" -ForegroundColor Yellow
Write-Host "   - GEMINI_INTEGRATION_COMPLETE.md - Quick overview" -ForegroundColor Gray
Write-Host "   - GEMINI_SETUP.md - Detailed setup guide" -ForegroundColor Gray
Write-Host "   - README.md - Full documentation" -ForegroundColor Gray
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
