"""Read-only P4 whole-stage architecture census, actual world coordinates."""
import os,sys,json,hashlib
sys.dont_write_bytecode=True
import bpy,numpy as np
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../../../..'));sys.path.insert(0,ROOT+'/blender/scripts')
import postcard_look_verify as V
HERE=os.path.dirname(__file__)
bpy.ops.wm.open_mainfile(filepath=HERE+'/stage/hole_10.blend',load_ui=False)
S=V.Snap('blend',type('C',(),dict(hole=10,tag='10'))())
rows=[];all_widths=[];shape_fails=[]
for n,ob in sorted(S.meshes.items()):
 if 'lk_v3_columns' not in ob:continue
 columns=json.loads(ob['lk_v3_columns']);world=S.wld(ob)['W'];widths=[];depth=[]
 for c in columns:
  p=world[slice(*c['verts'])]
  widths.append(float(np.linalg.norm(p[:,:2,None]-p[:,:2].T[None,:,:],axis=1).max()))
  depth.append(float(p[:,2].max()-p[:,2].min()))
 shape=V.rock_shape(S.loc(ob))
 if not shape['ok']:shape_fails.append(dict(name=n,detail=shape))
 row=dict(name=n,columns=len(columns),sides=sorted(set(c['sides'] for c in columns)),faces=len(ob.data.polygons),triangles=len(S.loc(ob)['T']),world_width_min=min(widths),world_width_max=max(widths),depth_min=min(depth),depth_max=max(depth),horizontal_span=float(np.linalg.norm(np.ptp(world[:,:2],axis=0))),shape=shape,scale=list(ob.scale),support_gap_metadata=ob.get('lk_v3_support_gap_m'))
 rows.append(row);all_widths.extend(widths)
res=dict(objects=len(rows),sha256_blend=hashlib.sha256(open(HERE+'/stage/hole_10.blend','rb').read()).hexdigest(),actual_shafts=sum(r['columns'] for r in rows),world_width_min=min(all_widths),world_width_max=max(all_widths),width_gate_pass=min(all_widths)>=.6 and max(all_widths)<=1.8,faces_max=max(r['faces'] for r in rows),faces_gate_pass=max(r['faces'] for r in rows)<=490,horizontal_span_max=max(r['horizontal_span'] for r in rows),span_gate_pass=max(r['horizontal_span'] for r in rows)<=20,shape_failures=shape_fails,shape_gate_pass=not shape_fails,objects_measured=rows,extra_strict_support_containment=dict(pass_=False,evidence='prototypes/support/measurements.json',reason='Repeated world-float cut-cap vertices can extend micrometres outside full base; extra diagnostic FAIL retained. Actual bearing98.56..99.55%, exact specified per-shaft vertical gap0 in prototype.'))
def cv(x):
 if isinstance(x,np.bool_):return bool(x)
 if isinstance(x,np.integer):return int(x)
 if isinstance(x,np.floating):return float(x)
 if isinstance(x,np.ndarray):return x.tolist()
 raise TypeError(type(x).__name__)
json.dump(res,open(HERE+'/geometry_metrics.json','w'),indent=2,default=cv)
print('GEOMETRY_SUMMARY '+json.dumps({k:v for k,v in res.items() if k!='objects_measured'},default=cv),flush=True)
