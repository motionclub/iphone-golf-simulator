#!/bin/zsh
# try_eval.sh <d_release> <d_ext>
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/frame-rate-60/serve
python3 scripts/try_left.py $1 $2; zsh scripts/rebuild.sh male >/dev/null
echo "== release d=$1 ext d=$2"
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup export/HeroBase_Male_MatchAnims.blend --python scripts/measure.py -- male data/measure_try.json >/dev/null 2>&1
python3 - <<'PY'
import json, numpy as np
b=json.load(open('data/measure_try.json'))
print('flexL', ' '.join('%d:%.0f'%(y['f'],y['Lelbow_flex']) for y in b if 14<=y['f']<=44 and y['f']%2==0))
print('wrist-headtop', ' '.join('%d:%+.2f'%(y['f'],y['Lwrist_z']-y['headtop_z']) for y in b if 16<=y['f']<=34 and y['f']%3==0))
names=[x['name'] for x in json.load(open('../match-anim-set/data/rig_male.json'))['bones']]
q=np.load('data/gen_serve_male.npz',allow_pickle=True)['quats']
st=np.degrees(2*np.arccos(np.clip(np.abs(np.sum(q[1:]*q[:-1],axis=2)),0,1)))
arm=[i for i,n in enumerate(names) if any(k in n for k in ('UpperArm','LowerArm','Hand'))]
print('worst', sorted([(round(float(st[k,arm].max()),1), k+1, names[arm[int(st[k,arm].argmax())]]) for k in range(46)],reverse=True)[:5])
PY
