# lite.py -- <in.fbx> <out.fbx> <sheet.png> : the same kit with its heavy foliage decimated (silhouette kept), same object
# names, materials, UVs and vertex colours; _FAR objects untouched. Also renders original vs lite per decimated object.
import bpy, sys, math, os
a = sys.argv[sys.argv.index('--') + 1:]; src, dst, sheet = a[0], a[1], a[2]
RATIO = {'PINE': .5, 'PALM': .55, 'CONIFER_D': .75, 'CONIFER': .45, 'SHRUB': .6}
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=src)
objs = [o for o in bpy.data.objects if o.type == 'MESH']
def tris(o): o.data.calc_loop_triangles(); return len(o.data.loop_triangles)
report = []
done = []
for o in objs:
    if o.name.endswith('_FAR'): continue
    r = next((v for k, v in RATIO.items() if o.name.startswith(k)), None)
    if r is None or tris(o) < 3000: continue
    before = tris(o)
    orig = o.copy(); orig.data = o.data.copy(); orig.name = o.name + '__ORIG'; bpy.context.scene.collection.objects.link(orig)
    m = o.modifiers.new('lite', 'DECIMATE'); m.decimate_type = 'COLLAPSE'; m.ratio = r; m.use_collapse_triangulate = True
    bpy.context.view_layer.objects.active = o
    for s in bpy.context.view_layer.objects.selected: s.select_set(False)
    o.select_set(True); bpy.ops.object.modifier_apply(modifier='lite')
    report.append((o.name, before, tris(o))); done.append((o, orig))
for n, b, t in report: print('LITE %-14s %6d -> %6d (%.0f%%)' % (n, b, t, 100 * t / b))
# export without the originals
for o, orig in done: orig.hide_set(True); orig.hide_render = True
for s in bpy.context.view_layer.objects.selected: s.select_set(False)
for o in bpy.data.objects:
    if o.type == 'MESH' and not o.name.endswith('__ORIG'): o.select_set(True)
bpy.ops.export_scene.fbx(filepath=dst, use_selection=True, mesh_smooth_type='FACE', add_leaf_bones=False, bake_anim=False)
# render: each decimated object, original left / lite right, from a near (golfer at the tree) and a mid (40 m) camera
scn = bpy.context.scene; scn.render.engine = 'BLENDER_WORKBENCH'; scn.display.shading.light = 'STUDIO'; scn.display.shading.color_type = 'VERTEX' if any(o.data.color_attributes for o, _ in done) else 'MATERIAL'
scn.render.resolution_x, scn.render.resolution_y = 640, 360
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); scn.collection.objects.link(cam); scn.camera = cam
tiles = []
for o, orig in done:
    for x in bpy.data.objects:
        if x.type == 'MESH': x.hide_render = True
    for which, ob in (('orig', orig), ('lite', o)):
        ob.hide_render = False
        ob.location = (0, 0, 0); bb = [ob.matrix_world @ __import__('mathutils').Vector(c) for c in ob.bound_box]
        h = max(v.z for v in bb) - min(v.z for v in bb); cz = (max(v.z for v in bb) + min(v.z for v in bb)) / 2
        for dist, tag in ((h * 1.4, 'near'), (h * 4.5, 'mid')):
            cam.location = (0, -dist, cz); cam.rotation_euler = (math.radians(90), 0, 0); cam.data.lens = 35
            path = os.path.join(os.path.dirname(sheet), f'_{o.name}_{which}_{tag}.png'); scn.render.filepath = path
            bpy.ops.render.render(write_still=True); tiles.append(path)
        ob.hide_render = True
print('TILES', len(tiles))
