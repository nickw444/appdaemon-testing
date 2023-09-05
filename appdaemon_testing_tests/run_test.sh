#!/bin/bash
test_dir=$(realpath "$(dirname $0)")
git_dir=$(realpath "${test_dir}/../")
echo ">>> ${git_dir}"
pushd ${git_dir} > /dev/null
PYTHONPATH=${git_dir} pytest-watch -- --sw --random-order -vs $@
popd > /dev/null