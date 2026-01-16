#!/usr/bin/env bash
set -e

echo "== Basic packages =="
apt update
apt install -y neovim tmux nvtop curl git # assumes root, fine for runpod

echo "== Install uv =="
if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi

# Make uv visible
export PATH="$HOME/.local/bin:$PATH"

echo "== Persist PATH for future shells =="
grep -q 'LOCAL_BIN_PATH' ~/.bashrc || cat >> ~/.bashrc <<'EOF'
# LOCAL_BIN_PATH
export PATH="$HOME/.local/bin:$PATH"
EOF

echo "== Git identity =="
git config --global user.email "jbmopper@gmail.com"
git config --global user.name "jbmopper"

echo "== Editor defaults =="
export VISUAL=nvim
export EDITOR=nvim
grep -q 'VISUAL=nvim' ~/.bashrc || cat >> ~/.bashrc <<'EOF'
export VISUAL=nvim
export EDITOR=nvim
EOF

echo "== Persistent cache directories on volume =="
mkdir -p /workspace/.cache/uv
mkdir -p /workspace/.cache/huggingface

cat > /workspace/env.sh <<'EOF'
# uv cache
export UV_CACHE_DIR=/workspace/.cache/uv
export UV_LINK_MODE=copy

# HuggingFace / Transformers cache
export HF_HOME=/workspace/.cache/huggingface
export HUGGINGFACE_HUB_CACHE=/workspace/.cache/huggingface/hub
export TRANSFORMERS_CACHE=/workspace/.cache/huggingface/transformers
export HF_DATASETS_CACHE=/workspace/.cache/huggingface/datasets

# Editor
export VISUAL=nvim
export EDITOR=nvim

# Allow HuggingFace code evaluation (HumanEval/MBPP execute generated code)
export HF_ALLOW_CODE_EVAL=1
EOF

# Load it now
source /workspace/env.sh

echo "== Auto-source env.sh for future shells =="
grep -q 'source /workspace/env.sh' ~/.bashrc || echo "source /workspace/env.sh" >> ~/.bashrc

echo "== Done. Launching tmux =="
tmux new -As work 