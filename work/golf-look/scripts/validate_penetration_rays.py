import bpy,sys,json,numpy as np
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from dcommon import evaluated_co,mesh_tris,activate_clip
from follow_lib import bvh_from
W=Path(__file__).resolve().parents[1];sex=sys.argv[-1];rig=bpy.data.objects['Rig_'+sex];body=bpy.data.objects['Body_F' if sex=='Female' else 'Body_M'];d=json.loads((W/f'data/surface_penetration_{sex}.json').read_text())
for row in d['poses']:
 activate_clip(rig,row['action']);bpy.context.scene.frame_set(-1);bpy.context.scene.frame_set(0);bpy.context.view_layer.update();tree=bvh_from(evaluated_co(body,bpy.context.evaluated_depsgraph_get()),mesh_tris(body.data))
 for part in row['pieces']:
  if not part['over3mm']:continue
  counts=[]
  for direction in [(1,.137,.347),(.219,1,.413),(.319,.179,1)]:
   origin=Vector(part['worstWorld']);direction=Vector(direction).normalized();count=0
   for _ in range(100):
    loc,n,idx,dist=tree.ray_cast(origin,direction,10)
    if loc is None:break
    count+=1;origin=loc+direction*.00001
   counts.append(count)
  part['rayCrossings']=counts;part['insideVotes']=sum(k%2 for k in counts)
 print(row['action'],[(p['piece'],round(p['penetrationMaxMm'],2),p.get('rayCrossings')) for p in row['pieces'] if p['over3mm']],flush=True)
(W/f'data/surface_penetration_rays_{sex}.json').write_text(json.dumps(d,indent=2))
