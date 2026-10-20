"""blender -b <start.blend> --python apply_coords.py -- coords.npy out.blend [cn_weight.npy]
Writes vertex POSITIONS.  Optional third argument (round 5): a per-vertex weight (0..1, ORIGINAL vertex order) - on the corners of weighted vertices the authored custom-normal OFFSET
is scaled by (1 - w): raw code0 *= (1 - w) (code0 == 0 means 'use the computed loop normal'; code1, the azimuth, is untouched).  Reason (round-5 finding): the offsets were baked on the
ORIGINAL mesh and, where the geometry moved by millimetres, flatten the new under-butt fold shading.  Everything else (UVs, smooth flags, other loops' codes) is untouched."""
import bpy, numpy as np, sys
a=sys.argv[sys.argv.index('--')+1:]
coords=np.load(a[0]); out=a[1]
o=bpy.data.objects['Body_F']; me=o.data
assert len(me.vertices)==len(coords)
me.vertices.foreach_set('co',coords.astype(np.float32).ravel()); me.update()
if len(a)>2:
    w=np.load(a[2]).astype(np.float64); assert len(w)==len(me.vertices)
    attr=me.attributes['custom_normal']; nl=len(me.loops)
    cn=np.empty(nl*2,np.int32); attr.data.foreach_get('value',cn); cn=cn.reshape(-1,2)
    lv=np.empty(nl,np.int32); me.loops.foreach_get('vertex_index',lv)
    new=cn.copy(); new[:,0]=np.round(cn[:,0]*(1.0-w[lv])).astype(np.int32)
    attr.data.foreach_set('value',new.ravel()); me.update()
    print("custom-normal offsets scaled on",int(((new!=cn).any(1)).sum()),"corners")
print("attrs:",sorted(x.name for x in me.attributes))
bpy.ops.wm.save_as_mainfile(filepath=out,copy=False); print("saved",out)
