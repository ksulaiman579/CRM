Write-Host "Starting Telecom CRM Development Environment (Portable Mode)..."

Write-Host "Starting Backend..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; .\python\python.exe -m uvicorn app.main:app --reload --port 8000"

Write-Host "Waiting for backend API to be healthy..."
$healthy = $false
while (-not $healthy) {
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -ErrorAction Stop
        if ($response.status -eq "ok") {
            $healthy = $true
            Write-Host "Backend API is healthy!"
        }
    } catch {
        Start-Sleep -Seconds 2
    }
}

Write-Host "Starting Frontend..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; `$env:PATH = `"P:\antydidy\frontend\node;`" + `$env:PATH; npm run dev"

