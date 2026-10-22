import bpy,sys,json,numpy as np
from pathlib import Path
from mathutils import Matrix
sys.path.insert(0,str(Path(__file__).resolve().parent))
from dcommon import evaluated_co,activate_clip
from follow_lib import bvh_from
W=Path(__file__).resolve().parents[1];sex=sys.argv[-1]
rig=bpy.data.objects['Rig_'+sex];body=bpy.data.objects['Body_F' if sex=='Female' else 'Body_M'];o=bpy.data.objects['Golf_Polo']
rig.animation_data.action=None;rig.data.pose_position='POSE'
for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
bpy.context.view_layer.update();o.data.calc_loop_triangles()
at=o.data.attributes['GolfOuterFace'];tri=np.array([tuple(t.vertices) for t in o.data.loop_triangles if at.data[t.polygon_index].value==1])
ids=[16250,16647,14014,10190,14911] if sex=='Male' else [9562,9165,790,9751,9600]
rows=[]
for state in ['REST','ReadyIdle','Top','Impact','Finish']:
 if state!='REST':activate_clip(rig,'ReadyIdle' if state=='ReadyIdle' else 'GolfProof_RH_'+state)
 bpy.context.scene.frame_set(0);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();b=evaluated_co(body,dg);co=evaluated_co(o,dg);tree=bvh_from(co,tri)
 for idx in ids:
  loc,n,t,d=tree.find_nearest(tuple(b[idx]));verts=tri[t];bind=np.array([tuple(o.data.vertices[j].co) for j in verts]);bn=np.cross(bind[1]-bind[0],bind[2]-bind[0]);bn/=max(1e-15,np.linalg.norm(bn))
  rows.append(dict(state=state,body=idx,tri=int(t),distanceMm=d*1000,signedMm=float(np.dot(b[idx]-np.array(loc),n)*1000),bindTriangle=bind.tolist(),bindNormal=bn.tolist(),posedNormal=list(n),bodyBindNormal=list(body.data.vertices[idx].normal)))
print(json.dumps(rows,indent=2),flush=True)
(W/f'data/outer_provenance_{sex}.json').write_text(json.dumps(rows,indent=2)+'\n')
