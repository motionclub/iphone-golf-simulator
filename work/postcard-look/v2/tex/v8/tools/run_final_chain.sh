#!/bin/bash
# real-project verification of the installed v8 maps, serialised by heavy.sh: GolfLookSmoke, PostcardImportCheck, the 9 stills into v8/stills_final3 (NOT ArtDir)
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator; V=$R/work/postcard-look/v2/tex/v8; cd $R
bash work/postcard-look/v2/runtime/run_smoke.sh v8s5 > $V/final_smoke.out 2>&1
bash work/postcard-look/v2/runtime/run_importcheck.sh v8i3 > $V/final_importcheck.out 2>&1
bash work/postcard-look/v2/runtime/run_stills.sh v8f3 work/postcard-look/v2/tex/v8/stills_final3 GOLF_STILLS_CFG=$R/work/postcard-look/v2/proof/stills_cfg_9.json > $V/final_stills.out 2>&1
bash work/postcard-look/v2/proof/run_probe_installed.sh v8probe2 > $V/final_probe.out 2>&1
echo done > $V/final_chain.done
