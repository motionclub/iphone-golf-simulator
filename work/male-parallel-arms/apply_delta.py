"""blender -b <src.blend> --python apply_delta.py -- <delta.npz> <out.blend> [--allow-base-mismatch]
Applies a zone delta (indices, base, new) to src: requires src coords at those indices == delta base (i.e. nobody else touched them)."""
import bpy, sys, numpy as np
a=sys.argv[sys.argv.index('--')+1:]
d=np.load(a[0]); idx=d['indices']; base=d['base'].astype(np.float32); new=d['new'].astype(np.float32); out=a[1]
me=bpy.data.objects['Body_M'].data; n=len(me.vertices)
V=np.zeros(n*3,dtype=np.float32); me.vertices.foreach_get('co',V); V=V.reshape(-1,3)
mis=(V[idx]!=base).any(1).sum()
print('BASE_MISMATCH',int(mis))
if mis and '--allow-base-mismatch' not in a: raise SystemExit('refusing: %d delta vertices were modified by someone else'%mis)
V[idx]=new
me.vertices.foreach_set('co',V.ravel()); me.update()
bpy.ops.wm.save_as_mainfile(filepath=out,copy=False)
print('WROTE',out,len(idx))
