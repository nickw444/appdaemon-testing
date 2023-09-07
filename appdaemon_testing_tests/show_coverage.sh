#!/bin/bash
test_dir=$(realpath "$(dirname $0)")
git_dir=$(realpath "${test_dir}/../")
appdaemon_testing_dir=$(realpath "${git_dir}/appdaemon_testing/")
pushd ${git_dir} > /dev/null
coverage run --source ${appdaemon_testing_dir} -m pytest 
coverage report -m
coverage html 
echo ${git_dir}/htmlcov/index.html
popd > /dev/null