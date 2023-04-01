#!/bin/bash

set -eux

export MODELS_DIR="${MODELS_DIR:-/models}"

if [ ! -d "$MODELS_DIR" ]; then
  mkdir "$MODELS_DIR"
fi

pushd "$MODELS_DIR"

if [ ! -f "${MODEL_FILE}.pth" ]; then
  wget -q https://huggingface.co/BlinkDL/rwkv-4-pile-1b5/resolve/main/RWKV-4-Pile-1B5-20220929-ctx4096.pth
fi

popd

flask run -h 0.0.0.0 -p 8080
