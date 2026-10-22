"""Dump a geometry fingerprint of every library mesh (positions, faces, UV, material slots, smooth flags), colours EXCLUDED.
usage: blender -b --factory-startup --python geom_baseline.py -- OUT.json"""
import sys, os, json, hashlib
import numpy as np
sys.dont_write_bytecode = True
HERE = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "..", "..", "blender", "scripts"))
sys.path.insert(0, HERE)
import bpy
import postcard_props_lib as PL
bpy.ops.wm.read_factory_settings(use_empty=True)
PL.write_plants_atlas  # noqa (do not write: only read)
lib = PL.ensure_library()
for k in ("ROCK_BOULDER_A_WET", "ROCK_SLAB_A_WET", "ROCK_BLOCK_A_BASALT", "ROCK_BOULDER_B_BASALT", "ROCK_SEASTACK_A_WET", "ROCK_SEASTACK_C_BASALT"):
    lib[k] = PL.library_object(k)
out = {}
for k, ob in sorted(lib.items()):
    me = ob.data
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get("co", co)
    polys = [tuple(p.vertices) for p in me.polygons]
    mi = np.empty(len(me.polygons), np.int32); me.polygons.foreach_get("material_index", mi)
    sm = np.empty(len(me.polygons), np.int8); me.polygons.foreach_get("use_smooth", sm)
    uv = PL.__dict__.get("_x")  # placeholder
    lay = me.uv_layers.active
    u = np.empty(len(me.loops) * 2)
    try: lay.uv.foreach_get("vector", u)
    except Exception: lay.data.foreach_get("uv", u)
    h = hashlib.sha256()
    h.update(np.round(co, 6).tobytes()); h.update(str(polys).encode()); h.update(mi.tobytes()); h.update(sm.tobytes()); h.update(np.round(u, 6).tobytes())
    h.update(str([m.name for m in me.materials]).encode())
    out[k] = dict(sha=h.hexdigest(), verts=len(me.vertices), faces=len(me.polygons))
json.dump(out, open(sys.argv[sys.argv.index("--") + 1], "w"), indent=1)
print("wrote", len(out), "meshes")
