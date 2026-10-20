"""Merge the FEMALE ARMS zone (chat B, work/female-arms-form2) into a HeroBase_Female blend.

  blender -b <target.blend> --python merge_arms_delta.py -- arms_delta.npz out.blend [--order base|limbs] [--force]

--order limbs (default): target has the limbs-chat vertex order (22,419 verts: HeroBase_Female_limbs.blend, torso+limbs preview).
--order base           : target has the ArtDir/start vertex order (22,444 verts: HeroBase_Female.blend, torso candidate).
                         Arm vertices all exist in both orders (they were not touched by the limbs chat).

Every moved arm vertex must still be at its START position in the target (bit-exact float32); conflicts are reported and
skipped (--force overwrites). Positions only: custom normals, UVs, materials, topology, other objects untouched."""
import bpy, numpy as np, sys, json
a=sys.argv[sys.argv.index('--')+1:]
dz=np.load(a[0]); out=a[1]; force='--force' in a
order=a[a.index('--order')+1] if '--order' in a else 'limbs'
idx=dz['moved_idx_limbs_order'] if order=='limbs' else dz['moved_idx_base_order']
need=int(dz['vertex_count_limbs_order'] if order=='limbs' else dz['vertex_count_base_order'])
o=bpy.data.objects['Body_F']; me=o.data; n=len(me.vertices)
assert n==need, f"vertex count mismatch {n} vs {need} for --order {order}"
co=np.empty(n*3,np.float32); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
start=dz['start_co']; new=dz['new_co']
same=(co[idx]==start).all(1)
ok=np.ones(len(idx),bool) if force else same
co[idx[ok]]=new[ok]
me.vertices.foreach_set('co',co.ravel()); me.update()
rep={'arm_vertices_in_delta':int(len(idx)),'applied':int(ok.sum()),'conflicts':int((~same).sum()),'forced':force,'order':order,'conflict_idx_first20':[int(i) for i in idx[~same][:20]]}
print("MERGE_REPORT",json.dumps(rep))
bpy.ops.wm.save_as_mainfile(filepath=out,copy=False)
