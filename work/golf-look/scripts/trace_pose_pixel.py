import bpy,sys,json,numpy as np,math,os
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from dcommon import evaluated_co,mesh_tris,activate_clip
from follow_lib import bvh_from
W=Path(__file__).resolve().parents[1];rig=bpy.data.objects['Rig_Male'];action=os.getenv('TRACE_ACTION','GolfProof_RH_Top');activate_clip(rig,action);bpy.context.scene.frame_set(0);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
target=Vector((0,0,.87));d=3.1;el=math.radians(5);az=math.radians(28);eye=target+Vector((d*math.cos(el)*math.sin(az),-d*math.cos(el)*math.cos(az),d*math.sin(el)))
cd=bpy.data.cameras.new('DiagnosticProjection');cam=bpy.data.objects.new('DiagnosticProjection',cd);bpy.context.scene.collection.objects.link(cam);cam.location=eye;cam.rotation_euler=(target-eye).to_track_quat('-Z','Y').to_euler();cd.lens=50;cd.sensor_width=36;bpy.context.view_layer.update();proj=cam.calc_matrix_camera(dg,x=600,y=800).inverted();rotation=cam.matrix_world.to_3x3()
trees=[]
for o in bpy.data.objects:
 if o.type=='MESH' and (o.name=='Body_M' or o.name.startswith('Golf_')) and o.name!='Golf_Glove_Right':trees.append((o,bvh_from(evaluated_co(o,dg),mesh_tris(o.data))))
rows=[]
for x,y in json.loads(os.getenv('TRACE_PIXELS','[[295,445],[295,430],[295,460],[288,450],[305,435],[280,470],[300,470]]')):
 q=proj@Vector((2*(x+.5)/600-1,1-2*(y+.5)/800,-1,1));q/=q.w;ray=rotation@q.xyz.normalized();hits=[]
 for o,t in trees:
  p,n,idx,dist=t.ray_cast(eye,ray,10)
  if p is not None:
   tri=mesh_tris(o.data)[idx];vs=[o.data.vertices[i] for i in tri];hits.append(dict(name=o.name,distance=dist,bind=[list(v.co) for v in vs],weights=[{o.vertex_groups[g.group].name:g.weight for g in v.groups} for v in vs]))
 rows.append(dict(x=x,y=y,hits=sorted(hits,key=lambda h:h['distance'])[:5]))
(W/f'data/pose_pixel_trace_{action}.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2),flush=True)
