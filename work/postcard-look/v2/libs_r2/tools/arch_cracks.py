"""Boundary-edge (crack) analysis of the DRESS_ARCH meshes of a blend. usage: Blender -b --factory-startup --python arch_cracks.py -- BLEND"""
import sys, collections
import bpy, bmesh
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
for ob in bpy.data.objects:
    if ob.type != 'MESH' or not ob.name.startswith("DRESS_ARCH"):
        continue
    me = ob.data
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bm.edges.ensure_lookup_table()
    bnd = [e for e in bm.edges if len(e.link_faces) == 1]
    nm = [e for e in bm.edges if len(e.link_faces) > 2]
    print("ARCH", ob.name, "faces", len(bm.faces), "verts", len(bm.verts), "edges", len(bm.edges), "boundary", len(bnd), "nonmanifold(>2)", len(nm))
    L = [e.calc_length() for e in bnd]
    # classify: base (z<0.02), else
    base = [e for e in bnd if max(v.co.z for v in e.verts) < 0.02]
    other = [e for e in bnd if e not in base]
    print("  boundary at z<0.02:", len(base), " other:", len(other), " other total length m: %.2f" % sum(e.calc_length() for e in other))
    # cluster others by facing: report the biggest ones
    other.sort(key=lambda e: -e.calc_length())
    for e in other[:25]:
        a_, b_ = e.verts[0].co, e.verts[1].co
        print("   len %.3f  (%.3f,%.3f,%.3f)->(%.3f,%.3f,%.3f)" % (e.calc_length(), a_.x, a_.y, a_.z, b_.x, b_.y, b_.z))
    # tiny faces
    areas = sorted(f.calc_area() for f in bm.faces)
    print("  min face areas:", [round(x, 6) for x in areas[:8]], " faces < 1 cm2:", sum(1 for x in areas if x < 1e-4), " < 3 cm2:", sum(1 for x in areas if x < 3e-4))
    bm.free()
