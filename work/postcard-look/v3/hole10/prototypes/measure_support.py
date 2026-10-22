"""Exact per-shaft support and unchanged local rock gates for a tall sector."""
import os,sys,json,types
sys.dont_write_bytecode=True
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../../../../..'))
sys.path.insert(0,ROOT+'/blender/scripts');sys.path.insert(0,os.path.dirname(__file__))
import bpy,numpy as np
import postcard_lib as P
import postcard_props_lib as PL
import postcard_look_verify as V
from compact_columns import compact_ring_tile
OUT=os.path.dirname(__file__)+'/support';os.makedirs(OUT,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True);PL._COUNTERS.clear();PL.reset_scatter(None)
D=P.start('hole10_design',out_dir=OUT)
path=[(300+300*np.cos(t),-100+300*np.sin(t)) for t in np.linspace(.4,.4+9.375/300,3)]
rows=[];bands=[];bottoms=None
for i,top in enumerate((20.2,44.2,70.2)):
 r=compact_ring_tile(D,path,[top-.35,top+.35,top-.2],seed=38,bottoms=bottoms,name='ROCK_WALL_FAR_BAND_'+str(i))
 ob=r['object'];S=V.Snap('blend',types.SimpleNamespace(tag='10'));shape=V.rock_shape(S.loc(ob));v,t=S.oriented(ob);cols,side=V.count_columns(v,t)
 gates=dict(ROCK_SHAPE=shape['ok'],PCA=shape['r3']>=V.ROCK_TH['stretch_r3_min'],CAP_COLUMNS=cols>=V.TH['columns'] and side>=.45,
            FACES=len(ob.data.polygons)<=490,WORLD_WIDTH=all(.6<=x['width']<=1.8 for x in r['columns']),WORLD_SPAN=r['horizontal_span']<=20)
 row=dict(band=i,gates=gates,pass_=all(gates.values()),shape=shape,cap_columns=cols,side_fraction=side,triangles=len(t),polygons=len(ob.data.polygons),top_min=min(x['top'] for x in r['columns']),top_max=max(x['top'] for x in r['columns']),horizontal_span=r['horizontal_span'])
 rows.append(row);bands.append(r);bottoms=[s['top'] for s in r['columns']]
 for g,ok in gates.items():print(f"GATE: BAND{i}:{g} {'PASS' if ok else 'FAIL'}",flush=True)
 print(json.dumps(row),flush=True)
# Geometry-level exact contact. A top fracture is a convex truncated cap;
# the next full cap shares its footprint and bears on that real planar cap.
support=[]
for layer in range(1,len(bands)):
 below,above=bands[layer-1],bands[layer]
 V0=np.array([tuple(v.co) for v in below['object'].data.vertices]);V1=np.array([tuple(v.co) for v in above['object'].data.vertices])
 for j,(a,b) in enumerate(zip(below['columns'],above['columns'])):
  low=V0[slice(*a['verts'])];high=V1[slice(*b['verts'])]
  cap=low[np.abs(low[:,2]-low[:,2].max())<1e-5,:2]
  foot=high[np.abs(high[:,2]-high[:,2].min())<1e-5,:2]
  ix=V.convex_hull_2d([tuple(x) for x in cap]);poly=cap[ix]
  fx=V.convex_hull_2d([tuple(x) for x in foot]);fpoly=foot[fx]
  area=lambda pp:float(abs(np.dot(pp[:,0],np.roll(pp[:,1],-1))-np.dot(pp[:,1],np.roll(pp[:,0],-1)))*.5)
  # The repeated base polygon contains the prior cut cap. Direct hull vertex
  # containment plus exact repeated width/grid validates this bearing share.
  def inside(pt):
   ed=np.roll(fpoly,-1,axis=0)-fpoly;dd=pt-fpoly
   cross=ed[:,0]*dd[:,1]-ed[:,1]*dd[:,0]
   return bool((cross>=-1e-6).all() or (cross<=1e-6).all())
  support.append(dict(layer=layer,column=j,grid=a['grid_index'],gap=float(high[:,2].min()-low[:,2].max()),bearing_share=area(poly)/area(fpoly),all_cap_vertices_supported=all(inside(pt) for pt in poly),same_width=bool(abs(a['width']-b['width'])<=1e-8)))
support_ok=all(abs(s['gap'])==0 and s['bearing_share']>=.8 and s['all_cap_vertices_supported'] and s['same_width'] for s in support)
print('GATE: EXACT_SUPPORT','PASS' if support_ok else 'FAIL',json.dumps(support),flush=True)
result=dict(bands=rows,support=support,support_pass=support_ok,total_triangles=sum(x['triangles'] for x in rows),pass_=all(x['pass_'] for x in rows) and support_ok)
with open(OUT+'/measurements.json','w') as f:json.dump(result,f,indent=2)
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/fixture.blend',relative_remap=False)
sys.exit(0 if result['pass_'] else 1)
