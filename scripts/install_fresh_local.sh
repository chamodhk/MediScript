#!/usr/bin/env bash
# =============================================================================
# MediScript – Robust local installation script
# Supports: Ubuntu 20.04+, Debian 11+, any apt-based Linux distro
# Requires: Internet access, sudo privileges
#
# Usage:
#   bash install_fresh_local.sh [INSTALL_DIR]
#
# Environment overrides:
#   INSTALL_DIR=~/MediScript          where to clone the repo
#   BRANCH=main                       git branch to check out
#   REPO_URL=https://...              override git remote
#   INSTALL_OLLAMA=1                  install Ollama (default: 1)
#   PULL_OLLAMA_MODEL=1               pull phi3 model after Ollama install (default: 1)
#   INSTALL_NGROK=1                   install ngrok for Twilio webhook tunnelling (default: 1)
#   SKIP_FRONTEND_BUILD=0             skip npm run build verification (default: 0)
#   FORCE_RESEED=0                    re-run seed even if DB already exists (default: 0)
# =============================================================================

set -Eeuo pipefail

# ── Defaults ──────────────────────────────────────────────────────────────────
REPO_URL="${REPO_URL:-https://github.com/chamodhk/MediScript.git}"
INSTALL_DIR="${1:-${INSTALL_DIR:-$HOME/MediScript}}"
BRANCH="${BRANCH:-main}"
INSTALL_OLLAMA="${INSTALL_OLLAMA:-1}"
PULL_OLLAMA_MODEL="${PULL_OLLAMA_MODEL:-1}"
INSTALL_NGROK="${INSTALL_NGROK:-1}"
SKIP_FRONTEND_BUILD="${SKIP_FRONTEND_BUILD:-0}"
FORCE_RESEED="${FORCE_RESEED:-0}"
PYTHON_VERSION="3.13"
NODE_MIN_MAJOR=18
OLLAMA_MODEL="phi3"

# ── Colour helpers ─────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[1;34m'; RESET='\033[0m'

log()  { printf "\n${BLUE}[%s] %s${RESET}\n" "$(date '+%H:%M:%S')" "$*"; }
ok()   { printf "  ${GREEN}✓ %s${RESET}\n" "$*"; }
warn() { printf "  ${YELLOW}⚠ %s${RESET}\n" "$*" >&2; }
fail() { printf "\n${RED}ERROR: %s${RESET}\n" "$*" >&2; exit 1; }
have() { command -v "$1" >/dev/null 2>&1; }

# ── Sudo wrapper (works as root too) ──────────────────────────────────────────
SUDO=""
if [[ $EUID -ne 0 ]]; then
  have sudo || fail "sudo is not available. Run as root or install sudo first."
  SUDO="sudo"
fi

apt_install() {
  log "apt-get install: $*"
  $SUDO apt-get install -y --no-install-recommends "$@"
}

# ── Step 1: Validate platform ─────────────────────────────────────────────────
log "Checking platform"
[[ "$(uname -s)" == "Linux" ]] || fail "This script targets Linux only."
have apt-get               || fail "Only apt-based distros (Ubuntu/Debian) are supported."
ok "Linux + apt detected"

# ── Step 2: System package prerequisites ──────────────────────────────────────
log "Updating apt and installing base system packages"
$SUDO apt-get update -q

MISSING_PKGS=()
for pkg in git curl wget ca-certificates gnupg ffmpeg build-essential python3-dev; do
  if ! dpkg -s "$pkg" >/dev/null 2>&1; then
    MISSING_PKGS+=("$pkg")
  fi
done

if [[ ${#MISSING_PKGS[@]} -gt 0 ]]; then
  apt_install "${MISSING_PKGS[@]}"
else
  ok "All base packages already installed"
fi

# ── Step 3: Node.js (>=18) ────────────────────────────────────────────────────
log "Checking Node.js"
NODE_OK=0
if have node; then
  NODE_MAJOR=$(node --version | sed 's/v\([0-9]*\).*/\1/')
  if [[ "$NODE_MAJOR" -ge "$NODE_MIN_MAJOR" ]]; then
    ok "Node.js $(node --version) already installed"
    NODE_OK=1
  else
    warn "Node.js $(node --version) is too old (need ≥${NODE_MIN_MAJOR}), upgrading via NodeSource"
  fi
fi

if [[ "$NODE_OK" -eq 0 ]]; then
  log "Installing Node.js ${NODE_MIN_MAJOR}.x via NodeSource"
  curl -fsSL https://deb.nodesource.com/setup_${NODE_MIN_MAJOR}.x | $SUDO bash -
  apt_install nodejs
  ok "Node.js $(node --version) installed"
fi

have npm || fail "npm not found after Node.js install"
ok "npm $(npm --version)"

# ── Step 4: uv ────────────────────────────────────────────────────────────────
log "Checking uv"
# Ensure uv is in PATH even if it was installed in this session
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"

if ! have uv; then
  log "Installing uv (Python package and project manager)"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # Re-source after install
  export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
  have uv || fail "uv installation failed – check https://docs.astral.sh/uv/"
fi
ok "uv $(uv --version)"

# ── Step 5: Python 3.13 via uv ────────────────────────────────────────────────
log "Ensuring Python ${PYTHON_VERSION} is available via uv"
if ! uv python list --only-installed 2>/dev/null | grep -q "cpython-${PYTHON_VERSION}"; then
  log "Downloading CPython ${PYTHON_VERSION}"
  uv python install "${PYTHON_VERSION}"
fi
PYTHON_BIN="$(uv python find "${PYTHON_VERSION}")"
ok "Python at: $PYTHON_BIN"
"$PYTHON_BIN" --version

# ── Step 6: Clone / update repository ────────────────────────────────────────
log "Setting up repository at $INSTALL_DIR"
if [[ -d "$INSTALL_DIR/.git" ]]; then
  warn "Repository already exists – pulling latest changes"
  git -C "$INSTALL_DIR" fetch --all --tags --prune
  CURRENT_BRANCH=$(git -C "$INSTALL_DIR" rev-parse --abbrev-ref HEAD)
  if [[ "$CURRENT_BRANCH" != "$BRANCH" ]]; then
    git -C "$INSTALL_DIR" checkout "$BRANCH"
  fi
  git -C "$INSTALL_DIR" pull --ff-only origin "$BRANCH" || \
    warn "Could not fast-forward; local changes may be present"
elif [[ -e "$INSTALL_DIR" ]]; then
  fail "Target path already exists but is not a git repo: $INSTALL_DIR"
else
  mkdir -p "$(dirname "$INSTALL_DIR")"
  git clone --branch "$BRANCH" "$REPO_URL" "$INSTALL_DIR"
fi
ok "Repository at $INSTALL_DIR (branch: $BRANCH)"

BACKEND_DIR="$INSTALL_DIR/backend"
FRONTEND_DIR="$INSTALL_DIR/frontend"

# ── Step 7: Backend directory scaffolding ─────────────────────────────────────
log "Creating required backend directories"
mkdir -p "$BACKEND_DIR/static/prescriptions" "$BACKEND_DIR/temp"
ok "Directories ready"

# ── Step 8: Backend .env ──────────────────────────────────────────────────────
BACKEND_ENV="$BACKEND_DIR/.env"
if [[ -f "$BACKEND_ENV" ]]; then
  ok "Keeping existing backend .env"
else
  log "Writing default backend .env"
  cat >"$BACKEND_ENV" <<'EOF'
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
EOF
  ok "backend/.env written"
fi

# ── Step 9: Python virtual environment (uv) ───────────────────────────────────
VENV_DIR="$BACKEND_DIR/.venv"
log "Creating Python ${PYTHON_VERSION} virtual environment at $VENV_DIR"
uv venv --python "${PYTHON_VERSION}" "$VENV_DIR"
VENV_PYTHON="$VENV_DIR/bin/python"
VENV_PIP="$VENV_DIR/bin/pip"
ok "venv: $VENV_DIR  ($(${VENV_PYTHON} --version))"

# ── Step 10: Install Python dependencies ──────────────────────────────────────
log "Installing Python dependencies from requirements.txt"

# Detect if NVIDIA GPU + CUDA are available
GPU_AVAILABLE=0
if have nvidia-smi && nvidia-smi >/dev/null 2>&1; then
  GPU_AVAILABLE=1
  ok "NVIDIA GPU detected – installing full requirements (including CUDA packages)"
else
  warn "No NVIDIA GPU detected – will install CPU-only variants of GPU packages"
fi

# Function to attempt uv pip install with a requirements file
try_install_requirements() {
  local req_file="$1"
  shift
  uv pip install \
    --python "$VENV_PYTHON" \
    -r "$req_file" \
    "$@" 2>&1
}

REQ_FILE="$BACKEND_DIR/requirements.txt"

if [[ "$GPU_AVAILABLE" -eq 1 ]]; then
  # Full install including CUDA wheels
  try_install_requirements "$REQ_FILE" || fail "pip install failed even with GPU present. Check output above."
else
  # Build a CPU-friendly requirements file by removing GPU-only packages
  CPU_REQ="$(mktemp /tmp/mediscript_cpu_req.XXXXXX.txt)"
  trap 'rm -f "$CPU_REQ"' EXIT

  # Filter out CUDA/nvidia/triton packages that don't make sense on CPU-only machines
  grep -vE \
    '^(nvidia-|cuda-|triton==)' \
    "$REQ_FILE" >"$CPU_REQ"

  # Replace torch/torchaudio/torchvision with CPU-only builds from PyTorch index
  # Extract pinned versions from requirements.txt
  TORCH_VER=$(grep    -m1 '^torch==' "$REQ_FILE"        | cut -d= -f3 || true)
  TORCHAUDIO_VER=$(grep -m1 '^torchaudio==' "$REQ_FILE" | cut -d= -f3 || true)
  TORCHVISION_VER=$(grep -m1 '^torchvision==' "$REQ_FILE" | cut -d= -f3 || true)

  # Remove existing torch lines from the CPU req file and re-add without version pins
  # so PyTorch CPU index can satisfy them
  sed -i '/^torch==/d;/^torchaudio==/d;/^torchvision==/d' "$CPU_REQ"

  # Attempt 1: install non-torch packages first
  log "Installing non-torch dependencies (CPU)"
  if ! try_install_requirements "$CPU_REQ"; then
    warn "Some packages in requirements.txt failed – retrying with --no-deps for problematic ones"
    # Best-effort: install what we can
    uv pip install --python "$VENV_PYTHON" -r "$CPU_REQ" --no-deps 2>&1 || true
    uv pip install --python "$VENV_PYTHON" -r "$CPU_REQ" 2>&1 || true
  fi

  # Attempt 2: install torch CPU builds
  log "Installing PyTorch (CPU-only) from PyTorch index"
  TORCH_INDEX="https://download.pytorch.org/whl/cpu"

  if [[ -n "$TORCH_VER" ]]; then
    uv pip install \
      --python "$VENV_PYTHON" \
      --extra-index-url "$TORCH_INDEX" \
      "torch==${TORCH_VER}" \
      ${TORCHAUDIO_VER:+"torchaudio==${TORCHAUDIO_VER}"} \
      ${TORCHVISION_VER:+"torchvision==${TORCHVISION_VER}"} \
      2>&1 || \
    {
      warn "Pinned torch version not found in CPU index – installing latest stable CPU torch"
      uv pip install \
        --python "$VENV_PYTHON" \
        --extra-index-url "$TORCH_INDEX" \
        "torch" "torchaudio" "torchvision" \
        2>&1 || warn "torch install failed; transcription features may not work"
    }
  else
    uv pip install \
      --python "$VENV_PYTHON" \
      --extra-index-url "$TORCH_INDEX" \
      "torch" "torchaudio" "torchvision" \
      2>&1 || warn "torch install failed; transcription features may not work"
  fi
fi

# Verify critical imports
log "Verifying critical backend imports"
IMPORT_ERRORS=0
for module in fastapi sqlalchemy alembic uvicorn pydantic passlib; do
  if "$VENV_PYTHON" -c "import $module" 2>/dev/null; then
    ok "import $module"
  else
    warn "import $module FAILED – trying to install manually"
    uv pip install --python "$VENV_PYTHON" "$module" || true
    IMPORT_ERRORS=$((IMPORT_ERRORS + 1))
  fi
done

if [[ "$IMPORT_ERRORS" -gt 0 ]]; then
  warn "$IMPORT_ERRORS import(s) failed above. The backend may be partially functional."
fi

# ── Step 11: Database migrations ──────────────────────────────────────────────
log "Running Alembic database migrations"
(
  cd "$BACKEND_DIR"
  "$VENV_DIR/bin/alembic" upgrade head
)
ok "Migrations applied"

# ── Step 12: Seed demo data ────────────────────────────────────────────────────
DB_FILE="$BACKEND_DIR/mediscript.db"
if [[ ! -f "$DB_FILE" || "$FORCE_RESEED" -eq 1 ]]; then
  log "Seeding demo data"
  (
    cd "$BACKEND_DIR"
    PYTHONPATH="$BACKEND_DIR" "$VENV_PYTHON" -m core.seed
  )
  ok "Demo data seeded"
else
  log "Database already exists – running seed (idempotent)"
  (
    cd "$BACKEND_DIR"
    PYTHONPATH="$BACKEND_DIR" "$VENV_PYTHON" -m core.seed
  )
  ok "Seed complete"
fi

# ── Step 13: Smoke-test backend import ────────────────────────────────────────
log "Smoke-testing backend application import"
(
  cd "$INSTALL_DIR"
  PYTHONPATH="$BACKEND_DIR:$INSTALL_DIR" \
    "$VENV_PYTHON" -c "
import sys
sys.path[:0] = ['backend', '.']
import main
print('backend main.py import OK')
"
) && ok "Backend import smoke test passed" \
  || warn "Backend import smoke test failed – check logs above"

# ── Step 14: Frontend .env.local ──────────────────────────────────────────────
FRONTEND_ENV="$FRONTEND_DIR/.env.local"
if [[ -f "$FRONTEND_ENV" ]]; then
  ok "Keeping existing frontend .env.local"
else
  log "Writing default frontend .env.local"
  cat >"$FRONTEND_ENV" <<'EOF'
VITE_API_BASE_URL=http://localhost:8000/api
EOF
  ok "frontend/.env.local written"
fi

# ── Step 15: Frontend dependencies ────────────────────────────────────────────
log "Installing frontend npm dependencies"
(
  cd "$FRONTEND_DIR"
  if [[ -f package-lock.json ]]; then
    npm ci
  else
    npm install
  fi
)
ok "npm install complete"

# ── Step 16: Frontend build verification ──────────────────────────────────────
if [[ "$SKIP_FRONTEND_BUILD" -eq 0 ]]; then
  log "Building frontend (verification pass)"
  (
    cd "$FRONTEND_DIR"
    npm run build
  )
  ok "Frontend build succeeded"
else
  warn "Skipping frontend build (SKIP_FRONTEND_BUILD=1)"
fi

# ── Step 17: Ollama ───────────────────────────────────────────────────────────
if [[ "$INSTALL_OLLAMA" -eq 1 ]]; then
  log "Checking Ollama"
  if have ollama; then
    ok "Ollama already installed: $(ollama --version 2>/dev/null || echo 'version unknown')"
  else
    log "Installing Ollama via official installer"
    curl -fsSL https://ollama.com/install.sh | sh
    have ollama || fail "Ollama installation failed"
    ok "Ollama installed"
  fi

  if [[ "$PULL_OLLAMA_MODEL" -eq 1 ]]; then
    log "Pulling Ollama model: $OLLAMA_MODEL (this may take several minutes)"
    # Start Ollama server in background if not already running
    OLLAMA_STARTED=0
    if ! curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then
      ollama serve &>/dev/null &
      OLLAMA_PID=$!
      OLLAMA_STARTED=1
      # Wait for it to be ready
      for i in $(seq 1 30); do
        if curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then
          break
        fi
        sleep 1
      done
    fi

    if curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then
      ollama pull "$OLLAMA_MODEL" && ok "Model $OLLAMA_MODEL pulled" \
        || warn "Failed to pull $OLLAMA_MODEL – you can run: ollama pull $OLLAMA_MODEL"
    else
      warn "Ollama server did not become ready; pull skipped. Run: ollama serve && ollama pull $OLLAMA_MODEL"
    fi

    if [[ "${OLLAMA_STARTED:-0}" -eq 1 ]]; then
      kill "$OLLAMA_PID" 2>/dev/null || true
    fi
  fi
else
  warn "Skipping Ollama install (INSTALL_OLLAMA=0)"
fi

# ── Step 18: LibreTranslate (NOT USED) ───────────────────────────────────────
# Translation is handled in-process via the HuggingFace NLLB model
# (zaanind/nllb-ensi-v1.6) through the transformers library.
# LIBRETRANSLATE_URL exists in config.py but is never called by any service.
# Nothing to install here.

# ── Step 19: ngrok ────────────────────────────────────────────────────────────
# ngrok tunnels localhost:8000 to a public HTTPS URL so the Twilio sandbox
# can POST incoming WhatsApp messages to /api/twilio/webhook.
if [[ "$INSTALL_NGROK" -eq 1 ]]; then
  log "Checking ngrok"
  if have ngrok; then
    ok "ngrok already installed: $(ngrok version 2>/dev/null || echo 'unknown version')"
  else
    log "Installing ngrok via official apt repository"
    # Add ngrok's signed apt repo
    curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc \
      | $SUDO tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
    echo "deb https://ngrok-agent.s3.amazonaws.com buster main" \
      | $SUDO tee /etc/apt/sources.list.d/ngrok.list >/dev/null
    $SUDO apt-get update -q
    $SUDO apt-get install -y ngrok

    if ! have ngrok; then
      # Fallback 1: snap
      if have snap; then
        warn "apt install failed — trying snap"
        $SUDO snap install ngrok
      fi
    fi

    if have ngrok; then
      ok "ngrok installed: $(ngrok version)"
    else
      warn "ngrok install failed. Download manually from: https://ngrok.com/download"
    fi
  fi
else
  warn "Skipping ngrok install (INSTALL_NGROK=0)"
fi

# ── Step 20: Convenience start scripts ────────────────────────────────────────
log "Writing start scripts"

# Backend start script
BACKEND_START="$INSTALL_DIR/scripts/start_backend.sh"
cat >"$BACKEND_START" <<EOF
#!/usr/bin/env bash
cd "$BACKEND_DIR"
PYTHONPATH="$BACKEND_DIR" exec "$VENV_DIR/bin/python" run.py "\$@"
EOF
chmod +x "$BACKEND_START"

# Frontend start script
FRONTEND_START="$INSTALL_DIR/scripts/start_frontend.sh"
cat >"$FRONTEND_START" <<EOF
#!/usr/bin/env bash
cd "$FRONTEND_DIR"
exec npm run dev "\$@"
EOF
chmod +x "$FRONTEND_START"

# ngrok start script
NGROK_START="$INSTALL_DIR/scripts/start_ngrok.sh"
cat >"$NGROK_START" <<'EOF'
#!/usr/bin/env bash
# Expose the MediScript backend to the internet for Twilio webhooks.
# Usage: bash start_ngrok.sh [--authtoken <your-token>]
#
# After running, copy the HTTPS forwarding URL and set it in the Twilio sandbox:
#   Twilio Console → Messaging → Try it out → Send a WhatsApp message
#   Sandbox Configuration → "WHEN A MESSAGE COMES IN":
#     https://<random>.ngrok-free.app/api/twilio/webhook
exec ngrok http 8000 "$@"
EOF
chmod +x "$NGROK_START"

ok "Start scripts written"

# ── Step 20: Final summary ────────────────────────────────────────────────────
cat <<SUMMARY

${GREEN}════════════════════════════════════════════════════════════════${RESET}
${GREEN}  MediScript installation complete!${RESET}
${GREEN}════════════════════════════════════════════════════════════════${RESET}

  Repo:     $INSTALL_DIR
  Backend:  $BACKEND_DIR
  Frontend: $FRONTEND_DIR
  Database: $BACKEND_DIR/mediscript.db
  Python:   ${PYTHON_VERSION} (${VENV_DIR})

${BLUE}── Start services (run each in a separate terminal) ────────────${RESET}

  1. Ollama (AI structuring):
       ollama serve
       # First time only: ollama pull ${OLLAMA_MODEL}

  2. Backend API (http://localhost:8000):
       $BACKEND_START

  3. Frontend (https://localhost:5173):
       $FRONTEND_START

  4. ngrok (Twilio WhatsApp webhook tunnel):
       $NGROK_START
       # Copy the HTTPS URL shown (e.g. https://abc123.ngrok-free.app)
       # Paste into Twilio sandbox → "WHEN A MESSAGE COMES IN":
       #   https://<id>.ngrok-free.app/api/twilio/webhook

${BLUE}── Twilio sandbox webhook setup ────────────────────────────────${RESET}

  1. Start ngrok:       bash $NGROK_START
  2. Copy the HTTPS forwarding URL from ngrok's output
  3. Go to: https://console.twilio.com → Messaging → Try it out
             → Send a WhatsApp message → Sandbox Configuration
  4. Set "WHEN A MESSAGE COMES IN" to:
       https://<your-ngrok-id>.ngrok-free.app/api/twilio/webhook
  5. Set HTTP method to: POST
  6. Add TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN to:
       $BACKEND_ENV

${BLUE}── Demo credentials ────────────────────────────────────────────${RESET}

  admin@mediscript.com       / password@123   → /admin
  doctor1@mediscript.com     / password@123   → /doctor
  doctor2@mediscript.com     / password@123   → /doctor
  pharmacy1@mediscript.com   / password@123   → /pharmacy/1
  pharmacy2@mediscript.com   / password@123   → /pharmacy/2

${BLUE}── Notes ───────────────────────────────────────────────────────${RESET}

  • The frontend uses self-signed HTTPS (accept the cert warning in browser).
  • Whisper (speech-to-text) downloads the '${WHISPER_MODEL:-small}' model on first use (~244 MB).
  • The NLLB translation model downloads on first use (~1.2 GB).
  • Twilio WhatsApp features require TWILIO_ACCOUNT_SID + TWILIO_AUTH_TOKEN in:
      $BACKEND_ENV
  • ngrok free tier gives a new random URL each restart — update the Twilio webhook accordingly.
  • To reseed demo data: FORCE_RESEED=1 bash $0

${GREEN}════════════════════════════════════════════════════════════════${RESET}

SUMMARY
