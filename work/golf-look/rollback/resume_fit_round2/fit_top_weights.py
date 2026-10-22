"""Garment-only nearest-surface weight transfer on the frozen body.

Run on a completed Golf_<Sex>_Draft.blend. Body triangles supply barycentric
weights; hand/finger/foot triangles are excluded. Preserves closed shirt walls
and moves only locally invalid shirt points outside the body. G7 must be rerun.
"""
import bpy,json,sys,hashlib,shutil
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parent))
from follow_lib import bary_of
W=Path(__file__).resolve().parents[1];sex=sys.argv[-1]
rig=bpy.data.objects['Rig_'+sex];body=bpy.data.objects['Body_F' if sex=='Female' else 'Body_M']
def identity():
    return hashlib.sha256(repr(([(tuple(v.co),[(g.group,g.weight) for g in v.groups]) for v in body.data.vertices],[tuple(p.vertices) for p in body.data.polygons],[(b.name,tuple(map(tuple,b.matrix_local))) for b in rig.data.bones])).encode()).hexdigest()
before=identity();rig.animation_data.action=None;rig.data.pose_position='REST'
for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
bpy.context.view_layer.update()
names=[b.name for b in rig.data.bones]
allowed={n for n in names if not any(k in n for k in ['Hand','Thumb','Index','Middle','Ring','Little','Foot','Toes','LowerLeg'])}
weights=[{body.vertex_groups[g.group].name:g.weight for g in v.groups} for v in body.data.vertices]
body.data.calc_loop_triangles()
tris=[tuple(t.vertices) for t in body.data.loop_triangles if all(sum(w for n,w in weights[i].items() if n in allowed)>.5 for i in t.vertices)]
co=np.array([tuple(v.co) for v in body.data.vertices]);bv=BVHTree.FromPolygons(co.tolist(),tris,all_triangles=True)
rows=[]
objects=[o for o in bpy.data.objects if o.type=='MESH' and (o.name=='Golf_Polo' or o.name.startswith(('Golf_Button_','Golf_Placket_')))]
for o in objects:
    samples=[];moved=0;maxmove=0
    # Normals are recorded before moving points so paired walls stay distinct.
    normals=[v.normal.copy() for v in o.data.vertices]
    for v in o.data.vertices:
        loc,n,idx,dist=bv.find_nearest(v.co)
        t=tris[idx];bary=bary_of(np.array(loc),co[t[0]],co[t[1]],co[t[2]])
        w={}
        for k,i in enumerate(t):
            for name,value in weights[i].items():
                if name in allowed:w[name]=w.get(name,0)+float(bary[k])*value
        w=dict(sorted(w.items(),key=lambda x:x[1],reverse=True)[:4]);total=sum(w.values())
        samples.append({name:value/total for name,value in w.items() if value>1e-8})
        if o.name=='Golf_Polo':
            signed=(v.co-loc).dot(n)
            wall=normals[v.index].dot(n)
            # Even modest ease replaces the previous 16 mm outward correction,
            # which inflated the bust, sleeves and collar into a lumpy envelope.
            target=.006 if wall>.15 else .0045
            amount=max(0,target-signed)
            if amount:
                v.co+=n*amount;moved+=1;maxmove=max(maxmove,amount)
    for group in list(o.vertex_groups):o.vertex_groups.remove(group)
    groups={n:o.vertex_groups.new(name=n) for n in names}
    for i,w in enumerate(samples):
        for n,value in w.items():groups[n].add([i],value,'REPLACE')
    o.data.update()
    rows.append(dict(object=o.name,vertices=len(samples),moved_vertices=moved,max_clearance_move_mm=maxmove*1000,max_influences=max(len(x) for x in samples)))
assert before==identity(),'Body or rest rig changed'
rig.data.pose_position='POSE';rig.animation_data.action=bpy.data.actions['ReadyIdle']
if rig.animation_data.action.slots:rig.animation_data.action_slot=rig.animation_data.action.slots[0]
bpy.context.scene.frame_set(0)
out=Path(bpy.data.filepath)
old_sha=hashlib.sha256(out.read_bytes()).hexdigest()
backup=W/'rollback/top_weight_inputs'/f'{out.stem}_{old_sha[:12]}.blend'
backup.parent.mkdir(parents=True,exist_ok=True)
if not backup.exists():shutil.copy2(out,backup)
bpy.ops.wm.save_as_mainfile(filepath=str(out))
(W/f'data/top_transfer_{sex}.json').write_text(json.dumps(dict(sex=sex,method='nearest body triangle barycentric transfer; four weights; excluded hand/finger/foot triangles',body_and_rest_rig_unchanged=True,rows=rows,G7='not certified; rerun all pose diagnostics'),indent=2)+'\n')
print('TOP_TRANSFER',sex,rows,flush=True)
