#!/bin/bash

if [ -f ./registrar.db ]; then
    rm registrar.db
fi

python3 create.py
