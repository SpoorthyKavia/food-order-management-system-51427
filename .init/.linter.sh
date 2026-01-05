#!/bin/bash
cd /home/kavia/workspace/code-generation/food-order-management-system-51427/food_ordering_api
source venv/bin/activate
flake8 .
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi

