#!/usr/bin/env bash
# =============================================================================
# MediScript – Arch Linux installation script
# Supports: Arch Linux and Arch-based distros (Manjaro, EndeavourOS, CachyOS…)
# Requires: Internet access, sudo privileges
#
# Usage:
#   bash scripts/install_arch.sh [INSTALL_DIR]
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
#   AUR_HELPER=auto                   yay | paru | none (default: auto-detect)
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
AUR_HELPER="${AUR_HELPER:-auto}"
PYTHON_VERSION="3.13"
OLLAMA_MODEL="phi3"

# ── Colour helpers ─────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[1;34m'; RESET='\033[0m'

log()  { printf "\n${BLUE}[%s] %s${RESET}\n" "$(date '+%H:%M:%S')" "$*"; }
ok()   { printf "  ${GREEN}✓ %s${RESET}\n" "$*"; }
warn() { printf "  ${YELLOW}⚠ %s${RESET}\n" "$*" >&2; }
fail() { printf "\n${RED}ERROR: %s${RESET}\n" "$*" >&2; exit 1; }
have() { command -v "$1" >/dev/null 2>&1; }

# ── Sudo wrapper ───────────────────────────────────────────────────────────────
SUDO=""
if [[ $EUID -ne 0 ]]; then
  have sudo || fail "sudo is not available. Run as root or install sudo first."
  SUDO="sudo"
fi

# ── Step 1: Validate platform ─────────────────────────────────────────────────
log "Checking platform"
[[ "$(uname -s)" == "Linux" ]] || fail "This script targets Linux only."
have pacman                    || fail "pacman not found — this script is for Arch Linux only."
ok "Arch Linux + pacman detected"

# ── Step 2: Detect AUR helper ─────────────────────────────────────────────────
log "Detecting AUR helper"
detect_aur_helper() {
  if [[ "$AUR_HELPER" != "auto" ]]; then
    if [[ "$AUR_HELPER" == "none" ]]; then
      echo ""
    elif have "$AUR_HELPER"; then
      echo "$AUR_HELPER"
    else
      warn "Requested AUR helper '$AUR_HELPER' not found; falling back to direct downloads"
      echo ""
    fi
    return
  fi
  if have yay;  then echo "yay";  return; fi
  if have paru; then echo "paru"; return; fi
  echo ""
}
AUR="$(detect_aur_helper)"
if [[ -n "$AUR" ]]; then
  ok "AUR helper: $AUR"
else
  warn "No AUR helper found (yay/paru). AUR packages will be downloaded directly."
fi

# ── Step 3: System packages ────────────────────────────────────────────────────
log "Syncing pacman database and installing base packages"

# Install ffmpeg only if no ffmpeg binary is already in PATH.
# ffmpeg4.4 (a common AUR/extra package) provides the ffmpeg binary and conflicts
# with the mainline ffmpeg package via libvpx ABI version differences.
FFMPEG_PKGS=()
if ! have ffmpeg; then
  FFMPEG_PKGS=(ffmpeg)
else
  ok "ffmpeg already available ($(ffmpeg -version 2>&1 | head -1)) — skipping pacman install"
fi

# Always do a full system upgrade first on Arch — partial upgrades (-Sy without -u)
# cause broken shared library dependencies (e.g. libsimdjson, libvpx mismatches).
$SUDO pacman -Syu --noconfirm --needed \
  git curl wget ca-certificates \
  base-devel \
  "${FFMPEG_PKGS[@]}" \
  nodejs npm \
  unzip

ok "System packages installed"

# Verify Node version is recent enough (Arch is rolling so it should always be)
NODE_MAJOR=$(node --version | sed 's/v\([0-9]*\).*/\1/')
if [[ "$NODE_MAJOR" -lt 18 ]]; then
  warn "Node.js $(node --version) is older than 18 — this is unexpected on Arch. Check your mirrors."
fi
ok "Node.js $(node --version)"
ok "npm $(npm --version)"

# ── Step 4: uv ────────────────────────────────────────────────────────────────
log "Checking uv"
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"

if ! have uv; then
  log "Installing uv"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
  have uv || fail "uv install failed — check https://docs.astral.sh/uv/"
fi
ok "uv $(uv --version)"

# ── Step 5: Python 3.13 via uv ────────────────────────────────────────────────
# Arch ships its own Python (usually latest stable), but we pin to 3.13 via uv
# to guarantee the exact version regardless of what Arch's repos currently ship.
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
  warn "Repository already exists — pulling latest"
  git -C "$INSTALL_DIR" fetch --all --tags --prune
  CURRENT_BRANCH=$(git -C "$INSTALL_DIR" rev-parse --abbrev-ref HEAD)
  if [[ "$CURRENT_BRANCH" != "$BRANCH" ]]; then
    git -C "$INSTALL_DIR" checkout "$BRANCH"
  fi
  git -C "$INSTALL_DIR" pull --ff-only origin "$BRANCH" || \
    warn "Could not fast-forward; local changes may be present — continuing"
elif [[ -e "$INSTALL_DIR" ]]; then
  fail "Path exists but is not a git repo: $INSTALL_DIR. Remove it or set a different INSTALL_DIR."
else
  mkdir -p "$(dirname "$INSTALL_DIR")"
  git clone --branch "$BRANCH" "$REPO_URL" "$INSTALL_DIR"
fi
ok "Repository ready (branch: $BRANCH)"

BACKEND_DIR="$INSTALL_DIR/backend"
FRONTEND_DIR="$INSTALL_DIR/frontend"

# ── Step 7: Backend directory scaffolding ─────────────────────────────────────
log "Creating required backend directories"
mkdir -p "$BACKEND_DIR/static/prescriptions" "$BACKEND_DIR/temp"
ok "Directories ready"

# ── Step 8: backend/.env ──────────────────────────────────────────────────────
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

# ── Step 9: Python virtual environment ────────────────────────────────────────
VENV_DIR="$BACKEND_DIR/.venv"
log "Creating Python ${PYTHON_VERSION} venv at $VENV_DIR"
uv venv --python "${PYTHON_VERSION}" "$VENV_DIR"
VENV_PYTHON="$VENV_DIR/bin/python"
ok "venv ready  ($("$VENV_PYTHON" --version))"

# ── Step 10: Python dependencies ──────────────────────────────────────────────
log "Installing Python dependencies from requirements.txt"

# Detect NVIDIA GPU + CUDA
GPU_AVAILABLE=0
if have nvidia-smi && nvidia-smi >/dev/null 2>&1; then
  GPU_AVAILABLE=1
  ok "NVIDIA GPU detected — installing full requirements (including CUDA packages)"
else
  warn "No NVIDIA GPU detected — installing CPU-only variants"
fi

REQ_FILE="$BACKEND_DIR/requirements.txt"

if [[ "$GPU_AVAILABLE" -eq 1 ]]; then
  uv pip install \
    --python "$VENV_PYTHON" \
    -r "$REQ_FILE" \
    || fail "pip install failed. Check the output above."
else
  # Build a CPU-only requirements file: strip nvidia-*/cuda-*/triton packages
  CPU_REQ="$(mktemp /tmp/mediscript_arch_cpu_req.XXXXXX.txt)"
  trap 'rm -f "$CPU_REQ"' EXIT

  grep -vE '^(nvidia-|cuda-|triton==)' "$REQ_FILE" >"$CPU_REQ"

  # Pull pinned torch versions so we can fetch from the CPU wheel index
  TORCH_VER=$(grep       -m1 '^torch=='        "$REQ_FILE" | cut -d= -f3 || true)
  TORCHAUDIO_VER=$(grep  -m1 '^torchaudio=='   "$REQ_FILE" | cut -d= -f3 || true)
  TORCHVISION_VER=$(grep -m1 '^torchvision=='  "$REQ_FILE" | cut -d= -f3 || true)

  # Remove torch lines — we'll reinstall them from the PyTorch CPU index
  sed -i '/^torch==/d;/^torchaudio==/d;/^torchvision==/d' "$CPU_REQ"

  log "Installing non-torch packages"
  uv pip install --python "$VENV_PYTHON" -r "$CPU_REQ" || {
    warn "Some packages failed — retrying best-effort"
    uv pip install --python "$VENV_PYTHON" -r "$CPU_REQ" --no-deps 2>&1 || true
    uv pip install --python "$VENV_PYTHON" -r "$CPU_REQ" 2>&1 || true
  }

  log "Installing PyTorch (CPU) from https://download.pytorch.org/whl/cpu"
  TORCH_INDEX="https://download.pytorch.org/whl/cpu"
  if [[ -n "$TORCH_VER" ]]; then
    uv pip install \
      --python "$VENV_PYTHON" \
      --extra-index-url "$TORCH_INDEX" \
      "torch==${TORCH_VER}" \
      ${TORCHAUDIO_VER:+"torchaudio==${TORCHAUDIO_VER}"} \
      ${TORCHVISION_VER:+"torchvision==${TORCHVISION_VER}"} \
      || {
        warn "Pinned torch version not in CPU index — installing latest stable torch"
        uv pip install \
          --python "$VENV_PYTHON" \
          --extra-index-url "$TORCH_INDEX" \
          torch torchaudio torchvision \
          || warn "torch install failed; transcription will not work"
      }
  else
    uv pip install \
      --python "$VENV_PYTHON" \
      --extra-index-url "$TORCH_INDEX" \
      torch torchaudio torchvision \
      || warn "torch install failed; transcription will not work"
  fi
fi

# Verify critical imports
log "Verifying critical backend imports"
IMPORT_ERRORS=0
for module in fastapi sqlalchemy alembic uvicorn pydantic passlib; do
  if "$VENV_PYTHON" -c "import $module" 2>/dev/null; then
    ok "import $module"
  else
    warn "import $module FAILED — trying to install manually"
    uv pip install --python "$VENV_PYTHON" "$module" || true
    IMPORT_ERRORS=$((IMPORT_ERRORS + 1))
  fi
done
[[ "$IMPORT_ERRORS" -gt 0 ]] && warn "$IMPORT_ERRORS import(s) failed; backend may be partially functional"

# ── Step 11: Database migrations ──────────────────────────────────────────────
log "Running Alembic database migrations"
(
  cd "$BACKEND_DIR"
  "$VENV_DIR/bin/alembic" upgrade head
)
ok "Migrations applied"

# ── Step 12: Seed demo data ────────────────────────────────────────────────────
log "Seeding demo data (idempotent)"
(
  cd "$BACKEND_DIR"
  PYTHONPATH="$BACKEND_DIR" "$VENV_PYTHON" -m core.seed
)
ok "Seed complete"

# ── Step 13: Backend smoke test ───────────────────────────────────────────────
log "Smoke-testing backend import"
(
  cd "$INSTALL_DIR"
  PYTHONPATH="$BACKEND_DIR:$INSTALL_DIR" \
    "$VENV_PYTHON" -c "
import sys; sys.path[:0] = ['backend', '.']
import main
print('backend import OK')
"
) && ok "Backend smoke test passed" \
  || warn "Backend smoke test failed — check imports in main.py"

# ── Step 14: Frontend .env.local ──────────────────────────────────────────────
FRONTEND_ENV="$FRONTEND_DIR/.env.local"
if [[ -f "$FRONTEND_ENV" ]]; then
  ok "Keeping existing frontend .env.local"
else
  log "Writing default frontend .env.local"
  echo "VITE_API_BASE_URL=http://localhost:8000/api" >"$FRONTEND_ENV"
  ok "frontend/.env.local written"
fi

# ── Step 15: Frontend dependencies ────────────────────────────────────────────
log "Installing frontend npm dependencies"
(
  cd "$FRONTEND_DIR"
  if [[ -f package-lock.json ]]; then npm ci; else npm install; fi
)
ok "npm install complete"

# ── Step 16: Frontend build verification ──────────────────────────────────────
if [[ "$SKIP_FRONTEND_BUILD" -eq 0 ]]; then
  log "Building frontend (verification)"
  (cd "$FRONTEND_DIR" && npm run build)
  ok "Frontend build succeeded"
else
  warn "Skipping frontend build (SKIP_FRONTEND_BUILD=1)"
fi

# ── Step 17: Ollama ───────────────────────────────────────────────────────────
if [[ "$INSTALL_OLLAMA" -eq 1 ]]; then
  log "Checking Ollama"
  if have ollama; then
    ok "Ollama already installed: $(ollama --version 2>/dev/null || echo 'unknown version')"
  else
    log "Installing Ollama"
    # Ollama is in Arch's official extra repo
    if $SUDO pacman -S --noconfirm --needed ollama 2>/dev/null; then
      ok "Ollama installed via pacman"
    elif [[ -n "$AUR" ]]; then
      warn "ollama not in official repos — trying AUR via $AUR"
      "$AUR" -S --noconfirm ollama-bin
    else
      warn "ollama not in official repos and no AUR helper — using official install script"
      curl -fsSL https://ollama.com/install.sh | sh
    fi
    have ollama || fail "Ollama installation failed"
  fi

  if [[ "$PULL_OLLAMA_MODEL" -eq 1 ]]; then
    log "Pulling Ollama model: $OLLAMA_MODEL"
    OLLAMA_STARTED=0
    if ! curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then
      ollama serve &>/dev/null &
      OLLAMA_PID=$!
      OLLAMA_STARTED=1
      for i in $(seq 1 30); do
        curl -sf http://localhost:11434/api/tags >/dev/null 2>&1 && break
        sleep 1
      done
    fi

    if curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then
      ollama pull "$OLLAMA_MODEL" && ok "Model $OLLAMA_MODEL pulled" \
        || warn "Pull failed — run manually: ollama pull $OLLAMA_MODEL"
    else
      warn "Ollama server not ready; run: ollama serve && ollama pull $OLLAMA_MODEL"
    fi

    [[ "${OLLAMA_STARTED:-0}" -eq 1 ]] && kill "$OLLAMA_PID" 2>/dev/null || true
  fi
else
  warn "Skipping Ollama install (INSTALL_OLLAMA=0)"
fi

# ── Step 18: ngrok ────────────────────────────────────────────────────────────
if [[ "$INSTALL_NGROK" -eq 1 ]]; then
  log "Checking ngrok"
  if have ngrok; then
    ok "ngrok already installed: $(ngrok version 2>/dev/null || echo 'unknown version')"
  else
    log "Installing ngrok"
    NGROK_INSTALLED=0

    # Option 1: AUR (most idiomatic on Arch)
    if [[ -n "$AUR" ]]; then
      "$AUR" -S --noconfirm ngrok && NGROK_INSTALLED=1
    fi

    # Option 2: direct binary download (no AUR needed)
    if [[ "$NGROK_INSTALLED" -eq 0 ]]; then
      warn "Falling back to direct ngrok binary download"
      NGROK_ZIP="/tmp/ngrok-arch.zip"
      curl -Lo "$NGROK_ZIP" \
        "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.zip"
      unzip -o "$NGROK_ZIP" -d /tmp/ngrok-bin
      $SUDO mv /tmp/ngrok-bin/ngrok /usr/local/bin/ngrok
      $SUDO chmod +x /usr/local/bin/ngrok
      rm -rf "$NGROK_ZIP" /tmp/ngrok-bin
      NGROK_INSTALLED=1
    fi

    if have ngrok; then
      ok "ngrok installed: $(ngrok version)"
    else
      warn "ngrok install failed. Download from: https://ngrok.com/download"
    fi
  fi
else
  warn "Skipping ngrok install (INSTALL_NGROK=0)"
fi

# ── Step 19: Convenience start scripts ────────────────────────────────────────
log "Writing start scripts"
SCRIPTS_DIR="$INSTALL_DIR/scripts"

BACKEND_START="$SCRIPTS_DIR/start_backend.sh"
cat >"$BACKEND_START" <<EOF
#!/usr/bin/env bash
cd "$BACKEND_DIR"
PYTHONPATH="$BACKEND_DIR" exec "$VENV_DIR/bin/python" run.py "\$@"
EOF
chmod +x "$BACKEND_START"

FRONTEND_START="$SCRIPTS_DIR/start_frontend.sh"
cat >"$FRONTEND_START" <<EOF
#!/usr/bin/env bash
cd "$FRONTEND_DIR"
exec npm run dev "\$@"
EOF
chmod +x "$FRONTEND_START"

NGROK_START="$SCRIPTS_DIR/start_ngrok.sh"
cat >"$NGROK_START" <<'EOF'
#!/usr/bin/env bash
# Expose MediScript backend to the internet for Twilio webhooks.
# After starting, copy the HTTPS forwarding URL and paste it into:
#   Twilio Console → Messaging → Try it out → Send a WhatsApp message
#   → Sandbox Configuration → "WHEN A MESSAGE COMES IN":
#     https://<random>.ngrok-free.app/api/twilio/webhook
exec ngrok http 8000 "$@"
EOF
chmod +x "$NGROK_START"

ok "Start scripts written"

# ── Step 20: Final summary ────────────────────────────────────────────────────
cat <<SUMMARY

${GREEN}════════════════════════════════════════════════════════════════${RESET}
${GREEN}  MediScript installation complete! (Arch Linux)${RESET}
${GREEN}════════════════════════════════════════════════════════════════${RESET}

  Repo:     $INSTALL_DIR
  Backend:  $BACKEND_DIR
  Frontend: $FRONTEND_DIR
  Database: $BACKEND_DIR/mediscript.db
  Python:   ${PYTHON_VERSION} (${VENV_DIR})

${BLUE}── Start services (each in a separate terminal) ────────────────${RESET}

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

  • Frontend uses self-signed HTTPS (accept the cert warning in browser).
  • Whisper downloads the '${WHISPER_MODEL:-small}' model on first use (~244 MB).
  • The NLLB translation model downloads on first use (~1.2 GB).
  • Twilio features require TWILIO_ACCOUNT_SID + TWILIO_AUTH_TOKEN in:
      $BACKEND_ENV
  • ngrok free tier gives a new random URL on every restart — update
    the Twilio webhook URL each time you restart ngrok.
  • To reseed demo data: FORCE_RESEED=1 bash $0

${GREEN}════════════════════════════════════════════════════════════════${RESET}

SUMMARY
