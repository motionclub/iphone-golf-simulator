"""Merge the FEMALE TORSO zone into any HeroBase_Female blend that has the same vertex count/order.

  blender -b <target.blend> --python merge_torso_delta.py -- torso_delta.npz out.blend [--force] [--vmap map.npz]

--vmap: target blend has a different vertex order/count (e.g. the limbs chat's blend). map.npz must hold `base_to_final`
        (start-vertex index -> target index, -1 = vertex no longer exists). Torso vertices mapped to -1 are reported and skipped.

For every torso vertex in torso_delta.npz the target position must still equal the START position
(bit-exact float32) - i.e. no other chat touched that vertex. Conflicting vertices are reported and
SKIPPED (use --force to overwrite them). Nothing else is modified (positions only; custom normals,
UVs, materials, topology, other objects are left alone). Writes out.blend and prints a JSON report.

ROUND 5: if the delta carries `cn_vertex_weight` (float32 per ORIGINAL vertex) the authored custom-normal OFFSET (raw code0 of the `custom_normal` attribute) is scaled by (1-w) on the corners of the
weighted vertices that were actually moved (code0 == 0 -> computed loop normal; code1 untouched).  Skip it with --no-normals.  Apply ONCE (it is a scaling, not idempotent)."""
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
n_cn=0
if 'cn_vertex_weight' in dz.files and '--no-normals' not in a and 'custom_normal' in me.attributes:
    wo=dz['cn_vertex_weight'].astype(np.float64)                 # weights in ORIGINAL vertex order
    wt=np.zeros(n)                                                # -> target vertex order, only for vertices whose position was applied
    wt[tidx[apply_mask]]=wo[idx[apply_mask]]
    # vertices of the zone that were not moved by the delta but carry weight (smoothing taper): map through the same index map
    allw=np.nonzero((wo>0)&~np.isin(np.arange(len(wo)),idx[~apply_mask]))[0]; ta=allw if vmap is None else vmap[allw]; ok=ta>=0
    extra=ta[ok]; keep=wt[extra]==0
    wt[extra[keep]]=wo[allw[ok]][keep]
    nl=len(me.loops); attr=me.attributes['custom_normal']
    cn=np.empty(nl*2,np.int32); attr.data.foreach_get('value',cn); cn=cn.reshape(-1,2)
    lv=np.empty(nl,np.int32); me.loops.foreach_get('vertex_index',lv)
    new=cn.copy(); new[:,0]=np.round(cn[:,0]*(1.0-wt[lv])).astype(np.int32)
    attr.data.foreach_set('value',new.ravel()); me.update(); n_cn=int(((new!=cn).any(1)).sum())
rep={'torso_vertices_in_delta':int(len(idx)),'applied':int(apply_mask.sum()),'conflicts(target differs from start)':int((~same).sum()),'forced':bool(force),'vertices_missing_in_target':int(gone.sum()),
     'conflict_vertex_indices_first20':[int(i) for i in conf[:20]],'custom_normal_corners_rescaled':n_cn}
print("MERGE_REPORT",json.dumps(rep))
bpy.ops.wm.save_as_mainfile(filepath=out,copy=False)
