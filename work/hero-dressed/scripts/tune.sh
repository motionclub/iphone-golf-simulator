#!/bin/zsh
# usage: DR_*=... scripts/tune.sh <male|female> <label>   builds into a scratch blend with the knobs in the environment and runs the 8 gate poses; appends to logs/tuning_log.md
W=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/hero-dressed
B=/Applications/Blender.app/Contents/MacOS/Blender
S=/private/tmp/claude-501/-Users-adnanyonathan-Documents-Codex-2026-09-20-wh-outputs-iphone-golf-simulator/e6a7ae79-f7d7-42dd-b152-50de544740e5/scratchpad
tag=$1; label=$2
G=$(python3 -c "print('$tag'.capitalize())")
export DR_OUT_BLEND=$S/tune_${tag}_${label}.blend
cd $W
$B -b --factory-startup ../match-anim-set/export/HeroBase_${G}_MatchAnims.blend --python scripts/build_dressed.py -- $tag > $S/tune_build_${tag}_${label}.log 2>&1
$B -b --factory-startup $DR_OUT_BLEND --python scripts/measure_follow.py -- $tag gate $S/tune_${tag}_${label}.json > $S/tune_measure_${tag}_${label}.log 2>&1
python3 - <<PY
import json,os
d=json.load(open('$S/tune_${tag}_${label}.json'))
knobs={k:v for k,v in os.environ.items() if k.startswith('DR_') and k!='DR_OUT_BLEND'}
line='| $tag | $label | '+str(knobs)+' | '+' ; '.join('%s poke %.1f/%.1f float %.1f/%.1f%s'%(p,s['poke_max_mm'],s['poke_p99_worst_mm'],s['float_max_mm'],s['float_p99_worst_mm'],'' if s['pass_'] else ' F') for p,s in d['summary'].items())+' |'
print(line)
open('$W/logs/tuning_log.md','a').write(line+'\n')
PY
