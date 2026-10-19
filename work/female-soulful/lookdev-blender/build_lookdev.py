# Builds lookdev.blend: original-seam female + golf polo, OSL ports of the Unity
# female materials (Mode 0 = clone before, 1 = staged after). Sources are read only.
import bpy, math, mathutils
R="/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/"
L=R+"work/female-soulful/lookdev-blender/"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=R+"Unity/Assets/Resources/Tennis/OriginalSeam/Female.fbx")
src=R+"work/female-soulful/source/golf_top.blend"
with bpy.data.libraries.load(src,link=False) as (a,b): b.objects=["Kit_Top"]
top=b.objects[0]; bpy.context.scene.collection.objects.link(top)
sc=bpy.context.scene
sc.render.engine='CYCLES'; sc.cycles.device='CPU'; sc.cycles.shading_system=True
sc.cycles.samples=24; sc.cycles.use_denoising=False; sc.cycles.max_bounces=0
sc.view_settings.view_transform='Standard'; sc.view_settings.look='None'
sc.render.resolution_x=720; sc.render.resolution_y=720
w=bpy.data.worlds.new("Studio"); sc.world=w; w.use_nodes=True
bg=w.node_tree.nodes["Background"]; bg.inputs[0].default_value=(0.19,0.19,0.20,1); bg.inputs[1].default_value=1
def scripted(name, osl, params, tangent=False):
    m=bpy.data.materials.new(name); m.use_nodes=True; nt=m.node_tree; nt.nodes.clear()
    s=nt.nodes.new("ShaderNodeScript"); s.mode='EXTERNAL'; s.filepath=L+osl
    with bpy.context.temp_override(): pass
    bpy.ops.wm.read_factory_settings if False else None
    o=nt.nodes.new("ShaderNodeOutputMaterial")
    return m,nt,s,o
mats={}
def finish(m,nt,s,o,params,tangent=False):
    for k,val in params.items():
        if isinstance(val,tuple) and len(val)==3: val=val+(1.0,)
        if k in s.inputs: s.inputs[k].default_value=val
        else: print("MISSING socket",k,list(s.inputs.keys()))
    nt.links.new(s.outputs["Out"],o.inputs["Surface"])
    if tangent:
        t=nt.nodes.new("ShaderNodeTangent"); t.direction_type='UV_MAP'; t.uv_map="UVMap"
        nt.links.new(t.outputs[0],s.inputs["Tangent"])
skinTone=(0.933,0.733,0.561)
body=bpy.data.objects["Body"]
m,nt,s,o=scripted("LD_Skin","fem_skin.osl",{})
finish(m,nt,s,o,{"ToneSRGB":skinTone})
body.data.materials.clear(); body.data.materials.append(m)
feat=bpy.data.objects["ReferenceFeatures"]
roles={"Sclera":1,"IrisIn":2,"Iris":2,"Limbal":3,"Pupil":3,"Catch":4,"Brow":3}
for i,fm in enumerate(feat.data.materials):
    key=fm.name.replace("Reference_Face_","")
    bs=[n for n in fm.node_tree.nodes if n.type=="BSDF_PRINCIPLED"][0]
    col=tuple(bs.inputs["Base Color"].default_value)
    mm,nt,s,o=scripted("LD_"+key,"fem_eye.osl",{})
    finish(mm,nt,s,o,{"Albedo":col[:3],"Role":roles.get(key,3)})
    feat.data.materials[i]=mm
D=R+"work/female-soulful/out/GolfKitHero_Female/unity/"
mt,nt,s,o=scripted("LD_Polo","fem_cloth.osl",{})
finish(mt,nt,s,o,{"MaskMap":L+"Top_M_rgb.png","IdMap":L+"Top_M_id.png","NormalMap":D+"Top_N.png","Atlas":"/private/tmp/female-soulful-UnityClone/Assets/Resources/Tennis/KitsV2/KitV2_FabricAtlas.png"},tangent=True)
top.data.materials.clear(); top.data.materials.append(mt)
# metres per UV unit on the polo (Unity: _WeaveTile = mpu / tileMetres .034)
me=top.data; uv=me.uv_layers.active.data; tot3=tot2=0
for p in me.polygons:
    for k in range(p.loop_total):
        a=p.loop_start+k; bb=p.loop_start+(k+1)%p.loop_total
        tot3+=(me.vertices[me.loops[a].vertex_index].co-me.vertices[me.loops[bb].vertex_index].co).length
        tot2+=(uv[a].uv-uv[bb].uv).length
mpu=tot3/max(tot2,1e-9); [n for n in mt.node_tree.nodes if n.type=="SCRIPT"][0].inputs["WeaveTile"].default_value=mpu/.034
cam=bpy.data.objects.new("Cam",bpy.data.cameras.new("Cam")); sc.collection.objects.link(cam); sc.camera=cam
bpy.ops.wm.save_as_mainfile(filepath=L+"lookdev.blend")
print("BUILT mpu",mpu)
