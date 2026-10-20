"""blender -b blend --python render_views.py -- outprefix [zc] [scale] [matcap] [views(comma)] [res WxH]
Torso close-ups, hair hidden. matcap e.g. clay_studio.exr | check_reflection_vertical.exr | basic_side.exr ; 'studio' = STUDIO light."""
import bpy, sys, math
from mathutils import Vector
a=sys.argv[sys.argv.index('--')+1:]
pre=a[0]; zc=float(a[1]) if len(a)>1 else 1.08; scale=float(a[2]) if len(a)>2 else 0.95
mc=a[3] if len(a)>3 else 'studio'
vw=a[4].split(',') if len(a)>4 else ['front','q3F','side','q3B','back']
res=a[5].split('x') if len(a)>5 else ['700','900']
xc=float(a[6]) if len(a)>6 else 0.0
sc=bpy.context.scene
for o in bpy.data.objects:
    if o.type=='MESH' and o.name!='Body_F': o.hide_render=True
    if o.type=='EMPTY': o.hide_render=True
sc.render.engine='BLENDER_WORKBENCH'
sh=sc.display.shading; sh.color_type='SINGLE'; sh.single_color=(0.80,0.80,0.82); sh.show_cavity=False; sh.show_shadows=False
if mc=='studio': sh.light='STUDIO'
else:
    sh.light='MATCAP'
    if mc.endswith('.png') and '/' in mc:
        _sl=bpy.context.preferences.studio_lights.load(mc,'MATCAP'); sh.studio_light=_sl.name
    else: sh.studio_light=mc
sc.render.resolution_x=int(res[0]); sc.render.resolution_y=int(res[1])
w=bpy.data.worlds.new('w'); sc.world=w; w.use_nodes=False; w.color=(0.88,0.88,0.89)
cam=bpy.data.objects.new('c',bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera=cam
cam.data.type='ORTHO'; cam.data.ortho_scale=scale
views={'front':0,'q3F':-22,'q3Fb':-40,'side':-90,'q3B':-158,'back':180,'y20':-20,'y-20':20,'y25':-25,'y-25':25,'y160':-160,'y-160':160,'y155':-155,'y-155':155}
for name in vw:
    th=math.radians(views[name])
    pos=Vector((5*math.sin(th)+xc, -5*math.cos(th), zc))
    d=(Vector((xc,0,zc))-pos).normalized()
    cam.location=pos; cam.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=f'{pre}_{name}.png'; bpy.ops.render.render(write_still=True)
