import bpy, numpy as np, sys, pickle
def load(p):
    bpy.ops.wm.open_mainfile(filepath=p); me = bpy.data.objects['Body_M'].data
    V = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', V); return V.reshape(-1, 3), [list(p.vertices) for p in me.polygons]
A, FA = load('baseline/HeroBase_Male_Silhouette.blend'); B, FB = load('baseline/artdir_current_4287ba52.blend')
np.savez('baseline/artdir_current_mesh.npz', co=B); pickle.dump(FB, open('baseline/artdir_current_faces.pkl', 'wb'))
print('verts', len(A), len(B), 'polys', len(FA), len(FB))
def xlim(z): return np.where(z < 1.20, 0.205, np.where(z < 1.24, 0.205 + (z - 1.20) / 0.04 * 0.075, 0.28))
z = A[:, 2]; Zm = (z >= 0.77) & (z < 1.40) & (np.abs(A[:, 0]) <= xlim(z)); zi = np.where(Zm)[0]
n = len(A)
Bn = B[:n]
mv = np.any(A != Bn, axis=1)
print('first-n index compare: moved', int(mv.sum()), 'in torso zone', int((mv & Zm).sum()), 'outside', int((mv & ~Zm).sum()))
print('torso-zone verts identical by index:', bool(np.all(A[zi] == B[zi])), 'count', len(zi))
# faces: first-n identical?
same_faces = sum(1 for f, g in zip(FA, FB) if f == g)
print('polys identical by index (first %d):' % len(FA), same_faces, 'of', len(FA))
# which faces differ and do they touch zone verts?
diff_f = [i for i, (f, g) in enumerate(zip(FA, FB)) if f != g]
touchzone = sum(1 for i in diff_f if any(Zm[v] for v in FA[i] if v < n))
print('differing polys', len(diff_f), 'touching old zone verts', touchzone)
if mv.any():
    P = A[mv]; print('moved bbox x %.3f..%.3f y %.3f..%.3f z %.3f..%.3f' % (P[:,0].min(), P[:,0].max(), P[:,1].min(), P[:,1].max(), P[:,2].min(), P[:,2].max()))
    ax = np.abs(P[:, 0]); print('  hand/forearm-like (|x|>0.44):', int((ax > 0.44).sum()), 'of', len(P))
extra = B[n:]; print('extra verts', len(extra), 'bbox x %.3f..%.3f z %.3f..%.3f' % (extra[:,0].min(), extra[:,0].max(), extra[:,2].min(), extra[:,2].max()) if len(extra) else '')
