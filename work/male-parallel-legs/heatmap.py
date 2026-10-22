"""blender -b --factory-startup --python heatmap.py -- <base.blend> <new.blend> <out_prefix>   : displacement heatmap of Body_M (new vs base): grey = bit-identical, blue->red = moved (0..30 mm)"""
import sys, math
import numpy as np, bpy
from mathutils import Vector
a=sys.argv[sys.argv.index('--')+1:]; base,new,pre=a
bpy.ops.wm.open_mainfile(filepath=base)
mb=bpy.data.objects['Body_M'].data; n=len(mb.vertices); Vb=np.empty(n*3); mb.vertices.foreach_get('co',Vb); Vb=Vb.reshape(-1,3).astype(np.float32)
bpy.ops.wm.open_mainfile(filepath=new)
body=bpy.data.objects['Body_M']; me=body.data; Vn=np.empty(n*3); me.vertices.foreach_get('co',Vn); Vn=Vn.reshape(-1,3).astype(np.float32)
d=np.linalg.norm(Vn.astype(float)-Vb.astype(float),axis=1)*1000
moved=np.any(Vn!=Vb,axis=1)
def color(mm,mv):
    if not mv: return (0.28,0.28,0.30,1)
    t=min(mm/30.0,1.0)**0.5
    # blue -> cyan -> yellow -> red
    stops=[(0,(0.1,0.2,0.9)),(0.35,(0.1,0.8,0.9)),(0.65,(0.95,0.9,0.1)),(1.0,(0.95,0.15,0.1))]
    for (t0,c0),(t1,c1) in zip(stops[:-1],stops[1:]):
        if t<=t1: u=(t-t0)/(t1-t0); return tuple(c0[i]+(c1[i]-c0[i])*u for i in range(3))+(1,)
    return (*stops[-1][1],1)
cols=[color(d[i],moved[i]) for i in range(n)]
attr=me.color_attributes.new('disp','FLOAT_COLOR','POINT')
flat=np.array(cols,np.float32).reshape(-1); attr.data.foreach_set('color',flat)
mat=bpy.data.materials.new('hm'); mat.use_nodes=True; nt=mat.node_tree; nt.nodes.clear()
ca=nt.nodes.new('ShaderNodeAttribute'); ca.attribute_name='disp'; em=nt.nodes.new('ShaderNodeEmission'); out=nt.nodes.new('ShaderNodeOutputMaterial')
nt.links.new(ca.outputs['Color'],em.inputs['Color']); nt.links.new(em.outputs['Emission'],out.inputs['Surface'])
me.materials.clear(); me.materials.append(mat)
for o in bpy.data.objects:
    if o.type=='EMPTY' or o.type=='CAMERA': o.hide_render=True
fo=bpy.data.objects.get('Face_M'); 
if fo: fo.hide_render=True
sc=bpy.context.scene; sc.render.engine='BLENDER_EEVEE'; sc.render.film_transparent=False
sc.render.resolution_x=700; sc.render.resolution_y=1100
sc.view_settings.view_transform='Standard'; sc.view_settings.look='None'
w=bpy.data.worlds.new('w'); sc.world=w; w.use_nodes=True; w.node_tree.nodes['Background'].inputs[0].default_value=(0.06,0.06,0.07,1)
cd=bpy.data.cameras.new('c'); cd.type='ORTHO'; cd.ortho_scale=1.9; co=bpy.data.objects.new('c',cd); sc.collection.objects.link(co); sc.camera=co
for name,az in (('front',0),('back',180),('side',90)):
    ang=math.radians(az); dvec=Vector((math.sin(ang),-math.cos(ang),0.0)); tgt=Vector((0,0,0.85))
    co.location=tgt+dvec*4; co.rotation_euler=(-dvec).to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=f'{pre}_{name}.png'; bpy.ops.render.render(write_still=True)
print('HEAT_DONE',int(moved.sum()),float(d.max()))
