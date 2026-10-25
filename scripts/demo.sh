#!/usr/bin/env bash
# Replays the README demo: a passing baseline run, then the gate rejecting a noisy model.
# Used to record docs/demo.cast (asciinema rec -c "bash scripts/demo.sh" docs/demo.cast).
set -u

type_cmd() {
  printf '\033[1;32m$\033[0m '
  local text="$1"
  for ((i = 0; i < ${#text}; i++)); do
    printf '%s' "${text:i:1}"
    sleep 0.02
  done
  printf '\n'
  sleep 0.4
}

run() {
  type_cmd "$1"
  eval "$1"
  sleep 1.5
}

run "ls examples/stories examples/openapi"
run "testgen run --gate -o out/baseline"
run 'testgen run -c configs/noisy-model.yaml -o out/noisy-model --gate; echo "exit code: $?"'
sleep 1
