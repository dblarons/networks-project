#!/bin/bash

if [ -f ./registrar.db ]; then
    rm registrar.db
fi

python3 create.py

# Compile flatbuffers
flatc --python -o registrar/ -I flatbuffers/ flatbuffers/registrar.fbs
