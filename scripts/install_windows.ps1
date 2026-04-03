#Requires -Version 5.1
<#
.SYNOPSIS
    MediScript Windows installer — uv + Python 3.13

.DESCRIPTION
    Installs the full MediScript stack on a fresh Windows 10/11 machine.
    Uses winget for system packages and uv for Python environment management.

    Prerequisites installed automatically:
      Git, Node.js 22 LTS, ffmpeg, uv, Python 3.13, ngrok, Ollama (optional)

.PARAMETER InstallDir
    Where to clone the repository. Default: $env:USERPROFILE\MediScript

.PARAMETER Branch
    Git branch to check out. Default: main

.PARAMETER RepoUrl
    Override the git remote URL.

.PARAMETER InstallOllama
    Install Ollama and pull the phi3 model after installation.

.PARAMETER SkipNgrok
    Skip ngrok installation (default: install ngrok).

.PARAMETER SkipFrontendBuild
    Skip the `npm run build` verification step (faster, but doesn't catch build errors).

.PARAMETER ForceReseed
    Re-run the database seed even when mediscript.db already exists.

.EXAMPLE
    # Default install
    .\install_windows.ps1

.EXAMPLE
    # Install to a custom directory and also install Ollama
    .\install_windows.ps1 -InstallDir C:\Apps\MediScript -InstallOllama

.NOTES
    Run from an elevated PowerShell prompt (Run as Administrator) so that
    winget can install machine-wide packages without UAC interruptions.

    If execution policy blocks the script, run:
        Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
#>

[CmdletBinding()]
param(
    [string] $InstallDir      = "$env:USERPROFILE\MediScript",
    [string] $Branch          = "main",
    [string] $RepoUrl         = "https://github.com/chamodhk/MediScript.git",
    [switch] $InstallOllama,
    [switch] $SkipNgrok,
    [switch] $SkipFrontendBuild,
    [switch] $ForceReseed
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ── Constants ──────────────────────────────────────────────────────────────────
$PythonVersion    = "3.13"
$OllamaModel      = "phi3"
$NodeMinMajor     = 18
$TorchCpuIndex    = "https://download.pytorch.org/whl/cpu"
$TorchCudaIndex   = "https://download.pytorch.org/whl/cu121"

# ── Colour helpers ─────────────────────────────────────────────────────────────
function Write-Log  { param([string]$Msg) Write-Host "`n[$(Get-Date -f 'HH:mm:ss')] $Msg" -ForegroundColor Cyan }
function Write-Ok   { param([string]$Msg) Write-Host "  v $Msg" -ForegroundColor Green }
function Write-Warn { param([string]$Msg) Write-Host "  ! $Msg" -ForegroundColor Yellow }
function Write-Fail { param([string]$Msg) Write-Host "`nERROR: $Msg" -ForegroundColor Red; exit 1 }

function Test-Command {
    param([string]$Name)
    $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

# Refresh PATH from registry so newly-installed tools are visible in this session
function Update-SessionPath {
    $machine = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
    $user    = [System.Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = "$machine;$user;$env:LOCALAPPDATA\Microsoft\WinGet\Packages;" +
                "$env:USERPROFILE\.local\bin;$env:USERPROFILE\.cargo\bin"
}

function Invoke-Cmd {
    param([string]$Desc, [scriptblock]$Block)
    Write-Log $Desc
    & $Block
    if ($LASTEXITCODE -and $LASTEXITCODE -ne 0) {
        Write-Fail "$Desc failed with exit code $LASTEXITCODE"
    }
}

# ── Step 1: Platform check ─────────────────────────────────────────────────────
Write-Log "Checking platform"
if (-not $IsWindows -and $PSVersionTable.PSVersion.Major -ge 6) {
    Write-Fail "This script is for Windows only. Use install_fresh_local.sh on Linux/macOS."
}
Write-Ok "Windows detected"

# ── Step 2: winget availability ───────────────────────────────────────────────
Write-Log "Checking winget"
if (-not (Test-Command "winget")) {
    Write-Fail @"
winget (Windows Package Manager) is not available.
Install it from: https://aka.ms/getwinget
Or update via Microsoft Store → App Installer.
"@
}
Write-Ok "winget $(winget --version)"

function Install-WingetPackage {
    param([string]$Id, [string]$Name)
    Write-Log "Installing $Name via winget"
    winget install --id $Id --silent --accept-package-agreements --accept-source-agreements
    Update-SessionPath
}

# ── Step 3: Git ────────────────────────────────────────────────────────────────
Write-Log "Checking Git"
if (-not (Test-Command "git")) {
    Install-WingetPackage "Git.Git" "Git"
    Update-SessionPath
}
if (-not (Test-Command "git")) { Write-Fail "Git not found after install. Restart PowerShell and rerun." }
Write-Ok "git $(git --version)"

# ── Step 4: Node.js ────────────────────────────────────────────────────────────
Write-Log "Checking Node.js"
$NodeOk = $false
if (Test-Command "node") {
    $NodeMajor = [int](node --version).TrimStart('v').Split('.')[0]
    if ($NodeMajor -ge $NodeMinMajor) {
        Write-Ok "Node.js $(node --version) already installed"
        $NodeOk = $true
    } else {
        Write-Warn "Node.js $(node --version) too old (need >= $NodeMinMajor) — upgrading"
    }
}
if (-not $NodeOk) {
    Install-WingetPackage "OpenJS.NodeJS.LTS" "Node.js LTS"
    Update-SessionPath
    if (-not (Test-Command "node")) {
        Write-Fail "node not found after install. Restart PowerShell and rerun."
    }
    Write-Ok "Node.js $(node --version) installed"
}
if (-not (Test-Command "npm")) { Write-Fail "npm not found after Node.js install." }
Write-Ok "npm $(npm --version)"

# ── Step 5: ffmpeg ────────────────────────────────────────────────────────────
Write-Log "Checking ffmpeg"
if (-not (Test-Command "ffmpeg")) {
    # Try winget first; fall back to Chocolatey if available
    $ffmpegInstalled = $false
    try {
        winget install --id Gyan.FFmpeg --silent --accept-package-agreements --accept-source-agreements
        Update-SessionPath
        $ffmpegInstalled = Test-Command "ffmpeg"
    } catch {}

    if (-not $ffmpegInstalled -and (Test-Command "choco")) {
        Write-Warn "winget ffmpeg failed, trying Chocolatey"
        choco install ffmpeg -y
        Update-SessionPath
        $ffmpegInstalled = Test-Command "ffmpeg"
    }

    if (-not $ffmpegInstalled) {
        Write-Warn @"
ffmpeg not installed. Audio transcription (Whisper) will not work.
Install manually: https://ffmpeg.org/download.html#build-windows
Then add the bin\ folder to your PATH.
"@
    } else {
        Write-Ok "ffmpeg installed"
    }
} else {
    Write-Ok "ffmpeg already in PATH"
}

# ── Step 6: uv ─────────────────────────────────────────────────────────────────
Write-Log "Checking uv"
Update-SessionPath
if (-not (Test-Command "uv")) {
    Write-Log "Installing uv"
    $uvInstall = (Invoke-WebRequest -Uri "https://astral.sh/uv/install.ps1" -UseBasicParsing).Content
    Invoke-Expression $uvInstall
    Update-SessionPath
}
if (-not (Test-Command "uv")) {
    Write-Fail "uv not found after install. Add $env:USERPROFILE\.local\bin to your PATH and rerun."
}
Write-Ok "uv $(uv --version)"

# ── Step 7: Python 3.13 via uv ────────────────────────────────────────────────
Write-Log "Ensuring Python $PythonVersion is available via uv"
$installedPythons = uv python list --only-installed 2>$null
if ($installedPythons -notmatch "cpython-$PythonVersion") {
    Write-Log "Downloading CPython $PythonVersion"
    uv python install $PythonVersion
}
$PythonBin = (uv python find $PythonVersion).Trim()
if (-not (Test-Path $PythonBin)) { Write-Fail "Python $PythonVersion binary not found at: $PythonBin" }
Write-Ok "Python at: $PythonBin"
& $PythonBin --version

# ── Step 8: Clone / update repository ────────────────────────────────────────
Write-Log "Setting up repository at $InstallDir"
if (Test-Path "$InstallDir\.git") {
    Write-Warn "Repository already exists — pulling latest"
    $currentBranch = git -C $InstallDir rev-parse --abbrev-ref HEAD
    if ($currentBranch -ne $Branch) { git -C $InstallDir checkout $Branch }
    git -C $InstallDir fetch --all --tags --prune
    git -C $InstallDir pull --ff-only origin $Branch
} elseif (Test-Path $InstallDir) {
    Write-Fail "Path exists but is not a git repo: $InstallDir. Remove it or choose a different InstallDir."
} else {
    New-Item -ItemType Directory -Path (Split-Path $InstallDir) -Force | Out-Null
    git clone --branch $Branch $RepoUrl $InstallDir
}
Write-Ok "Repository at $InstallDir (branch: $Branch)"

$BackendDir  = "$InstallDir\backend"
$FrontendDir = "$InstallDir\frontend"
$VenvDir     = "$BackendDir\.venv"
$VenvPython  = "$VenvDir\Scripts\python.exe"
$VenvAlembic = "$VenvDir\Scripts\alembic.exe"

# ── Step 9: Backend directory scaffolding ─────────────────────────────────────
Write-Log "Creating required backend directories"
New-Item -ItemType Directory -Path "$BackendDir\static\prescriptions" -Force | Out-Null
New-Item -ItemType Directory -Path "$BackendDir\temp" -Force | Out-Null
Write-Ok "Directories ready"

# ── Step 10: Backend .env ─────────────────────────────────────────────────────
$BackendEnv = "$BackendDir\.env"
if (Test-Path $BackendEnv) {
    Write-Ok "Keeping existing backend .env"
} else {
    Write-Log "Writing default backend .env"
    @"
DATABASE_URL=sqlite+aiosqlite:///./mediscript.db
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173,https://localhost:5173,https://127.0.0.1:5173
JWT_SECRET_KEY=mediscript-local-dev-secret-please-change
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
WHISPER_MODEL=small
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=phi3
LIBRETRANSLATE_URL=http://localhost:5000
APP_ENV=development
REMINDER_TIMEZONE=Asia/Colombo
REMINDER_POLL_SECONDS=60
"@ | Set-Content -Encoding UTF8 $BackendEnv
    Write-Ok "backend\.env written"
}

# ── Step 11: Python virtual environment ────────────────────────────────────────
Write-Log "Creating Python $PythonVersion venv at $VenvDir"
uv venv --python $PythonVersion $VenvDir
if (-not (Test-Path $VenvPython)) { Write-Fail "venv python not found at $VenvPython" }
Write-Ok "venv ready  ($(& $VenvPython --version))"

# ── Step 12: Install Python dependencies ──────────────────────────────────────
Write-Log "Installing Python dependencies"

# Detect NVIDIA GPU
$GpuAvailable = $false
if (Test-Command "nvidia-smi") {
    try {
        $null = nvidia-smi 2>$null
        if ($LASTEXITCODE -eq 0) { $GpuAvailable = $true }
    } catch {}
}

if ($GpuAvailable) {
    Write-Ok "NVIDIA GPU detected — will install CUDA-enabled torch"
} else {
    Write-Warn "No NVIDIA GPU detected — will install CPU-only torch"
}

$ReqFile   = "$BackendDir\requirements.txt"
$CpuReqFile = "$env:TEMP\mediscript_win_req.txt"

# On Windows we always filter out:
#   nvidia-*/cuda-*  — Linux-only CUDA wheel packages
#   triton           — Linux-only (no Windows wheel)
#   uvloop           — Linux/macOS-only (no Windows wheel)
#   fastar           — not available for Windows
$WinExcludePattern = '^(nvidia-|cuda-|triton==|uvloop==|fastar==)'

(Get-Content $ReqFile) | Where-Object { $_ -notmatch $WinExcludePattern } | Set-Content $CpuReqFile

# Strip torch lines so we can reinstall from the correct index
$filtered = (Get-Content $CpuReqFile) | Where-Object { $_ -notmatch '^(torch|torchaudio|torchvision)==' }
$filtered | Set-Content $CpuReqFile

# Read pinned torch versions from original requirements.txt
$TorchVer       = (Get-Content $ReqFile | Select-String '^torch==')       -replace 'torch==',       '' | Select-Object -First 1
$TorchaudioVer  = (Get-Content $ReqFile | Select-String '^torchaudio==')  -replace 'torchaudio==',  '' | Select-Object -First 1
$TorchvisionVer = (Get-Content $ReqFile | Select-String '^torchvision==') -replace 'torchvision==', '' | Select-Object -First 1

# Step A: install all non-torch packages
Write-Log "Installing non-torch packages from filtered requirements"
uv pip install --python $VenvPython -r $CpuReqFile
if ($LASTEXITCODE -ne 0) {
    Write-Warn "Some packages failed — retrying package by package (best-effort)"
    Get-Content $CpuReqFile | ForEach-Object {
        $pkg = $_.Trim()
        if ($pkg -and -not $pkg.StartsWith('#')) {
            uv pip install --python $VenvPython $pkg 2>$null
        }
    }
}

# Step B: install torch from correct index
$TorchIndex = if ($GpuAvailable) { $TorchCudaIndex } else { $TorchCpuIndex }
Write-Log "Installing PyTorch from $TorchIndex"

$TorchPackages = @("torch", "torchaudio", "torchvision")
if ($TorchVer)       { $TorchPackages[0] = "torch==$TorchVer" }
if ($TorchaudioVer)  { $TorchPackages[1] = "torchaudio==$TorchaudioVer" }
if ($TorchvisionVer) { $TorchPackages[2] = "torchvision==$TorchvisionVer" }

$torchResult = uv pip install --python $VenvPython --extra-index-url $TorchIndex @TorchPackages 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Warn "Pinned torch version not found in index — installing latest stable torch"
    uv pip install --python $VenvPython --extra-index-url $TorchIndex torch torchaudio torchvision
    if ($LASTEXITCODE -ne 0) {
        Write-Warn "torch install failed. Transcription features may not work."
    }
}

# Step C: verify critical imports
Write-Log "Verifying critical backend imports"
$CriticalModules = @("fastapi", "sqlalchemy", "alembic", "uvicorn", "pydantic", "passlib")
foreach ($mod in $CriticalModules) {
    $result = & $VenvPython -c "import $mod" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Ok "import $mod"
    } else {
        Write-Warn "import $mod FAILED — attempting manual install"
        uv pip install --python $VenvPython $mod
    }
}

# ── Step 13: Database migrations ──────────────────────────────────────────────
Write-Log "Running Alembic database migrations"
Push-Location $BackendDir
try {
    & $VenvAlembic upgrade head
    if ($LASTEXITCODE -ne 0) { Write-Fail "Alembic migration failed" }
    Write-Ok "Migrations applied"
} finally {
    Pop-Location
}

# ── Step 14: Seed demo data ────────────────────────────────────────────────────
$DbFile = "$BackendDir\mediscript.db"
Write-Log "Seeding demo data (idempotent)"
Push-Location $BackendDir
try {
    $env:PYTHONPATH = $BackendDir
    & $VenvPython -m core.seed
    if ($LASTEXITCODE -ne 0) { Write-Fail "Database seeding failed" }
    Write-Ok "Seed complete"
} finally {
    Pop-Location
    Remove-Item Env:\PYTHONPATH -ErrorAction SilentlyContinue
}

# ── Step 15: Backend smoke test ───────────────────────────────────────────────
Write-Log "Smoke-testing backend import"
Push-Location $InstallDir
try {
    $env:PYTHONPATH = "$BackendDir;$InstallDir"
    & $VenvPython -c "import sys; sys.path[:0]=['backend','.']; import main; print('backend import OK')"
    if ($LASTEXITCODE -eq 0) { Write-Ok "Backend import smoke test passed" }
    else                      { Write-Warn "Backend import smoke test failed — check imports" }
} finally {
    Pop-Location
    Remove-Item Env:\PYTHONPATH -ErrorAction SilentlyContinue
}

# ── Step 16: Frontend .env.local ──────────────────────────────────────────────
$FrontendEnv = "$FrontendDir\.env.local"
if (Test-Path $FrontendEnv) {
    Write-Ok "Keeping existing frontend .env.local"
} else {
    Write-Log "Writing default frontend .env.local"
    "VITE_API_BASE_URL=http://localhost:8000/api" | Set-Content -Encoding UTF8 $FrontendEnv
    Write-Ok "frontend\.env.local written"
}

# ── Step 17: Frontend dependencies ────────────────────────────────────────────
Write-Log "Installing frontend npm dependencies"
Push-Location $FrontendDir
try {
    if (Test-Path "package-lock.json") { npm ci }
    else                               { npm install }
    if ($LASTEXITCODE -ne 0) { Write-Fail "npm install failed" }
    Write-Ok "npm install complete"
} finally {
    Pop-Location
}

# ── Step 18: Frontend build verification ──────────────────────────────────────
if (-not $SkipFrontendBuild) {
    Write-Log "Building frontend (verification)"
    Push-Location $FrontendDir
    try {
        npm run build
        if ($LASTEXITCODE -ne 0) { Write-Fail "Frontend build failed" }
        Write-Ok "Frontend build succeeded"
    } finally {
        Pop-Location
    }
} else {
    Write-Warn "Skipping frontend build (-SkipFrontendBuild)"
}

# ── Step 19: Ollama ───────────────────────────────────────────────────────────
if ($InstallOllama) {
    Write-Log "Checking Ollama"
    if (-not (Test-Command "ollama")) {
        Write-Log "Installing Ollama via winget"
        winget install --id Ollama.Ollama --silent --accept-package-agreements --accept-source-agreements
        Update-SessionPath
    }

    if (Test-Command "ollama") {
        Write-Ok "Ollama installed"
        Write-Log "Pulling model: $OllamaModel (this may take several minutes)"

        # Start Ollama in background if not already running
        $ollamaProc = $null
        try {
            $null = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -UseBasicParsing -TimeoutSec 2
            Write-Ok "Ollama already running"
        } catch {
            Write-Log "Starting Ollama service temporarily"
            $ollamaProc = Start-Process ollama -ArgumentList "serve" -PassThru -WindowStyle Hidden
            Start-Sleep -Seconds 5
        }

        # Wait up to 30s for Ollama to be ready
        $ready = $false
        for ($i = 0; $i -lt 30; $i++) {
            try {
                $null = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -UseBasicParsing -TimeoutSec 1
                $ready = $true; break
            } catch { Start-Sleep -Seconds 1 }
        }

        if ($ready) {
            ollama pull $OllamaModel
            if ($LASTEXITCODE -eq 0) { Write-Ok "Model $OllamaModel pulled" }
            else                     { Write-Warn "Failed to pull $OllamaModel — run: ollama pull $OllamaModel" }
        } else {
            Write-Warn "Ollama not ready — run manually: ollama serve && ollama pull $OllamaModel"
        }

        if ($ollamaProc) { Stop-Process -Id $ollamaProc.Id -ErrorAction SilentlyContinue }
    } else {
        Write-Warn "Ollama not found after install. Download from: https://ollama.com/download/windows"
    }
} else {
    Write-Warn "Skipping Ollama install (pass -InstallOllama to enable)"
}

# ── Step 20: ngrok ────────────────────────────────────────────────────────────
# ngrok tunnels localhost:8000 to a public HTTPS URL so the Twilio sandbox
# can POST incoming WhatsApp messages to /api/twilio/webhook.
if (-not $SkipNgrok) {
    Write-Log "Checking ngrok"
    if (-not (Test-Command "ngrok")) {
        Write-Log "Installing ngrok via winget"
        winget install --id Ngrok.Ngrok --silent --accept-package-agreements --accept-source-agreements
        Update-SessionPath
    }

    if (Test-Command "ngrok") {
        Write-Ok "ngrok installed: $(ngrok version 2>$null)"
    } else {
        Write-Warn "ngrok not found after install. Download from: https://ngrok.com/download/windows and add to PATH."
    }
} else {
    Write-Warn "Skipping ngrok install (-SkipNgrok)"
}

# ── Step 21: Convenience start scripts (.bat) ─────────────────────────────────
Write-Log "Writing start scripts"
$ScriptsDir = "$InstallDir\scripts"

@"
@echo off
cd /d "$BackendDir"
set PYTHONPATH=$BackendDir
"$VenvPython" run.py %*
"@ | Set-Content "$ScriptsDir\start_backend.bat" -Encoding UTF8

@"
@echo off
cd /d "$FrontendDir"
npm run dev %*
"@ | Set-Content "$ScriptsDir\start_frontend.bat" -Encoding UTF8

@"
@echo off
ollama serve %*
"@ | Set-Content "$ScriptsDir\start_ollama.bat" -Encoding UTF8

@"
@echo off
REM Expose the MediScript backend to the internet for Twilio webhooks.
REM After running, copy the HTTPS forwarding URL and set it in the Twilio sandbox:
REM   Twilio Console -> Messaging -> Try it out -> Send a WhatsApp message
REM   Sandbox Configuration -> "WHEN A MESSAGE COMES IN":
REM     https://<random>.ngrok-free.app/api/twilio/webhook
ngrok http 8000 %*
"@ | Set-Content "$ScriptsDir\start_ngrok.bat" -Encoding UTF8

Write-Ok "Start scripts written to $ScriptsDir"

# ── Step 22: Final summary ─────────────────────────────────────────────────────
Write-Host ""
Write-Host "================================================================" -ForegroundColor Green
Write-Host "  MediScript installation complete!" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Repo:     $InstallDir"
Write-Host "  Backend:  $BackendDir"
Write-Host "  Frontend: $FrontendDir"
Write-Host "  Database: $BackendDir\mediscript.db"
Write-Host "  Python:   $PythonVersion ($VenvDir)"
Write-Host ""
Write-Host "── Start services (run each in a separate terminal) ────────────" -ForegroundColor Cyan
Write-Host ""
Write-Host "  1. Ollama (AI structuring):"
Write-Host "       $ScriptsDir\start_ollama.bat"
Write-Host "       # First time only: ollama pull $OllamaModel"
Write-Host ""
Write-Host "  2. Backend API (http://localhost:8000):"
Write-Host "       $ScriptsDir\start_backend.bat"
Write-Host ""
Write-Host "  3. Frontend (https://localhost:5173):"
Write-Host "       $ScriptsDir\start_frontend.bat"
Write-Host ""
Write-Host "  4. ngrok (Twilio WhatsApp webhook tunnel):"
Write-Host "       $ScriptsDir\start_ngrok.bat"
Write-Host "       # Copy the HTTPS URL shown, e.g. https://abc123.ngrok-free.app"
Write-Host ""
Write-Host "── Twilio sandbox webhook setup ─────────────────────────────────" -ForegroundColor Cyan
Write-Host ""
Write-Host "  1. Start ngrok:   $ScriptsDir\start_ngrok.bat"
Write-Host "  2. Copy the HTTPS forwarding URL from ngrok's output"
Write-Host "  3. Go to: https://console.twilio.com -> Messaging -> Try it out"
Write-Host "            -> Send a WhatsApp message -> Sandbox Configuration"
Write-Host "  4. Set 'WHEN A MESSAGE COMES IN' to:"
Write-Host "       https://<your-ngrok-id>.ngrok-free.app/api/twilio/webhook"
Write-Host "  5. Set HTTP method to: POST"
Write-Host "  6. Add credentials to: $BackendEnv"
Write-Host "       TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxx"
Write-Host "       TWILIO_AUTH_TOKEN=your_auth_token"
Write-Host ""
Write-Host "── Demo credentials ─────────────────────────────────────────────" -ForegroundColor Cyan
Write-Host ""
Write-Host "  admin@mediscript.com       / password@123   -> /admin"
Write-Host "  doctor1@mediscript.com     / password@123   -> /doctor"
Write-Host "  doctor2@mediscript.com     / password@123   -> /doctor"
Write-Host "  pharmacy1@mediscript.com   / password@123   -> /pharmacy/1"
Write-Host "  pharmacy2@mediscript.com   / password@123   -> /pharmacy/2"
Write-Host ""
Write-Host "── Notes ────────────────────────────────────────────────────────" -ForegroundColor Cyan
Write-Host ""
Write-Host "  * The frontend uses self-signed HTTPS (accept the cert warning in browser)."
Write-Host "  * Whisper downloads the 'small' model on first transcription (~244 MB)."
Write-Host "  * The NLLB translation model downloads on first use (~1.2 GB)."
Write-Host "  * ngrok free tier gives a new random URL each restart — update Twilio webhook accordingly."
Write-Host "  * Twilio WhatsApp features need credentials in: $BackendEnv"
Write-Host "  * To reseed demo data: .\install_windows.ps1 -ForceReseed"
Write-Host ""
Write-Host "================================================================" -ForegroundColor Green
