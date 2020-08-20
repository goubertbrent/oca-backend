#!/usr/bin/env bash
rm -rf tmp
mkdir tmp
cd tmp
mkdir fa_iconen
mkdir pins
mkdir output
cd output
mkdir icons_v1_pins
mkdir icons_v1_trans


cd ..
cd ..

python generate_pins_1_fa_icons.py --size=32 --color=#FFFFFF --file=tmp/fa_iconen/ --css=font-awesome.css ALL
python generate_pins_2_get_config.py
python generate_pins_3_pins.py