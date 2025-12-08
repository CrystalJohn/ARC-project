# Start Full Stack: Backend + Worker + Frontend
# Opens browser automatically for testing

$ErrorActionPreference = "Continue"

Write-Host "=== Starting Full Stack RAG Application ===" -ForegroundColor Cyan
Write-Host ""

# Configuration
$BACKEND_PORT = 8000
$FRONTEND_PORT = 5173
$QDRANT_PORT = 6333

# Step 1: Check and start Qdrant
Write-Host "Step 1: Checking Qdrant..." -ForegroundColor Yellow

# Check if Qdrant container exists
$qdrantContainer = docker ps -a --filter "name=arc-qdrant" --format "{{.Names}}"

if ($qdrantContainer -eq "arc-qdrant") {
    # Container exists, check if running
    $qdrantStatus = docker ps --filter "name=arc-qdrant" --format "{{.Status}}"
    
    if ($qdrantStatus) {
        Write-Host "  Qdrant container is running" -ForegroundColor Green
        
        # Check if healthy
        try {
            $response = Invoke-RestMethod -Uri "http://localhost:$QDRANT_PORT/collections" -Method Get -TimeoutSec 2
            Write-Host "  Qdrant is healthy" -ForegroundColor Green
        } catch {
            Write-Host "  Qdrant is unhealthy, restarting..." -ForegroundColor Yellow
            docker restart arc-qdrant | Out-Null
            Start-Sleep -Seconds 5
            Write-Host "  Qdrant restarted" -ForegroundColor Green
        }
    } else {
        Write-Host "  Starting existing Qdrant container..." -ForegroundColor Yellow
        docker start arc-qdrant | Out-Null
        Start-Sleep -Seconds 5
        Write-Host "  Qdrant started" -ForegroundColor Green
    }
} else {
    Write-Host "  Creating new Qdrant container..." -ForegroundColor Yellow
    docker run -d --name arc-qdrant -p ${QDRANT_PORT}:6333 -p 6334:6334 qdrant/qdrant | Out-Null
    Start-Sleep -Seconds 10
    Write-Host "  Qdrant container created and started" -ForegroundColor Green
}

Write-Host ""

# Step 2: Start Backend
Write-Host "Step 2: Starting Backend API..." -ForegroundColor Yellow

# Check if backend is already running
try {
    $backendHealth = Invoke-RestMethod -Uri "http://localhost:$BACKEND_PORT/health" -Method Get -TimeoutSec 2 -ErrorAction SilentlyContinue
    Write-Host "  Backend is already running on port $BACKEND_PORT" -ForegroundColor Green
    $backendJob = $null
} catch {
    # Start backend
    $backendJob = Start-Job -ScriptBlock {
        param($port)
        Set-Location "D:\AWS\ARC-project\backend"
        python -m uvicorn app.main:app --reload --port $port --host 0.0.0.0
    } -ArgumentList $BACKEND_PORT
    
    Write-Host "  Backend starting (Job ID: $($backendJob.Id))..." -ForegroundColor Gray
    
    # Wait for backend to be ready
    $maxWait = 30
    $elapsed = 0
    $backendReady = $false
    
    while ($elapsed -lt $maxWait) {
        try {
            $response = Invoke-RestMethod -Uri "http://localhost:$BACKEND_PORT/health" -Method Get -TimeoutSec 2 -ErrorAction SilentlyContinue
            Write-Host "  Backend is ready on http://localhost:$BACKEND_PORT" -ForegroundColor Green
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
}

Write-Host ""

# Step 3: Start Worker
Write-Host "Step 3: Starting SQS Worker..." -ForegroundColor Yellow

$workerJob = Start-Job -ScriptBlock {
    Set-Location "D:\AWS\ARC-project\backend"
    python run_worker.py
}

Write-Host "  Worker started (Job ID: $($workerJob.Id))" -ForegroundColor Green

Write-Host ""

# Step 4: Start Frontend
Write-Host "Step 4: Starting Frontend..." -ForegroundColor Yellow

# Check if frontend is already running
try {
    $frontendCheck = Invoke-WebRequest -Uri "http://localhost:$FRONTEND_PORT" -Method Get -TimeoutSec 2 -ErrorAction SilentlyContinue
    Write-Host "  Frontend is already running on port $FRONTEND_PORT" -ForegroundColor Green
    $frontendJob = $null
} catch {
    # Start frontend
    $frontendJob = Start-Job -ScriptBlock {
        param($port)
        Set-Location "D:\AWS\ARC-project"
        npm run dev -- --port $port --host
    } -ArgumentList $FRONTEND_PORT
    
    Write-Host "  Frontend starting (Job ID: $($frontendJob.Id))..." -ForegroundColor Gray
    
    # Wait for frontend to be ready
    $maxWait = 30
    $elapsed = 0
    $frontendReady = $false
    
    while ($elapsed -lt $maxWait) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:$FRONTEND_PORT" -Method Get -TimeoutSec 2 -ErrorAction SilentlyContinue
            Write-Host "  Frontend is ready on http://localhost:$FRONTEND_PORT" -ForegroundColor Green
            $frontendReady = $true
            break
        } catch {
            Start-Sleep -Seconds 2
            $elapsed += 2
            Write-Host "  ." -NoNewline -ForegroundColor Gray
        }
    }
    
    if (-not $frontendReady) {
        Write-Host ""
        Write-Host "  Warning: Frontend may not be ready yet" -ForegroundColor Yellow
    }
}

Write-Host ""

# Step 5: Open Browser
Write-Host "Step 5: Opening browser..." -ForegroundColor Yellow
Start-Sleep -Seconds 2
Start-Process "http://localhost:$FRONTEND_PORT"
Write-Host "  Browser opened" -ForegroundColor Green

Write-Host ""
Write-Host "=== Full Stack Started ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Services running:" -ForegroundColor Yellow
Write-Host "  - Qdrant:   http://localhost:$QDRANT_PORT" -ForegroundColor Gray
Write-Host "  - Backend:  http://localhost:$BACKEND_PORT" -ForegroundColor Gray
Write-Host "  - Frontend: http://localhost:$FRONTEND_PORT" -ForegroundColor Gray
Write-Host ""

if ($backendJob) {
    Write-Host "  - Backend Job ID: $($backendJob.Id)" -ForegroundColor Gray
}
if ($workerJob) {
    Write-Host "  - Worker Job ID:  $($workerJob.Id)" -ForegroundColor Gray
}
if ($frontendJob) {
    Write-Host "  - Frontend Job ID: $($frontendJob.Id)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "To view logs:" -ForegroundColor Yellow
if ($backendJob) {
    Write-Host "  Backend: Receive-Job -Id $($backendJob.Id) -Keep" -ForegroundColor Gray
}
if ($workerJob) {
    Write-Host "  Worker:  Receive-Job -Id $($workerJob.Id) -Keep" -ForegroundColor Gray
}
if ($frontendJob) {
    Write-Host "  Frontend: Receive-Job -Id $($frontendJob.Id) -Keep" -ForegroundColor Gray
}

Write-Host ""
Write-Host "To stop all services:" -ForegroundColor Yellow
Write-Host "  Press Ctrl+C or run: .\stop-services.ps1" -ForegroundColor Gray
Write-Host ""
Write-Host "Ready to test! Upload documents and chat in the browser." -ForegroundColor Green
Write-Host ""

# Save job IDs for cleanup script
$jobIds = @()
if ($backendJob) { $jobIds += $backendJob.Id }
if ($workerJob) { $jobIds += $workerJob.Id }
if ($frontendJob) { $jobIds += $frontendJob.Id }

if ($jobIds.Count -gt 0) {
    $jobIds -join "," | Out-File -FilePath ".running-jobs.txt" -Encoding UTF8
}

# Keep script running and monitor
Write-Host "Monitoring services (Press Ctrl+C to stop)..." -ForegroundColor Yellow
Write-Host ""

try {
    while ($true) {
        Start-Sleep -Seconds 10
        
        # Check job states
        $allJobs = @()
        if ($backendJob) { $allJobs += $backendJob.Id }
        if ($workerJob) { $allJobs += $workerJob.Id }
        if ($frontendJob) { $allJobs += $frontendJob.Id }
        
        foreach ($jobId in $allJobs) {
            $job = Get-Job -Id $jobId -ErrorAction SilentlyContinue
            if ($job -and $job.State -ne "Running") {
                Write-Host "Warning: Job $jobId stopped ($($job.State))" -ForegroundColor Red
                
                # Show last error if any
                $errors = Receive-Job -Id $jobId -ErrorAction SilentlyContinue 2>&1 | Select-Object -Last 5
                if ($errors) {
                    Write-Host "Last errors:" -ForegroundColor Red
                    $errors | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
                }
            }
        }
    }
} finally {
    Write-Host ""
    Write-Host "Stopping services..." -ForegroundColor Yellow
    
    # Stop all jobs
    if ($backendJob) {
        Stop-Job -Id $backendJob.Id -ErrorAction SilentlyContinue
        Remove-Job -Id $backendJob.Id -ErrorAction SilentlyContinue
    }
    if ($workerJob) {
        Stop-Job -Id $workerJob.Id -ErrorAction SilentlyContinue
        Remove-Job -Id $workerJob.Id -ErrorAction SilentlyContinue
    }
    if ($frontendJob) {
        Stop-Job -Id $frontendJob.Id -ErrorAction SilentlyContinue
        Remove-Job -Id $frontendJob.Id -ErrorAction SilentlyContinue
    }
    
    # Clean up job IDs file
    if (Test-Path ".running-jobs.txt") {
        Remove-Item ".running-jobs.txt" -Force
    }
    
    Write-Host "All services stopped" -ForegroundColor Green
    Write-Host ""
}
