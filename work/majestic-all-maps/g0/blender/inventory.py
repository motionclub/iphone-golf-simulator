# inventory.py -- <fbx>... : triangle count per mesh object of each FBX (read only)
import bpy, sys
args = sys.argv[sys.argv.index('--') + 1:]
for f in args:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=f)
    rows = []
    for o in bpy.data.objects:
        if o.type != 'MESH': continue
        me = o.data; me.calc_loop_triangles()
        rows.append((len(me.loop_triangles), o.name))
    rows.sort(reverse=True)
    print('==', f.split('/')[-1], 'objects', len(rows), 'total', sum(r[0] for r in rows))
    for t, n in rows[:30]: print('  %7d  %s' % (t, n))
