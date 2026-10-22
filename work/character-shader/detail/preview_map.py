"""Preview a baked kit map on its mesh (Blender Workbench). Blender -b --factory-startup --python preview_map.py -- Male Kit_Top front|collar|back|shoe  out.png"""
import sys, os, math, numpy as np, bpy
from mathutils import Vector
a=sys.argv[sys.argv.index("--")+1:]; SEX,PIECE,VIEW,OUT=a[0],a[1],a[2],a[3]
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),"..","..",".."))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=os.path.join(ROOT,f"Unity/Assets/Characters/MatchHeroKit/{SEX}_Kit.fbx"))
arr=np.load(os.path.join(os.path.dirname(__file__),"maps",f"{SEX}_{PIECE}.npy"))
h,w=arr.shape
img=bpy.data.images.new("m",w,h,alpha=False,float_buffer=False)
img.colorspace_settings.name="Non-Color"
px=np.zeros((h,w,4),dtype=np.float32); 
s=arr[::-1]  # the bake writes PNG row order (row 0 = top = v 1); Blender image buffers start at the bottom
px[...,0]=px[...,1]=px[...,2]=s; px[...,3]=1
img.pixels=px.ravel(); img.pack()
obj=bpy.data.objects[PIECE]
for o in bpy.data.objects:
    if o.type=='MESH' and o is not obj: o.hide_render=True
mat=bpy.data.materials.new("pm"); mat.use_nodes=True
nt=mat.node_tree; nt.nodes.clear()
tex=nt.nodes.new("ShaderNodeTexImage"); tex.image=img; tex.interpolation='Closest'
out=nt.nodes.new("ShaderNodeOutputMaterial"); bsdf=nt.nodes.new("ShaderNodeBsdfPrincipled")
nt.links.new(tex.outputs[0],bsdf.inputs["Base Color"]); nt.links.new(bsdf.outputs[0],out.inputs[0])
obj.data.materials.clear(); obj.data.materials.append(mat)
sc=bpy.context.scene; sc.render.engine='BLENDER_WORKBENCH'
sh=sc.display.shading; sh.light='STUDIO'; sh.color_type='TEXTURE'; sh.show_cavity=False; sh.studio_light='rim.sl' if False else sh.studio_light
sc.render.resolution_x=1400; sc.render.resolution_y=1400
sc.display.render_aa='8'
bb=[obj.matrix_world@Vector(c) for c in obj.bound_box]; mn=Vector([min(v[i] for v in bb) for i in range(3)]); mx=Vector([max(v[i] for v in bb) for i in range(3)])
c=(mn+mx)/2
cam=bpy.data.objects.new("c",bpy.data.cameras.new("c")); sc.collection.objects.link(cam); sc.camera=cam
cam.data.type='ORTHO'
# Blender coords: -Y is the hero's forward (front); +Z up.
views={"front":(Vector((c.x,mn.y-3,c.z)),1.2*max(mx.z-mn.z,mx.x-mn.x)),
       "back":(Vector((c.x,mx.y+3,c.z)),1.2*max(mx.z-mn.z,mx.x-mn.x)),
       "collar":(Vector((0,mn.y-3,mx.z-0.09)),0.30),
       "side":(Vector((mx.x+3,c.y,c.z)),1.2*max(mx.z-mn.z,mx.y-mn.y)),
       "shoe":(Vector((c.x,mn.y-3,c.z)),0.35)}
pos,scale=views[VIEW]; cam.location=pos
tgt=Vector((pos.x,c.y,pos.z)) if VIEW in("front","back","collar","shoe") else Vector((c.x,c.y,pos.z))
if VIEW=="side": cam.location=Vector((pos.x,c.y,c.z)); tgt=c
d=(tgt-cam.location); cam.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
cam.data.ortho_scale=scale
sc.render.filepath=OUT; bpy.ops.render.render(write_still=True)
