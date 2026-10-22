"""Read-only Phase4 feasibility measurements. No production asset writes."""
import os,sys,json,types,hashlib
sys.dont_write_bytecode=True
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../../../..'))
sys.path.insert(0,ROOT+'/blender/scripts')
import bpy,numpy as np
import postcard_lib as P
import postcard_props_lib as PL
import postcard_look_verify as V
import golf_look_textures as T
OUT=ROOT+'/work/postcard-look/v3/hole10'
E=T.read_png(ROOT+'/Unity/Assets/Resources/Course/Look/Basalt_E.png')[...,:3]/255
N=T.read_png(ROOT+'/Unity/Assets/Resources/Course/Look/Basalt_N.png')[...,:3]/255
G=E.max(2)>.2;col=G.mean(0)
metric=V.basalt_metrics(E,N,8.0)
oldload=V.look_png
try:
    V.look_png=lambda _C,n:E if n=='Basalt_E' else N if n=='Basalt_N' else None
    basalt_ok,basalt_detail=V.g_basalt_tex(None,None)
finally:V.look_png=oldload
rows=[]
for h,w in ((18,4.5),(17.6,3),(17.6,4),(17.6,5.5),(16,5.2)):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    PL._COUNTERS.clear();PL.reset_scatter(None)
    D=P.start('hole08_design',out_dir=OUT+'/no_export')
    ob=PL.build_needle(D,(0,0,0),h,w,seed=3,surf=False)['needle']
    snap=V.Snap('blend',types.SimpleNamespace(tag='08'))
    shape=V.rock_shape(snap.loc(ob))
    rows.append(dict(height=h,requested_width=w,seed=3,r3=shape['r3'],r3_min=V.ROCK_TH['stretch_r3_min'],
                     pca_ok=shape['r3']>=V.ROCK_TH['stretch_r3_min'],shape_ok=shape['ok'],shape_why=shape['why']))
res=dict(basalt_prisms=dict(ok=basalt_ok,detail=basalt_detail,metrics=metric),
         u_window_feasibility=dict(min_column_glow_fraction=float(col.min()),max_column_glow_fraction=float(col.max()),
                                   no_glow_columns=int((col==0).sum()),safe_columns=int((col<=.0002).sum()),
                                   zone_glow_limit=.0002,conclusion='No nonempty vertical u-zone of the current tile can satisfy the inherited glow-free-zone gate.'),
         needle_pca=rows)
with open(OUT+'/constraint_measurements.json','w') as f:json.dump(res,f,indent=2)
print(json.dumps(res,indent=2),flush=True)
