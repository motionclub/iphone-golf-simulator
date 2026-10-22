#!/bin/zsh
# eval_male.sh <tag> : rebuild + measure + print tip steps, the flip list and the key rows
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/frame-rate-60/serve
tag=${1:-male}; H=$( [ $tag = male ] && echo Male || echo Female )
zsh scripts/rebuild.sh $tag | tail -1
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup export/HeroBase_${H}_MatchAnims.blend --python scripts/measure.py -- $tag data/measure_cur_$tag.json >/dev/null 2>&1
python3 - $tag <<'PY'
import json, sys, numpy as np
tag=sys.argv[1]
b=json.load(open(f'data/measure_cur_{tag}.json')); prev=None; out=[]
for y in b:
    t=np.array(y['rk_tip'])
    if prev is not None and y['f']<=48: out.append((round(float(np.linalg.norm(t-prev))*1000),y['f'],round(y['rk_elev'])))
    prev=t
print('tip steps mm (>250):',[o for o in out if o[0]>250 and o[1]<42])
names=[x['name'] for x in json.load(open('../match-anim-set/data/rig_%s.json'%tag))['bones']]
q=np.load(f'data/gen_serve_{tag}.npz',allow_pickle=True)['quats']
st=lambda i:np.degrees(2*np.arccos(np.clip(np.abs(np.sum(q[1:,i]*q[:-1,i],axis=1)),0,1)))
for bn in ('RightUpperArm','RightLowerArm','RightHand','LeftUpperArm','LeftLowerArm','LeftHand'):
    i=names.index(bn); print(' ',bn,'steps>25 (f<46):',[(k+1,round(float(v))) for k,v in enumerate(st(i)) if v>25 and k+1<46])
PY
