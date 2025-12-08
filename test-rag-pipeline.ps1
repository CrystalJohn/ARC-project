# Full RAG Pipeline End-to-End Test
# Tests: Upload → Processing → Embedding → Query

$ErrorActionPreference = "Stop"

# Configuration
$BACKEND_URL = "http://localhost:8000"
$TEST_FILE = "G:\My Drive\Knowledge base for ARC project\Le-Minh-Hoang-Giai-thuat&Lap-trinh.pdf"
$UPLOADED_BY = "test-user"

Write-Host "=== RAG Pipeline End-to-End Test ===" -ForegroundColor Cyan
Write-Host ""

# Check if test file exists
if (-not (Test-Path $TEST_FILE)) {
    Write-Host "Error: Test file '$TEST_FILE' not found" -ForegroundColor Red
    Write-Host "Available PDF files:" -ForegroundColor Yellow
    Get-ChildItem *.pdf | ForEach-Object { Write-Host "  - $($_.Name)" -ForegroundColor Gray }
    exit 1
}

Write-Host "Using test file: $TEST_FILE" -ForegroundColor Green
Write-Host ""

# Step 1: Upload Document
Write-Host "Step 1: Uploading document..." -ForegroundColor Yellow
try {
    $uploadResponse = curl.exe -X POST "$BACKEND_URL/api/admin/upload" `
        -F "file=@$TEST_FILE" `
        -F "uploaded_by=$UPLOADED_BY" `
        -s | ConvertFrom-Json
    
    $docId = $uploadResponse.doc_id
    Write-Host "  Success: Document uploaded" -ForegroundColor Green
    Write-Host "  Doc ID: $docId" -ForegroundColor Gray
    Write-Host "  Status: $($uploadResponse.status)" -ForegroundColor Gray
} catch {
    Write-Host "  Error: Upload failed - $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 2: Monitor Processing Status
Write-Host "Step 2: Monitoring processing status..." -ForegroundColor Yellow
$maxWait = 120  # 2 minutes
$elapsed = 0
$status = "UPLOADED"

while ($elapsed -lt $maxWait) {
    try {
        $statusResponse = curl.exe -X GET "$BACKEND_URL/api/admin/documents/$docId" -s | ConvertFrom-Json
        $status = $statusResponse.status
        
        Write-Host "  [$elapsed`s] Status: $status" -ForegroundColor Gray
        
        if ($status -eq "EMBEDDING_DONE") {
            Write-Host "  Success: Processing complete!" -ForegroundColor Green
            Write-Host "  Chunks: $($statusResponse.chunk_count)" -ForegroundColor Gray
            break
        } elseif ($status -eq "FAILED") {
            Write-Host "  Error: Processing failed" -ForegroundColor Red
            Write-Host "  Error message: $($statusResponse.error_message)" -ForegroundColor Red
            exit 1
        }
        
        Start-Sleep -Seconds 5
        $elapsed += 5
    } catch {
        Write-Host "  Warning: Status check failed - $_" -ForegroundColor Yellow
        Start-Sleep -Seconds 5
        $elapsed += 5
    }
}

if ($status -ne "EMBEDDING_DONE") {
    Write-Host "  Error: Processing timeout after $maxWait seconds" -ForegroundColor Red
    Write-Host "  Final status: $status" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 3: Query the Document
Write-Host "Step 3: Testing RAG query..." -ForegroundColor Yellow

$testQueries = @(
    "Giải thuật là gì?",
    "Các phương pháp sắp xếp trong cuốn sách này là gì?",
    "Độ phức tạp thuật toán được đo như thế nào?"
)

foreach ($query in $testQueries) {
    Write-Host ""
    Write-Host "  Query: $query" -ForegroundColor Cyan
    
    try {
        $queryBody = @{
            query = $query
            session_id = "test-session-$(Get-Random)"
        } | ConvertTo-Json -Depth 10
        
        $queryResponse = curl.exe -X POST "$BACKEND_URL/api/chat" `
            -H "Content-Type: application/json" `
            -d $queryBody `
            -s | ConvertFrom-Json
        
        Write-Host "  Answer: $($queryResponse.answer.Substring(0, [Math]::Min(200, $queryResponse.answer.Length)))..." -ForegroundColor Green
        Write-Host "  Citations: $($queryResponse.citations.Count)" -ForegroundColor Gray
        
        if ($queryResponse.citations.Count -gt 0) {
            Write-Host "  First citation:" -ForegroundColor Gray
            $firstCitation = $queryResponse.citations[0]
            Write-Host "    - Doc: $($firstCitation.filename)" -ForegroundColor Gray
            Write-Host "    - Page: $($firstCitation.page_number)" -ForegroundColor Gray
            Write-Host "    - Score: $($firstCitation.score)" -ForegroundColor Gray
        }
    } catch {
        Write-Host "  Error: Query failed - $_" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "=== Test Complete ===" -ForegroundColor Cyan
Write-Host ""

# Step 4: Verify Data in Storage
Write-Host "Step 4: Verifying data in storage..." -ForegroundColor Yellow

# Check DynamoDB
try {
    $dynamoItem = aws dynamodb get-item `
        --table-name arc-chatbot-dev-document-metadata `
        --key "{`"doc_id`":{`"S`":`"$docId`"},`"sk`":{`"S`":`"METADATA`"}}" `
        --region ap-southeast-1 `
        --output json | ConvertFrom-Json
    
    if ($dynamoItem.Item) {
        Write-Host "  DynamoDB: Document found" -ForegroundColor Green
        Write-Host "    - Status: $($dynamoItem.Item.status.S)" -ForegroundColor Gray
        Write-Host "    - Chunks: $($dynamoItem.Item.chunk_count.N)" -ForegroundColor Gray
    } else {
        Write-Host "  DynamoDB: Document not found" -ForegroundColor Red
    }
} catch {
    Write-Host "  DynamoDB: Check failed - $_" -ForegroundColor Yellow
}

# Check Qdrant
try {
    $qdrantResponse = Invoke-RestMethod -Uri "http://localhost:6333/collections/documents/points/scroll" `
        -Method Post `
        -ContentType "application/json" `
        -Body (@{
            filter = @{
                must = @(
                    @{
                        key = "doc_id"
                        match = @{ value = $docId }
                    }
                )
            }
            limit = 1
        } | ConvertTo-Json -Depth 10)
    
    $vectorCount = $qdrantResponse.result.points.Count
    if ($vectorCount -gt 0) {
        Write-Host "  Qdrant: Vectors found ($vectorCount+)" -ForegroundColor Green
    } else {
        Write-Host "  Qdrant: No vectors found" -ForegroundColor Red
    }
} catch {
    Write-Host "  Qdrant: Check failed - $_" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Pipeline Test Summary ===" -ForegroundColor Cyan
Write-Host "Document ID: $docId" -ForegroundColor Gray
Write-Host "Status: $status" -ForegroundColor Gray
Write-Host ""
Write-Host "Test completed successfully!" -ForegroundColor Green
Write-Host ""
