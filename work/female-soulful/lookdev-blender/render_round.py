# exec'd inside the GUI Blender: renders VIEWS in both modes to renders/<tag>_<view>_<mode>.png
import bpy, math, mathutils
L="/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-soulful/lookdev-blender/"
sc=bpy.context.scene; cam=sc.camera
def scripts():
    for m in bpy.data.materials:
        if m.node_tree:
            for n in m.node_tree.nodes:
                if n.type=="SCRIPT": yield n
for n in scripts(): n.filepath=n.filepath   # recompile external OSL
def setp(name,val):
    for n in scripts():
        if name in n.inputs: n.inputs[name].default_value=val
def view(target,dist,yaw,fov,w,h):
    t=mathutils.Vector(target); y=math.radians(yaw)
    cam.location=t+mathutils.Vector((-math.sin(y)*dist,-math.cos(y)*dist,0))
    cam.rotation_euler=(t-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.sensor_fit='VERTICAL'; cam.data.angle=math.radians(fov)
    sc.render.resolution_x=w; sc.render.resolution_y=h
VIEWS={"face":((0,-0.09,1.52),.78,28,24,640,640),"eyes":((0,-0.10,1.557),.30,22,12,720,360),
       "polo":((0,-0.02,1.24),1.15,30,28,640,640),"bust":((0,-0.05,1.42),1.30,30,28,560,700)}
def run(tag,views,modes=(0,1)):
    out=[]
    for name in views:
        view(*VIEWS[name])
        for k in modes:
            setp("Mode",k); sc.render.filepath=L+f"renders/{tag}_{name}_{'before' if k==0 else 'after'}.png"
            bpy.ops.render.render(write_still=True); out.append(sc.render.filepath)
    return out
