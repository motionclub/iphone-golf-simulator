"""blender -b <blend> --python vcrender_f.py -- <coords.npy> <lum.npz(front,back: per-vertex 0..255)> <outprefix> [views front,back]
Renders Body_F with per-vertex luminance (flat vertex colours) through plate-registered orthographic cameras (1280x720, S m/px)."""
import sys, numpy as np, bpy
from mathutils import Vector
a=sys.argv[sys.argv.index('--')+1:]
V=np.load(a[0]); L=np.load(a[1]); pre=a[2]; views=(a[3] if len(a)>3 else 'front,back').split(',')
S=0.0025954198473282443
me=bpy.data.objects['Body_F'].data
assert len(V)==len(me.vertices)
me.vertices.foreach_set('co',V.astype(np.float64).ravel()); me.update()
for o in bpy.data.objects:
    if o.type=='EMPTY' or (o.type=='MESH' and o.name!='Body_F'): o.hide_render=True
    if o.type=='LIGHT': o.hide_render=True
sc=bpy.context.scene; sc.render.engine='BLENDER_WORKBENCH'; sh=sc.display.shading
sh.light='FLAT'; sh.color_type='VERTEX'; sh.show_object_outline=False; sh.show_specular_highlight=False
sc.render.film_transparent=False; sc.view_settings.view_transform='Standard'; sc.view_settings.look='None'
sc.render.resolution_x,sc.render.resolution_y=1280,720; sc.render.resolution_percentage=100
sc.render.image_settings.file_format='PNG'; sc.render.image_settings.color_mode='RGB'
w=bpy.data.worlds.new('w'); sc.world=w; w.use_nodes=False; w.color=(0.0,0.0,0.0)
try: sc.display.render_aa='8'
except Exception: pass
cam=bpy.data.objects.new('c',bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera=cam; cam.data.type='ORTHO'
def srgb_to_lin(c):
    c=np.asarray(c,float); return np.where(c<=0.04045,c/12.92,((c+0.055)/1.055)**2.4)
def shot(name,scale,center,d):
    cam.data.ortho_scale=scale; d=Vector(d); cam.location=Vector(center)-d*3; cam.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
    lum=np.clip(L[name]/255.0,0,1); lin=srgb_to_lin(lum)
    col=np.zeros((len(V),4)); col[:,0]=col[:,1]=col[:,2]=lin; col[:,3]=1
    if 'lc' in me.color_attributes: me.color_attributes.remove(me.color_attributes['lc'])
    ca=me.color_attributes.new('lc','FLOAT_COLOR','POINT'); ca.data.foreach_set('color',col.ravel()); me.color_attributes.active_color=ca
    sc.render.filepath=f'{pre}_{name}.png'; bpy.ops.render.render(write_still=True)
zc=(679-360)*S
if 'front' in views: shot('front',1280*S,((640-440)*S,0,zc),(0,1,0))
if 'back' in views: shot('back',1280*S,((847-640)*S,0,zc),(0,-1,0))
print('VCRENDER_DONE')
