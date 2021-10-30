#!/usr/bin/env bash

build() {
  # pyoxidizer build --target-triple x86_64-unknown-linux-musl
  pyoxidizer build
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]
then
  build
fi
