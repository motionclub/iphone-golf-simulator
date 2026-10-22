"""Merge the FEMALE TORSO zone into any HeroBase_Female blend that has the same vertex count/order.

  blender -b <target.blend> --python merge_torso_delta.py -- torso_delta.npz out.blend [--force] [--vmap map.npz]

--vmap: target blend has a different vertex order/count (e.g. the limbs chat's blend). map.npz must hold `base_to_final`
        (start-vertex index -> target index, -1 = vertex no longer exists). Torso vertices mapped to -1 are reported and skipped.

For every torso vertex in torso_delta.npz the target position must still equal the START position
(bit-exact float32) - i.e. no other chat touched that vertex. Conflicting vertices are reported and
SKIPPED (use --force to overwrite them). Nothing else is modified (positions only; custom normals,
UVs, materials, topology, other objects are left alone). Writes out.blend and prints a JSON report."""
import bpy, numpy as np, sys, json
a=sys.argv[sys.argv.index('--')+1:]
dz=np.load(a[0]); out=a[1]; force='--force' in a
vmap=np.load(a[a.index('--vmap')+1])['base_to_final'] if '--vmap' in a else None
o=bpy.data.objects['Body_F']; me=o.data
n=len(me.vertices)
if vmap is None: assert n==int(dz['vertex_count']), f"vertex count mismatch {n} vs {int(dz['vertex_count'])} (use --vmap)"
co=np.empty(n*3,np.float32); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
idx=dz['moved_idx']; start=dz['start_co']; new=dz['new_co']
tidx=idx if vmap is None else vmap[idx]
gone=tidx<0
tsafe=np.where(gone,0,tidx)
same=(co[tsafe]==start).all(1)&~gone
conf=idx[~same]
apply_mask=(same if not force else np.ones(len(idx),bool))&~gone
co[tidx[apply_mask]]=new[apply_mask]
me.vertices.foreach_set('co',co.ravel()); me.update()
rep={'torso_vertices_in_delta':int(len(idx)),'applied':int(apply_mask.sum()),'conflicts(target differs from start)':int((~same).sum()),'forced':bool(force),'vertices_missing_in_target':int(gone.sum()),
     'conflict_vertex_indices_first20':[int(i) for i in conf[:20]]}
print("MERGE_REPORT",json.dumps(rep))
bpy.ops.wm.save_as_mainfile(filepath=out,copy=False)
