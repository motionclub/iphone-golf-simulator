import bpy,numpy as np,json,hashlib,math,sys
from pathlib import Path
from mathutils import Vector
W=Path(__file__).resolve().parent;R=W.parents[1];D=R/'ArtDir/hero/base_lock'
name=sys.argv[sys.argv.index('--')+1];O=W/name;O.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(W/'baseline/HeroBase_Male_Silhouette.blend'));o=bpy.data.objects['Body_M'];me=o.data
co=np.load(W/(name+'.npy'));base=np.load(W/'baseline/mesh.npz')['co'];inv=json.loads((W/'baseline/invariants.json').read_text())
for v,p in zip(me.vertices,co):v.co=tuple(p)
me.update();scene=bpy.context.scene;active=scene.camera;path=scene.render.filepath
for v in ['bald_front','bald_back']:
 scene.camera=bpy.data.objects['Locked_'+v];scene.render.filepath=str(O/(v+'.png'));bpy.ops.render.render(write_still=True)
scene.camera=active;scene.render.filepath=path;bpy.ops.wm.save_as_mainfile(filepath=str(O/'candidate.blend'))
cam=bpy.data.objects.new('Transient_Hand_Review',active.data.copy());scene.collection.objects.link(cam);cam.data.background_images.clear();scene.camera=cam
def shot(n,a):
 target=Vector((.600,-.10,.872));a=math.radians(a);cam.location=target+Vector((math.sin(a)*3,-math.cos(a)*3,0));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.25;scene.render.resolution_x=800;scene.render.resolution_y=800;scene.render.filepath=str(O/(n+'.png'));bpy.ops.render.render(write_still=True)
for n,a in [('hand_front',0),('hand_threequarter',45),('hand_left',90),('hand_back',180),('hand_right',270)]:shot(n,a)
for n,a in [('body_left',90),('body_right',270),('body_threequarter',45)]:
 target=Vector((0,0,.84));a=math.radians(a);cam.location=target+Vector((math.sin(a)*5,-math.cos(a)*5,0));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=1280*1.7/593;scene.render.resolution_x=1280;scene.render.resolution_y=720;scene.render.filepath=str(O/(n+'.png'));bpy.ops.render.render(write_still=True)
np.save(O/'actual.npy',np.array([tuple(v.co) for v in me.vertices]));print('HAND_CANDIDATE_RENDERED',name)
