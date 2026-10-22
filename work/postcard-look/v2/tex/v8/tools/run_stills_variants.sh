#!/bin/bash
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator; V=$R/work/postcard-look/v2/tex/v8; SC=/private/tmp/claude-501/-Users-adnanyonathan-Documents-Codex-2026-09-20-wh-outputs-iphone-golf-simulator/b67a5225-b7e5-4252-b92f-b4ee9f4f2d01/scratchpad
for k in A B; do
  cp $V/smoke_$k/Smoke_C.png $SC/UnityClone/Assets/Resources/Course/Look/Smoke_C.png
  bash $V/tools/run_clone_stills.sh smk$k $V/stills_smk$k $V/stills_cfg_h10.json > $V/clone_smk$k.out 2>&1
done
echo done > $V/stills_variants.done
