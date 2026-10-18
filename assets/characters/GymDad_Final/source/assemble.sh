#!/bin/sh
# Concatenates parts/g00..g08 into build_gym_dad.py (the single-file builder required by the task).
cd "$(dirname "$0")" || exit 1
cat parts/g00_header.py parts/g01_helpers.py parts/g02_defs.py parts/g03_body.py parts/g04_arms.py parts/g05_head.py parts/g06_props.py parts/g07_final.py > build_gym_dad.py
if [ -f parts/g08_render.py ]; then cat parts/g08_render.py >> build_gym_dad.py; fi
echo "assembled build_gym_dad.py ($(wc -l < build_gym_dad.py) lines)"
