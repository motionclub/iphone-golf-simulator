"""Execute proposed generator code in memory; all output remains scratch."""
import os,sys,json,hashlib
sys.dont_write_bytecode=True
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../../../../..'))
sys.path.insert(0,ROOT+'/blender/scripts')
import numpy as np
from PIL import Image
import golf_look_textures as original
HERE=os.path.dirname(__file__);OUT=HERE+'/bounded_v6_source';os.makedirs(OUT,exist_ok=True)
ns={'__name__':'scratch_texture_proposal','__file__':ROOT+'/blender/scripts/golf_look_textures.py'}
code=open(HERE+'/golf_look_textures_candidate.py').read();exec(compile(code,ns['__file__'],'exec'),ns)
maps=ns['mat_basalt'](1024,1101)
for k,a in maps.items():
 if k=='N':a=a*.5+.5
 ns['write_png'](OUT+'/Basalt_'+k+'.png',np.round(np.clip(a,0,1)*255).astype(np.uint8))
rows=[]
def gate(name,ok,detail):
 rows.append(dict(name=name,ok=bool(ok),detail=detail));print('GATE:',name,'PASS' if ok else 'FAIL',detail,flush=True)
decoded={'Basalt_'+k+'.png':np.asarray(Image.open(OUT+'/Basalt_'+k+'.png')) for k in 'CNE'}
original.basalt_gates(decoded,gate)
# The opt-out path executes the original prism function with no new transforms.
ns['BASALT_P']['bounded']=0
legacy=ns['mat_basalt'](256,1101);baseline=original.mat_basalt(256,1101)
gate('BOUNDED_OPT_OUT_ARRAY_BYTE_COMPATIBILITY_256',all(np.array_equal(legacy[k],baseline[k]) for k in 'CNE'),dict(max_abs={k:float(np.max(np.abs(legacy[k]-baseline[k]))) for k in 'CNE'},scope='same original generator at256; no claim that new bounded default is byte-compatible'))
result=dict(scope='Actual proposed generator execution in-memory; production sources and installed PNGs untouched.',gates=rows,ok=all(r['ok'] for r in rows),sha256={k:hashlib.sha256(open(OUT+'/Basalt_'+k+'.png','rb').read()).hexdigest() for k in 'CNE'})
json.dump(result,open(OUT+'/source_gates.json','w'),indent=2)
# The geometry/emission layout is identical to the decoded-map candidate.
json.dump(json.load(open(HERE+'/bounded_v6/layout.json')),open(OUT+'/layout.json','w'),indent=2)
sys.exit(0 if result['ok'] else 1)
