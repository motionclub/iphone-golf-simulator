#!/bin/zsh
# try_p1.sh <az> <el> <d> : set the release hand (p1) of the left arm, rebuild male, run the offline toss model
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/serve-toss-arm
python3 - $1 $2 $3 <<'PY'
import re, sys
p='scripts/serve_new.py'; s=open(p).read()
s=re.sub(r"p1 = np.array\(ls\([-\d.]+, [-\d.]+, [\d.]+\)\)", "p1 = np.array(ls(%s, %s, %s))"%tuple(sys.argv[1:4]), s)
open(p,'w').write(s)
PY
zsh scripts/rebuild.sh male | tail -1
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup export/HeroBase_Male_MatchAnims.blend --python scripts/sim_toss.py -- male 2>&1 | grep SIM
