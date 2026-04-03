#!/usr/bin/env bash

set -Eeuo pipefail

REPO_URL="${REPO_URL:-https://github.com/chamodhk/MediScript.git}"
INSTALL_DIR="${1:-$HOME/MediScript}"
BRANCH="${BRANCH:-}"
PYTHON_BIN="${PYTHON_BIN:-}"
NODE_BIN="${NODE_BIN:-node}"
NPM_BIN="${NPM_BIN:-npm}"
INSTALL_OLLAMA="${INSTALL_OLLAMA:-0}"

log() {
  printf '\n[%s] %s\n' "$(date '+%H:%M:%S')" "$*"
}

fail() {
  printf '\nERROR: %s\n' "$*" >&2
  exit 1
}

have_cmd() {
  command -v "$1" >/dev/null 2>&1
}

detect_package_manager() {
  if have_cmd apt-get; then
    echo "apt"
    return
  fi

  if have_cmd brew; then
    echo "brew"
    return
  fi

  echo ""
}

install_with_apt() {
  local sudo_cmd=""
  if have_cmd sudo; then
    sudo_cmd="sudo"
  fi

  log "Installing missing system packages with apt"
  ${sudo_cmd} apt-get update
  ${sudo_cmd} apt-get install -y git curl ffmpeg python3 python3-venv python3-pip nodejs npm
}

install_with_brew() {
  log "Installing missing system packages with Homebrew"
  brew install git python@3.13 node ffmpeg curl
}

ensure_base_prereqs() {
  local pm
  pm="$(detect_package_manager)"

  if have_cmd git && have_cmd curl && have_cmd "$NODE_BIN" && have_cmd "$NPM_BIN"; then
    return
  fi

  case "$pm" in
    apt)
      install_with_apt
      ;;
    brew)
      install_with_brew
      ;;
    *)
      fail "Missing required tools (git/curl/node/npm) and no supported package manager was found."
      ;;
  esac
}

pick_python() {
  if [[ -n "$PYTHON_BIN" ]]; then
    echo "$PYTHON_BIN"
    return
  fi

  if have_cmd python3.13; then
    echo "python3.13"
    return
  fi

  if have_cmd python3; then
    echo "python3"
    return
  fi

  local pm
  pm="$(detect_package_manager)"
  case "$pm" in
    apt)
      install_with_apt
      ;;
    brew)
      install_with_brew
      ;;
    *)
      fail "Python 3 is required but was not found."
      ;;
  esac

  if have_cmd python3.13; then
    echo "python3.13"
    return
  fi

  if have_cmd python3; then
    echo "python3"
    return
  fi

  fail "Python 3 is still unavailable after attempting installation."
}

ensure_python_version() {
  local python_cmd="$1"
  if ! "$python_cmd" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)'; then
    fail "Python 3.11+ is required. Set PYTHON_BIN to a newer interpreter."
  fi
}

clone_or_update_repo() {
  mkdir -p "$(dirname "$INSTALL_DIR")"

  if [[ -d "$INSTALL_DIR/.git" ]]; then
    log "Updating existing repository in $INSTALL_DIR"
    git -C "$INSTALL_DIR" fetch --all --tags
    if [[ -n "$BRANCH" ]]; then
      git -C "$INSTALL_DIR" checkout "$BRANCH"
      git -C "$INSTALL_DIR" pull --ff-only origin "$BRANCH"
    else
      git -C "$INSTALL_DIR" pull --ff-only
    fi
    return
  fi

  if [[ -e "$INSTALL_DIR" ]]; then
    fail "Target path already exists and is not a git repository: $INSTALL_DIR"
  fi

  log "Cloning $REPO_URL into $INSTALL_DIR"
  if [[ -n "$BRANCH" ]]; then
    git clone --branch "$BRANCH" "$REPO_URL" "$INSTALL_DIR"
  else
    git clone "$REPO_URL" "$INSTALL_DIR"
  fi
}

write_backend_env() {
  local env_file="$1"
  if [[ -f "$env_file" ]]; then
    log "Keeping existing backend env file: $env_file"
    return
  fi

  log "Creating backend env file"
  cat >"$env_file" <<'EOF'
DATABASE_URL=sqlite+aiosqlite:///./mediscript.db
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173
JWT_SECRET_KEY=mediscript-local-dev-secret
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
}

write_frontend_env() {
  local env_file="$1"
  if [[ -f "$env_file" ]]; then
    log "Keeping existing frontend env file: $env_file"
    return
  fi

  log "Creating frontend env file"
  cat >"$env_file" <<'EOF'
VITE_API_BASE_URL=http://localhost:8000/api
EOF
}

setup_backend() {
  local repo_dir="$1"
  local python_cmd="$2"
  local backend_dir="$repo_dir/backend"
  local venv_dir="$backend_dir/.venv"

  log "Preparing backend directories"
  mkdir -p "$backend_dir/static/prescriptions" "$backend_dir/temp"
  write_backend_env "$backend_dir/.env"

  log "Creating backend virtual environment"
  "$python_cmd" -m venv "$venv_dir"

  log "Installing backend dependencies"
  "$venv_dir/bin/python" -m pip install --upgrade pip setuptools wheel
  "$venv_dir/bin/pip" install -r "$backend_dir/requirements.txt"

  log "Running database migrations"
  (
    cd "$backend_dir"
    ./.venv/bin/alembic upgrade head
  )

  log "Seeding local demo data"
  (
    cd "$backend_dir"
    ./.venv/bin/python -m core.seed
  )

  log "Smoke-testing backend import"
  (
    cd "$repo_dir"
    "$venv_dir/bin/python" -c 'import sys; sys.path[:0] = ["backend", "."]; import main; print("backend import ok")'
  )
}

setup_frontend() {
  local repo_dir="$1"
  local frontend_dir="$repo_dir/frontend"

  write_frontend_env "$frontend_dir/.env.local"

  log "Installing frontend dependencies"
  (
    cd "$frontend_dir"
    if [[ -f package-lock.json ]]; then
      "$NPM_BIN" ci
    else
      "$NPM_BIN" install
    fi
  )

  log "Building frontend once to verify install"
  (
    cd "$frontend_dir"
    "$NPM_BIN" run build
  )
}

install_ollama_if_requested() {
  if [[ "$INSTALL_OLLAMA" != "1" ]]; then
    return
  fi

  if have_cmd ollama; then
    log "Ollama already installed"
    return
  fi

  case "$(uname -s)" in
    Linux|Darwin)
      log "Installing Ollama"
      curl -fsSL https://ollama.com/install.sh | sh
      ;;
    *)
      fail "Automatic Ollama install is only supported for Linux and macOS."
      ;;
  esac
}

print_next_steps() {
  local repo_dir="$1"
  cat <<EOF

Install complete.

Repo: $repo_dir

Start backend:
  cd "$repo_dir/backend"
  ./.venv/bin/python run.py

Start frontend:
  cd "$repo_dir/frontend"
  $NPM_BIN run dev

Default demo logins:
  admin@mediscript.com / password@123
  doctor1@mediscript.com / password@123
  doctor2@mediscript.com / password@123
  pharmacy1@mediscript.com / password@123
  pharmacy2@mediscript.com / password@123

Notes:
  - The backend uses SQLite at backend/mediscript.db by default.
  - Translation and transcription features download models on first use.
  - Twilio WhatsApp features need TWILIO_* values in backend/.env.
  - AI structuring expects an Ollama service; rerun with INSTALL_OLLAMA=1 if you want the script to install it.
EOF
}

main() {
  ensure_base_prereqs
  local python_cmd
  python_cmd="$(pick_python)"
  ensure_python_version "$python_cmd"

  clone_or_update_repo
  install_ollama_if_requested
  setup_backend "$INSTALL_DIR" "$python_cmd"
  setup_frontend "$INSTALL_DIR"
  print_next_steps "$INSTALL_DIR"
}

main "$@"
