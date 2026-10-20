"""Proof sheets. PYTHONPATH=pylib python3.13 compose_proof.py"""
import sys, json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, '.')
from relcorr import blur
R = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'); W = R / 'work/male-parallel-torso3'
OUT = W / 'proof'; OUT.mkdir(exist_ok=True)
CHK = json.load(open(OUT / 'male-torso-checks.json'))
def font(sz, bold=False):
    for p in ('/System/Library/Fonts/Helvetica.ttc', '/System/Library/Fonts/Supplemental/Arial Bold.ttf' if bold else '/System/Library/Fonts/Supplemental/Arial.ttf'):
        try: return ImageFont.truetype(p, sz)
        except Exception: pass
    return ImageFont.load_default()
F1, F2, F3 = font(34, True), font(22), font(19)
PL = Image.open(R / 'ArtDir/hero/base_lock/male_body_plain.jpg').convert('RGB'); SH = Image.open(R / 'ArtDir/hero/base_lock/male_multiangle_body.jpg').convert('RGB')
def header(w, lines, h=None, col=(30, 32, 38)):
    h = h or (24 + 44 + 30 * (len(lines) - 1) + 14); im = Image.new('RGB', (w, h), col); d = ImageDraw.Draw(im)
    d.text((20, 14), lines[0], font=F1, fill=(240, 240, 240))
    for i, l in enumerate(lines[1:]): d.text((20, 62 + 30 * i), l, font=F2, fill=(190, 195, 205))
    return im
def label(im, txt, pos=(10, 8)):
    d = ImageDraw.Draw(im); w = d.textlength(txt, font=F2); d.rectangle((pos[0] - 6, pos[1] - 4, pos[0] + w + 8, pos[1] + 28), fill=(0, 0, 0)); d.text(pos, txt, font=F2, fill=(255, 255, 255)); return im
def hstack(ims, gap=8, bg=(0, 0, 0)):
    h = max(i.height for i in ims); s = Image.new('RGB', (sum(i.width for i in ims) + gap * (len(ims) - 1), h), bg); x = 0
    for i in ims: s.paste(i, (x, 0)); x += i.width + gap
    return s
def vstack(ims, gap=8, bg=(0, 0, 0)):
    w = max(i.width for i in ims); s = Image.new('RGB', (w, sum(i.height for i in ims) + gap * (len(ims) - 1)), bg); y = 0
    for i in ims: s.paste(i, (0, y)); y += i.height + gap
    return s
def relief(im, k=5, s=14):
    g = np.asarray(im.convert('L')).astype('float32'); d = np.clip((g - blur(g, s)) * k + 128, 0, 255).astype('uint8'); return Image.fromarray(d).convert('RGB')
def fit(im, w): return im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)
G = CHK['gates']; hdr_gate = f"GATE: MALE_TORSO {CHK['GATE_MALE_TORSO']}"
sil = CHK['silhouette_pct']['body']; sb = CHK['silhouette_pct_baseline_body']; dep = CHK['torso_depth_vs_side_plates_mm_z0.92_1.30']
sub1 = f"zone: {CHK['zone']['verts_moved_inside_zone']} verts moved, outside zone {CHK['zone']['verts_moved_outside_zone']} (head/neck, arms, hands, legs, feet bit-identical)  |  topology unchanged: {CHK['verts']} verts / {CHK['tris']} tris"
sub2 = f"silhouette bald front {sil['bald_front']:.2f}% / back {sil['bald_back']:.2f}% (gate <=5.0; baseline {sb['bald_front']:.2f} / {sb['bald_back']:.2f})  |  torso depth vs side plates rms {dep['baseline']['rms_mm']:.1f} -> {dep['final']['rms_mm']:.1f} mm"
d0, d1 = CHK['dihedral_zone_baseline'], CHK['dihedral_zone_final']
sub3 = f"pelvis shelf: sharp edges (>55 deg) in zone {d0['over_55']} -> {d1['over_55']}, worst crease {d0['max']:.0f} -> {d1['max']:.0f} deg  |  shading correlation with plate (6 regions) {CHK['form_correlation_vs_plate']['dog_1.2_5.0']['mean_baseline']:+.2f} -> {CHK['form_correlation_vs_plate']['dog_1.2_5.0']['mean_final']:+.2f}"
# ============ MAIN: front + back, real render + relief; plate | baseline | torso edit
FB = {'front': (225, 140, 485, 440), 'back': (790, 140, 1050, 440)}
rows = []
for v in ('front', 'back'):
    box = FB[v]; PW = 380
    p = PL.crop(box); b = Image.open(W / f'r/P_base/{v}.png').convert('RGB').crop(box); f = Image.open(W / f'r/P_final/{v}.png').convert('RGB').crop(box)
    pc = PL; bc = Image.open(W / f'r/P_basec/{v}.png').convert('RGB'); fc = Image.open(W / f'r/P_finalc/{v}.png').convert('RGB')
    rel = [relief(pc).crop(box), relief(bc).crop(box), relief(fc).crop(box)]
    panels = [fit(label(x.copy(), t), PW) for x, t in zip([p, b, f], (f'{v.upper()} plate', 'baseline (Micro1i)', 'torso edit'))] + [fit(label(x.copy(), t), PW) for x, t in zip(rel, ('plate relief', 'baseline relief', 'torso relief'))]
    rows.append(hstack(panels))
main = vstack([header(rows[0].width, [hdr_gate, sub1, sub2, sub3]), rows[0], rows[1]])
main.save(OUT / '02t_torso_proof_m.png'); print('main', main.size)
# ============ 3/4 views: plate | baseline | torso edit (4 yaw views)
K = 0.00582; ZT, ZB = 1.42, 0.74; ITEMS = [('3/4 front L', 183, 672, 'yaw38_2.0_0.95'), ('3/4 front R', 480, 672, 'yaw-38_2.0_0.95'), ('3/4 back L', 788, 672, 'yaw142_2.0_0.95'), ('3/4 back R', 1090, 672, 'yaw-142_2.0_0.95')]
cols = []
for lab, cx, sole, fnm in ITEMS:
    y0 = int(sole - ZT / K); y1 = int(sole - ZB / K); pl = SH.crop((cx - 62, y0, cx + 62, y1)); H = 520; pl = pl.resize((int(pl.width * H / pl.height), H), Image.LANCZOS)
    col = [label(pl, f'plate {lab}')]
    for t, nm in (('P_base', 'baseline'), ('P_final', 'torso edit')):
        m = Image.open(W / f'r/{t}/{fnm}.png').convert('RGB'); py = lambda z: 500 - (z - 0.95) / 0.002
        mm = m.crop((int(500 - 62 * K / 0.002), int(py(ZT)), int(500 + 62 * K / 0.002), int(py(ZB)))); mm = mm.resize((int(mm.width * H / mm.height), H), Image.LANCZOS); col.append(label(mm, nm))
    cols.append(vstack(col, 6))
q3 = vstack([header(hstack(cols).width, [hdr_gate + '  -  3/4 views vs multi-angle plate', 'torso crop z 0.74-1.42; plate sheet left, Unity-like skin render middle/right'], h=96), hstack(cols, 8)])
q3.save(OUT / '02t_torso_proof_q3_m.png'); print('q3', q3.size)
# ============ side silhouettes (left/right): plate mask vs mesh, baseline and final
M = R / 'work/male-silhouette'; cam = {c['name']: c for c in json.load(open(M / 'reference-cameras.json'))['views']}
def mk(p):
    a = np.array(Image.open(p).convert('RGBA')); return (a[:, :, 3] > 127) if a[:, :, 3].min() < 250 else (a[:, :, 0] > 127)
def overlay(view, rd, Z=6):
    c = cam[view]; t = mk(M / f'{view}_target.png'); r = mk(Path(rd) / f'{view}.png'); mpp = c['metres_per_pixel']
    ya, yb = int(c['sole_y'] - 1.45 / mpp), int(c['sole_y'] - 0.74 / mpp); xa, xb = c['roi'][0] - 6, c['roi'][2] + 6
    im = np.zeros((yb - ya, xb - xa, 3), 'uint8') + 40
    both = t & r; tt = t & ~r; rr = r & ~t
    sub = lambda m: m[ya:yb, xa:xb]
    im[sub(both)] = (170, 170, 170); im[sub(tt)] = (60, 220, 140); im[sub(rr)] = (255, 90, 150)
    return Image.fromarray(im).resize(((xb - xa) * Z, (yb - ya) * Z), Image.NEAREST)
panels = []
for view in ('left', 'right'):
    for rd, nm in ((W / 'r/sil_base', 'baseline'), (W / 'r/audit_final/sil_body', 'torso edit')):
        panels.append(label(overlay(view, rd), f'{view} - {nm}'))
side = vstack([header(hstack(panels).width, [hdr_gate + '  -  side silhouettes vs plate', 'green = plate only, pink = mesh only, grey = agree. Torso depth deficit (plate - mesh, z 0.92-1.30): mean %+.1f -> %+.1f mm, rms %.1f -> %.1f mm' % (dep['baseline']['mean_deficit_mm'], dep['final']['mean_deficit_mm'], dep['baseline']['rms_mm'], dep['final']['rms_mm']), 'arms/hands in the profile views are not part of the torso zone and are unchanged'], h=130), hstack(panels, 10)])
side.save(OUT / '02t_torso_proof_side_m.png'); print('side', side.size)
# ============ pelvis seam raking
cols = []
for v, nm in (('q3f', 'front 3/4'), ('back', 'back'), ('left', 'side')):
    a = Image.open(W / f'r/P_basek/{v}_a.png').convert('RGB').resize((640, 640), Image.LANCZOS); b = Image.open(W / f'r/P_finalk/{v}_a.png').convert('RGB').resize((640, 640), Image.LANCZOS)
    cols.append(vstack([label(a, f'{nm} - baseline'), label(b, f'{nm} - torso edit')], 6))
pel = vstack([header(hstack(cols).width, [hdr_gate + '  -  pelvis shelf / glute / groin, raking light', 'baseline: hard overhanging shelf with torn shards (49 creases >55 deg, worst 122 deg); edit: faired transition, glute volume, groin crease; thigh shards below z 0.77 are legs zone (untouched)'], h=100), hstack(cols, 8)])
pel.save(OUT / '02t_torso_proof_pelvis_m.png'); print('pelvis', pel.size)
# ============ zone heat map
z = Image.open(W / 'r/zonemap_all.png').convert('RGB'); zs = fit(z, 1500)
zone = vstack([header(1500, [hdr_gate + '  -  zone map', 'colour = |displacement| 0..20 mm (blue->red); grey = bit-identical. %d of %d vertices moved, all inside the torso zone.' % (CHK['zone']['verts_moved'], CHK['verts'])], h=100), zs], 0)
zone.save(OUT / '02t_torso_zone_m.png'); print('zone', zone.size)
