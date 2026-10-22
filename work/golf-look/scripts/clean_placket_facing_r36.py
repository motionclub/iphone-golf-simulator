"""Retain the placket footprint with a continuous facing and turned edges.

The old solid strip folded its two coincident layers onto the same shirt surface.
Only that connected component is replaced; buttons and all other cloth remain.
"""
import bpy,bmesh,sys,json,shutil,numpy as np
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from dcommon import mesh_co,evaluated_co,activate_clip
from follow_lib import bvh_from
w=Path(__file__).resolve().parents[1];sex=sys.argv[-1];path=Path(bpy.data.filepath)
bk=w/'rollback/placket_facing_r36';bk.mkdir(exist_ok=True)
for p in [path,w/f'export/Golf_{sex}_SwingProof.blend']:shutil.copy2(p,bk/p.name)
o=bpy.data.objects['Golf_Polo'];rig=bpy.data.objects['Rig_'+sex];co=mesh_co(o);adj=[set() for _ in co]
for e in o.data.edges:a,b=e.vertices;adj[a].add(b);adj[b].add(a)
seen=set();comps=[]
for i in range(len(co)):
 if i in seen:continue
 todo=[i];seen.add(i);ids=[]
 while todo:
  a=todo.pop();ids.append(a)
  for b in adj[a]:
   if b not in seen:seen.add(b);todo.append(b)
 comps.append(ids)
strip=[ids for ids in comps if 100<len(ids)<6000 and abs(co[ids].mean(0)[0])<.025 and np.ptp(co[ids,0])<.05]
assert len(strip)==1;strip=strip[0];main=set(max(comps,key=len));buttons=[ids for ids in comps if len(ids)==50 and abs(co[ids].mean(0)[0])<.025];assert len(buttons)==3
profile=json.loads(o['GolfCorrectiveProfile']);me=o.data;outer=me.attributes['GolfOuterFace'];me.calc_loop_triangles()
tri=np.array([q.vertices[:] for q in me.loop_triangles if all(i in main for i in q.vertices) and outer.data[q.polygon_index].value==1])
x0,x1=np.min(co[strip,0]),np.max(co[strip,0]);z0,z1=np.min(co[strip,2]),np.max(co[strip,2]);y=np.median(co[strip,1])
nx,nz=6,32;seeds=[]
for z in np.linspace(z0,z1,nz+1):
 for x in np.linspace(x0,x1,nx+1):seeds.append([x,y,z])
seeds=np.array(seeds);boundary=[j*(nx+1)+i for j in range(nz+1) for i in range(nx+1) if i in [0,nx] or j in [0,nz]]
rest=np.array(rig.data.bones['Chest'].matrix_local.inverted());posed=[];buttonTargets=[]
for ai,a in enumerate(profile['anchors']):
 activate_clip(rig,a['action']);bpy.context.scene.frame_set(-1);bpy.context.scene.frame_set(0)
 for k,item in enumerate(profile['anchors'][1:],1):me.shape_keys.key_blocks[item['shape']].value=float(ai==k)
 bpy.context.view_layer.update();Q=evaluated_co(o,bpy.context.evaluated_depsgraph_get());tree=bvh_from(Q,tri)
 M=np.array(rig.matrix_world@rig.pose.bones['Chest'].matrix)@rest;inv=np.linalg.inv(M);N=M[:3,:3]@np.array([0,-1,0.]);N/=np.linalg.norm(N);front=[]
 for s in seeds:
  p=(M@np.r_[s,1])[:3];hit,n,k,d=tree.ray_cast(Vector(p+N*.15),Vector(-N),.4);assert hit is not None
  front.append(np.array(hit)+N*.0035)
 front=np.array(front);allPoints=np.concatenate([front,front[boundary]-N*.0018])
 posed.append((np.c_[allPoints,np.ones(len(allPoints))]@inv.T)[:,:3])
 bt={}
 for ids in buttons:
  p=Q[ids].mean(0);hit,n,k,d=tree.ray_cast(Vector(p+N*.15),Vector(-N),.4);assert hit is not None
  new=Q[ids]+np.array(hit)+N*.0065-p
  for i,q in zip(ids,new):bt[i]=(inv@np.r_[q,1])[:3]
 buttonTargets.append(bt)
for ai,a in enumerate(profile['anchors']):
 key=me.shape_keys.key_blocks['Basis' if ai==0 else a['shape']]
 for i,p in buttonTargets[ai].items():key.data[i].co=p
for key in me.shape_keys.key_blocks:key.value=0
bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();bmesh.ops.delete(bm,geom=[bm.verts[i] for i in strip],context='VERTS')
keys=[bm.verts.layers.shape[k.name] for k in me.shape_keys.key_blocks];deform=bm.verts.layers.deform.verify();verts=[]
for j,p in enumerate(posed[0]):
 v=bm.verts.new(p);v[deform][o.vertex_groups['Chest'].index]=1
 for ai,layer in enumerate(keys):v[layer]=posed[ai][j]
 verts.append(v)
mat=next((i for i,m in enumerate(me.materials) if m and 'Shirt' in m.name),0)
def face(indices):
 f=bm.faces.new([verts[i] for i in indices]);f.material_index=mat;f.smooth=True
for j in range(nz):
 for i in range(nx):
  a=j*(nx+1)+i;b=a+1;c=b+nx+1;d=a+nx+1
  face([a,b,c]);face([a,c,d])
edgeMap={a:len(seeds)+i for i,a in enumerate(boundary)}
rim=list(range(nx+1))+[j*(nx+1)+nx for j in range(1,nz+1)]+[nz*(nx+1)+i for i in range(nx-1,-1,-1)]+[j*(nx+1) for j in range(nz-1,0,-1)]
for a,b in zip(rim,rim[1:]+rim[:1]):face([b,a,edgeMap[a],edgeMap[b]])
bm.to_mesh(me);bm.free();me.update()
for k in me.shape_keys.key_blocks:k.value=0
activate_clip(rig,'ReadyIdle');bpy.context.scene.frame_set(-1);bpy.context.scene.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(path));bpy.ops.wm.save_as_mainfile(filepath=str(w/f'export/Golf_{sex}_SwingProof.blend'))
row=dict(sex=sex,replacedComponentVertices=len(strip),facingVertices=len(seeds),turnedEdgeMm=1.8,anchors=8,footprint=[float(x0),float(x1),float(z0),float(z1)],status='candidate; render/export/identity checks follow')
(w/f'data/placket_facing_{sex}_r36.json').write_text(json.dumps(row,indent=2));print(row,flush=True)
