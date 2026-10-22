import bpy, sys, math, json
sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/blender/scripts')
from mathutils import Vector
YD=0.9144
R='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/postcard-look/v2/review_08/r2/img/'
sc=bpy.context.scene
sc.render.engine='BLENDER_EEVEE'
try: sc.view_settings.view_transform='AgX'
except: pass
w=sc.world or bpy.data.worlds.new('W'); sc.world=w; w.use_nodes=True
bg=w.node_tree.nodes['Background']; bg.inputs[0].default_value=(0.55,0.72,0.95,1); bg.inputs[1].default_value=1.0
for n in ("BALL_START","HOLE_CUP","MARKER_TEE","MARKER_PIN","MARKER_UP"):
    o=bpy.data.objects.get(n); 
    if o: o.hide_render=True
dg=bpy.context.evaluated_depsgraph_get()
def gz(x,y):
    ok,loc,n,i,ob,mw=sc.ray_cast(dg,Vector((x,y,60)),Vector((0,0,-1)))
    o=Vector((x,y,60))
    for _ in range(40):
        ok,loc,n,i,ob,mw=sc.ray_cast(dg,o,Vector((0,0,-1)),distance=100)
        if not ok: return 0
        if ob.name.startswith(('TERRAIN','FAIRWAY','GREEN','TEE_BOX','BUNKER')): return loc.z
        o=loc-Vector((0,0,0.001))
    return 0
def cam(name,loc,look,fov=60):
    c=bpy.data.cameras.new(name); ob=bpy.data.objects.new(name,c); sc.collection.objects.link(ob)
    ob.location=loc; ob.rotation_euler=(Vector(look)-Vector(loc)).to_track_quat('-Z','Y').to_euler()
    c.sensor_fit='VERTICAL'; c.angle_y=math.radians(fov); c.clip_start=0.27; c.clip_end=6000; return ob
def shot(ob,name,res):
    sc.camera=ob; sc.render.resolution_x,sc.render.resolution_y=res; sc.render.resolution_percentage=100
    sc.render.filepath=R+name+'.png'; sc.eevee.taa_render_samples=24
    bpy.ops.render.render(write_still=True)
def address(ball,aim,name):
    bx,by=ball[0]*YD,ball[1]*YD; z=gz(bx,by); d=Vector((aim[0]*YD-bx,aim[1]*YD-by,0)).normalized()
    b=Vector((bx,by,z)); loc=b-d*4.5*YD+Vector((0,0,2.4*YD)); look=b+d*1.5*YD
    shot(cam(name,loc,look),name,(900,1600))
address((0,0),(19,178),'tee')
address((19,178),(-6,340),'approach')
# landmark: unity world yards x right, z down hole, y up -> blender (x,y=z,z=y) metres
def lm(p): return Vector((p[0]*YD,p[2]*YD,p[1]*YD))
shot(cam('arch',lm((-9.84,10.37,301.84)),lm((-28.7,10.72,317.0))),'arch',(900,1600))
# aerials like the still: from left/behind tee, high, looking toward the green
shot(cam('aer1',Vector((-120,-60,95)),Vector((10,150,0))),'aerial1',(1600,900))
shot(cam('aer2',Vector((-70,330,45)),Vector((0,230,3))),'aerial_green',(1600,900))
shot(cam('aer3',Vector((60,150,70)),Vector((-8,300,3))),'aerial_mid',(1600,900))
address((0.8,18),(19,178),'pathball')
