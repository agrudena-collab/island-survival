#!/bin/sh
# Concatenates parts/b00..b08 into build_business_dad.py (single-file builder).
cd "$(dirname "$0")" || exit 1
cat parts/b00_header.py parts/b01_helpers.py parts/b02_defs.py parts/b03_body.py parts/b04_arms.py parts/b05_head.py parts/b06_props.py parts/b07_final.py > build_business_dad.py
if [ -f parts/b08_render.py ]; then cat parts/b08_render.py >> build_business_dad.py; fi
echo "assembled build_business_dad.py ($(wc -l < build_business_dad.py) lines)"
