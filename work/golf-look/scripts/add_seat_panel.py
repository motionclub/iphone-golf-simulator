"""A real trouser seat gusset fitted to the eight-pose Hips-space envelope."""
import bpy,sys,json,math,shutil,numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from dcommon import activate_clip,evaluated_co
W=Path(__file__).resolve().parents[1];rig=bpy.data.objects['Rig_Male'];body=bpy.data.objects['Body_M'];sc=bpy.context.scene;p=Path(bpy.data.filepath)
bk=W/'rollback/seat_panel_r1'/p.name;bk.parent.mkdir(parents=True,exist_ok=True)
if not bk.exists():shutil.copy2(p,bk)
if 'Golf_SeatPanel' in bpy.data.objects:bpy.data.objects.remove(bpy.data.objects['Golf_SeatPanel'],do_unlink=True)
source=[v.index for v in body.data.vertices if abs(v.co.x)<.095 and .61<v.co.z<1.02 and v.co.y>.015]
cloud=[];rest=rig.matrix_world@rig.data.bones['Hips'].matrix_local
# Read the existing proof actions without transferring any motion to gameplay.
with bpy.data.libraries.load(str(W/'export/Golf_Male_SwingProof.blend'),link=False) as (src,dst):dst.actions=[n for n in src.actions if n.startswith('GolfProof_')]
for hand in ['RH','LH']:
 for state in ['ReadyIdle','Top','Impact','Finish']:
  name='ReadyIdle' if hand=='RH' and state=='ReadyIdle' else f'GolfProof_{hand}_{state}'
  activate_clip(rig,name);sc.frame_set(0);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();co=evaluated_co(body,dg)[source];M=np.array(rest@(rig.matrix_world@rig.pose.bones['Hips'].matrix).inverted());cloud.extend((co@M[:3,:3].T+M[:3,3]).tolist())
cloud=np.array(cloud);rig.animation_data.action=None;rig.data.pose_position='REST'
for b in rig.pose.bones:b.matrix_basis=Matrix.Identity(4)
bpy.context.view_layer.update()
nx,nz=25,25;xs=np.linspace(-.145,.145,nx);zs=np.linspace(.61,1.005,nz);height=np.zeros((nz,nx))
for j,z in enumerate(zs):
 for i,x in enumerate(xs):
  near=(np.abs(cloud[:,0]-x)<.028)&(np.abs(cloud[:,2]-z)<.023)
  if near.any():y=cloud[near,1].max()
  else:
   score=((cloud[:,0]-x)/.03)**2+((cloud[:,2]-z)/.025)**2;y=cloud[np.argpartition(score,8)[:8],1].max()
  height[j,i]=y+.009
# Smooth the envelope conservatively; retain a clearance margin at the seams.
for _ in range(3):
 h=height.copy();h[1:-1,1:-1]=(height[1:-1,1:-1]*4+height[:-2,1:-1]+height[2:,1:-1]+height[1:-1,:-2]+height[1:-1,2:])/8;height=np.maximum(height-.001,h)
verts=[(float(x),float(height[j,i]),float(z)) for j,z in enumerate(zs) for i,x in enumerate(xs)]
faces=[(j*nx+i,j*nx+i+1,(j+1)*nx+i+1,(j+1)*nx+i) for j in range(nz-1) for i in range(nx-1)]
# +Y is the outward seat direction.
faces=[tuple(reversed(f)) for f in faces]
me=bpy.data.meshes.new('Golf seat gusset');me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new('Golf_SeatPanel',me);sc.collection.objects.link(o);me.materials.append(bpy.data.materials['Golf_Bottom'])
for f in me.polygons:f.use_smooth=True
group=o.vertex_groups.new(name='Hips');group.add(list(range(len(verts))),1,'REPLACE')
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
sol=o.modifiers.new('Actual seat seam thickness','SOLIDIFY');sol.thickness=.002;sol.offset=-1;bpy.ops.object.modifier_apply(modifier=sol.name)
arm=o.modifiers.new('Same match rig','ARMATURE');arm.object=rig;o.parent=rig
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.1,island_margin=.015);bpy.ops.object.mode_set(mode='OBJECT')
rig.data.pose_position='POSE';activate_clip(rig,'ReadyIdle');sc.frame_set(0);bpy.ops.wm.save_as_mainfile(filepath=str(p));me.calc_loop_triangles()
(W/'data/seat_panel_r1.json').write_text(json.dumps(dict(sourceBodyVertices=len(source),poseSamples=len(cloud),triangles=len(me.loop_triangles),maxRestY=float(height.max()),weights='Hips rigid; eight-pose inverse envelope',status='candidate; render and collision checks required'),indent=2)+'\n')
print('SEAT PANEL',len(me.loop_triangles),height.min(),height.max(),flush=True)
