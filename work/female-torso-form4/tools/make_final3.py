"""Build the FORM3 deliverable from a full parameter JSON (written by rung.run_g / data/P_*.json):
   python3 tools/make_final3.py data/P_final.json
 -> data/co_FORM3_final.npy, export/HeroBase_Female_torso_form3_candidate.blend, export/torso_form3_delta.npz (relative to the ORIGINAL ArtDir start 200dc3b9),
    audit/form3.npz|json, export/form3_checks.json (audit numbers consumed by gates3.py)"""
import sys, json, subprocess, hashlib, shutil
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-torso-form4/tools')
from torso3 import *
import torso2 as t2
import seam, rough

B = '/Applications/Blender.app/Contents/MacOS/Blender'
ROOT = WD.parent.parent
ARTDIR_BLEND = ROOT / 'ArtDir/hero/base_lock/blender/HeroBase_Female.blend'
pj = sys.argv[1] if len(sys.argv) > 1 else str(WD / 'data/P_final.json')
P = json.load(open(pj))
shutil.copy(pj, WD / 'export/form3_params.json')
json.dump({**DEFAULT3, **P}, open(WD / 'export/form3_params_full.json', 'w'), indent=1, default=float)   # effective parameters incl. defaults of tools/torso3.py
dF, dB = fit_walls(P, iters=4, verbose=False, zlo=0.82, zhi=1.30, fz=(0.82, 1.12), bz=(0.82, 1.30))
co = build3(P, dF, dB)
assert np.isfinite(co).all()
np.save(WD / 'data/co_FORM3_final.npy', co)
np.save(WD / 'export/form3_wall_corrections.npy', np.stack([dF, dB]))
out_blend = str(WD / 'export/HeroBase_Female_torso_form3_candidate.blend')
r = subprocess.run([B, '-b', str(WD / 'START_form2_candidate.blend'), '--python', str(WD / 'tools/apply_coords.py'), '--', str(WD / 'data/co_FORM3_final.npy'), out_blend], capture_output=True, text=True)
assert 'saved' in r.stdout, r.stdout[-500:]
r = subprocess.run([B, '-b', out_blend, '--python', str(WD / 'tools/dump_blend.py'), '--', str(WD / 'audit/form3.npz')], capture_output=True, text=True)
assert 'dumped' in r.stdout
if not (WD / 'audit/artdir.npz').exists():
    r = subprocess.run([B, '-b', str(ARTDIR_BLEND), '--python', str(WD / 'tools/dump_blend.py'), '--', str(WD / 'audit/artdir.npz')], capture_output=True, text=True)
    assert 'dumped' in r.stdout
A = np.load(WD / 'audit/start_form2.npz'); Bz = np.load(WD / 'audit/form3.npz'); AD = np.load(WD / 'audit/artdir.npz')
ma = json.load(open(WD / 'audit/start_form2.json')); mb = json.load(open(WD / 'audit/form3.json')); mad = json.load(open(WD / 'audit/artdir.json'))
co0 = A['Body_F/co']; co1 = Bz['Body_F/co']; orig32 = AD['Body_F/co']
assert np.array_equal(orig32, np.load(WD / 'data/orig.npz')['co'].astype(np.float32))
moved = (co0 != co1).any(1); moved_o = (orig32 != co1).any(1)
res = {'moved_vs_form2_start': int(moved.sum()), 'moved_outside_zone_vs_form2_start': int((moved & ~T).sum()), 'moved_vs_artdir_200dc3b9': int(moved_o.sum()),
       'moved_outside_zone_vs_artdir_200dc3b9': int((moved_o & ~T).sum()), 'border_vertices': int(BORDER.sum()), 'border_vertices_moved_vs_artdir': int((moved_o & BORDER).sum()),
       'border_vertices_moved_vs_form2_start': int((moved & BORDER).sum()), 'zone_vertices': int(T.sum()), 'nan_or_inf': int((~np.isfinite(co1)).sum())}
topo = {k: bool(np.array_equal(A[f'Body_F/{k}'], Bz[f'Body_F/{k}'])) for k in ('poly_start', 'poly_total', 'loop_vert', 'edges', 'mat_index', 'smooth', 'custom_normal_raw')}
topo.update({k + '_vs_artdir': bool(np.array_equal(AD[f'Body_F/{k}'], Bz[f'Body_F/{k}'])) for k in ('poly_start', 'poly_total', 'loop_vert', 'edges', 'mat_index', 'smooth', 'custom_normal_raw')})
topo['uv'] = bool(np.array_equal(A['Body_F/uv/UVMap'], Bz['Body_F/uv/UVMap'])); topo['hair_identical'] = bool(np.array_equal(A['Hair_F/co'], Bz['Hair_F/co']))
topo['tris_form2_start_vs_new'] = [ma['objects'][0]['tris'], mb['objects'][0]['tris']]
other = {}
for oa, ob in zip(ma['objects'], mb['objects']):
    other[oa['name'] + '_matrix_identical'] = bool(oa['matrix_world'] == ob['matrix_world'])
    other[oa['name'] + '_materials_identical'] = bool(oa.get('materials') == ob.get('materials'))
topo['other_objects_identical'] = all(other.values())
res['topology'] = topo
res['topology_detail_other'] = other
mi = np.where(moved_o)[0]
np.savez_compressed(WD / 'export/torso_form3_delta.npz', moved_idx=mi.astype(np.int32), start_co=orig32[mi], new_co=co1[mi], zone_mask=T, vertex_count=np.int32(len(co1)))
res['delta_moved_vertices'] = int(len(mi))
tri = TRI
def fn(c):
    v0, v1, v2 = c[tri[:, 0]], c[tri[:, 1]], c[tri[:, 2]]; n = np.cross(v1 - v0, v2 - v0); return n / np.maximum(np.linalg.norm(n, axis=1), 1e-18)[:, None]
zt = T[tri].any(1); dot = (fn(CO0) * fn(co1.astype(np.float64))).sum(1)
res['flipped_zone_tris_vs_original'] = int(((dot < 0) & zt).sum()); res['zone_tris_turned_gt60deg'] = int(((dot < 0.5) & zt).sum())
res['max_vertex_move_mm_vs_original'] = float(np.linalg.norm(co1.astype(np.float64) - CO0, axis=1).max() * 1000)
f2 = np.load(WD / 'data/co_start_f2.npy'); c7 = np.load(WD / 'data/co_chat7.npy')
res['dihedral'] = {'original': seam.stats(CO0), 'chat7': seam.stats(c7), 'form2': seam.stats(f2), 'form3': seam.stats(co1.astype(np.float64))}
res['border_steps_mm'] = {'form3': seam.border_steps(co1.astype(np.float64))[0], 'form2': seam.border_steps(f2)[0]}
inner = T & (D_ARM > 0.012) & (D_LEG > 0.012) & (D_TOP > 0.012)
rn = {k: rough.second_diff_noise(v) for k, v in (('original', CO0), ('chat7', c7), ('form2', f2), ('form3', co1.astype(np.float64)))}
res['bi_laplacian_roughness_mm_zone_interior'] = {k: {'mean': float(v[inner].mean() * 1000), 'p95': float(np.percentile(v[inner], 95) * 1000), 'max': float(v[inner].max() * 1000)} for k, v in rn.items()}
# self intersection: exact triangle-triangle test (mathutils BVHTree.overlap); whole-mesh count (inherited: eyes/teeth/ears/hands) and the pairs touching the torso zone
si = {}
for tag, bl in (('original', str(ARTDIR_BLEND)), ('form2', str(WD / 'START_form2_candidate.blend')), ('form3', out_blend)):
    jp = WD / f'audit/selfint_{tag}.json'
    r = subprocess.run([B, '-b', bl, '--python', str(WD / 'tools/selfint.py'), '--', str(jp), str(WD / 'data/zone_chat7.npz')], capture_output=True, text=True)
    assert 'SELFINT' in r.stdout, r.stdout[-400:]
    j = json.load(open(jp))
    si[tag] = {'whole_mesh': j['intersecting_pairs_whole_mesh'], 'touching_torso_zone': j['intersecting_pairs_touching_torso_zone']}
res['self_intersection_pairs'] = si
# custom-normal fidelity: decoded corner normals vs geometric vertex normals, zone vertices
nf = {}
for tag, bl in (('original', str(ARTDIR_BLEND)), ('form2', str(WD / 'START_form2_candidate.blend')), ('form3', out_blend)):
    jp = WD / f'audit/normals_{tag}.json'
    r = subprocess.run([B, '-b', bl, '--python', str(WD / 'tools/normals_check.py'), '--', str(jp), str(WD / 'data/zone_chat7.npz')], capture_output=True, text=True)
    assert 'NORMALS_OK' in r.stdout, r.stdout[-400:]
    nf[tag] = json.load(open(jp))
res['custom_normals_vs_geometry_deg_zone'] = nf
json.dump(res, open(WD / 'export/form3_checks.json', 'w'), indent=1)
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
print(json.dumps({k: res[k] for k in ('moved_outside_zone_vs_form2_start', 'moved_outside_zone_vs_artdir_200dc3b9', 'border_vertices_moved_vs_artdir', 'delta_moved_vertices', 'flipped_zone_tris_vs_original', 'zone_tris_turned_gt60deg', 'max_vertex_move_mm_vs_original', 'self_intersection_pairs', 'custom_normals_vs_geometry_deg_zone')}, indent=1))
print('border steps', res['border_steps_mm']['form3']); print('topology', topo)
print('SHA blend', sha(out_blend)[:16], 'delta', sha(str(WD / 'export/torso_form3_delta.npz'))[:16], 'artdir', sha(str(ARTDIR_BLEND))[:16])
