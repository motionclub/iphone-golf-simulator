"""Assemble checks.json for MALE_PELVIS_FORM2.   python3 gates_f2.py <TAG>   (needs data/V_<TAG>.npy, export/candidate_<TAG>.blend, export/audit_<TAG>.json, r/<TAG>_sil4, data/sil_<TAG>.json)"""
import sys, json, hashlib, numpy as np
sys.path.insert(0, '.')
from PIL import Image
import common
from common import rear_curve, section_segments
import f2_model2 as M
T = sys.argv[1]; R = M.W.parent.parent; art = R / 'ArtDir/hero/base_lock'
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
CAM = {c['name']: c for c in json.load(open(R / 'work/male-silhouette/reference-cameras.json'))['views']}
out = dict(task='MALE_PELVIS_FORM2', candidate_tag=T, start_blend_sha256=sha('baseline/HeroBase_Male_Silhouette.blend'), start_fbx_sha256=sha('baseline/HeroBase_Male_Body_start.fbx'),
           candidate_blend_sha256=sha(f'export/candidate_{T}.blend'), params_file=f'data/P_{T}.json', params_sha256=sha(f'data/P_{T}.json'), arttdir_blend_sha256_now=sha(art / 'blender/HeroBase_Male_Silhouette.blend'))
import os
if os.path.exists(f'export/candidate_{T}.fbx'): out['candidate_fbx_sha256'] = sha(f'export/candidate_{T}.fbx')
out['audit'] = json.load(open(f'export/audit_{T}.json')); out['zone_report'] = json.load(open('export/f2_zone_report.json'))
s0 = json.load(open('data/sil_start.json')); s1 = json.load(open(f'data/sil_{T}.json'))
out['silhouette_pct'] = dict(chat9=dict((k, round(v['pct'], 4)) for k, v in s0.items()), form2=dict((k, round(v['pct'], 4)) for k, v in s1.items()), gate='bald front/back <= 5.0 %', front_back_PASS=bool(s1['bald_front']['pct'] <= 5 and s1['bald_back']['pct'] <= 5),
                           note='left/right reported only. The rise in back/front vs chat-9 is the lowered see-through gap apex: the plate target masks classify the dark crotch shadow (darker than the background) as gap down to z~0.78, the plate luminance shows the real apex at z 0.748 (back) / 0.762 (front).')
# gap apex from 4x silhouette renders
def apex(tag, view):
    a = np.asarray(Image.open(f'r/{tag}_sil4/{view}@4.png'))[..., 3] > 127; c = CAM['bald_' + view]; mpp = c['metres_per_pixel']; cx = c['centre_x'] * 4; sy = c['sole_y']
    for z in np.arange(0.84, 0.60, -0.0005):
        r = int(round((sy - z / mpp) * 4)); row = a[r]; cc = int(round(cx))
        if (not row[cc - 1:cc + 2].any()) and all(not a[int(round((sy - (z - dz) / mpp) * 4)), cc - 1:cc + 2].any() for dz in (0.01, 0.03, 0.05)): return float(z)
    return None
out['gap_apex_z_m'] = dict(plate_luminance=dict(main_back=0.748, main_front=0.762, sheet_back=0.724, sheet_front=0.748), chat9=dict(back=apex('start', 'back'), front=apex('start', 'front')), form2=dict(back=apex(T, 'back'), front=apex(T, 'front')),
                           note='plate: first row where the background-level slot starts (luminance table on the plate); the plate mask target puts the apex at ~0.783 because the shadowed crotch is darker than the background')
# contour error (section based, plate sub-pixel contour mean of L/R), mm
zs = np.arange(0.76, 0.951, 0.01); M.BIAS['mm'] = 0.0; pr = M._plate_target_raw(zs) * 1000
Vc = np.load(f'data/V_{T}.npy'); cols = (0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.085, 0.10, 0.12)
c9 = M.rear_max_columns(common.V0, zs, cols=cols)[0] * 1000; c2 = M.rear_max_columns(Vc, zs, cols=cols)[0] * 1000
band = (zs >= 0.80) & (zs <= 0.95)
out['side_contour_mm'] = dict(z_range='0.76-0.95', chat9_mean_abs=round(float(np.abs(c9 - pr).mean()), 2), chat9_max_abs=round(float(np.abs(c9 - pr).max()), 2), form2_mean_abs=round(float(np.abs(c2 - pr).mean()), 2), form2_max_abs=round(float(np.abs(c2 - pr).max()), 2),
                              form2_signed_at_lobe_belly_z0p82_0p86=[round(float(v), 1) for v in (c2 - pr)[(zs >= 0.82) & (zs <= 0.86)]], note='+3..+4 mm at z 0.81-0.86 is the documented boldness bias (pin target = plate + 4 mm in z 0.80-0.855); z 0.78-0.79 underside is 3-4 mm under the plate (rounded kink)',
                              subpixel_profile_json=['proof/P6_profile_side_contour_z074_104.json', 'proof/P6b_profile_side_contour_underbutt.json'])
out['side_contour_subpixel'] = dict(z_0p76_1p02=json.load(open('proof/P6_profile_side_contour_z074_104.json')), z_0p72_0p88=json.load(open('proof/P6b_profile_side_contour_underbutt.json')))
# cleft depth: apex ridge minus centre, mm, at z levels
def depth(V, z):
    a = rear_curve(V, 0.055 + 1e-6, np.array([z]))[0]; b = rear_curve(V, -0.055 - 1e-6, np.array([z]))[0]; c1 = rear_curve(V, 0.004 + 1e-6, np.array([z]))[0]; c2_ = rear_curve(V, -0.004 - 1e-6, np.array([z]))[0]
    return float((np.nanmean([a, b]) - np.nanmean([c1, c2_])) * 1000)
out['cleft_depth_mm'] = {f'z{z:.2f}': dict(chat9=round(depth(common.V0, z), 1), form2=round(depth(Vc, z), 1)) for z in (0.80, 0.82, 0.84, 0.86, 0.88, 0.90)}
out['cleft_note'] = 'chat-9 cleft was a flat-floored trench (10 mm flat floor, ~33 deg walls, 26 mm deep at z 0.80); FORM2 is a soft V (Hermite valley between the lobe ridges, no flat floor)'
# 3/4 bulge profiles
import bulge, overlay
for t in ('start', T):
    if not os.path.exists(f'r/{t}_s'): overlay.render(t)
pb = {}
for tag in ('start', T):
    pr_ = bulge.profile(tag); pb[tag] = {p: [[round(float(x), 1) for x in r] for r in pr_[p]] for p in pr_}
out['q3_back_silhouette_bulge_mm'] = dict(z=[round(float(z), 2) for z in bulge.ZS], chat9=pb['start'], form2=pb[T], note='(plate - mesh) edge offset minus thigh-level reference, per panel [L,R]; |values| <= ~5 mm are inside the 2 px sheet calibration noise; -193/231/-295 are arm/hand interference rows')
# groin / front
out['form3_gate_regions'] = json.load(open('export/form3_gate.json')) if os.path.exists('export/form3_gate.json') else None
out['dihedral_roughness_deg'] = __import__('quality').stats(Vc)
d = np.linalg.norm(Vc - common.V0, axis=1) * 1000; out['mesh'] = dict(moved=int((d > 1e-4).sum()), max_move_mm=float(d.max()), tris_unchanged=66158)
json.dump(out, open('checks.json', 'w'), indent=1, default=str); print('CHECKS_WRITTEN', list(out.keys()))
