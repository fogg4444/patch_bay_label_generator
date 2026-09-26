#!/bin/bash

source ./venv/bin/activate

pip3 install pillow
# python3 -m pip install Pillow==9.5.0

rm ./label_outputs/*

python3 ./generate.py

python3 ./generate_html.py

open -a Preview printable_reference/reference_sheet.pdf