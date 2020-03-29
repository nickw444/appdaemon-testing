#!/bin/bash
set -eu

REPO_DIR="$(git rev-parse --show-toplevel)"

main() {
  cd "${REPO_DIR}";
  rm -rf docs;
  mkdir -p target
  pdoc --html --force -o target/docs  --filter 'pytest,HassDriver'  appdaemon_testing/;
  mv target/docs/appdaemon_testing docs/
}

main "$@"
