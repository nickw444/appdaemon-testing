#!/bin/bash
REPO_DIR="$(git rev-parse --show-toplevel)"

main() {
  cd "${REPO_DIR}";
  rm -rf docs;
  pdoc --html --force -o docs  --filter 'pytest,HassDriver'  appdaemon_testing/;
}

main "$@"
