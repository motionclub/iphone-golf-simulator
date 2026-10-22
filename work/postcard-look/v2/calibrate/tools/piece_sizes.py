import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
Y = 1.0936
rows = []
for o in bpy.data.objects:
    if o.type != 'MESH' or not o.name.startswith('ROCK_'): continue
    ws = [o.matrix_world @ Vector(c) for c in o.bound_box]
    xs = [w.x for w in ws]; ys = [w.y for w in ws]; zs = [w.z for w in ws]
    ex, ey = (max(xs) - min(xs)) * Y, (max(ys) - min(ys)) * Y
    rows.append((o.name, max(ex, ey), (max(zs) - min(zs)) * Y, len(o.data.polygons)))
rows.sort(key=lambda r: -r[1])
print("ROCK_ objects: %d; widest bounds (yd): %s" % (len(rows), ", ".join("%s %.1f" % (r[0], r[1]) for r in rows[:8])))
sk = [r for r in rows if r[0].startswith('ROCK_SKIN')]
print("ROCK_SKIN pieces: %d, widest %.1f yd, median %.1f yd, tris-ish faces total %d" % (len(sk), sk[0][1] if sk else 0, sorted(r[1] for r in sk)[len(sk)//2] if sk else 0, sum(r[3] for r in sk)))
print("pieces wider than 24 yd: %d" % sum(1 for r in rows if r[1] > 24))
