#!/bin/bash
cd ..
Xvfb -ac :99 -screen 0 640x480x8 & export DISPLAY=:99
cd app/

coverage run -m unittest tests/test_*.py
status=$?
if [[ $status != 0 ]]; then
  echo "ERROR ---> There are test failures inside check: " $status
  exit $status
fi

coverage report;
coverage report -i > tests/coverage.txt