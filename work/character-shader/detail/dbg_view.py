import sys, os, numpy as np, bpy
from mathutils import Vector
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),"..","..",".."))
a=sys.argv[sys.argv.index("--")+1:]; SEX,PIECE,KEY,THR,VIEW,OUT=a[0],a[1],a[2],float(a[3]),a[4],a[5]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=os.path.join(ROOT,f"Unity/Assets/Characters/MatchHeroKit/{SEX}_Kit.fbx"))
d=np.load(os.path.join(os.path.dirname(__file__),"maps",f"_dbg_{SEX}_{PIECE}.npz"))
obj=bpy.data.objects[PIECE]; m=obj.data
for o in bpy.data.objects:
    if o.type=='MESH' and o is not obj: o.hide_render=True
v=d[KEY]; on=(v>THR)
col=m.color_attributes.new("dbg","FLOAT_COLOR","POINT")
arr=np.zeros((len(m.vertices),4),dtype=np.float32); arr[:,3]=1; arr[:,0]=np.where(on,1.0,0.75); arr[:,1]=np.where(on,0.05,0.75); arr[:,2]=np.where(on,0.05,0.75)
col.data.foreach_set("color",arr.ravel()); m.color_attributes.active_color=col
sc=bpy.context.scene; sc.render.engine='BLENDER_WORKBENCH'; sh=sc.display.shading; sh.light='STUDIO'; sh.color_type='VERTEX'
sc.render.resolution_x=1200; sc.render.resolution_y=1200
bb=[obj.matrix_world@Vector(c) for c in obj.bound_box]; mn=Vector([min(x[i] for x in bb) for i in range(3)]); mx=Vector([max(x[i] for x in bb) for i in range(3)]); c=(mn+mx)/2
cam=bpy.data.objects.new("c",bpy.data.cameras.new("c")); sc.collection.objects.link(cam); sc.camera=cam; cam.data.type='ORTHO'
sz=1.15*max(mx.z-mn.z,mx.x-mn.x)
if VIEW=="front": cam.location=Vector((c.x,mn.y-3,c.z))
elif VIEW=="back": cam.location=Vector((c.x,mx.y+3,c.z))
else: cam.location=Vector((mx.x+3,c.y,c.z))
cam.rotation_euler=(c-cam.location).to_track_quat('-Z','Y').to_euler(); cam.data.ortho_scale=sz
sc.render.filepath=OUT; bpy.ops.render.render(write_still=True)
