"""Proof sheets for Micro1l (Pillow; run with Blender's python3.13 + PYTHONPATH=pylib).
python3.13 compose_proof_l.py <which: jaw|cheek|lips|stubble|all> [after_tag=l2f]
Writes proof/*.png (work dir).  Plate-framed crops use the 4x renders r/ul_start_p4 (Micro1k = current ArtDir) and r/ul_<after>_p4."""
import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1l-head')
from j_lib import *
from PIL import ImageFilter, ImageFont
import os
which = sys.argv[1]; AF = sys.argv[2] if len(sys.argv) > 2 else 'l2f'; BEFORE_TAG = os.environ.get('BEFORE_TAG', 'start'); PFX = os.environ.get('PFX', 'male_head_micro1l'); BEFORE_LAB = os.environ.get('BEFORE_LAB', 'Micro1k (before)'); AFTER_LAB = os.environ.get('AFTER_LAB', 'Micro1l (after)'); CLAY = os.environ.get('CLAY_DIR', 'r/clay_final'); BF = os.environ.get('BEFORE_F', 'r/ul_start_f'); STUB_SFX = os.environ.get('STUB', 'l2')
OUT = W / 'proof'; OUT.mkdir(exist_ok=True)
F = lambda s: ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', s)
DIRS = dict(k=W / f'r/ul_{BEFORE_TAG}_p4', l=W / f'r/ul_{AF}_p4')
RS = 4.0


def crop_view(view, zlo, zhi, wide=1.0, y0=None, y1=None, up=3.0):
    """plate crop + the two renders cropped identically; returns [(label, img)]"""
    box = BOXES[view]
    if view in ('q3L', 'q3R'):
        r0 = int(397 + (TOP - zhi) / K); r1 = int(397 + (TOP - zlo) / K); c0, c1 = (60, 300) if view == 'q3L' else (470, 710)
        cm = 0.5 * (c0 + c1); hw = 0.5 * (c1 - c0) * wide; c0 = int(cm - hw); c1 = int(cm + hw)
    elif view == 'front':
        r0 = int(rowz(zhi)); r1 = int(rowz(zlo)); c0 = int(CX - 0.105 / K * wide); c1 = int(CX + 0.105 / K * wide)
    else:
        a = -0.15 * wide if y0 is None else y0; b = 0.03 if y1 is None else y1
        r0 = int(rowz(zhi)); r1 = int(rowz(zlo)); c0 = int(prof_col(a, view)); c1 = int(prof_col(b, view))
    pl = PLATE.crop((c0, r0, c1, r1)); pl = pl.resize((int(pl.width * up), int(pl.height * up)), Image.LANCZOS); tiles = [pl]
    for key in ('k', 'l'):
        rn = Image.open(DIRS[key] / f'plate_{view}.png').convert('RGB')
        tiles.append(rn.crop((int((c0 - box[0]) * RS), int((r0 - box[1]) * RS), int((c1 - box[0]) * RS), int((r1 - box[1]) * RS))).resize(pl.size, Image.LANCZOS))
    return tiles


def boost(im, k=4.0, sig=12):
    g = np.asarray(im.convert('L')).astype(float); b = np.asarray(im.convert('L').filter(ImageFilter.GaussianBlur(sig))).astype(float)
    return Image.fromarray(np.clip(128 + (g - b) * k, 0, 255).astype(np.uint8)).convert('RGB')


def label(im, text, size=16, fill=(255, 255, 0), dy=5):
    im = im.copy(); ImageDraw.Draw(im).text((8, dy), text, font=F(size), fill=fill); return im


def row_of(tiles, labels, dy=5):
    Wt = sum(t.width for t in tiles) + 6 * (len(tiles) - 1); sheet = Image.new('RGB', (Wt, tiles[0].height), (14, 14, 16)); x = 0
    for t, l in zip(tiles, labels): sheet.paste(label(t, l, dy=dy), (x, 0)); x += t.width + 6
    return sheet


def stack(rows, title, out, gap=8, tw=None):
    Wd = max(r.width for r in rows); H = sum(r.height for r in rows) + gap * (len(rows) - 1) + 34
    sheet = Image.new('RGB', (Wd, H), (14, 14, 16)); ImageDraw.Draw(sheet).text((8, 8), title, font=F(18), fill=(255, 255, 255)); y = 34
    for r in rows: sheet.paste(r, (0, y)); y += r.height + gap
    sheet.save(out); print(out, sheet.size)


def clay_rows(cr_dir, light, views, names, labels):
    im = Image.open(cr_dir / f'{light}_' + '-'.join(views) + '.png') if False else None


LAB = ['PLATE', BEFORE_LAB, AFTER_LAB]
if which in ('jaw', 'all'):
    rows = []
    rows.append(row_of(crop_view('front', 1.40, 1.60, 0.95, up=2.6), [f'{l} - front' for l in LAB]))
    rows.append(row_of(crop_view('q3L', 1.42, 1.60, 1.0, up=2.6), [f'{l} - 3/4 L' for l in LAB]))
    rows.append(row_of(crop_view('q3R', 1.42, 1.60, 1.0, up=2.6), [f'{l} - 3/4 R' for l in LAB]))
    rows.append(row_of(crop_view('left', 1.42, 1.60, 1.0, y0=-0.18, y1=0.0, up=2.6), [f'{l} - profile' for l in LAB]))
    stack(rows, f'Micro1l JAW - plate | {BEFORE_LAB} | {AFTER_LAB}, plate-framed, Unity-like soft studio', OUT / f'{PFX}_JAW_plate_1k_1l_soft.png')
    # boosted-contrast version (reveals tonal edge relief the way the plate shows it)
    rows = []
    for v, z0, z1, wd, kw, nm in (('front', 1.40, 1.60, 0.95, {}, 'front'), ('q3L', 1.42, 1.60, 1.0, {}, '3/4 L'), ('left', 1.42, 1.60, 1.0, dict(y0=-0.18, y1=0.0), 'profile')):
        t = crop_view(v, z0, z1, wd, up=2.6, **kw); t = [t[0]] + [t[1], t[2]]
        rows.append(row_of([boost(x, 3.0 if i == 0 else 4.5) for i, x in enumerate(t)], [f'{l} - {nm} (local-contrast x4)' for l in LAB]))
    stack(rows, f'Micro1l JAW - local-contrast view (edge relief): plate | {BEFORE_LAB} | {AFTER_LAB}', OUT / f'{PFX}_JAW_plate_1k_1l_contrast.png')
    # clay (hard + soft)
    for light in ('hard', 'soft'):
        a = Image.open(W / f'{CLAY}/{light}_jaw_f-jaw_q3-jaw_s-back_q-cheek_f-cheek_q.png').convert('RGB'); Wc = 640
        names = ['jaw_f', 'jaw_q3', 'jaw_s', 'back_q']; rows_ = []
        for r, nm in enumerate(names):
            t = [a.crop((c * Wc, r * Wc, (c + 1) * Wc, (r + 1) * Wc)) for c in range(2)]
            rows_.append(row_of(t, [f'{BEFORE_LAB} {nm} clay-{light}', f'{AFTER_LAB} {nm} clay-{light}'], dy=612))
        # 2x2 grid to keep the sheet compact
        g = Image.new('RGB', (rows_[0].width * 2 + 8, rows_[0].height * 2 + 8), (14, 14, 16))
        for i, rr in enumerate(rows_): g.paste(rr, ((i % 2) * (rr.width + 8), (i // 2) * (rr.height + 8)))
        stack([g], f'Micro1l JAW - clay ({light} light, matte grey): front / 3/4 / profile / 3/4-back: {BEFORE_LAB} | {AFTER_LAB}', OUT / f'{PFX}_JAW_clay_{light}.png')
    # 3/4 back (Unity-like) vs plates 15/16
    FL = R / 'ArtDir/hero/base_lock/face_lock'
    tl = []
    for nm, d_ in ((BEFORE_LAB, W / BF), (AFTER_LAB, W / f'r/ul_{AF}_f')):
        tl.append(Image.open(d_ / 'face_threequarter_back.png').convert('RGB'))
    pl = Image.open(FL / '15_ma_threequarter_back_left.png').convert('RGB'); s = tl[0].height / pl.height; pl = pl.resize((int(pl.width * s), tl[0].height), Image.LANCZOS)
    jq = [Image.open(d_ / 'jaw_q.png').convert('RGB') for d_ in (W / BF, W / f'r/ul_{AF}_f')]
    rows = [row_of([pl] + tl, ['PLATE 15 (3/4 back; shirt/hair-free head)', f'{BEFORE_LAB} - 3/4 back', f'{AFTER_LAB} - 3/4 back']), row_of(jq, [f'{BEFORE_LAB} jaw 3/4 (soft)', f'{AFTER_LAB} jaw 3/4 (soft)'])]
    stack(rows, f'Micro1l JAW - 3/4-back and jaw 3/4: {BEFORE_LAB} | {AFTER_LAB} (Unity-like soft studio)', OUT / f'{PFX}_JAW_3q_back.png')

if which in ('cheek', 'all'):
    rows = []
    rows.append(row_of(crop_view('q3L', 1.47, 1.60, 0.9, up=3.2), [f'{l} - 3/4 L cheek' for l in LAB]))
    rows.append(row_of(crop_view('q3R', 1.47, 1.60, 0.9, up=3.2), [f'{l} - 3/4 R cheek' for l in LAB]))
    rows.append(row_of(crop_view('front', 1.47, 1.60, 1.0, up=3.0), [f'{l} - front cheeks' for l in LAB]))
    stack(rows, f'Micro1l CHEEK - plate | {BEFORE_LAB} | {AFTER_LAB}, 3/4 + front crops', OUT / f'{PFX}_CHEEK_plate_before_after.png')
    for light in ('hard', 'soft'):
        a = Image.open(W / f'{CLAY}/{light}_jaw_f-jaw_q3-jaw_s-back_q-cheek_f-cheek_q.png').convert('RGB'); Wc = 640
        t = []
        for r, nm in ((4, 'cheek_f'), (5, 'cheek_q')):
            t.append(row_of([a.crop((c * Wc, r * Wc, (c + 1) * Wc, (r + 1) * Wc)) for c in range(2)], [f'{BEFORE_LAB} {nm} clay-{light}', f'{AFTER_LAB} {nm} clay-{light}'], dy=612))
        stack(t, f'Micro1l CHEEK - clay ({light} light): {BEFORE_LAB} | {AFTER_LAB}', OUT / f'{PFX}_CHEEK_clay_{light}.png')

if which in ('lips', 'all'):
    rows = []
    rows.append(row_of(crop_view('front', 1.478, 1.538, 0.55, up=6.0), [f'{l} - front lips' for l in LAB]))
    rows.append(row_of(crop_view('q3L', 1.478, 1.538, 0.55, up=6.0), [f'{l} - 3/4 lips' for l in LAB]))
    rows.append(row_of(crop_view('left', 1.46, 1.54, 1.0, y0=-0.185, y1=-0.085, up=6.0), [f'{l} - profile lips' for l in LAB]))
    stack(rows, f'Micro1l LIPS - plate | {BEFORE_LAB} | {AFTER_LAB}', OUT / f'{PFX}_LIPS_plate_before_after.png')

if which in ('stubble', 'all'):
    a = [Image.open(W / f'r/ul_{STUB_SFX}f_faces' / f'{v}.png').convert('RGB') for v in ('face_front', 'face_threequarter', 'face_profile')] if (W / f'r/ul_{STUB_SFX}f_faces').exists() else None
    if a:
        b = [Image.open(W / f'r/ul_{STUB_SFX}sA_faces' / f'{v}.png').convert('RGB') for v in ('face_front', 'face_threequarter', 'face_profile')]
        r1 = row_of(a, ['no stubble - front', 'no stubble - 3/4', 'no stubble - profile']); r2 = row_of(b, ['light stubble EXAMPLE - front', 'light stubble EXAMPLE - 3/4', 'light stubble EXAMPLE - profile'])
        stack([r1, r2], 'Micro1l STUBBLE EXAMPLE (preview only - shader overlay on the same mesh, not part of the mesh/FBX)', OUT / f'{PFX}_STUBBLE_example.png')
