# Academic Research Chatbot - Development Startup Script (Windows)
# This script helps start all services for local development

Write-Host "🚀 Starting Academic Research Chatbot Development Environment" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env exists
if (-not (Test-Path .env)) {
    Write-Host "❌ Error: .env file not found" -ForegroundColor Red
    Write-Host "Please copy .env.example to .env and configure it"
    exit 1
}

Write-Host "✓ .env file found" -ForegroundColor Green

# Check if backend/.env exists (optional)
if (-not (Test-Path backend/.env)) {
    Write-Host "⚠  backend/.env not found (optional)" -ForegroundColor Yellow
}

# Function to check if port is in use
function Test-Port {
    param($Port)
    $connection = Test-NetConnection -ComputerName localhost -Port $Port -WarningAction SilentlyContinue
    if ($connection.TcpTestSucceeded) {
        Write-Host "⚠  Port $Port is already in use" -ForegroundColor Yellow
        return $false
    } else {
        Write-Host "✓ Port $Port is available" -ForegroundColor Green
        return $true
    }
}

# Check required ports
Write-Host ""
Write-Host "Checking ports..."
Test-Port 8000  # Backend
Test-Port 5173  # Frontend
Test-Port 6333  # Qdrant

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Starting services..." -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Start Qdrant (Docker)
Write-Host "1️⃣  Starting Qdrant (Docker)..." -ForegroundColor Cyan
Set-Location backend

$qdrantRunning = docker-compose ps | Select-String "qdrant.*Up"
if ($qdrantRunning) {
    Write-Host "✓ Qdrant is already running" -ForegroundColor Green
} else {
    docker-compose up -d
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Qdrant started successfully" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to start Qdrant" -ForegroundColor Red
        Set-Location ..
        exit 1
    }
}
Set-Location ..

# Wait for Qdrant to be ready
Write-Host "   Waiting for Qdrant to be ready..."
Start-Sleep -Seconds 3

try {
    $response = Invoke-WebRequest -Uri "http://localhost:6333/collections" -UseBasicParsing -ErrorAction Stop
    Write-Host "✓ Qdrant is ready" -ForegroundColor Green
} catch {
    Write-Host "⚠  Qdrant may not be ready yet" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "2️⃣  Starting Backend (FastAPI)..." -ForegroundColor Cyan
Write-Host "   Open a new PowerShell terminal and run:" -ForegroundColor White
Write-Host "   cd backend" -ForegroundColor Yellow
Write-Host "   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000" -ForegroundColor Yellow
Write-Host ""

Write-Host "3️⃣  Starting Frontend (React)..." -ForegroundColor Cyan
Write-Host "   Open another PowerShell terminal and run:" -ForegroundColor White
Write-Host "   npm run dev" -ForegroundColor Yellow
Write-Host ""

Write-Host "4️⃣  Starting IDP Worker..." -ForegroundColor Cyan
Write-Host "   Open another PowerShell terminal and run:" -ForegroundColor White
Write-Host "   cd backend" -ForegroundColor Yellow
Write-Host "   python run_worker.py" -ForegroundColor Yellow
Write-Host ""

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "📋 Quick Start Checklist" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Terminal 1 (Qdrant):"
Write-Host "  ✓ Already started by this script" -ForegroundColor Green
Write-Host ""
Write-Host "Terminal 2 (Backend):"
Write-Host "  cd backend"
Write-Host "  python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
Write-Host ""
Write-Host "Terminal 3 (Frontend):"
Write-Host "  npm run dev"
Write-Host ""
Write-Host "Terminal 4 (IDP Worker) - REQUIRED for document processing:"
Write-Host "  cd backend"
Write-Host "  python run_worker.py"
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "🌐 Access URLs" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Frontend:  http://localhost:5173" -ForegroundColor White
Write-Host "Backend:   http://localhost:8000" -ForegroundColor White
Write-Host "API Docs:  http://localhost:8000/docs" -ForegroundColor White
Write-Host "Qdrant:    http://localhost:6333/dashboard" -ForegroundColor White
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "📚 Next Steps" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Start backend in Terminal 2"
Write-Host "2. Start frontend in Terminal 3"
Write-Host "3. Start IDP Worker in Terminal 4 (for document processing)"
Write-Host "4. Open http://localhost:5173 in browser"
Write-Host "5. Login with Cognito credentials"
Write-Host "6. Upload documents in /admin (Worker will auto-process)"
Write-Host "7. Chat in /chat"
Write-Host ""
Write-Host "For detailed testing guide, see: docs/full-stack-testing-guide.md"
Write-Host ""
Write-Host "✨ Happy coding!" -ForegroundColor Green
