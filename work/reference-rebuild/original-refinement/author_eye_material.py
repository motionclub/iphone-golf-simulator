"""One work-only material A/B on the accepted original-seam geometry.

Eye-local UVs and relative colour maps only. No position, normal, weight,
topology, eye proportion, skin material or rig edits.
"""
import bpy, pathlib, math, json
from mathutils import Vector

R = pathlib.Path.cwd()
O = R / 'work/reference-rebuild/original-refinement'
REPORT = {}

def ss(a,b,x):
    t=max(0,min(1,(x-a)/(b-a)))
    return t*t*(3-2*t)

def pixel(kind,u,v):
    if kind == 'iris':
        r=math.sqrt((2*u-1)**2+(2*v-1)**2)
        middle=math.exp(-((r-.71)/.22)**2)
        outside=ss(.86,1,r)
        # A broad warm mid-ring; no radial spikes, veins or starburst.
        a=.68+.32*middle-.16*outside
        return (a, a*(.91+.09*middle), a*(.82+.18*middle), 1)
    edge=ss(.62,1,abs(2*u-1))
    upper=ss(.40,1,v)
    return (1-.12*edge-.12*upper, 1-.15*edge-.13*upper, 1-.18*edge-.14*upper, 1)

def image(kind):
    size=128
    im=bpy.data.images.new('OriginalEye_'+kind,width=size,height=size,alpha=True)
    im.colorspace_settings.name='Non-Color'
    im.pixels=[c for y in range(size) for x in range(size) for c in pixel(kind,(x+.5)/size,(y+.5)/size)]
    im.pack()
    im.filepath_raw=str(O/f'eye-relative-{kind}.png');im.file_format='PNG';im.save()
    return im

for sex in ('Male','Female'):
    bpy.ops.wm.open_mainfile(filepath=str(O/f'{sex}_OriginalSeamPilot.blend'))
    sc=bpy.context.scene;ob=bpy.data.objects['ReferenceFeatures'];me=ob.data;body=bpy.data.objects['Body']
    oldPositions=[tuple(v.co) for v in me.vertices];oldBody=[tuple(v.co) for v in body.data.vertices]
    uv=me.uv_layers.new(name='OriginalEyeLocal')
    regions={}
    for kind in ('Iris','Sclera'):
        polys=[p for p in me.polygons if kind in me.materials[p.material_index].name]
        for side in (-1,1):
            ps=[p for p in polys if sum(me.vertices[i].co.x for i in p.vertices)*side>0]
            ids={i for p in ps for i in p.vertices}
            c=sum((me.vertices[i].co for i in ids),Vector())/len(ids)
            normal=sum((p.normal*p.area for p in ps),Vector()).normalized()
            if normal.y>0:normal=-normal
            up=Vector((0,0,1));up=(up-normal*up.dot(normal)).normalized();right=up.cross(normal).normalized()
            width=max(abs((me.vertices[i].co-c).dot(right)) for i in ids)
            height=max(abs((me.vertices[i].co-c).dot(up)) for i in ids)
            if kind=='Iris':width=height=max(width,height)
            for p in ps:
                for li in p.loop_indices:
                    d=me.vertices[me.loops[li].vertex_index].co-c
                    uv.data[li].uv=(.5+.5*d.dot(right)/width,.5+.5*d.dot(up)/height)
            regions[f'{kind}_{side}']={'centre':list(c),'right':list(right),'up':list(up),'normal':list(normal),'halfExtent':[width,height],'vertices':len(ids)}
    maps={kind:image(kind) for kind in ('iris','sclera')}
    for m in me.materials:
        p=m.node_tree.nodes.get('Principled BSDF')
        if 'Brow' in m.name:
            p.inputs['Roughness'].default_value=.88;p.inputs['Specular IOR Level'].default_value=.10
        elif 'Iris' in m.name or 'Sclera' in m.name:
            kind='iris' if 'Iris' in m.name else 'sclera'
            base=(.285,.106,.021,1) if kind=='iris' else (.874,.884,.823,1)
            p.inputs['Roughness'].default_value=.10 if kind=='iris' else .20
            tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=maps[kind];tex.interpolation='Linear';tex.extension='EXTEND'
            mult=m.node_tree.nodes.new('ShaderNodeMixRGB');mult.blend_type='MULTIPLY';mult.inputs[0].default_value=1;mult.inputs[1].default_value=base
            m.node_tree.links.new(tex.outputs['Color'],mult.inputs[2]);m.node_tree.links.new(mult.outputs[0],p.inputs['Base Color'])
    assert oldPositions==[tuple(v.co) for v in me.vertices]
    assert oldBody==[tuple(v.co) for v in body.data.vertices]
    sc.unit_settings.system='METRIC';sc.unit_settings.scale_length=1
    bpy.ops.wm.save_as_mainfile(filepath=str(O/f'{sex}_OriginalSeamEyeMaterial.blend'))
    for item in sc.objects:item.select_set(item.name in ('Body','ReferenceFeatures') or item.type=='ARMATURE')
    bpy.context.view_layer.objects.active=body
    bpy.ops.export_scene.fbx(filepath=str(O/f'{sex}_OriginalSeamEyeMaterial.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',use_mesh_modifiers=False,mesh_smooth_type='OFF',add_leaf_bones=False,bake_anim=False,path_mode='STRIP',use_armature_deform_only=False)
    # Same source camera/light recipe as the accepted seam plates.
    eye=sum((Vector(v['centre']) for k,v in regions.items() if k.startswith('Iris')),Vector())/2
    target=eye+Vector((0,0,-.018));cam=sc.camera;sc.cycles.samples=32
    for angle,delta in (('front',(0,-1.1,.015)),('threequarter',(.42,-1.1,.025))):
        cam.location=eye+Vector(delta);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
        sc.render.filepath=str(O/f'{sex.lower()}_eye_material_{angle}.png');bpy.ops.render.render(write_still=True)
    REPORT[sex]={'featureVertices':len(me.vertices),'bodyVertices':len(body.data.vertices),'positionChangeMetres':0,'normalsTopologyWeightsChanged':False,'regions':regions,'maps':['eye-relative-iris.png','eye-relative-sclera.png'],'source':str(O/f'{sex}_OriginalSeamEyeMaterial.blend')}
    (O/'eye-material-manifest.json').write_text(json.dumps(REPORT,indent=2))
    print('ORIGINAL_EYE_MATERIAL',sex,'position_change=0','UV+albedo+roughness only')
