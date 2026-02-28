#!/usr/bin/env bash
# Post-create setup for GitHub Codespaces
# Called by devcontainer.json postCreateCommand
set -e

echo "🔧 Initializing submodules…"
git submodule update --init --recursive

echo "🐍 Installing DeerFlow backend…"
cd deer-flow
pip install -e '.[dev]'
pip install mcp-server-fetch==2025.4.7

echo "⚙️  Generating config files…"
make config

echo "🐳 Enabling aio sandbox in config.yaml…"
sed -i 's|^  use: src\.sandbox\.local:LocalSandboxProvider|  use: src.community.aio_sandbox:AioSandboxProvider|' config.yaml

echo "📦 Installing frontend dependencies…"
cd frontend
npm install -g pnpm
pnpm install
cd ..

echo "🔑 Authenticating to GHCR…"
echo "$GITHUB_TOKEN" | docker login ghcr.io -u "$GITHUB_USER" --password-stdin 2>/dev/null || true

echo "📥 Pre-pulling aio sandbox image…"
docker pull enterprise-public-cn-beijing.cr.volces.com/vefaas-public/all-in-one-sandbox:latest 2>/dev/null || true

echo "✅ Post-create setup complete"
