# Start Backend and Worker Services
# Run this before testing the RAG pipeline

Write-Host "=== Starting RAG Services ===" -ForegroundColor Cyan
Write-Host ""

# Check if Qdrant is running, if not start it
Write-Host "Checking Qdrant..." -ForegroundColor Yellow
try {
    $qdrantHealth = Invoke-RestMethod -Uri "http://localhost:6333/collections" -Method Get -TimeoutSec 2
    Write-Host "  Qdrant is already running" -ForegroundColor Green
} catch {
    Write-Host "  Qdrant not running, starting it..." -ForegroundColor Yellow
    
    # Start Qdrant in Docker
    $qdrantJob = Start-Job -ScriptBlock {
        docker run --rm -p 6333:6333 -p 6334:6334 qdrant/qdrant
    }
    
    Write-Host "  Qdrant container started (Job ID: $($qdrantJob.Id))" -ForegroundColor Green
    Write-Host "  Waiting for Qdrant to be ready..." -ForegroundColor Gray
    
    # Wait for Qdrant to be ready
    $maxWait = 30
    $elapsed = 0
    $qdrantReady = $false
    
    while ($elapsed -lt $maxWait) {
        try {
            $response = Invoke-RestMethod -Uri "http://localhost:6333/collections" -Method Get -TimeoutSec 2 -ErrorAction SilentlyContinue
            Write-Host "  Qdrant is ready!" -ForegroundColor Green
            $qdrantReady = $true
            break
        } catch {
            Start-Sleep -Seconds 2
            $elapsed += 2
            Write-Host "  ." -NoNewline -ForegroundColor Gray
        }
    }
    
    if (-not $qdrantReady) {
        Write-Host ""
        Write-Host "  Error: Qdrant failed to start" -ForegroundColor Red
        Stop-Job -Id $qdrantJob.Id -ErrorAction SilentlyContinue
        Remove-Job -Id $qdrantJob.Id -ErrorAction SilentlyContinue
        exit 1
    }
    
    # Store job ID for cleanup
    $global:qdrantJobId = $qdrantJob.Id
}

Write-Host ""

# Start Backend
Write-Host "Starting Backend API..." -ForegroundColor Yellow
$backendJob = Start-Job -ScriptBlock {
    Set-Location "D:\AWS\ARC-project\backend"
    python -m uvicorn app.main:app --reload --port 8000
}
Write-Host "  Backend started (Job ID: $($backendJob.Id))" -ForegroundColor Green
Write-Host "  URL: http://localhost:8000" -ForegroundColor Gray

# Wait for backend to be ready
Write-Host "  Waiting for backend to be ready..." -ForegroundColor Gray
$maxWait = 30
$elapsed = 0
$backendReady = $false

while ($elapsed -lt $maxWait) {
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get -TimeoutSec 2 -ErrorAction SilentlyContinue
        Write-Host "  Backend is ready!" -ForegroundColor Green
        $backendReady = $true
        break
    } catch {
        Start-Sleep -Seconds 2
        $elapsed += 2
        Write-Host "  ." -NoNewline -ForegroundColor Gray
    }
}

if (-not $backendReady) {
    Write-Host ""
    Write-Host "  Warning: Backend may not be ready yet" -ForegroundColor Yellow
}

Write-Host ""

# Start Worker
Write-Host "Starting SQS Worker..." -ForegroundColor Yellow
$workerJob = Start-Job -ScriptBlock {
    Set-Location "D:\AWS\ARC-project\backend"
    python run_worker.py
}
Write-Host "  Worker started (Job ID: $($workerJob.Id))" -ForegroundColor Green

Write-Host ""
Write-Host "=== Services Started ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Running services:" -ForegroundColor Yellow
Write-Host "  - Qdrant: http://localhost:6333" -ForegroundColor Gray
Write-Host "  - Backend: http://localhost:8000 (Job $($backendJob.Id))" -ForegroundColor Gray
Write-Host "  - Worker: Processing SQS messages (Job $($workerJob.Id))" -ForegroundColor Gray
Write-Host ""
Write-Host "To view logs:" -ForegroundColor Yellow
Write-Host "  Backend: Receive-Job -Id $($backendJob.Id) -Keep" -ForegroundColor Gray
Write-Host "  Worker:  Receive-Job -Id $($workerJob.Id) -Keep" -ForegroundColor Gray
Write-Host ""
Write-Host "To stop services:" -ForegroundColor Yellow
Write-Host "  Stop-Job -Id $($backendJob.Id),$($workerJob.Id)" -ForegroundColor Gray
Write-Host "  Remove-Job -Id $($backendJob.Id),$($workerJob.Id)" -ForegroundColor Gray
Write-Host ""
Write-Host "Ready to test! Run: .\test-rag-pipeline.ps1" -ForegroundColor Green
Write-Host ""

# Keep script running to show logs
Write-Host "Press Ctrl+C to stop all services" -ForegroundColor Yellow
Write-Host ""

try {
    while ($true) {
        Start-Sleep -Seconds 5
        
        # Check if jobs are still running
        $backendState = (Get-Job -Id $backendJob.Id).State
        $workerState = (Get-Job -Id $workerJob.Id).State
        
        if ($backendState -ne "Running") {
            Write-Host "Warning: Backend stopped ($backendState)" -ForegroundColor Red
        }
        if ($workerState -ne "Running") {
            Write-Host "Warning: Worker stopped ($workerState)" -ForegroundColor Red
        }
    }
} finally {
    Write-Host ""
    Write-Host "Stopping services..." -ForegroundColor Yellow
    
    # Stop backend and worker
    Stop-Job -Id $backendJob.Id,$workerJob.Id -ErrorAction SilentlyContinue
    Remove-Job -Id $backendJob.Id,$workerJob.Id -ErrorAction SilentlyContinue
    
    # Stop Qdrant if we started it
    if ($global:qdrantJobId) {
        Write-Host "Stopping Qdrant..." -ForegroundColor Yellow
        Stop-Job -Id $global:qdrantJobId -ErrorAction SilentlyContinue
        Remove-Job -Id $global:qdrantJobId -ErrorAction SilentlyContinue
    }
    
    Write-Host "All services stopped" -ForegroundColor Green
}
