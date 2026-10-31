#!/usr/bin/env bash
if [ "$1" = "--clear" ]; then
  rm instance/demo.sqlite
fi

.venv/bin/python -m flask --app api run
