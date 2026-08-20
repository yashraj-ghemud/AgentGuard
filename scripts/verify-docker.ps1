# Docker Compose Verification Script
# Verifies that all AgentGuard services are properly configured and running

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "AgentGuard Docker Verification" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Docker is installed
Write-Host "[1/8] Checking Docker installation..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "✓ Docker installed: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker not found. Please install Docker Desktop." -ForegroundColor Red
    exit 1
}

# Check Docker Compose is installed
Write-Host "[2/8] Checking Docker Compose..." -ForegroundColor Yellow
try {
    $composeVersion = docker-compose --version
    Write-Host "✓ Docker Compose installed: $composeVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker Compose not found." -ForegroundColor Red
    exit 1
}

# Check Docker is running
Write-Host "[3/8] Checking Docker daemon..." -ForegroundColor Yellow
try {
    docker ps | Out-Null
    Write-Host "✓ Docker daemon is running" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker daemon not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}

# Check docker-compose.yml exists
Write-Host "[4/8] Checking docker-compose.yml..." -ForegroundColor Yellow
if (Test-Path "docker-compose.yml") {
    Write-Host "✓ docker-compose.yml found" -ForegroundColor Green
} else {
    Write-Host "✗ docker-compose.yml not found in current directory" -ForegroundColor Red
    exit 1
}

# Check .env file
Write-Host "[5/8] Checking .env configuration..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "✓ .env file found" -ForegroundColor Green
} else {
    Write-Host "⚠ .env file not found. Creating from .env.example..." -ForegroundColor Yellow
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "✓ .env created from .env.example" -ForegroundColor Green
    } else {
        Write-Host "✗ .env.example not found" -ForegroundColor Red
        exit 1
    }
}

# Validate docker-compose configuration
Write-Host "[6/8] Validating Docker Compose configuration..." -ForegroundColor Yellow
try {
    docker-compose config | Out-Null
    Write-Host "✓ Docker Compose configuration is valid" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker Compose configuration has errors" -ForegroundColor Red
    exit 1
}

# Check if services are running
Write-Host "[7/8] Checking service status..." -ForegroundColor Yellow
$services = docker-compose ps --services 2>$null
if ($services) {
    Write-Host "Services configured:" -ForegroundColor Cyan
    $services | ForEach-Object { Write-Host "  - $_" -ForegroundColor Gray }
    
    $running = docker-compose ps --filter "status=running" -q
    if ($running) {
        Write-Host "✓ Some services are running" -ForegroundColor Green
        Write-Host ""
        Write-Host "Service Health:" -ForegroundColor Cyan
        docker-compose ps
    } else {
        Write-Host "⚠ No services currently running" -ForegroundColor Yellow
        Write-Host "Run 'docker-compose up -d' to start services" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠ No services detected" -ForegroundColor Yellow
}

# Check port availability
Write-Host "[8/8] Checking port availability..." -ForegroundColor Yellow
$ports = @(3000, 5432, 6379, 8000)
$portsOk = $true
foreach ($port in $ports) {
    $connection = Test-NetConnection -ComputerName localhost -Port $port -InformationLevel Quiet -WarningAction SilentlyContinue 2>$null
    if ($connection) {
        Write-Host "⚠ Port $port is already in use" -ForegroundColor Yellow
        $portsOk = $false
    } else {
        Write-Host "✓ Port $port is available" -ForegroundColor Green
    }
}

if (-not $portsOk) {
    Write-Host ""
    Write-Host "⚠ Some ports are in use. Services may fail to start." -ForegroundColor Yellow
    Write-Host "   Stop conflicting services or modify ports in docker-compose.yml" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Verification Complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Start services:     docker-compose up -d" -ForegroundColor Gray
Write-Host "  2. Check status:       docker-compose ps" -ForegroundColor Gray
Write-Host "  3. View logs:          docker-compose logs -f" -ForegroundColor Gray
Write-Host "  4. Run migrations:     docker-compose exec backend alembic upgrade head" -ForegroundColor Gray
Write-Host "  5. Seed data:          docker-compose exec backend python scripts/seed_data.py" -ForegroundColor Gray
Write-Host "  6. Access frontend:    http://localhost:3000" -ForegroundColor Gray
Write-Host "  7. Access API docs:    http://localhost:8000/docs" -ForegroundColor Gray
Write-Host ""
