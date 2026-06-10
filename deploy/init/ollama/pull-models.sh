#!/bin/sh
# T-02-04 — idempotent Ollama model bootstrap.
#
# Runs in the ollama-init one-shot service once Ollama reports healthy.
# Pulls the pinned model (OLLAMA_MODEL, default qwen3:14b per D-02/D-36). Safe to rerun.
set -eu

HOST="${OLLAMA_HOST:-ollama:11434}"
MODEL="${OLLAMA_MODEL:-qwen3:14b}"

export OLLAMA_HOST="$HOST"

echo "Pulling Ollama model: $MODEL (host=$HOST)"
ollama pull "$MODEL"
echo "Ollama model ready: $MODEL"
