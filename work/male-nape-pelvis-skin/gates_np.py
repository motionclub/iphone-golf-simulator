"""Assemble checks.json (zones + silhouette + gate numbers) for the nape + pelvis edit.  blender python3.13: gates_np.py (needs r/start_m, r/FIN_m clay renders, r/sil_start, r/sil_FIN, audit/zone reports)"""
import sys, json, hashlib
sys.path.insert(0, '.')
import numpy as np
from common import *
import metric as MT
from PIL import Image
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
R_ = MT.R; art = R_ / 'ArtDir/hero/base_lock'
out = dict(task='MALE_NAPE_PELVIS', start_blend_sha256='548a83f4bf3f8624e452955bfef84e3f5bf84a3088f8cd9ae5325dc20d426495', installed_blend_sha256=sha(art / 'blender/HeroBase_Male_Silhouette.blend'),
           start_fbx_sha256='2e0740d7127556fc2176e4d35d7f8d916180e856187de3de71b46ef16f5e5bfc', installed_fbx_sha256=sha(art / 'unity_import/HeroBase_Male_Body.fbx'))
a = json.load(open('export/audit_np.json')); z = json.load(open('export/np_zone_report.json'))
out['zones'] = dict(declared=z['zones'], brief_nominal=dict(NAPE='z[1.28,1.42] |x|<=.18', PELVIS='z[0.77,1.05] |x|<=.22'),
                    note='declared zones extend the brief by: nape up to z 1.50 (hump shoulder at 1.42-1.46 + fade), pelvis down to z 0.725 (underbutt / leg-top fade band) and up to 1.07 (blend)')
out['mesh_audit'] = {k: a[k] for k in ('TOPOLOGY_IDENTICAL', 'NAN', 'moved', 'moved_in_NAPE', 'moved_in_PELVIS', 'ZONE_OUTSIDE_NAPE', 'ZONE_OUTSIDE_PELVIS', 'max_move_mm', 'mean_move_mm_moved', 'max_dx_mm', 'max_dy_mm' if 'max_dy_mm' in a else 'max_dx_mm', 'max_dz_mm',
                                    'max_move_nape_mm', 'max_move_pelvis_mm', 'moved_below_z0p77', 'max_move_below_z0p77_mm', 'moved_legs_feet_z_lt_0p735', 'moved_head_z_ge_1p47', 'moved_loop_groups', 'moved_arms_hands_absx_gt_0p215_z_gt_0p78', 'face_m_identical',
                                    'micro1k_strip_vertices', 'micro1k_strip_max_move_mm', 'flipped_faces_vs_start', 'min_face_normal_dot', 'faces_turned_gt_45deg', 'degenerate_faces_after', 'self_intersections_start', 'self_intersections_after', 'self_intersections_new', 'custom_normals') if k in a}
out['zone_edge_max_move_mm'] = z['max_move_at_zone_edge_band_mm']; out['moved_before_mask_outside_zone'] = dict(vertices=z['moved_outside_zone_before_mask'], max_mm=z['max_outside_zone_mm_before_mask'], note='displacement-field smoothing spread, set to exactly 0 by the zone mask')
s0 = json.load(open('data/sil_start.json')); s1 = json.load(open('data/sil_FIN2.json'))
out['silhouette_pct'] = dict(start={k: round(v['pct'], 4) for k, v in s0.items()}, installed={k: round(v['pct'], 4) for k, v in s1.items()}, gate='bald front/back <= 5.0 %', front_back_PASS=bool(s1['bald_front']['pct'] <= 5 and s1['bald_back']['pct'] <= 5), note='left/right are reported only (not gated)')
out['nape_contour'] = json.load(open('proof/np_profile_nape_side.json')); out['pelvis_contour'] = json.load(open('proof/np_profile_pelvis_side.json'))
# lobes: rear depth across x
def depth(V, z, us):
    return [float(rear_curve(V, u + 1e-5, np.array([z]))[0] * 1000) for u in us]
V1 = np.load('data/V_FIN2.npy'); us = [0.0, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10, 0.12]
lob = {}
for zz in (0.80, 0.84, 0.88, 0.92):
    for nm, V in (('start', V0), ('installed', V1)):
        d = depth(V, zz, us); pk = int(np.nanargmax(d)); lob.setdefault(f'z{zz:.2f}', {})[nm] = dict(center_mm=round(d[0], 1), peak_mm=round(d[pk], 1), peak_x_mm=us[pk] * 1000, cleft_depth_mm=round(d[pk] - d[0], 1))
out['glute_lobes_rear_depth'] = lob
# band-pass correlation vs plate (Unity-like clay)
out['bandpass_correlation_vs_plate'] = dict(start={k: round(v, 3) for k, v in MT.score('start').items()}, installed={k: round(v, 3) for k, v in MT.score('FIN2').items()}, note='DoG(1.2,5.0) px (sheet panels 0.8/3.0), Pearson r; *_sr = render/plate band-pass std ratio')
# roughness (dihedral) stats
import roughness as RG
d0 = RG.dihedral(V0); d1 = RG.dihedral(V1); rz = {}
for nm, m in RG.zones.items():
    rz[nm] = dict(edges=int(m.sum()), start_p99=round(float(np.percentile(d0[m], 99)), 1), start_max=round(float(d0[m].max()), 1), installed_p99=round(float(np.percentile(d1[m], 99)), 1), installed_max=round(float(d1[m].max()), 1), new_edges_gt40deg=int(((d1 > 40) & (d0 < 25) & m).sum()))
out['dihedral_roughness_deg'] = rz
sys.path.insert(0, '../male-parallel-torso3')
import relcorr as RC
REG3 = {'chest': (1.15, 1.32), 'abdomen': (0.90, 1.15), 'pelvis': (0.80, 0.90)}; tg = {}
for tag, nm in (('start', 'start'), ('FIN2', 'installed')):
    row = {}
    for v in ('front', 'back'):
        mesh = Image.open(f'r/{tag}_m/{v}.png').convert('L'); A_, B_ = RC.dog(RC.PL, 1.2, 5.0), RC.dog(mesh, 1.2, 5.0)
        for rn, (z0, z1) in REG3.items(): m = RC.torso_mask(v, z0, z1, 0.12); row[f'{v}_{rn}'] = round(float(np.corrcoef(A_[m], B_[m])[0, 1]), 3)
    row['mean'] = round(float(np.mean(list(row.values()))), 3); tg[nm] = row
out['torso_form3_gate_regions'] = dict(values=tg, note='torso FORM3 gate metric (Unity-clay band-pass r, |x|<0.12, DoG 1.2/5) recomputed on this chat\'s renders; regions chest z1.15-1.32, abdomen .90-1.15, pelvis .80-.90')
json.dump(out, open('checks.json', 'w'), indent=1); print('CHECKS_WRITTEN')
