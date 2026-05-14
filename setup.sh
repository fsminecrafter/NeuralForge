#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# NeuralForge Studio — Setup Script (Linux / macOS / WSL)
# ─────────────────────────────────────────────────────────────────────────────
set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()    { echo -e "${BLUE}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERR]${NC}   $*"; }

echo ""
echo "  ⬡  NeuralForge Studio — Setup"
echo "  ────────────────────────────────────────"
echo ""

# ── Detect OS ──────────────────────────────────────────────────────────────
OS="$(uname -s)"
info "Operating system: $OS"

# ── Check Python ───────────────────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
    error "Python 3 not found."
    if [[ "$OS" == "Linux" ]]; then
        info "Install with: sudo apt install python3 python3-pip"
    fi
    exit 1
fi

PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
info "Python version: $PY_VER"

# ── Check tkinter ──────────────────────────────────────────────────────────
info "Checking tkinter..."
if ! python3 -c "import tkinter" 2>/dev/null; then
    warn "tkinter not found."
    if [[ "$OS" == "Linux" ]]; then
        info "Installing python3-tk..."
        sudo apt-get update -qq
        sudo apt-get install -y python3-tk
    else
        error "Please install tkinter manually for your OS."
        exit 1
    fi
else
    success "tkinter available"
fi

# ── Virtual environment ────────────────────────────────────────────────────
VENV_DIR="$(dirname "$0")/.venv"
if [[ ! -d "$VENV_DIR" ]]; then
    info "Creating virtual environment at .venv ..."
    python3 -m venv "$VENV_DIR"
    success "Virtual environment created"
else
    success "Virtual environment already exists"
fi

source "$VENV_DIR/bin/activate"

# ── pip dependencies ───────────────────────────────────────────────────────
info "Installing Python dependencies..."
pip install --quiet --upgrade pip

# Core deps — airllm is optional (used only if user wants local quantized models)
pip install --quiet requests

# Optional: airllm for direct quantized model loading (huge models on <16GB VRAM)
read -p "  Install airllm for direct quantized model loading? [y/N] " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    info "Installing airllm (may take a while, requires PyTorch)..."
    pip install --quiet airllm torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
    success "airllm installed"
else
    info "Skipping airllm (Ollama will be used for model inference)"
fi

# ── Check / install Ollama ─────────────────────────────────────────────────
echo ""
info "Checking Ollama..."
if ! command -v ollama &>/dev/null; then
    warn "Ollama not found."
    read -p "  Install Ollama now? [Y/n] " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        info "Installing Ollama..."
        curl -fsSL https://ollama.com/install.sh | sh
        success "Ollama installed"
    else
        warn "Ollama not installed. You'll need it to run models."
        warn "Install later: https://ollama.com/download"
    fi
else
    success "Ollama found: $(ollama --version 2>/dev/null || echo 'installed')"
fi

# ── Suggest starter models ─────────────────────────────────────────────────
echo ""
info "Recommended starter models (via Ollama):"
echo "   Agent:    ollama pull qwen2.5:7b"
echo "   Scripter: ollama pull qwen2.5-coder:7b"
echo ""
read -p "  Pull these now? [y/N] " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if command -v ollama &>/dev/null; then
        ollama pull qwen2.5:7b
        ollama pull qwen2.5-coder:7b
        success "Models downloaded"
    else
        warn "Ollama not available, skipping model pull"
    fi
fi

# ── Create launcher ────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LAUNCHER="$SCRIPT_DIR/launch.sh"
cat > "$LAUNCHER" <<EOF
#!/usr/bin/env bash
cd "$SCRIPT_DIR"
source .venv/bin/activate
python3 main.py "\$@"
EOF
chmod +x "$LAUNCHER"
success "Launcher created: $LAUNCHER"

# ── Desktop shortcut (Linux) ───────────────────────────────────────────────
if [[ "$OS" == "Linux" ]] && [[ -d "$HOME/.local/share/applications" ]]; then
    read -p "  Create desktop shortcut? [y/N] " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cat > "$HOME/.local/share/applications/neuralforge.desktop" <<EOF
[Desktop Entry]
Name=NeuralForge Studio
Comment=AI-powered coding assistant
Exec=bash $LAUNCHER
Terminal=false
Type=Application
Categories=Development;
EOF
        success "Desktop shortcut created"
    fi
fi

echo ""
echo "  ────────────────────────────────────────"
success "Setup complete!"
echo ""
echo "  To launch NeuralForge Studio:"
echo "    ./launch.sh"
echo "  or:"
echo "    source .venv/bin/activate && python3 main.py"
echo ""
