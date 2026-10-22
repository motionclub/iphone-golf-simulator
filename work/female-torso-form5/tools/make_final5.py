"""Build the FORM5 deliverable.   python3 tools/make_final5.py [P5_final.json] [P_glute4.json] [PP5_final.json]
 -> data/co_FORM5_final.npy, export/HeroBase_Female_torso_form5_candidate.blend (positions only, applied to START_form4_candidate.blend),
    export/torso_form5_delta.npz (relative to the ORIGINAL ArtDir 200dc3b9, documented mask zone5 = chat-7 zone + LEG-TOP extension),
    audit/form5.npz|json, export/form5_checks.json (audit numbers consumed by gates5.py)"""
import sys, json, subprocess, hashlib, shutil, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import torso4 as t4
from torso4 import CO0, T, BORDER, CLS, TRI, EA, EB, N
import torso2 as t2
import build5, seam, rough

WD = t2.WD
B = '/Applications/Blender.app/Contents/MacOS/Blender'
ROOT = WD.parent.parent
ARTDIR_BLEND = ROOT / 'ArtDir/hero/base_lock/blender/HeroBase_Female.blend'
START = WD / 'START_form4_candidate.blend'
pc = sys.argv[1] if len(sys.argv) > 1 else str(WD / 'data/P5_final.json')
pg = sys.argv[2] if len(sys.argv) > 2 else str(WD / 'data/P_glute4.json')
pp = sys.argv[3] if len(sys.argv) > 3 else str(WD / 'data/PP5_final.json')
PC, PG, PP = json.load(open(pc)), json.load(open(pg)), json.load(open(pp))
shutil.copy(pc, WD / 'export/form5_params_chest.json'); shutil.copy(pg, WD / 'export/form5_params_glute.json'); shutil.copy(pp, WD / 'export/form5_params_pelvis.json')
Z5 = np.load(WD / 'data/zone5.npz'); T5 = Z5['torso']; BORDER5 = Z5['border5']; EXT = Z5['ext']; RING = Z5['ring']
co, parts = build5.build_final5(PC, PG, PP, return_parts=True)
assert np.isfinite(co).all()
np.save(WD / 'data/co_FORM5_final.npy', co)
np.save(WD / 'export/form5_wall_corrections.npy', np.stack([parts['dFc'], parts['dBc'], parts['dFg'], parts['dBg']]))
out_blend = str(WD / 'export/HeroBase_Female_torso_form5_candidate.blend')
import cnweight5
CNW = cnweight5.cn_weight(co).astype(np.float32); np.save(WD / 'data/cn_weight_FORM5.npy', CNW)
r = subprocess.run([B, '-b', str(START), '--python', str(WD / 'tools/apply_coords.py'), '--', str(WD / 'data/co_FORM5_final.npy'), out_blend, str(WD / 'data/cn_weight_FORM5.npy')], capture_output=True, text=True)
assert 'saved' in r.stdout, r.stdout[-500:]
r = subprocess.run([B, '-b', out_blend, '--python', str(WD / 'tools/dump_blend.py'), '--', str(WD / 'audit/form5.npz')], capture_output=True, text=True)
assert 'dumped' in r.stdout
A = np.load(WD / 'audit/form4.npz'); Bz = np.load(WD / 'audit/form5.npz'); AD = np.load(WD / 'audit/artdir.npz')
ma = json.load(open(WD / 'audit/form4.json')); mb = json.load(open(WD / 'audit/form5.json'))
co0 = A['Body_F/co']; co1 = Bz['Body_F/co']; orig32 = AD['Body_F/co']
assert np.array_equal(orig32, np.load(WD / 'data/orig.npz')['co'].astype(np.float32))
moved = (co0 != co1).any(1); moved_o = (orig32 != co1).any(1)
res = {'moved_vs_form4_start': int(moved.sum()), 'moved_outside_zone5_vs_form4_start': int((moved & ~T5).sum()), 'moved_vs_artdir_200dc3b9': int(moved_o.sum()),
       'moved_outside_zone5_vs_artdir_200dc3b9': int((moved_o & ~T5).sum()), 'border5_vertices': int(BORDER5.sum()), 'border5_vertices_moved_vs_artdir': int((moved_o & BORDER5).sum()),
       'border5_vertices_moved_vs_form4_start': int((moved & BORDER5).sum()), 'zone5_vertices': int(T5.sum()), 'old_zone_vertices': int(T.sum()), 'legtop_extension_vertices': int(EXT.sum()),
       'legtop_floor_ring_vertices': int(RING.sum()), 'old_class1_border_now_interior': int((BORDER & (CLS == 1)).sum()), 'nan_or_inf': int((~np.isfinite(co1)).sum())}
keys = ('poly_start', 'poly_total', 'loop_vert', 'edges', 'mat_index', 'smooth', 'custom_normal_raw')
lvv = A['Body_F/loop_vert']; wl = CNW[lvv] > 0                                   # corners whose authored normal OFFSET was rescaled (round 5, disclosed)
topo = {k: bool(np.array_equal(A[f'Body_F/{k}'], Bz[f'Body_F/{k}'])) for k in keys if k != 'custom_normal_raw'}
topo.update({k + '_vs_artdir': bool(np.array_equal(AD[f'Body_F/{k}'], Bz[f'Body_F/{k}'])) for k in keys if k != 'custom_normal_raw'})
for ref, nm in ((A, ''), (AD, '_vs_artdir')):
    cr0, cr1 = ref['Body_F/custom_normal_raw'], Bz['Body_F/custom_normal_raw']
    topo['custom_normal_raw_identical_outside_weighted_corners' + nm] = bool(np.array_equal(cr0[~wl], cr1[~wl]))
    topo['custom_normal_raw_changed_corners' + nm] = int((cr0 != cr1).any(1).sum())
    topo['custom_normal_raw_code1_untouched' + nm] = bool(np.array_equal(cr0[:, 1], cr1[:, 1]))
topo['custom_normal_weighted_corners'] = int(wl.sum()); topo['custom_normal_weighted_vertices'] = int((CNW > 0).sum())
topo['custom_normal_raw'] = topo['custom_normal_raw_identical_outside_weighted_corners'] and topo['custom_normal_raw_code1_untouched']   # kept key: 'identical except the disclosed offset rescale'
topo['custom_normal_raw_vs_artdir'] = topo['custom_normal_raw_identical_outside_weighted_corners_vs_artdir'] and topo['custom_normal_raw_code1_untouched_vs_artdir']
topo['uv'] = bool(np.array_equal(A['Body_F/uv/UVMap'], Bz['Body_F/uv/UVMap'])); topo['hair_identical'] = bool(np.array_equal(A['Hair_F/co'], Bz['Hair_F/co']))
topo['tris_form4_start_vs_new'] = [ma['objects'][0]['tris'], mb['objects'][0]['tris']]
other = {}
for oa, ob in zip(ma['objects'], mb['objects']):
    other[oa['name'] + '_matrix_identical'] = bool(oa['matrix_world'] == ob['matrix_world']); other[oa['name'] + '_materials_identical'] = bool(oa.get('materials') == ob.get('materials'))
topo['other_objects_identical'] = all(other.values())
res['topology'] = topo; res['topology_detail_other'] = other
mi = np.where(moved_o)[0]
np.savez_compressed(WD / 'export/torso_form5_delta.npz', moved_idx=mi.astype(np.int32), start_co=orig32[mi], new_co=co1[mi], zone_mask=T5, border_mask=BORDER5, vertex_count=np.int32(len(co1)), cn_vertex_weight=CNW)
res['delta_moved_vertices'] = int(len(mi))
tri = TRI
def fn(c):
    v0, v1, v2 = c[tri[:, 0]], c[tri[:, 1]], c[tri[:, 2]]; n = np.cross(v1 - v0, v2 - v0); return n / np.maximum(np.linalg.norm(n, axis=1), 1e-18)[:, None]
zt = T5[tri].any(1); dot = (fn(CO0) * fn(co1.astype(np.float64))).sum(1)
res['flipped_zone5_tris_vs_original'] = int(((dot < 0) & zt).sum()); res['zone5_tris_turned_gt60deg'] = int(((dot < 0.5) & zt).sum())
res['max_vertex_move_mm_vs_original'] = float(np.linalg.norm(co1.astype(np.float64) - CO0, axis=1).max() * 1000)
c4 = np.load(WD / 'data/co_FORM4_final.npy').astype(np.float64); c1 = co1.astype(np.float64)
# dihedral stats on the zone5 interior edges (+ region-specific numbers are done in gates5)
ZP5 = T5[seam.PAIR_E[:, 0]] & T5[seam.PAIR_E[:, 1]]
def dstats(c):
    a = seam.dihedral(c)[ZP5]; return {'edges': int(ZP5.sum()), 'mean_deg': float(a.mean()), 'p95_deg': float(np.percentile(a, 95)), 'max_deg': float(a.max()), 'n_gt30': int((a > 30).sum()), 'n_gt40': int((a > 40).sum())}
res['dihedral'] = {'original': dstats(CO0), 'form4': dstats(c4), 'form5': dstats(c1)}
# border steps on the NEW border (floor ring = 'legs', old arm/top classes)
def steps(c):
    d = np.linalg.norm(c - CO0, axis=1) * 1000
    e = (T5[EA] & T5[EB]) & (BORDER5[EA] ^ BORDER5[EB]); st = np.abs(d[EA] - d[EB])[e]
    cls = np.where(BORDER5[EA], np.where(RING[EA], 1, CLS[EA]), np.where(RING[EB], 1, CLS[EB]))[e]
    return {n: {'max_mm': float(st[cls == k].max()) if (cls == k).any() else 0.0, 'p95_mm': float(np.percentile(st[cls == k], 95)) if (cls == k).any() else 0.0} for k, n in ((1, 'legs_floor'), (2, 'arm'), (3, 'top'))}
res['border_steps_mm'] = {'form5': steps(c1), 'form4': steps(c4)}
nb = np.zeros(N, bool); m = BORDER5[EA]; nb[EB[m]] = True; m = BORDER5[EB]; nb[EA[m]] = True
inner = T5 & ~BORDER5 & ~nb
rn = {k: rough.second_diff_noise(v) for k, v in (('original', CO0), ('form4', c4), ('form5', c1))}
res['bi_laplacian_roughness_mm_zone5_interior'] = {k: {'mean': float(v[inner].mean() * 1000), 'p95': float(np.percentile(v[inner], 95) * 1000), 'max': float(v[inner].max() * 1000)} for k, v in rn.items()}
si = {}
for tag, bl in (('original', str(ARTDIR_BLEND)), ('form4', str(START)), ('form5', out_blend)):
    jp = WD / f'audit/selfint5_{tag}.json'
    r = subprocess.run([B, '-b', bl, '--python', str(WD / 'tools/selfint.py'), '--', str(jp), str(WD / 'data/zone5.npz')], capture_output=True, text=True)
    assert 'SELFINT' in r.stdout, r.stdout[-400:]
    j = json.load(open(jp)); si[tag] = {'whole_mesh': j['intersecting_pairs_whole_mesh'], 'touching_zone5': j['intersecting_pairs_touching_torso_zone']}
res['self_intersection_pairs'] = si
nf = {}
for tag, bl in (('original', str(ARTDIR_BLEND)), ('form4', str(START)), ('form5', out_blend)):
    jp = WD / f'audit/normals5_{tag}.json'
    r = subprocess.run([B, '-b', bl, '--python', str(WD / 'tools/normals_check.py'), '--', str(jp), str(WD / 'data/zone5.npz')], capture_output=True, text=True)
    assert 'NORMALS_OK' in r.stdout, r.stdout[-400:]
    nf[tag] = json.load(open(jp))
res['custom_normals_vs_geometry_deg_zone5'] = nf
json.dump(res, open(WD / 'export/form5_checks.json', 'w'), indent=1)
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
print(json.dumps({k: res[k] for k in ('moved_outside_zone5_vs_form4_start', 'moved_outside_zone5_vs_artdir_200dc3b9', 'border5_vertices_moved_vs_artdir', 'delta_moved_vertices', 'flipped_zone5_tris_vs_original', 'zone5_tris_turned_gt60deg', 'max_vertex_move_mm_vs_original', 'self_intersection_pairs', 'custom_normals_vs_geometry_deg_zone5')}, indent=1))
print('border steps', res['border_steps_mm']['form5']); print('topology', topo)
print('SHA blend', sha(out_blend)[:16], 'delta', sha(str(WD / 'export/torso_form5_delta.npz'))[:16], 'artdir', sha(str(ARTDIR_BLEND))[:16])
