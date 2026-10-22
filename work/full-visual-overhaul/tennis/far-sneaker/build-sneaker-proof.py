import bpy, json, sys, hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = Path(__file__).resolve().parent
R = HERE.parents[3]
sys.path.insert(0, str(HERE))
from sealed_far_sneaker import build_sealed_far_sneaker
snapshots, reports = [], []
for sex in ['Male', 'Female']:
    source = R / 'ArtDir/golf/source/gallery3-inputs' / (sex + 'GolfMaster.blend')
    bpy.ops.wm.open_mainfile(filepath=str(source))
    rig = next(ob for ob in bpy.data.objects if ob.type == 'ARMATURE')
    rig.animation_data_clear()
    rig.data.pose_position = 'POSE'
    for bone in rig.pose.bones:
        bone.rotation_mode = 'QUATERNION'
        bone.rotation_quaternion = (1, 0, 0, 0)
        bone.location = (0, 0, 0)
        bone.scale = (1, 1, 1)
    body = next(ob for ob in bpy.data.objects if ob.type == 'MESH' and ob.name.startswith('Body'))
    for mod in body.modifiers:
        if mod.type == 'NODES': mod.show_viewport = False; mod.show_render = False
    bpy.context.view_layer.update()
    deps = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(deps)
    me = ev.to_mesh()
    bvh = BVHTree.FromPolygons([body.matrix_world @ v.co for v in me.vertices],
                               [list(p.vertices) for p in me.polygons])
    ev.to_mesh_clear()
    for side in ['L', 'R']:
        ob = bpy.data.objects['Kit_Shoe_' + side]
        ev = ob.evaluated_get(deps)
        me = ev.to_mesh()
        mesh = bpy.data.meshes.new(sex + '_source_sneaker_' + side)
        mesh.from_pydata([ob.matrix_world @ v.co for v in me.vertices], [],
                         [list(p.vertices) for p in me.polygons])
        mesh.update()
        for mat in me.materials: mesh.materials.append(mat)
        for poly, src in zip(mesh.polygons, me.polygons): poly.material_index = src.material_index
        ev.to_mesh_clear()
        candidate, count, audit = build_sealed_far_sneaker(mesh, bvh, sex + '_sneaker_' + side)
        reports.append({'sex': sex, 'side': side, 'input': str(source.relative_to(R)),
                        'input_sha256': hashlib.sha256(source.read_bytes()).hexdigest(), **audit})
        for label, item in [('SOURCE', mesh), ('FAR', candidate)]:
            snapshots.append({'name': sex + '_' + side + '_' + label,
                              'vertices': [list(v.co) for v in item.vertices],
                              'faces': [list(p.vertices) for p in item.polygons],
                              'roles': [p.material_index for p in item.polygons]})
    print('SNEAKER_DONE', sex, flush=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
materials = []
for name, color in [('Kit_Shoe', (.76, .79, .80, 1)), ('Kit_Sole', (.43, .47, .51, 1))]:
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = color
    mat.use_nodes = True
    mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = color
    mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = .65
    materials.append(mat)
for item in snapshots:
    mesh = bpy.data.meshes.new(item['name'])
    mesh.from_pydata(item['vertices'], [], item['faces'])
    mesh.update()
    for mat in materials: mesh.materials.append(mat)
    for poly, role in zip(mesh.polygons, item['roles']): poly.material_index = role; poly.use_smooth = True
    ob = bpy.data.objects.new(item['name'], mesh)
    bpy.context.collection.objects.link(ob)
    # Left column actual source, right column its sealed 280-triangle LOD.
    bounds = [[min(v.co[i] for v in mesh.vertices), max(v.co[i] for v in mesh.vertices)] for i in range(3)]
    centre = (bounds[0][0] + bounds[0][1]) * .5
    ob.location = Vector(((-.15 if item['name'].endswith('SOURCE') else .15) - centre, 0, -bounds[2][0]))
    ob.hide_render = '_R_' in item['name']
    ob.hide_viewport = '_R_' in item['name']
path = HERE / 'SealedFarSneakers.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(path))
(HERE / 'sneaker-audit.json').write_text(json.dumps({'scope': 'Actual approved fitted source on left; sealed rounded exterior LOD on right. Source preserved.', 'shoes': reports}, indent=2) + '\n')
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
sc.cycles.device = 'CPU'
sc.cycles.samples = 16
sc.cycles.use_denoising = True
sc.render.threads_mode = 'FIXED'
sc.render.threads = 4
sc.render.resolution_x = 900
sc.render.resolution_y = 620
sc.render.resolution_percentage = 100
sc.world = bpy.data.worlds.new('Neutral sneaker studio')
sc.world.use_nodes = True
sc.world.node_tree.nodes['Background'].inputs['Color'].default_value = (.22, .28, .34, 1)
sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value = .5
bpy.ops.object.light_add(type='AREA', location=(1, -1, 2))
bpy.context.object.data.energy = 180
bpy.context.object.data.size = 2
bpy.ops.object.camera_add()
cam = bpy.context.object
cam.data.type = 'ORTHO'
cam.data.ortho_scale = .65
sc.camera = cam
sc.view_settings.view_transform = 'AgX'
for sex in ['Male', 'Female']:
    for ob in bpy.data.objects:
        if ob.type == 'MESH': ob.hide_render = not (ob.name.startswith(sex + '_L_'))
    for label, location, aim in [('threequarter', (.65, -1.1, .72), (0, -.04, .075)),
                                 ('side', (.9, -.65, .18), (0, -.04, .075)),
                                 ('top', (0, -.03, 1), (0, -.03, .05))]:
        cam.location = location
        cam.rotation_euler = (Vector(aim) - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = str(HERE / (sex.lower() + '-' + label + '.png'))
        bpy.ops.render.render(write_still=True)
print('SNEAKER_PROOF_COMPLETE', path, flush=True)
