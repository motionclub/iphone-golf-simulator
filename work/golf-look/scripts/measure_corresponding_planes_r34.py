import bpy,sys,json,numpy as np
from pathlib import Path
from mathutils.kdtree import KDTree
sys.path.insert(0,str(Path(__file__).resolve().parent))
from dcommon import *
w=Path(__file__).resolve().parents[1];rig=bpy.data.objects['Rig_Male'];body=bpy.data.objects['Body_M'];pants=bpy.data.objects['Golf_Trousers'];B0=mesh_co(body);kd=KDTree(len(B0))
for i,p in enumerate(B0):kd.insert(p,i)
kd.balance();bind=np.array([q.vector[:] for q in pants.data.attributes['GolfSourceBind'].data]);ids=np.array([kd.find(p)[1] for p in bind]);pants.data.calc_loop_triangles();n=len(bind)//2;T=np.array([q.vertices[:] for q in pants.data.loop_triangles if not all(i>=n for i in q.vertices)]);T=T[np.all(T<n,axis=1)];BT=np.load(w/'data/native_body_tri_Male_r34.npy');lookup={tuple(sorted(t)):t for t in BT};common=[]
for t in T:
 k=lookup.get(tuple(sorted(ids[t])))
 if k is not None:common.append(t)
T=np.array(common);profile=json.loads(pants['GolfCorrectiveProfile']);rows=[]
for ai,a in enumerate(profile['anchors']):
 activate_clip(rig,a['action']);bpy.context.scene.frame_set(-1);bpy.context.scene.frame_set(0)
 for k,item in enumerate(profile['anchors'][1:],1):pants.data.shape_keys.key_blocks[item['shape']].value=float(ai==k)
 bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();B=evaluated_co(body,dg);P=evaluated_co(pants,dg);homes=B[ids[T]];N=np.cross(homes[:,1]-homes[:,0],homes[:,2]-homes[:,0]);N/=np.maximum(np.linalg.norm(N,axis=1)[:,None],1e-12);D=np.einsum('tvc,tc->tv',P[T]-homes,N)*1000
 worst=np.argsort(D.min(1))[:10];row=dict(action=a['action'],matchedTriangles=len(T),planeClearanceMinMm=float(D.min()),negativeFaces=int((D.min(1)<0).sum()),worst=[dict(garmentIds=T[k].tolist(),bodyIds=ids[T[k]].tolist(),bindCentre=bind[T[k]].mean(0).tolist(),gaps=D[k].tolist()) for k in worst]);rows.append(row);print(a['action'],row['planeClearanceMinMm'],row['negativeFaces'],row['worst'][:2],flush=True)
(w/'data/corresponding_plane_clearance_r34.json').write_text(json.dumps(rows,indent=2))
