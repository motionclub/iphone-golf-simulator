"""FORM5 proof images.  python3 tools/make_proofs4.py [coords.npy]   (default data/co_FORM5_final.npy); rows: plate | FORM4 | FORM5
04_plate_vs_form4_vs_form5_3q.png | 05_bust_closeups_soft/clay.png | 06_glute_closeups_soft/clay.png | 02_side_profile_overlay.png | 03_front_back_silhouette_overlay.png
07_mirror_stripe_test.png | 01_torso_before_after_soft/clay.png | 08_sections_vs_plate.png
Panels of one image share the same processing; `enh` is a contrast factor about mid-grey applied to the PLATE panels AND the model renders alike."""
import sys, os, json, subprocess, hashlib
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/gate7')
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageDraw
from board3 import *          # ROIs, sheet_tile, strip, label, banner, bgcomp, plate_crop, roi_shot, BL, START, HERE
import viz3

CO3 = sys.argv[1] if len(sys.argv) > 1 else HERE + '/data/co_FORM5_final.npy'     # newest = FORM5
CO2 = HERE + '/data/co_FORM4_final.npy'                                              # previous = FORM4 (Adnan: bust flat)
CO7 = HERE + '/data/co_chat7.npy'
OUT = os.environ.get('PROOF_OUT', HERE + '/proof')
os.makedirs(OUT, exist_ok=True)
SCR = OUT + '/scratch'
os.makedirs(SCR, exist_ok=True)
SHA3 = hashlib.sha256(open(HERE + '/export/HeroBase_Female_torso_form5_candidate.blend', 'rb').read()).hexdigest()[:8]     # FORM5
SHA2 = hashlib.sha256(open(HERE + '/START_form4_candidate.blend', 'rb').read()).hexdigest()[:8]                       # FORM4
LOOKS = {'soft': 'matcap:' + HERE + '/tools/matcap_platefit_g22.png', 'clay': 'matcap:clay_studio.exr', 'stripe': 'matcap:check_reflection_vertical.exr'}
ENH = 1.0


def render_set(tag, shots, look, variants):
    spec = {"variants": [{"tag": t, "coords": c} for t, c in variants], "out": f"{SCR}/{tag}", "shots": shots, "look": LOOKS[look]}
    r = subprocess.run([BL, '-b', START, '--python', HERE + '/tools/render3.py', '--', json.dumps(spec)], capture_output=True, text=True)
    assert 'RENDER_OK' in r.stdout, r.stdout[-1000:] + r.stderr[-500:]
    return {t: {s['name']: f"{SCR}/{tag}_{t}_{s['name']}.png" for s in shots} for t, _ in variants}


def enh(im, f=ENH):
    return ImageEnhance.Contrast(im).enhance(f) if f != 1.0 else im


def part_shots(part, px):
    if part == 'chest':
        zc, half = 1.20, 0.27
        fr = roi_shot('front', 'chest'); fr['res'] = [int(px * 0.833), px]
        sh = [fr,
              dict(name='fl', yaw=-20, xc=0.0, zc=zc, w=2 * half, res=[px, px]),
              dict(name='fr', yaw=20, xc=0.0, zc=zc, w=2 * half, res=[px, px]),
              dict(name='side', yaw=-90, xc=0.0, zc=zc, w=2 * half, res=[px, px])]
        plate = [plate_crop('chest', 1.0).resize((int(px * 0.833), px), Image.LANCZOS), sheet_tile(168, zc, half, px, enh=1.0), sheet_tile(472, zc, half, px, enh=1.0), sheet_tile(790, zc, half, px, bottom=False, enh=1.0)]
        names = ['front', '3/4 front L', '3/4 front R', 'side']
    else:
        zc, half = 0.90, 0.27
        fr = roi_shot('back', 'pelvis'); fr['res'] = [int(px * 1.176), px]
        sh = [fr,
              dict(name='bl', yaw=-150, xc=0.0, zc=zc, w=2 * half, res=[px, px]),
              dict(name='br', yaw=150, xc=0.0, zc=zc, w=2 * half, res=[px, px]),
              dict(name='side', yaw=-90, xc=0.0, zc=zc, w=2 * half, res=[px, px])]
        plate = [plate_crop('pelvis', 1.0).resize((int(px * 1.176), px), Image.LANCZOS), sheet_tile(775, zc, half, px, enh=1.0), sheet_tile(1078, zc, half, px, enh=1.0), sheet_tile(790, zc, half, px, bottom=False, enh=1.0)]
        names = ['back', '3/4 back L', '3/4 back R', 'side']
    return sh, plate, names


def closeups(part, look, title, fname, px=520):
    sh, plate, names = part_shots(part, px)
    files = render_set(f'cu_{part}_{look}', sh, look, [('f2', CO2), ('f3', CO3)])
    rows = []
    prow = strip([enh(p.convert('RGB')) for p in plate], [f'PLATE {n}' for n in names])
    rows.append(prow)
    for tag, lab, col in (('f2', f'FORM4 ({SHA2}…)', (90, 30, 30)), ('f3', f'FORM5 ({SHA3}…)', (20, 90, 50))):
        ims = [enh(bgcomp(files[tag][s['name']])) for s in sh]
        rr = strip(ims, [f'{lab} {n}' for n in names])
        rows.append(rr)
    W = max(r.width for r in rows)
    S_ = Image.new('RGB', (W, sum(r.height for r in rows)), (30, 30, 34))
    y = 0
    for r in rows:
        S_.paste(r, (0, y)); y += r.height
    kn = {'soft': 'soft plate-like matcap', 'clay': 'clay studio matcap', 'stripe': 'mirror-stripe matcap'}[look]
    banner(S_, title + f' - {kn}', f'Row 1 = plate (bald plate / multi-angle sheet), row 2 = FORM4, row 3 = FORM5. Soft = lighting fitted to the plate (from above/right, see tools/photo3.py). Model 3/4 yaw: front +-20 deg, back +-30 deg (matched by eye to the sheet panels). Same cameras for FORM4 and FORM5.').save(f'{OUT}/{fname}')
    print(fname)


# ---------------------------------------------------------------- 05 / 06 close-ups
closeups('chest', 'soft', 'BUST close-ups', '05_bust_closeups_soft.png')
closeups('chest', 'clay', 'BUST close-ups', '05_bust_closeups_clay.png')
closeups('pelvis', 'soft', 'GLUTE close-ups', '06_glute_closeups_soft.png')
closeups('pelvis', 'clay', 'GLUTE close-ups', '06_glute_closeups_clay.png')

# ---------------------------------------------------------------- 04 3/4 views: plate | FORM4 | FORM5 (soft)
S2b = 1.7039 / 290.5; V0b = 668.5
zc, half = 1.02, 0.30
px = 560
views = [('q1', -20, 168, 'plate 3/4 front L'), ('q2', 20, 472, 'plate 3/4 front R'), ('q3', -150, 775, 'plate 3/4 back L'), ('q4', 150, 1078, 'plate 3/4 back R')]
shots = [dict(name=n, yaw=y, xc=0.0, zc=zc, w=2 * half, res=[px, px]) for n, y, _, _ in views]
files = render_set('q34', shots, 'soft', [('f2', CO2), ('f3', CO3)])
rows = [strip([enh(sheet_tile(cx, zc, half, px, enh=1.0)) for _, _, cx, _ in views], [l for *_, l in views])]
for tag, lab in (('f2', f'FORM4 ({SHA2}…)'), ('f3', f'FORM5 ({SHA3}…)')):
    rows.append(strip([enh(bgcomp(files[tag][n])) for n, *_ in views], [f'{lab} {nm}' for (n, _, _, nm) in [(v[0], 0, 0, v[3].replace('plate ', '')) for v in views]]))
W = Image.new('RGB', (rows[0].width, sum(r.height for r in rows)))
y = 0
for r in rows:
    W.paste(r, (0, y)); y += r.height
banner(W, '3/4 VIEWS - plate | FORM4 | FORM5 (soft plate-like light)', 'Row 1 plate (multi-angle sheet), row 2 FORM4, row 3 FORM5. Light fitted to the plate; model yaw front +-20, back +-30 deg. The sheet figure has slightly larger hips/thighs and thinner arms than the bald plate.').resize((int(W.width * 0.62), int((W.height + 54) * 0.62)), Image.LANCZOS).save(f'{OUT}/04_plate_vs_form4_vs_form5_3q.png')
print('04')

# ---------------------------------------------------------------- 07 mirror stripes (chest + pelvis)
cs = [dict(name='c0', yaw=0, xc=0.0, zc=1.21, w=0.30, res=[560, 560]), dict(name='c1', yaw=-25, xc=0.0, zc=1.21, w=0.30, res=[560, 560]), dict(name='c2', yaw=25, xc=0.0, zc=1.21, w=0.30, res=[560, 560]),
      dict(name='p0', yaw=180, xc=0.0, zc=0.90, w=0.34, res=[560, 560]), dict(name='p1', yaw=-155, xc=0.0, zc=0.90, w=0.34, res=[560, 560]), dict(name='p2', yaw=155, xc=0.0, zc=0.90, w=0.34, res=[560, 560])]
fs = render_set('stripe', cs, 'stripe', [('f2', CO2), ('f3', CO3)])
rows = []
for tag, lab, col in (('f2', f'FORM4 ({SHA2}…)', (90, 30, 30)), ('f3', f'FORM5 ({SHA3}…)', (20, 90, 50))):
    rows.append(strip([bgcomp(fs[tag][s['name']]) for s in cs], [f'{lab}: ' + n for n in ('bust front', 'bust +25', 'bust -25', 'glute back', 'glute 3/4 L', 'glute 3/4 R')]))
W = Image.new('RGB', (rows[0].width, sum(r.height for r in rows)))
y = 0
for r in rows:
    W.paste(r, (0, y)); y += r.height
banner(W, 'SURFACE QUALITY - mirror-stripe test (regular rings = smooth mounds/lobes; broken or angular stripes = creases)', 'FORM4 vs FORM5 on identical cameras.  Residual jumble at the arm junction (right edge of the bust views) is inherited from the original mesh.').resize((int(W.width * 0.55), int((W.height + 54) * 0.55)), Image.LANCZOS).save(f'{OUT}/07_mirror_stripe_test.png')
print('07')

# ---------------------------------------------------------------- 01 full torso before/after
views5 = [('front', 0), ('q3F', -22), ('side', -90), ('q3B', -158), ('back', 180)]
sh5 = [dict(name=n, yaw=y, xc=0.0, zc=1.08, w=0.80, res=[600, 820]) for n, y in views5]
for look in ('soft', 'clay'):
    f5 = render_set(f'full_{look}', sh5, look, [('f2', CO2), ('f3', CO3)])
    rows = []
    for tag, lab in (('f2', f'FORM4 ({SHA2}…)'), ('f3', f'FORM5 ({SHA3}…)')):
        rows.append(strip([bgcomp(f5[tag][n]) for n, _ in views5], [f'{lab}: {n}' for n, _ in views5]))
    W = Image.new('RGB', (rows[0].width, rows[0].height * 2))
    W.paste(rows[0], (0, 0)); W.paste(rows[1], (0, rows[0].height))
    banner(W, f'FEMALE TORSO FORM4 -> FORM5 ({look} light)', 'Only the chest-to-pelvis shell vertices move (positions only); head/neck, arms, hands, legs, feet are bit-identical.').resize((int(W.width * 0.6), int((W.height + 54) * 0.6)), Image.LANCZOS).save(f'{OUT}/01_torso_before_after_{look}.png')
print('01')

# ---------------------------------------------------------------- 02 / 03 silhouettes (reuse chat-7/form2 machinery)
from sil import *
from torso2 import plate_front, plate_back
d0 = np.load(HERE + '/data/orig.npz'); tri = d0['tri']
plate_bald = Image.open(ROOT + 'ArtDir/hero/base_lock/female_body_bald.jpg').convert('RGB')
plate_sheet = Image.open(ROOT + 'ArtDir/hero/base_lock/female_multiangle_body.jpg').convert('RGB')
chk = json.load(open(HERE + '/export/form5_gate_scripts_checks.json'))
chk3 = json.load(open(HERE + '/../female-torso-form4/export/form4_gate_scripts_checks.json'))
co2 = np.load(CO2).astype(np.float64); co3 = np.load(CO3).astype(np.float64)
S2 = 1.7039 / 288.5; V0 = 338.5; X0 = 791.5
def side_uv(co): return np.stack([X0 + co[:, 1] / S2, V0 - co[:, 2] / S2], 1)
def edge(mask):
    mi = Image.fromarray((mask * 255).astype(np.uint8)); mx = np.asarray(mi.filter(ImageFilter.MaxFilter(3))) > 0; mn = np.asarray(mi.filter(ImageFilter.MinFilter(3))) > 0; return mx & ~mn
def side_panel(co, col, title, box=(735, 92, 860, 262), sc=6):
    base = plate_sheet.crop(box).resize(((box[2] - box[0]) * sc, (box[3] - box[1]) * sc), Image.LANCZOS); base = ImageEnhance.Contrast(base).enhance(1.5)
    M = raster(side_uv(co), tri, size=(1280, 720), ss=6); E = Image.fromarray((edge(M) * 255).astype(np.uint8)).crop(box).resize(base.size, Image.NEAREST)
    arr = np.asarray(base).copy(); e = np.asarray(E) > 0; arr[e] = col; im = Image.fromarray(arr); dr = ImageDraw.Draw(im)
    FFn = np.load(HERE + '/data/plate_front_fine4.npy'); FBn = np.load(HERE + '/data/plate_back_fine4.npy')
    for z in np.arange(0.84, 1.381, 0.01):
        v = (V0 - z / S2 - box[1]) * sc
        yvs = [np.interp(z, FFn[0], FFn[1])] + ([np.interp(z, FBn[0], FBn[1])] if z <= 0.885 else [plate_back(z)] if z <= 1.30 else [])
        for yv in yvs:
            u = (X0 + yv / S2 - box[0]) * sc; dr.ellipse([u - 4, v - 4, u + 4, v + 4], outline=(255, 215, 0), width=2)
    label(im, title, (8, 8), sz=22); return im
pa = side_panel(co2, (255, 60, 60), 'FORM4 (red = model silhouette)'); pb = side_panel(co3, (40, 230, 90), 'FORM5 (green = model silhouette)')
W = Image.new('RGB', (pa.width * 2, pa.height)); W.paste(pa, (0, 0)); W.paste(pb, (pa.width, 0))
sx = chk['side_profile_torso_band_xor_z0.82_1.30']; se = chk['side_contour_error_mm']
sx3 = chk3['side_profile_torso_band_xor_z0.82_1.30']['after']; se3 = chk3['side_contour_error_mm']['after']
banner(W, 'SIDE PROFILE vs PLATE (torso rows z 0.84-1.38)', f"yellow rings = SUB-PIXEL plate contour (front z .84-1.38, back z .84-.88 + old table above). Torso-band side XOR (chat-7 gate script, z .82-1.30): original {100*sx['before']:.1f}% -> FORM4 {100*sx3:.1f}% -> FORM5 {100*sx['after']:.1f}% (gate <=5%) | old-table contour err mean FORM4 {se3['front_mean']:.1f}/{se3['back_mean']:.1f} mm -> FORM5 {se['after']['front_mean']:.1f}/{se['after']['back_mean']:.1f} mm (front/back)").save(f'{OUT}/02_side_profile_overlay.png')
outs = []
for view, cx, name in (('front', 440, 'F_front_target.png'), ('back', 847, 'F_back_target.png')):
    T_ = np.asarray(Image.open(ROOT + 'ArtDir/hero/base_lock/proof/masks/' + name).convert('L')) > 127
    M = raster(project(co3, view), tri); arr = np.asarray(plate_bald).copy(); arr[edge(T_)] = (0, 200, 0); arr[edge(M)] = (255, 0, 0)
    crop = Image.fromarray(arr).crop((cx - 125, 125, cx + 125, 420)).resize((750, 885), Image.NEAREST); label(crop, view.upper() + ' (FORM5)  red=model  green=plate', (8, 8), sz=20); outs.append(crop)
W = Image.new('RGB', (1500, 885)); W.paste(outs[0], (0, 0)); W.paste(outs[1], (750, 0))
b = chk['torso_visible_edge_run_xor_rows_z0.82_1.165']['after']
banner(W, 'FRONT / BACK SILHOUETTE vs PLATE (female_body_bald, project framing)', f"torso visible-edge XOR (rows below armpit, arms excluded; chat-7 gate script): front {100*b['front']:.2f}%  back {100*b['back']:.2f}%  (gate <=5%; x untouched except <=2.6 mm denoise)").save(f'{OUT}/03_front_back_silhouette_overlay.png')
print('02/03')
print('proofs written', OUT)
