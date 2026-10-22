"""Scratch (role A4): build the library and print a markdown table of every kind (verts, faces, tris, size, materials)."""
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/blender/scripts")
import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
import postcard_props_lib as PL
PL.ensure_library()
rep = PL.library_report()
print("| kind | verts | faces | tris | size x*y*z m | materials |")
print("|---|---:|---:|---:|---|---|")
for k in PL.BUILDERS:
    v = rep[k]
    mn, mx = PL.lib_bbox(k)
    d = mx - mn
    print(f"| `{k}` | {v['verts']} | {v['faces']} | {v['tris']} | {d.x:.1f} x {d.y:.1f} x {d.z:.1f} (z {mn.z:.1f}..{mx.z:.1f}) | {', '.join(v['mats'])} |")
