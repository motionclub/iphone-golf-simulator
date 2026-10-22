"""blender -b --factory-startup --python probe_normals.py -- in.blend  : do authored custom normals exist on Body_F, and how far are they from geometry-only normals in the lower face?"""
import sys, bpy, numpy as np
inb = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.open_mainfile(filepath=inb)
ob = bpy.data.objects['Body_F']; me = ob.data
print('has_custom_normals', me.has_custom_normals, 'verts', len(me.vertices), 'loops', len(me.loops), 'polys', len(me.polygons))
print('attributes', [(a.name, a.domain, a.data_type) for a in me.attributes])
n = len(me.vertices)
V = np.empty(n * 3); me.vertices.foreach_get('co', V); V = V.reshape(-1, 3)
L = len(me.loops)
cn = np.empty(L * 3); me.corner_normals.foreach_get('vector', cn); cn = cn.reshape(-1, 3)   # effective (authored if present) corner normals
lv = np.empty(L, dtype=np.int32); me.loops.foreach_get('vertex_index', lv)
vn = np.empty(n * 3); me.vertices.foreach_get('normal', vn); vn = vn.reshape(-1, 3)         # geometry-only vertex normals
dot = np.einsum('ij,ij->i', cn, vn[lv]); ang = np.degrees(np.arccos(np.clip(dot, -1, 1)))
sel = (V[lv, 2] > 1.43) & (V[lv, 2] < 1.52) & (np.abs(V[lv, 0]) < 0.09) & (V[lv, 1] < -0.02)
print('lower-face loops', int(sel.sum()), ' angle(corner normal, geometry vertex normal) deg: mean %.2f p90 %.2f max %.2f' % (ang[sel].mean(), np.percentile(ang[sel], 90), ang[sel].max()))
allh = V[lv, 2] > 1.40
print('all head loops', int(allh.sum()), ' mean %.2f p90 %.2f p99 %.2f max %.2f' % (ang[allh].mean(), np.percentile(ang[allh], 90), np.percentile(ang[allh], 99), ang[allh].max()))
# per vertex: spread of corner normals (split normals?)
order = np.argsort(lv, kind='stable'); lv_s = lv[order]; cn_s = cn[order]
starts = np.r_[0, np.where(np.diff(lv_s) != 0)[0] + 1]
spread = np.zeros(n)
for a, b in zip(starts, np.r_[starts[1:], L]):
    c = cn_s[a:b]
    if len(c) > 1:
        m = c.mean(0); m /= max(np.linalg.norm(m), 1e-12)
        spread[lv_s[a]] = np.degrees(np.arccos(np.clip(c @ m, -1, 1))).max()
ss = (V[:, 2] > 1.43) & (V[:, 2] < 1.52) & (np.abs(V[:, 0]) < 0.09) & (V[:, 1] < -0.02)
print('lower-face verts with split normals >0.5 deg spread:', int((spread[ss] > 0.5).sum()), 'of', int(ss.sum()), ' max spread', spread[ss].max())
np.savez(sys.argv[sys.argv.index('--') + 2] if len(sys.argv) > sys.argv.index('--') + 2 else '/dev/null', lv=lv, ang=ang, spread=spread)
