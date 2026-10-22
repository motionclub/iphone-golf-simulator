"""FORM2 proof sheets (plate | PASS | FORM2). PYTHONPATH=pylib python3.13 compose_form2.py"""
import sys, json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, '.')
from relcorr import blur, PL as PLG, CAM
R = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'); W = R / 'work/male-parallel-torso2'; OUT = W / 'proof'
C = json.load(open(OUT / 'male-torso-form2-checks.json'))
def font(sz):
    try: return ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', sz)
    except Exception: return ImageFont.load_default()
F1, F2, F3 = font(34), font(22), font(19)
PL = PLG.convert('RGB'); SH = Image.open(R / 'ArtDir/hero/base_lock/male_multiangle_body.jpg').convert('RGB')
def header(w, lines, h=None):
    h = h or (24 + 44 + 30 * (len(lines) - 1) + 14); im = Image.new('RGB', (w, h), (30, 32, 38)); d = ImageDraw.Draw(im); d.text((20, 14), lines[0], font=F1, fill=(240, 240, 240))
    for i, l in enumerate(lines[1:]): d.text((20, 62 + 30 * i), l, font=F2, fill=(190, 195, 205))
    return im
def label(im, t, pos=(10, 8)):
    im = im.convert('RGB'); d = ImageDraw.Draw(im); w = d.textlength(t, font=F2); d.rectangle((pos[0] - 6, pos[1] - 4, pos[0] + w + 8, pos[1] + 28), fill=(0, 0, 0)); d.text(pos, t, font=F2, fill=(255, 255, 255)); return im
def hstack(ims, gap=8):
    h = max(i.height for i in ims); s = Image.new('RGB', (sum(i.width for i in ims) + gap * (len(ims) - 1), h)); x = 0
    for i in ims: s.paste(i, (x, 0)); x += i.width + gap
    return s
def vstack(ims, gap=8):
    w = max(i.width for i in ims); s = Image.new('RGB', (w, sum(i.height for i in ims) + gap * (len(ims) - 1))); y = 0
    for i in ims: s.paste(i, (0, y)); y += i.height + gap
    return s
def relief(im, k=5, s=14):
    g = np.asarray(im.convert('L')).astype('float32'); d = np.clip((g - blur(g, s)) * k + 128, 0, 255).astype('uint8'); return Image.fromarray(d).convert('RGB')
def fit(im, w): return im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)
ref = C['form_correlation_vs_plate']['torso1_PASS_reference_dog_1.2_5.0']; fk = C['form_correlation_vs_plate']['dog_1.2_5.0']; sil = C['silhouette_pct']['body']; sb = C['silhouette_pct_baseline_body']; dep = C['torso_depth_vs_side_plates_mm_z0.92_1.30']
pl = C['plate_lit_correlation']; ho = C['heldout_back_3q_panels']; pc = C['pec_crease']
HDR = [f"GATE: MALE_TORSO_FORM2 {C['GATE_MALE_TORSO_FORM2']}",
       f"zone: {C['zone']['verts_moved_inside_zone']} verts moved, outside zone {C['zone']['verts_moved_outside_zone']} (head/neck, arms, hands, legs, feet, Face_M, LOOP_* bit-identical)  |  topology identical: {C['verts']} verts / {C['tris']} tris",
       f"FORM mean r (6 torso regions) {ref and C['form_correlation_vs_plate']['torso1_PASS_reference_mean']:+.3f} -> {fk['mean_final']:+.3f} (target >= +0.25)  |  front chest {ref['front_chest']:+.2f} -> {fk['final']['front_chest']:+.2f}  |  back upper {ref['back_chest']:+.2f} -> {fk['final']['back_chest']:+.2f}  |  abdomen f/b {ref['front_abdomen']:+.2f}/{ref['back_abdomen']:+.2f} -> {fk['final']['front_abdomen']:+.2f}/{fk['final']['back_abdomen']:+.2f}",
       f"silhouette front {sil['bald_front']:.2f}% / back {sil['bald_back']:.2f}% (unchanged, gate <=5)  |  depth vs side plates rms {dep['baseline']['rms_mm']:.1f} -> {dep['final']['rms_mm']:.1f} mm  |  pelvis creases >55 deg {C['dihedral_zone_baseline']['pelvis_band_over_55']} -> {C['dihedral_zone_final']['pelvis_band_over_55']}  |  held-out back 3/4 panels r {ho['baseline']['q3BL']:.2f}/{ho['baseline']['q3BR']:.2f} -> {ho['final']['q3BL']:.2f}/{ho['final']['q3BR']:.2f}"]
# ---- main: front/back real + relief
FBOX = {'front': (225, 140, 485, 440), 'back': (790, 140, 1050, 440)}; rows = []
for v in ('front', 'back'):
    box = FBOX[v]; PW = 380
    ims = [PL.crop(box), Image.open(W / f'r/P2_base/{v}.png').convert('RGB').crop(box), Image.open(W / f'r/P2_final/{v}.png').convert('RGB').crop(box),
           relief(PL).crop(box), relief(Image.open(W / f'r/P2_basec/{v}.png').convert('RGB')).crop(box), relief(Image.open(W / f'r/P2_finalc/{v}.png').convert('RGB')).crop(box)]
    nm = [f'{v.upper()} plate', 'PASS (before)', 'FORM2', 'plate relief', 'PASS relief', 'FORM2 relief']; rows.append(hstack([fit(label(i.copy(), n), PW) for i, n in zip(ims, nm)]))
main = vstack([header(rows[0].width, HDR), rows[0], rows[1]]); main.save(OUT / '02f_form2_proof_m.png'); print('main', main.size)
# ---- q3: plate | PASS | FORM2 for 4 yaw views
K = 0.00582; ZT, ZB = 1.42, 0.74; ITEMS = [('3/4 front L', 183, 672, 'yaw38_2.0_0.95'), ('3/4 front R', 480, 672, 'yaw-38_2.0_0.95'), ('3/4 back L', 788, 672, 'yaw142_2.0_0.95'), ('3/4 back R', 1090, 672, 'yaw-142_2.0_0.95')]; cols = []
for lab, cx, sole, fn in ITEMS:
    y0 = int(sole - ZT / K); y1 = int(sole - ZB / K); p = SH.crop((cx - 62, y0, cx + 62, y1)); H = 500; p = p.resize((int(p.width * H / p.height), H), Image.LANCZOS); col = [label(p, f'plate {lab}')]
    for t, n in (('P2_base', 'PASS'), ('P2_final', 'FORM2')):
        m = Image.open(W / f'r/{t}/{fn}.png').convert('RGB'); py = lambda z: 500 - (z - 0.95) / 0.002
        mm = m.crop((int(500 - 62 * K / 0.002), int(py(ZT)), int(500 + 62 * K / 0.002), int(py(ZB)))); mm = mm.resize((int(mm.width * H / mm.height), H), Image.LANCZOS); col.append(label(mm, n))
    cols.append(vstack(col, 6))
q3 = vstack([header(hstack(cols).width, [HDR[0] + '  -  3/4 views vs the multi-angle plate sheet', 'rows: plate | PASS | FORM2 (Unity-like skin render, torso crop z 0.74-1.42). Back 3/4 panels were never used in the fit.'], h=96), hstack(cols, 8)]); q3.save(OUT / '02f_form2_proof_q3_m.png'); print('q3', q3.size)
# ---- side silhouettes
M = R / 'work/male-silhouette'; cam = {c['name']: c for c in json.load(open(M / 'reference-cameras.json'))['views']}
def mk(p):
    a = np.array(Image.open(p).convert('RGBA')); return (a[:, :, 3] > 127) if a[:, :, 3].min() < 250 else (a[:, :, 0] > 127)
def overlay(view, rd, Z=6):
    c = cam[view]; t = mk(M / f'{view}_target.png'); r = mk(Path(rd) / f'{view}.png'); mpp = c['metres_per_pixel']
    ya, yb = int(c['sole_y'] - 1.45 / mpp), int(c['sole_y'] - 0.74 / mpp); xa, xb = c['roi'][0] - 6, c['roi'][2] + 6; im = np.zeros((yb - ya, xb - xa, 3), 'uint8') + 40
    sub = lambda m: m[ya:yb, xa:xb]; im[sub(t & r)] = (170, 170, 170); im[sub(t & ~r)] = (60, 220, 140); im[sub(r & ~t)] = (255, 90, 150)
    return Image.fromarray(im).resize(((xb - xa) * Z, (yb - ya) * Z), Image.NEAREST)
panels = [label(overlay(v, rd), f'{v} - {n}') for v in ('left', 'right') for rd, n in ((W / 'r/sil_base', 'PASS'), (W / 'r/audit_final/sil_body', 'FORM2'))]
side = vstack([header(hstack(panels).width, [HDR[0] + '  -  side silhouettes vs plate', 'green = plate only, pink = mesh only, grey = agree.  Depth deficit (plate - mesh, z 0.92-1.30): mean %+.2f -> %+.2f mm, rms %.2f -> %.2f mm (limit 3.0)' % (dep['baseline']['mean_deficit_mm'], dep['final']['mean_deficit_mm'], dep['baseline']['rms_mm'], dep['final']['rms_mm']), 'the front-most / back-most surface per height is held to the PASS depth (guard 20 mm); arms/hands in the profile views are outside the zone and unchanged'], h=130), hstack(panels, 10)]); side.save(OUT / '02f_form2_proof_side_m.png'); print('side', side.size)
# ---- detail: plate-lit crops (chest, waist, upper back, glute) plate | PASS | FORM2
def boost(im, k=3.0): a = np.asarray(im.convert('L')).astype('float32'); return Image.fromarray(np.clip((a - 105) * k + 110, 0, 255).astype('uint8')).convert('RGB')
REGS = [('CHEST (front)', 'front', 1.08, 1.36, 0.21), ('WAIST / ABS (front)', 'front', 0.78, 1.12, 0.21), ('UPPER BACK', 'back', 1.10, 1.38, 0.21), ('LOWER BACK / GLUTE', 'back', 0.74, 1.10, 0.20)]; blocks = []
for nm, view, z0, z1, xh in REGS:
    c = CAM['bald_' + view]; mpp = c['metres_per_pixel']; box = (int(c['centre_x'] - xh / mpp), int(c['sole_y'] - z1 / mpp), int(c['centre_x'] + xh / mpp), int(c['sole_y'] - z0 / mpp)); Z = 2
    ims = [boost(PLG).crop(box), boost(Image.open(W / f'r/basesh/{view}.png')).crop(box), boost(Image.open(W / f'r/finalsh/{view}.png')).crop(box)]
    ims = [label(i.resize((i.width * Z, i.height * Z), Image.LANCZOS), t) for i, t in zip(ims, (f'{nm}: plate', 'PASS', 'FORM2'))]; blocks.append(hstack(ims, 6))
Wd = max(b.width for b in blocks); grid = vstack([hstack([blocks[0], blocks[2]], 14), hstack([blocks[1], blocks[3]], 14)], 14)
cr = f"pec crease: plate z {pc['plate']['crease_z']:.3f} drop {pc['plate']['drop_lum']:.0f} lum | PASS z {pc['base']['crease_z']:.3f} drop {pc['base']['drop_lum']:.0f} | FORM2 z {pc['final']['crease_z']:.3f} drop {pc['final']['drop_lum']:.0f}   (lower-pec shelf height and contrast)"
det = vstack([header(grid.width, [HDR[0] + '  -  detail under the plate\'s own lighting', 'meshes shaded with the lighting fitted on the untouched limbs (spherical-harmonic, per view); contrast boosted x3 for all three. mean r vs plate %.2f -> %.2f' % (pl['baseline']['mean'], pl['final']['mean']), cr], h=130), grid]); det.save(OUT / '02f_form2_proof_detail_m.png'); print('detail', det.size)
# ---- pelvis / glute raking + zone map
cols = []
for v, n in (('q3f', 'front 3/4'), ('back', 'back'), ('left', 'side')):
    a = Image.open(W / f'r/P2_basek/{v}_a.png').convert('RGB').resize((600, 600), Image.LANCZOS); b = Image.open(W / f'r/P2_finalk/{v}_a.png').convert('RGB').resize((600, 600), Image.LANCZOS); cols.append(vstack([label(a, f'{n} - PASS'), label(b, f'{n} - FORM2')], 6))
pel = vstack([header(hstack(cols).width, [HDR[0] + '  -  pelvis / glute under raking light', 'PASS vs FORM2: the repaired pelvis shelf stays clean (no creases >55 deg in the pelvis band); thigh-top slot below z 0.77 is the legs zone (untouched)'], h=96), hstack(cols, 8)]); pel.save(OUT / '02f_form2_proof_pelvis_m.png'); print('pelvis', pel.size)
