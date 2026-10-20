"""blender -b <start.blend> --python apply_coords_plain.py -- coords.npy out.blend
Only vertex positions are written. Normals/attributes/smooth flags are NOT touched (custom normal raw codes stay bit-identical;
their decoded value follows the new geometry because codes are stored relative to the computed loop normal)."""
import bpy, numpy as np, sys
a=sys.argv[sys.argv.index('--')+1:]
coords=np.load(a[0]); out=a[1]
o=bpy.data.objects['Body_F']; me=o.data
assert len(me.vertices)==len(coords)
me.vertices.foreach_set('co',coords.astype(np.float32).ravel()); me.update()
print("attrs:",sorted(x.name for x in me.attributes))
bpy.ops.wm.save_as_mainfile(filepath=out,copy=False); print("saved",out)
