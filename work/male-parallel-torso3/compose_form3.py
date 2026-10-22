"""FORM3 proof sheets (plate | FORM2 | FORM3).  PYTHONPATH=../male-micro1i/pylib python3.13 compose_form3.py [tag]"""
import sys, json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, '.')
from relcorr import blur, PL as PLG, CAM
TAG = sys.argv[1] if len(sys.argv) > 1 else 'FORM3'
R = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'); W = R / 'work/male-parallel-torso3'; OUT = W / 'proof'
C = json.load(open(OUT / 'male-torso-form3-checks.json'))
def font(sz):
    try: return ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', sz)
    except Exception: return ImageFont.load_default()
F1, F2, F3 = font(34), font(22), font(19)
PL = PLG.convert('RGB'); SH = Image.open(R / 'ArtDir/hero/base_lock/male_multiangle_body.jpg').convert('RGB')
def _wrap(text, fnt, width):
    out, cur = [], ''
    for wd in text.split(' '):
        t = (cur + ' ' + wd).strip()
        if ImageDraw.Draw(Image.new('RGB', (1, 1))).textlength(t, font=fnt) <= width: cur = t
        else: out.append(cur); cur = wd
    out.append(cur); return out
def header(w, lines, h=None):
    body = [seg for l in lines[1:] for seg in _wrap(l, F2, w - 40)]
    h = 24 + 44 + 28 * len(body) + 14; im = Image.new('RGB', (w, h), (30, 32, 38)); d = ImageDraw.Draw(im); d.text((20, 14), _wrap(lines[0], F1, w - 40)[0], font=F1, fill=(240, 240, 240))
    for i, l in enumerate(body): d.text((20, 62 + 28 * i), l, font=F2, fill=(190, 195, 205))
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
f = C['form_correlation_vs_plate']['dog_1.2_5.0']; f2, f3 = f['FORM2'], f['FORM3']; sil = C['silhouette_pct']['body']; sb = C['silhouette_pct_baseline_body']; dep = C['torso_depth_vs_side_plates_mm_z0.92_1.30']
pl = C['plate_lit_correlation']; ho = C['heldout_back_3q_panels']; pc = C['pec_crease_plate_lit']; un = C['pec_shelf_unity_lit']; gl = C['glute_lobe_split']; bd = C['banding']
verdict = C['GATE_MALE_TORSO_FORM3']
HDR = [f"GATE: MALE_TORSO_FORM3 {verdict}",
       f"zone: {C['zone']['verts_moved_inside_zone']} verts moved (all |x|<0.20), outside zone {C['zone']['verts_moved_outside_zone']} (head/neck, arms, hands, legs, feet, Face_M, LOOP_* bit-identical)  |  topology identical: {C['verts']} verts / {C['tris']} tris  |  z>=1.352 untouched",
       f"FORM mean r (6 regions) {f['mean_FORM2']:+.3f} -> {f['mean_FORM3']:+.3f}  |  front chest {f2['front_chest']:+.2f} -> {f3['front_chest']:+.2f}  |  abdomen {f2['front_abdomen']:+.2f} -> {f3['front_abdomen']:+.2f}  |  glute-upper {f2['back_pelvis']:+.2f} -> {f3['back_pelvis']:+.2f}  |  pelvis(f) {f2['front_pelvis']:+.2f} -> {f3['front_pelvis']:+.2f}  |  back upper {f2['back_chest']:+.2f} -> {f3['back_chest']:+.2f}",
       f"silhouette front {sil['bald_front']:.2f}% / back {sil['bald_back']:.2f}% (unchanged, gate <=5)  |  depth vs side plates rms {dep['baseline']['rms_mm']:.1f} -> {dep['final']['rms_mm']:.1f} mm  |  shelf drop plate-lit {pc['base']['drop_lum']:.0f} -> {pc[TAG]['drop_lum']:.0f} lum (plate {pc['plate']['drop_lum']:.0f}), Unity-style {un['skin']['FORM2']['drop_lum']:.0f} -> {un['skin']['FORM3']['drop_lum']:.0f}  |  glute cleft depth z.84 {gl['z0.84']['FORM2']['cleft_depth_mm']:+.0f} -> {gl['z0.84']['FORM3']['cleft_depth_mm']:+.0f} mm"]
# ---- main: front/back real + relief
FBOX = {'front': (225, 140, 485, 440), 'back': (790, 140, 1050, 440)}; rows = []
for v in ('front', 'back'):
    box = FBOX[v]; PW = 380
    ims = [PL.crop(box), Image.open(W / f'r/base/{v}.png').convert('RGB').crop(box), Image.open(W / f'r/{TAG}/{v}.png').convert('RGB').crop(box),
           relief(PL).crop(box), relief(Image.open(W / f'r/basec/{v}.png').convert('RGB')).crop(box), relief(Image.open(W / f'r/{TAG}c/{v}.png').convert('RGB')).crop(box)]
    nm = [f'{v.upper()} plate', 'FORM2 (before)', 'FORM3', 'plate relief', 'FORM2 relief', 'FORM3 relief']; rows.append(hstack([fit(label(i.copy(), n), PW) for i, n in zip(ims, nm)]))
main = vstack([header(rows[0].width, HDR), rows[0], rows[1]]); main.save(OUT / '03_form3_proof_m.png'); print('main', main.size)
# ---- q3
K = 0.00582; ZT, ZB = 1.42, 0.74; ITEMS = [('3/4 front L', 183, 672, 'yaw38_2.0_0.95'), ('3/4 front R', 480, 672, 'yaw-38_2.0_0.95'), ('3/4 back L', 788, 672, 'yaw142_2.0_0.95'), ('3/4 back R', 1090, 672, 'yaw-142_2.0_0.95')]; cols = []
for lab, cx, sole, fn in ITEMS:
    y0 = int(sole - ZT / K); y1 = int(sole - ZB / K); p = SH.crop((cx - 62, y0, cx + 62, y1)); H = 500; p = p.resize((int(p.width * H / p.height), H), Image.LANCZOS); col = [label(p, f'plate {lab}')]
    for t, n in (('base', 'FORM2'), (TAG, 'FORM3')):
        m = Image.open(W / f'r/{t}/{fn}.png').convert('RGB'); py = lambda z: 500 - (z - 0.95) / 0.002
        mm = m.crop((int(500 - 62 * K / 0.002), int(py(ZT)), int(500 + 62 * K / 0.002), int(py(ZB)))); mm = mm.resize((int(mm.width * H / mm.height), H), Image.LANCZOS); col.append(label(mm, n))
    cols.append(vstack(col, 6))
q3 = vstack([header(hstack(cols).width, [HDR[0] + '  -  3/4 views vs the multi-angle plate sheet', 'rows: plate | FORM2 | FORM3 (Unity-like skin render, torso crop z 0.74-1.42). The back 3/4 panels were never used in the fit; the front ones were not used either.'], h=96), hstack(cols, 8)]); q3.save(OUT / '03_form3_proof_q3_m.png'); print('q3', q3.size)
# ---- side silhouettes
M = R / 'work/male-silhouette'; cam = {c['name']: c for c in json.load(open(M / 'reference-cameras.json'))['views']}
def mk(p):
    a = np.array(Image.open(p).convert('RGBA')); return (a[:, :, 3] > 127) if a[:, :, 3].min() < 250 else (a[:, :, 0] > 127)
def overlay(view, rd, Z=6):
    c = cam[view]; t = mk(M / f'{view}_target.png'); r = mk(Path(rd) / f'{view}.png'); mpp = c['metres_per_pixel']
    ya, yb = int(c['sole_y'] - 1.45 / mpp), int(c['sole_y'] - 0.74 / mpp); xa, xb = c['roi'][0] - 6, c['roi'][2] + 6; im = np.zeros((yb - ya, xb - xa, 3), 'uint8') + 40
    sub = lambda m: m[ya:yb, xa:xb]; im[sub(t & r)] = (170, 170, 170); im[sub(t & ~r)] = (60, 220, 140); im[sub(r & ~t)] = (255, 90, 150)
    return Image.fromarray(im).resize(((xb - xa) * Z, (yb - ya) * Z), Image.NEAREST)
panels = [label(overlay(v, rd), f'{v} - {n}') for v in ('left', 'right') for rd, n in ((W / 'r/sil_base', 'FORM2'), (W / 'r/audit_form3/sil_body', 'FORM3'))]
side = vstack([header(hstack(panels).width, [HDR[0] + '  -  side silhouettes vs plate', 'green = plate only, pink = mesh only, grey = agree.  Depth deficit (plate - mesh, z 0.92-1.30): mean %+.2f -> %+.2f mm, rms %.2f -> %.2f mm (limit 3.0)' % (dep['baseline']['mean_deficit_mm'], dep['final']['mean_deficit_mm'], dep['baseline']['rms_mm'], dep['final']['rms_mm']), 'pec crests rise to the existing front-most line and the sternum / creases carve behind it, so the chest silhouette is held; the buttock lobes use <= 8 mm of back allowance at z 0.81-0.86 where the side plates are 6-12 mm deeper than the mesh'], h=130), hstack(panels, 10)]); side.save(OUT / '03_form3_proof_side_m.png'); print('side', side.size)
# ---- detail: plate-lit crops
def boost(im, k=3.0): a = np.asarray(im.convert('L')).astype('float32'); return Image.fromarray(np.clip((a - 105) * k + 110, 0, 255).astype('uint8')).convert('RGB')
REGS = [('CHEST (front)', 'front', 1.08, 1.36, 0.21), ('WAIST / ABS (front)', 'front', 0.78, 1.12, 0.21), ('UPPER BACK', 'back', 1.10, 1.38, 0.21), ('LOWER BACK / GLUTE', 'back', 0.74, 1.10, 0.20)]; blocks = []
for nm, view, z0, z1, xh in REGS:
    c = CAM['bald_' + view]; mpp = c['metres_per_pixel']; box = (int(c['centre_x'] - xh / mpp), int(c['sole_y'] - z1 / mpp), int(c['centre_x'] + xh / mpp), int(c['sole_y'] - z0 / mpp)); Z = 2
    ims = [boost(PLG).crop(box), boost(Image.open(W / f'r/basesh/{view}.png')).crop(box), boost(Image.open(W / f'r/{TAG}sh/{view}.png')).crop(box)]
    ims = [label(i.resize((i.width * Z, i.height * Z), Image.LANCZOS), t) for i, t in zip(ims, (f'{nm}: plate', 'FORM2', 'FORM3'))]; blocks.append(hstack(ims, 6))
grid = vstack([hstack([blocks[0], blocks[2]], 14), hstack([blocks[1], blocks[3]], 14)], 14)
cr = f"pec crease: plate z {pc['plate']['crease_z']:.3f} drop {pc['plate']['drop_lum']:.0f} lum | FORM2 z {pc['base']['crease_z']:.3f} drop {pc['base']['drop_lum']:.0f} | FORM3 z {pc[TAG]['crease_z']:.3f} drop {pc[TAG]['drop_lum']:.0f}   (lower-pec shelf height and contrast, plate-lit)"
det = vstack([header(grid.width, [HDR[0] + '  -  detail under the plate\'s own lighting', 'meshes shaded with the lighting fitted on the untouched limbs (spherical-harmonic, per view); contrast boosted x3 for all three. mean r vs plate %.2f -> %.2f' % (pl['FORM2']['mean'], pl['FORM3']['mean']), cr], h=130), grid]); det.save(OUT / '03_form3_proof_detail_m.png'); print('detail', det.size)
# ---- pelvis / glute raking
cols = []
for v, n in (('q3f', 'front 3/4'), ('back', 'back'), ('left', 'side')):
    a = Image.open(W / f'r/basek/{v}_a.png').convert('RGB').resize((600, 600), Image.LANCZOS); b = Image.open(W / f'r/{TAG}k/{v}_a.png').convert('RGB').resize((600, 600), Image.LANCZOS); cols.append(vstack([label(a, f'{n} - FORM2'), label(b, f'{n} - FORM3')], 6))
pel = vstack([header(hstack(cols).width, [HDR[0] + '  -  pelvis / glute under raking light', 'FORM2 vs FORM3: the pelvis shelf stays clean (no creases >55 deg in the pelvis band); the buttock lobes + cleft are in-zone (z >= 0.77), the thigh overhang / gluteal fold / crotch slot belong to the legs zone and are untouched'], h=96), hstack(cols, 8)]); pel.save(OUT / '03_form3_proof_pelvis_m.png'); print('pelvis', pel.size)
# ---- close-ups: chest / mid / glute  (plate raw|relief ; FORM2 skin|relief ; FORM3 skin|relief), single-column zoom
def closeup(name, view, z0, z1, xh, extra):
    c = CAM['bald_' + view]; mpp = c['metres_per_pixel']; box = (int(c['centre_x'] - xh / mpp), int(c['sole_y'] - z1 / mpp), int(c['centre_x'] + xh / mpp), int(c['sole_y'] - z0 / mpp)); Z = max(2, int(round(520 / (box[3] - box[1]))))
    def crop(im): im = im.crop(box); return im.resize((im.width * Z, im.height * Z), Image.LANCZOS)
    plr = relief(PL, 5, 10); rows = [hstack([label(crop(PL), f'plate {name}'), label(crop(plr), 'plate relief')], 6)]
    for t, n in (('base', 'FORM2'), (TAG, 'FORM3')):
        sk = Image.open(W / f'r/{t}/{view}.png').convert('RGB'); cl = Image.open(W / f'r/{t}c/{view}.png').convert('RGB'); rows.append(hstack([label(crop(sk), f'{n} skin'), label(crop(relief(cl, 5, 10)), f'{n} clay relief')], 6))
    sheet = vstack(rows, 6); out = vstack([header(sheet.width, [HDR[0] + f'  -  {name} close-up (plate | FORM2 | FORM3)'] + extra), sheet]); out.save(OUT / f'03_form3_closeup_{name}_m.png'); print(name, out.size)
closeup('chest', 'front', 1.08, 1.36, 0.20, [f"front chest band-pass r {f2['front_chest']:+.3f} -> {f3['front_chest']:+.3f}  |  lower-pec shelf crest-to-crease drop: plate-lit {pc['base']['drop_lum']:.1f} -> {pc[TAG]['drop_lum']:.1f} lum (plate {pc['plate']['drop_lum']:.1f}); Unity-style skin {un['skin']['FORM2']['drop_lum']:.1f} -> {un['skin']['FORM3']['drop_lum']:.1f}, clay {un['clay']['FORM2']['drop_lum']:.1f} -> {un['clay']['FORM3']['drop_lum']:.1f} lum", 'pec masses lifted to the silhouette extreme, sternum valley carved behind them, shelf crease deepened by the fit: no second line, fine-ripple energy %.2fx the plate (limit 2.0)' % bd['ripple_ratio_FORM3_over_plate']['front_chest']])
closeup('mid', 'front', 0.84, 1.20, 0.20, [f"front abdomen band-pass r {f2['front_abdomen']:+.3f} -> {f3['front_abdomen']:+.3f}  |  front pelvis {f2['front_pelvis']:+.3f} -> {f3['front_pelvis']:+.3f}  (plate-lit abdomen {pl['FORM2']['f-abd']:+.2f} -> {pl['FORM3']['f-abd']:+.2f})", 'soft flank planes, iliac V creases, no carve: longest dark horizontal run %.2f of the torso width, ripple %.2fx the plate' % (bd['detectors'][TAG]['belt_front_max_frac'], bd['ripple_ratio_FORM3_over_plate']['front_abdomen'])])
closeup('glute', 'back', 0.74, 1.04, 0.19, [f"back glute-upper band-pass r {f2['back_pelvis']:+.3f} -> {f3['back_pelvis']:+.3f}  |  twin lobes: centre-to-lobe-crest cleft depth z 0.84 / 0.86 = {gl['z0.84']['FORM2']['cleft_depth_mm']:+.1f} / {gl['z0.86']['FORM2']['cleft_depth_mm']:+.1f} -> {gl['z0.84']['FORM3']['cleft_depth_mm']:+.1f} / {gl['z0.86']['FORM3']['cleft_depth_mm']:+.1f} mm (positive = lobes proud of the cleft)", 'in-zone only (z >= 0.77): the plate\'s gluteal fold arcs, thigh overhang and the squared crotch slot below z 0.77 belong to the legs zone and are untouched'])
zi = [Image.open(W / f'r/zone_form3/{v}.png').convert('RGB') for v in ('front', 'back', 'left', 'q3')]
zi = [label(i, n) for i, n in zip(zi, ('front', 'back', 'left', 'q3'))]
zm = vstack([header(hstack(zi).width, [HDR[0] + '  -  displacement heat map (FORM3 vs FORM2 coordinates)', 'grey = bit-identical (everything outside the torso zone); blue -> yellow -> red = 0 -> 20 mm. Only |x| < 0.20, z 0.77-1.35 moves; max %.1f mm (glute lobes), mean of moved %.2f mm' % (C['max_displacement_mm'], C['mean_displacement_moved_mm'])]), hstack(zi, 8)]); zm.save(OUT / '03_form3_zone_m.png'); print('zone', zm.size)
print('COMPOSE_DONE')
