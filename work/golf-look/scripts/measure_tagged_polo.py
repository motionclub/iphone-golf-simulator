"""Independent primary-shell diagnostic with explicit outer-face provenance.

This resolves the inner-wall sign ambiguity in the older nearest-face tool.
It is not a complete G7 certificate: collar, openings and triangle interiors
are reported separately as unverified rather than silently ignored.
"""
import bpy,sys,json,numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from dcommon import evaluated_co,activate_clip,mesh_tris
from follow_lib import bvh_from
W=Path(__file__).resolve().parents[1];sex=sys.argv[-1];rig=bpy.data.objects['Rig_'+sex];body=bpy.data.objects['Body_F' if sex=='Female' else 'Body_M'];o=bpy.data.objects['Golf_Polo'];sc=bpy.context.scene
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
sc.frame_set(0);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();b=evaluated_co(body,dg);co=evaluated_co(o,dg)
attr=o.data.attributes['GolfOuterFace'];o.data.calc_loop_triangles();tri=np.array([tuple(t.vertices) for t in o.data.loop_triangles if attr.data[t.polygon_index].value==1]);tree=bvh_from(co,tri)
zone=[]
for v in body.data.vertices:
 if v.co.z<.953:continue
 hit,n,i,dist=tree.ray_cast(Vector(tuple(b[v.index])),v.normal,.075)
 if hit is not None:zone.append(v.index)
rows=[]
for hand in ['RH','LH']:
 for state in ['ReadyIdle','Top','Impact','Finish']:
  act='ReadyIdle' if hand=='RH' and state=='ReadyIdle' else f'GolfProof_{hand}_{state}'
  activate_clip(rig,act);sc.frame_set(0);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();b=evaluated_co(body,dg);co=evaluated_co(o,dg);tree=bvh_from(co,tri)
  signed=[];distance=[]
  for idx in zone:
   loc,n,t,d=tree.find_nearest(tuple(b[idx]));signed.append(float(np.dot(b[idx]-np.array(loc),n)));distance.append(d)
  signed=np.array(signed);k=int(np.argmax(signed));row=dict(hand=hand,state=state,samples=len(zone),outer_triangles=len(tri),max_positive_signed_mm=max(0,float(signed.max()*1000)),over_3mm=int((signed>.003).sum()),worst_body_vertex=int(zone[k]),distance_at_worst_mm=distance[k]*1000)
  rows.append(row);print(row,flush=True)
(W/f'data/tagged_polo_{sex}.json').write_text(json.dumps(dict(rows=rows,scope='primary-shell outer faces from Solidify material provenance; no inner-wall nearest-normal ambiguity',G7='FAIL: construction/openings/full triangle coverage still unverified'),indent=2)+'\n')
