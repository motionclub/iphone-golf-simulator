"""Actual unchanged inherited BASALT_PRISMS and candidate window values."""
import os,sys,json,hashlib
sys.dont_write_bytecode=True
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../../../../..'))
sys.path.insert(0,ROOT+'/blender/scripts')
import numpy as np
import postcard_look_verify as V
import golf_look_textures as T
OUT=os.path.join(os.path.dirname(__file__),(sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else os.environ.get('P7_CANDIDATE','bounded_v1')))
E=T.read_png(OUT+'/Basalt_E.png')[...,:3]/255
N=T.read_png(OUT+'/Basalt_N.png')[...,:3]/255
C=T.read_png(OUT+'/Basalt_C.png')[...,:3]/255
metrics=V.basalt_metrics(E,N,8)
old=V.look_png
try:
 V.look_png=lambda _C,n:E if n=='Basalt_E' else N if n=='Basalt_N' else None
 ok,detail=V.g_basalt_tex(None,None)
finally:V.look_png=old
G=E.max(2)>.2;safe=G.mean(0)<=.0002
profile=C.mean(2).mean(0).reshape(128,-1).mean(1)
layout=json.load(open(OUT+'/layout.json'));centers=layout['centers'];zones=layout['zones']
share=lambda a,b:float(G[:,np.arange(round(a*1024),round(b*1024))%1024].mean())
zmax=max(share(a,b) for a,b in zones)
emin=min(min(share(g-.016,g-.016+.05),share(g+.016-.05,g+.016)) for g in centers)
rounded=np.round(profile,3)
proposed=dict(GLOW_U=centers,GLOW_EDGE=.016,ZONES=zones,PROFILE128=rounded.tolist(),zone_glow_max=zmax,edge_window_min=emin,profile_dev=float(abs(profile-rounded).max()),
              numeric_gate_pass=zmax<=.0002 and emin>=.04 and float(abs(profile-rounded).max())<=.01)
result=dict(basalt_prisms=dict(ok=ok,detail=detail,metrics=metrics),safe_u_columns=int(safe.sum()),proposed_measured_constants=proposed,
            scope='Scratch source PNG measurement only; original current-builder window gate logged separately; actual native BASALT_JOINTS UNVERIFIED',
            sha256={k:hashlib.sha256(open(OUT+'/Basalt_'+k+'.png','rb').read()).hexdigest() for k in 'CNE'})
with open(OUT+'/inherited_prisms.json','w') as f:json.dump(result,f,indent=2)
print('GATE: BASALT_PRISMS','PASS' if ok else 'FAIL',detail,flush=True)
print(json.dumps(result,indent=2),flush=True)
sys.exit(0 if ok else 1)
