#!/bin/bash

set -eu

export MODELS_DIR="${MODELS_DIR:-/models}"

if [ ! -d "$MODELS_DIR" ]; then
  mkdir "$MODELS_DIR"
fi

pushd "$MODELS_DIR"

if [ ! -f "${MODEL_FILE}.pth" ]; then
  wget -q https://huggingface.co/BlinkDL/rwkv-4-raven/resolve/main/RWKV-4-Raven-1B5-v8-Eng-20230408-ctx4096.pth
fi

popd

flask run -h 0.0.0.0 -p 8080
