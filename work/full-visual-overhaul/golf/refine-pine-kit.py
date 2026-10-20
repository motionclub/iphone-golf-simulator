import bpy,math,random,json
from pathlib import Path
root=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
bpy.ops.wm.open_mainfile(filepath=str(root/'work/full-visual-overhaul/golf/ResortGeologyKit.blend'))
old=bpy.data.objects.get('PINE');bpy.data.objects.remove(old,do_unlink=True)
verts=[];faces=[];slots=[];rng=random.Random(6111)
def ring(z,r,cx=0,cy=0,phase=0,sides=10):
 start=len(verts)
 for j in range(sides):
  a=phase+j*math.tau/sides;radius=r*(.87+rng.random()*.20);verts.append((cx+math.cos(a)*radius,cy+math.sin(a)*radius,z))
 return start
def connect(a,b,slot,sides=10):
 for j in range(sides):faces.append((a+j,a+(j+1)%sides,b+(j+1)%sides,b+j));slots.append(slot)
a=ring(0,.044);b=ring(.85,.012);connect(a,b,0)
for k in range(5):
 z=.16+k*.155;r=.78-k*.135;phase=k*.43
 lower=ring(z,r,phase=phase);middle=ring(z+.10,r*.78,phase=phase+.09);top=ring(z+.29,.018,phase=phase)
 connect(lower,middle,1+k%2);connect(middle,top,2+k%2)
 faces.append(tuple(reversed([lower+j for j in range(10)])));slots.append(1)
 # Asymmetric outer branch fans break the regular cone silhouette.
 for j in range(3):
  a=phase+j*math.tau/3;cx=math.cos(a)*r*.62;cy=math.sin(a)*r*.62
  f=ring(z-.018,r*.28,cx,cy,phase=a,sides=6);t=ring(z+.16,.012,cx*.8,cy*.8,phase=a,sides=6);connect(f,t,1+j%3,6)
me=bpy.data.meshes.new('PINE');me.from_pydata(verts,[],faces);me.update()
for n in ['RESORT_BARK','RESORT_LEAF_DARK','RESORT_LEAF_MID','RESORT_LEAF_LIGHT']:me.materials.append(bpy.data.materials[n])
for p,slot in zip(me.polygons,slots):p.material_index=slot;p.use_smooth=True
o=bpy.data.objects.new('PINE',me);bpy.context.collection.objects.link(o)
bpy.ops.wm.save_as_mainfile(filepath=str(root/'work/full-visual-overhaul/golf/ResortGeologyKit.blend'))
for o in bpy.data.objects:o.select_set(o.type=='MESH')
bpy.ops.export_scene.fbx(filepath=str(root/'Unity/Assets/Resources/Course/Resort/BotanicalKit.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',bake_space_transform=False,bake_anim=False,use_mesh_modifiers=True,path_mode='STRIP')
me.calc_loop_triangles();print('PINE_REFINE_COMPLETE',len(me.loop_triangles))
