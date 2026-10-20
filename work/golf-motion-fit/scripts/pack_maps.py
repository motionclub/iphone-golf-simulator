"""Pack shared semantic garment atlases in the new geometry's actual UVs."""
import bpy,sys,json
import numpy as np
from pathlib import Path
from mathutils import Matrix
W=Path(__file__).resolve().parents[1];sex=sys.argv[-1];rig=bpy.data.objects['Rig_'+sex];rig.data.pose_position='REST';rig.animation_data.action=None
for o in bpy.data.objects:
 if o.type=='MESH' and o.data.shape_keys:
  o.data.shape_keys.animation_data_clear()
  for key in o.data.shape_keys.key_blocks:key.value=0
parts=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Golf_') and '_High' not in o.name and not o.name.startswith('Golf_Hair')]
buckets={}
for o in parts:
 group='Top' if o.name=='Golf_Polo' else 'Bottom' if o.name.startswith(('Golf_Trousers','Golf_PleatedSkort','Golf_InnerShorts','Golf_Belt','Golf_Buckle','Golf_Pocket')) else 'Head' if o.name.startswith(('Golf_Cap','Golf_Visor','Golf_CurvedBrim','Golf_Brim')) else o.name[5:]
 buckets.setdefault(group,[]).append(o)
for path in (W/'export').glob(sex+'_Kit_*.npz'):path.unlink()
profile=[]
for group,objects in buckets.items():
 bpy.ops.object.select_all(action='DESELECT')
 for o in objects:o.hide_set(False);o.hide_viewport=False;o.select_set(True)
 bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.1,island_margin=.012);bpy.ops.object.mode_set(mode='OBJECT')
 P=[];UV=[];N=[];TR=[];TL=[];MI=[];roles=[];vstart=lstart=0
 for o in objects:
  o.data.calc_loop_triangles();localroles=[m.name.split('.')[0] for m in o.data.materials];rolemap=[]
  for role in localroles:
   if role not in roles:roles.append(role)
   rolemap.append(roles.index(role))
  P.extend(tuple(v.co) for v in o.data.vertices);UV.extend(tuple(v.uv) for v in o.data.uv_layers.active.data);N.extend(tuple(n.vector) for n in o.data.corner_normals)
  for tri in o.data.loop_triangles:TR.append(tuple(i+vstart for i in tri.vertices));TL.append(tuple(i+lstart for i in tri.loops));MI.append(rolemap[tri.material_index])
  vstart+=len(o.data.vertices);lstart+=len(o.data.loops)
  profile.append(dict(part=o.name,atlas=group,normalMap=f'GolfMotion_{sex}_{group}_N',maskMap=f'GolfMotion_{sex}_{group}_M',fabricVersion=2,heroProfile=1))
 np.savez_compressed(W/f'export/{sex}_Kit_{group}.npz',P=np.asarray(P),uv=np.asarray(UV),normal=np.asarray(N),tri=np.asarray(TR),triloops=np.asarray(TL),material=np.asarray(MI),materials=np.asarray(roles))
rig.data.pose_position='POSE';rig.animation_data.action=bpy.data.actions[f'Drive_{sex}_RH'];bpy.context.scene.frame_set(0)
# Corrective animation is reinstalled after packing. Their meshes and keys persist.
(W/f'export/material_profiles_{sex}.json').write_text(json.dumps(profile,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(W/f'export/Golf_{sex}_Dressed.blend'),compress=True)
print('UV_PACK_COMPLETE',sex,len(buckets),flush=True)
