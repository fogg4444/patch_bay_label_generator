#!/bin/bash

pip3 install pillow
# python3 -m pip install Pillow==9.5.0

rm ./label_outputs/*

python3 ./generate.py