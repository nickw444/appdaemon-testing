#!/bin/bash
test_dir=$(realpath "$(dirname $0)")
git_dir=$(realpath "${test_dir}/../")
pushd ${git_dir} > /dev/null
pylint $(git ls-files '*.py' | grep -v notifier.py | grep -v hass_driver.py) --rcfile ${git_dir}/.pylintrc
popd > /dev/null