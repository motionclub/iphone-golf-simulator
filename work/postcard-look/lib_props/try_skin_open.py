"""Scratch (A4): build_basalt_skin with an open polyline, check every column stays inside (left of) the polyline."""
import sys, math
sys.dont_write_bytecode = True
sys.path.insert(0, "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/blender/scripts")
import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
import postcard_props_lib as PL
loop = [(10 * math.cos(a), 10 * math.sin(a)) for a in [i * math.tau / 48 for i in range(48)]]
c = PL.build_basalt_skin(None, loop, 6.0, -2.0, seed=1)
o = PL.build_basalt_skin(None, loop[:20], 6.0, -2.0, seed=2, closed=False, name="ROCK_SKIN_OPEN")
for name, objs in (("closed", c), ("open", o)):
    rmax = max(math.hypot(*(ob.matrix_world @ v.co).xy) for ob in objs for v in ob.data.vertices)
    zmax = max((ob.matrix_world @ v.co).z for ob in objs for v in ob.data.vertices)
    print(f"GATE: SKIN_{name.upper()}_INSIDE {'PASS' if rmax <= 10.0 and zmax <= 6.0 + 1e-6 else 'FAIL'} {len(objs)} objects, "
          f"{sum(len(ob.data.polygons) for ob in objs)} faces, max radius {rmax:.2f} m (outline 10 m, polygon inscribed), max z {zmax:.2f}")
