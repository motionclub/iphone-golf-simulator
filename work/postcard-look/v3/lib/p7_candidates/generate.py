import os,sys,json
sys.dont_write_bytecode=True
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../../../../..'))
sys.path.insert(0,ROOT+'/blender/scripts');sys.path.insert(0,os.path.dirname(__file__))
import numpy as np
from PIL import Image
import golf_look_textures as T
from bounded_network import bounded_network
OUT=os.path.join(os.path.dirname(__file__),'bounded_v6');os.makedirs(OUT,exist_ok=True)
# Read-only decoded existing maps supply unchanged calibrated prism structure.
base={k:(np.asarray(Image.open(ROOT+'/Unity/Assets/Resources/Course/Look/Basalt_'+k+'.png')).astype(np.float32)/255) for k in 'CNE'}
base['N']=base['N']*2-1
u,v=T.grid(1024,1024)
imgs,layout=bounded_network(u,v,base,variant=6)
for k,a in imgs.items():
 if k=='N':a=a*.5+.5
 T.write_png(OUT+'/Basalt_'+k+'.png',np.round(np.clip(a,0,1)*255).astype(np.uint8))
with open(OUT+'/layout.json','w') as f:json.dump(layout,f,indent=2)
rows=[]
def gate(name,ok,detail):
 rows.append(dict(name=name,ok=bool(ok),detail=detail));print('GATE:',name,'PASS' if ok else 'FAIL',detail,flush=True)
decoded={'Basalt_'+k+'.png':np.asarray(Image.open(OUT+'/Basalt_'+k+'.png')) for k in 'CNE'}
T.basalt_gates(decoded,gate)
with open(OUT+'/texture_gates.json','w') as f:json.dump(rows,f,indent=2)
# Current-production constants remain untouched. A later authorized integration
# must remeasure charts/profile and run this same original gate on disk.
print('RESULT:',all(r['ok'] for r in rows),flush=True)
sys.exit(0 if all(r['ok'] for r in rows) else 1)
