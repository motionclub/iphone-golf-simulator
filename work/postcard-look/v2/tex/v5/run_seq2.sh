#!/bin/bash
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
cd "$R"
(cd Unity/Assets/Resources/Course/Look && shasum -a 256 *.png) > work/postcard-look/v2/tex/v5/sha_at_final_runs.txt
work/postcard-look/v2/runtime/run_smoke.sh v5s3 > work/postcard-look/v2/tex/v5/smoke_v5s3.out 2>&1
for n in 1 2 3; do work/postcard-look/v2/calibrate/tools/run_probe.sh v5f$n > work/postcard-look/v2/tex/v5/probe_v5f$n.out 2>&1; done
(cd Unity/Assets/Resources/Course/Look && shasum -a 256 *.png) > work/postcard-look/v2/tex/v5/sha_after_final_runs.txt
echo done > work/postcard-look/v2/tex/v5/run_seq2.done
