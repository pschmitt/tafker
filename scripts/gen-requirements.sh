#!/usr/bin/env bash

gen_requirements() {
  cd "$(git rev-parse --show-toplevel)" || exit 9
  poetry export -f requirements.txt --without-hashes >! requirements.txt
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]
then
  gen_requirements
fi
