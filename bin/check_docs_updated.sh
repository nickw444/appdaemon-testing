#!/bin/bash
set -eu

REPO_DIR="$(git rev-parse --show-toplevel)"

main() {
  cd "${REPO_DIR}";
  ./bin/gen_docs.sh;

  if [[ -n $(git status -s docs) ]]; then
    echo "Error: ./docs not up to date. Please re-generate docs by running ./bin/gen_docs.sh";
    exit 1;
  fi
}

main "$@"
