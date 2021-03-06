#!/usr/bin/env bash

build_pyoxidizer() {
  cd "$(git rev-parse --show-toplevel)" || exit 9

  case "$1" in
    --static|static)
      pyoxidizer build --target-triple x86_64-unknown-linux-musl
      ;;
    *)
      pyoxidizer build
      ;;
  esac
}

build_pyinstaller() {
  local python_v="${PYTHON_VERSION:-3.9}"

  cd "$(git rev-parse --show-toplevel)" || exit 9

  docker run -it --rm \
    -v "${PWD}:/app" \
    -e OWNER=1000 \
    -e STATICX=1 \
    -e STATICX_ARGS="--strip" \
    "pschmitt/pyinstaller:${python_v}" \
    tafker/main.py
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]
then
  cd "$(cd "$(dirname "$0")" >/dev/null 2>&1; pwd -P)" || exit 9
  ./gen-requirements.sh

  case "$1" in
    pyinstaller)
      build_pyinstaller
      ;;
    *)
      build_pyoxidizer "$@"
      ;;
  esac
fi
