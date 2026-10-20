import bpy,numpy as np,json,hashlib,math,sys
from pathlib import Path
from mathutils import Vector
W=Path(__file__).resolve().parent; R=W.parents[1]; D=R/'ArtDir/hero/base_lock'
name=sys.argv[sys.argv.index('--')+1]; O=W/name; O.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(W/'baseline/HeroBase_Male_Silhouette.blend'))
o=bpy.data.objects['Body_M']; me=o.data; co=np.load(W/(name+'.npy')); base=np.load(W/'baseline/mesh.npz')['co']; inv=json.loads((W/'baseline/invariants.json').read_text())
for v,p in zip(me.vertices,co):v.co=tuple(p)
me.update(); scene=bpy.context.scene; original_camera=scene.camera; original_path=scene.render.filepath
assert np.array_equal(co[base[:,2]<1.35],base[base[:,2]<1.35])
for view in ['bald_front','bald_back']:
 scene.camera=bpy.data.objects['Locked_'+view]; scene.render.filepath=str(O/(view+'.png')); bpy.ops.render.render(write_still=True)
scene.camera=original_camera; scene.render.filepath=original_path
bpy.ops.wm.save_as_mainfile(filepath=str(O/'candidate.blend'))
cam=bpy.data.objects.new('Transient_Head_Review',original_camera.data.copy()); scene.collection.objects.link(cam);cam.data.background_images.clear()
def shot(name,angle,elev=0):
 a=math.radians(angle); e=math.radians(elev); target=Vector((0,-.045,1.505));cam.location=target+Vector((math.sin(a)*4*math.cos(e),-math.cos(a)*4*math.cos(e),4*math.sin(e)))
 cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.45; scene.camera=cam
 scene.render.resolution_x=800; scene.render.resolution_y=800; scene.render.filepath=str(O/(name+'.png')); bpy.ops.render.render(write_still=True)
for n,a in [('head_front',0),('head_front_left',45),('head_left',90),('head_back_left',135),('head_back',180),('head_back_right',225),('head_right',270),('head_front_right',315)]:shot(n,a)
shot('head_top',0,80)
actual=np.array([tuple(v.co) for v in me.vertices]); np.save(O/'actual.npy',actual)
top=hashlib.sha256(json.dumps([list(f.vertices) for f in me.polygons],separators=(',',':')).encode()).hexdigest(); assert top==inv['connectivity_sha256']
print('HEAD_CANDIDATE_RENDERED',name)
