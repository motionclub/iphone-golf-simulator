#!/bin/bash
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
cd "$R"
work/postcard-look/v2/runtime/run_smoke.sh v5s1 > work/postcard-look/v2/tex/v5/smoke_v5s1.out 2>&1
work/postcard-look/v2/calibrate/tools/run_probe.sh v5g5 > work/postcard-look/v2/tex/v5/probe_v5g5.out 2>&1
echo done > work/postcard-look/v2/tex/v5/run_seq1.done
