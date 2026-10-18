#!/bin/sh
# Concatenates parts/m00..m08 into build_millionaire_dad.py (single-file builder).
cd "$(dirname "$0")" || exit 1
cat parts/m00_header.py parts/m01_helpers.py parts/m02_defs.py parts/m03_body.py parts/m04_arms.py parts/m05_head.py parts/m06_case.py parts/m07_final.py > build_millionaire_dad.py
if [ -f parts/m08_render.py ]; then cat parts/m08_render.py >> build_millionaire_dad.py; fi
echo "assembled build_millionaire_dad.py ($(wc -l < build_millionaire_dad.py) lines)"
