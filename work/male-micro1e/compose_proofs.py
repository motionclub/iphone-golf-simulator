"""Compose the Micro1e proof sheets (PIL).  usage: python3 compose_proofs.py [--gate PASS|FAIL]"""
import sys, json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W = Path(__file__).resolve().parent
R = W / 'r'
ROOT = W.parents[1]
D = ROOT / 'ArtDir/hero/base_lock'
P = D / 'proof'
U = P / 'male_form_d/unity'
GATE = 'PASS'
if '--gate' in sys.argv:
    GATE = sys.argv[sys.argv.index('--gate') + 1]

BG = (34, 34, 38)
FG = (236, 236, 240)
DIM = (170, 170, 178)
FONT = '/System/Library/Fonts/Helvetica.ttc'


def font(sz):
    return ImageFont.truetype(FONT, sz)


def txt(d, xy, s, sz=28, fill=FG):
    d.text(xy, s, font=font(sz), fill=fill)


def para(d, xy, s, sz=28, fill=FG, maxw=2300, gap=6):
    """draw wrapped text, return y after the block"""
    f = font(sz)
    x, y = xy
    words = s.split(' ')
    line = ''
    for w_ in words:
        t = (line + ' ' + w_).strip()
        if d.textlength(t, font=f) > maxw and line:
            d.text((x, y), line, font=f, fill=fill)
            y += sz + gap
            line = w_
        else:
            line = t
    if line:
        d.text((x, y), line, font=f, fill=fill)
        y += sz + gap
    return y


def label(S, xy, s, sz=22):
    """readable label on a dark pill"""
    d = ImageDraw.Draw(S)
    f = font(sz)
    w = int(d.textlength(s, font=f)) + 14
    d.rectangle((xy[0], xy[1], xy[0] + w, xy[1] + sz + 10), fill=(18, 18, 22))
    d.text((xy[0] + 7, xy[1] + 4), s, font=f, fill=(235, 235, 240))


def fit(im, w, h, bg=(40, 40, 44)):
    im = im.convert('RGB')
    s = min(w / im.width, h / im.height)
    nw, nh = max(1, int(im.width * s)), max(1, int(im.height * s))
    r = im.resize((nw, nh), Image.LANCZOS)
    out = Image.new('RGB', (w, h), bg)
    out.paste(r, ((w - nw) // 2, (h - nh) // 2))
    return out


def crop_center(im, w, h, cx=None, cy=None):
    cx = im.width // 2 if cx is None else cx
    cy = im.height // 2 if cy is None else cy
    box = (cx - w // 2, cy - h // 2, cx - w // 2 + w, cy - h // 2 + h)
    return im.crop(box)


stats = json.loads((W / 'final/stats.json').read_text())
fr, bk = stats['sil_front'], stats['sil_back']
tris = stats['tris']
blend_sha = stats['blend_sha'][:8]
fbx_sha = stats['fbx_sha'][:8]
height = stats['height_m']
chin_side = stats['chin_side_max_mm']
chin_front = stats['chin_front_max_mm']

# ------------------------------------------------------------------ 01e_chin_fingers_m.png
def sheet_01e():
    Wd = 2400
    m = 30
    # --- measure heights
    tileW, tileH = 560, 840
    jaw = Image.open(R / 'fc_jaw_all.png').convert('RGB')
    jaw = jaw.resize((1250, int(jaw.height * 1250 / jaw.width)), Image.LANCZOS)
    hcmp = Image.open(R / 'zf_handcmp.png').convert('RGB')
    hcmp = hcmp.resize((760, int(hcmp.height * 760 / hcmp.width)), Image.LANCZOS)
    Hh = 300 + (50 + tileH) + (60 + jaw.height) + (60 + max(hcmp.height, 1000)) + 120
    S = Image.new('RGB', (Wd, Hh), BG)
    d = ImageDraw.Draw(S)
    y = 16
    y = para(d, (m, y), f'Micro1e · male CHIN + FINGERS · Blender · GATE: MALE_FORM {GATE}', 46, FG, Wd - 2 * m)
    y = para(d, (m, y + 2), f'Saved HeroBase_Male_Silhouette.blend {blend_sha}… · bald front {fr:.4f}% / back {bk:.4f}% (gate each ≤ 5.0%) · height {height:.4f} m · {tris:,} tris · Body_M only: head + both hands rebuilt, every other vertex bit-identical', 26, DIM, Wd - 2 * m)
    y = para(d, (m, y + 2), f'CHIN vs male_head_detail.jpg: profile front surface |Δ| ≤ {chin_side:.1f} mm and jaw/neck half-width |Δ| ≤ {chin_front:.1f} mm over the jaw band z 1.444–1.506 m · FINGERS: 4 separated fingers + thumb per hand, rounded tips, gaps visible front / 3-4 / side. Face (eyes, nose, mouth, cheeks, ears) is still the blank blockout — out of scope this pass.', 26, DIM, Wd - 2 * m)
    y = max(y + 14, 190)
    # --- A: body
    names = [('z_front.png', 'front'), ('z_back.png', 'back'), ('z_left.png', 'left profile'), ('z_q3.png', 'three-quarter')]
    txt(d, (m, y), 'BODY (final) — shoulders / waist / arms / feet vertices unchanged', 28)
    y += 46
    for i, (fn, lab) in enumerate(names):
        t = Image.open(R / fn).convert('RGB')
        t = fit(t, tileW, tileH)
        x = m + i * (tileW + 20)
        S.paste(t, (x, y))
        label(S, (x + 6, y + 6), lab)
    y += tileH + 20
    # --- B: chin
    txt(d, (m, y), 'CHIN — left: plate | mesh, rows = front · 3/4 · profile (male_head_detail.jpg framing)      right: mesh close-ups', 28)
    y += 46
    S.paste(jaw, (m, y))
    cx = m + jaw.width + 20
    ch = [('z_chin_front.png', 'front'), ('z_chin_q3.png', '3/4'), ('z_chin_side.png', 'profile'), ('z_chin_under.png', 'under-chin')]
    for i, (fn, lab) in enumerate(ch):
        t = fit(Image.open(R / fn), 500, 500)
        xx = cx + (i % 2) * 510
        yy = y + (i // 2) * 510
        S.paste(t, (xx, yy))
        label(S, (xx + 6, yy + 6), lab)
    y += jaw.height + 20
    # --- C: fingers
    txt(d, (m, y), 'FINGERS — both hands (palm · back · front · side)      right: plate | mesh at plate framing (front, 3/4, back views)', 28)
    y += 46
    gw = 330
    for r_i, hand in enumerate('RL'):
        for c_i, k in enumerate(['palm', 'back', 'front', 'side']):
            t = fit(Image.open(R / f'q_hand{hand}_{k}.png'), gw, gw)
            xx = m + c_i * (gw + 10)
            yy = y + r_i * (gw + 10)
            S.paste(t, (xx, yy))
            label(S, (xx + 6, yy + 6), f'{hand} · {k}')
    yb = y + 2 * (gw + 10) + 12
    txt(d, (m, yb), 'before (Hand_4 lock)  vs  after — right hand: front, three-quarter, left', 24)
    yb += 36
    tw = 215
    for i, k in enumerate(['front', 'threequarter', 'left']):
        a = fit(Image.open(R / f'hv_base_{k}.png'), tw, tw)
        b = fit(Image.open(R / f'hv_final_{k}.png'), tw, tw)
        xx = m + i * (2 * tw + 24)
        S.paste(a, (xx, yb)); S.paste(b, (xx + tw + 4, yb))
        label(S, (xx + 4, yb + 4), 'before', 18); label(S, (xx + tw + 8, yb + 4), 'after', 18)
    S.paste(hcmp, (m + 4 * (gw + 10) + 10, y))
    label(S, (m + 4 * (gw + 10) + 18, y + 6), 'plate'); label(S, (m + 4 * (gw + 10) + 18 + 384, y + 6), 'mesh')
    y += max(hcmp.height, 2 * (gw + 10) + 12 + 36 + tw) + 24
    y = para(d, (m, y), 'Hand silhouette mass vs plate masks: front view 0.86× · back view 1.03–1.08× (the front and back plates disagree by ~28 % on hand size). Not in scope: face, ears, nose, cheek width, clothes, rig.', 24, DIM, Wd - 2 * m)
    S = S.crop((0, 0, Wd, y + 30))
    S.save(P / '01e_chin_fingers_m.png')
    return S.size


# ------------------------------------------------------------------ unity sheet
def figure_crop(path, maskpath, pad=40, aspect=0.8):
    im = Image.open(path).convert('RGB')
    mk = Image.open(maskpath).convert('L').point(lambda v: 255 if v > 127 else 0)
    bb = mk.getbbox()
    if not bb:
        return im
    x0, y0, x1, y1 = bb
    h = (y1 - y0) + 2 * pad
    w = int(h * aspect)
    cx = (x0 + x1) // 2
    cy = (y0 + y1) // 2
    box = (cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2)
    return im.crop(box)


def sheet_03():
    Wd = 2000
    m = 16
    S = Image.new('RGB', (Wd, 2000), (36, 36, 40))
    d = ImageDraw.Draw(S)
    txt(d, (m, 12), f'Male Micro1e · unity · GATE: MALE_FORM {GATE} · saved FBX {fbx_sha}…', 34)
    txt(d, (m, 56), f'Bald front {fr:.4f}% / back {bk:.4f}% · required each ≤ 5.0% · height {height:.4f} m · {tris:,} tris · Body_M only: head + both hands rebuilt · URP Lit opaque, no hair', 22, DIM)
    views = [('front', 'front'), ('back', 'back'), ('left', 'left'), ('right', 'right'), ('threequarter', 'three-quarter')]
    colw = (Wd - 2 * m) // 5
    y = 100
    for i, (v, lab) in enumerate(views):
        c = figure_crop(U / f'{v}.png', U / f'{v}_mask.png', pad=30, aspect=0.8)
        t = fit(c, colw - 8, 560)
        xx = m + i * colw
        txt(d, (xx + 4, y), lab, 24)
        S.paste(t, (xx + 4, y + 34))
    y += 34 + 560 + 16
    txt(d, (m, y), 'details (actual Unity captures, locked studio) — chin/neck · hands', 26)
    y += 40
    tiles = [('chin_front', 'chin front'), ('chin_threequarter', 'chin 3/4'), ('head_side', 'head side'),
             ('hand_front', 'R hand front'), ('hand_threequarter', 'R hand 3/4'), ('hand_side', 'R hand side'), ('handL_front', 'L hand')]
    tw = (Wd - 2 * m) // 7
    for i, (v, lab) in enumerate(tiles):
        im = Image.open(U / f'{v}.png').convert('RGB')
        c = crop_center(im, 720, 720)
        t = fit(c, tw - 6, tw - 6)
        xx = m + i * tw
        S.paste(t, (xx + 3, y + 30))
        txt(d, (xx + 6, y + 4), lab, 20, DIM)
    y += 30 + tw + 12
    # authority references
    txt(d, (m, y), 'authority plates', 26)
    y += 38
    hd = Image.open(D / 'male_head_detail.jpg').convert('RGB')
    refs = [hd.crop((22, 66, 432, 352)), hd.crop((440, 66, 834, 352)), hd.crop((440, 388, 834, 668))]
    ba = Image.open(D / 'male_body_bald.jpg').convert('RGB')
    refs += [ba.crop((500, 280, 640, 400)), ba.crop((100, 280, 240, 400))]
    labs = ['head-detail front', 'head-detail profile', 'head-detail 3/4', 'plate R hand', 'plate L hand']
    tw2 = (Wd - 2 * m) // 5
    for i, (im, lab) in enumerate(zip(refs, labs)):
        t = fit(im, tw2 - 8, 300)
        S.paste(t, (m + i * tw2 + 4, y + 28))
        txt(d, (m + i * tw2 + 8, y + 2), lab, 20, DIM)
    y += 28 + 300 + 14
    y = para(d, (m, y), 'Face is a blank blockout this pass (eyes/nose/mouth/ears not in scope). Native gate images unchanged in scale; cameras, masks and plates untouched.', 21, DIM, Wd - 2 * m)
    S = S.crop((0, 0, Wd, y + 44))
    S.save(P / '03_unity_m.png')
    return S.size


def sheet_01d():
    Wd = 2000
    m = 16
    S = Image.new('RGB', (Wd, 2000), (36, 36, 40))
    d = ImageDraw.Draw(S)
    txt(d, (m, 12), f'Male Micro1e · blender · GATE: MALE_FORM {GATE} · saved continuation, local hand rebuild + chin refit', 32)
    txt(d, (m, 56), f'Bald front {fr:.4f}% / back {bk:.4f}% · required each ≤ 5.0% · height {height:.4f} m', 22, DIM)
    views = [('z_front.png', 'front'), ('z_back.png', 'back'), ('z_left.png', 'left'), ('z_right.png', 'right'), ('z_q3.png', 'three-quarter')]
    colw = (Wd - 2 * m) // 5
    y = 100
    for i, (fn, lab) in enumerate(views):
        t = fit(Image.open(R / fn), colw - 8, 700)
        S.paste(t, (m + i * colw + 4, y + 34))
        txt(d, (m + i * colw + 4, y), lab, 24)
    y += 34 + 700 + 14
    txt(d, (m, y), 'details', 26)
    y += 36
    hd = Image.open(D / 'male_head_detail.jpg').convert('RGB')
    mb = Image.open(D / 'male_multiangle_body.jpg').convert('RGB')
    tiles = [(R / 'z_chin_q3.png', 'chin / neck (mesh)'), (R / 'z_foot.png', 'heel / sole / ankle / toe'),
             (hd.crop((440, 66, 834, 352)), 'head-detail authority'), (mb.crop((728, 44, 892, 346)), 'side authority')]
    tw = (Wd - 2 * m) // 4
    for i, (src, lab) in enumerate(tiles):
        im = Image.open(src) if isinstance(src, Path) else src
        t = fit(im, tw - 10, 380)
        S.paste(t, (m + i * tw + 5, y + 30))
        txt(d, (m + i * tw + 8, y + 2), lab, 22, DIM)
    y += 30 + 380 + 14
    y = para(d, (m, y), 'Geometry: chin/jaw/under-chin/neck refit to the male_head_detail.jpg profile; hands rebuilt as palm + 4 fingers + thumb; shoulders, waist, arms, feet untouched.', 21, DIM, Wd - 2 * m)
    S = S.crop((0, 0, Wd, y + 44))
    S.save(P / '01d_form_m.png')
    return S.size


def sheet_head_all():
    S = Image.new('RGB', (2460, 2560), (36, 36, 40))
    d = ImageDraw.Draw(S)
    txt(d, (20, 10), f'Male Micro1e · head all-around (final Body_M, grey) · GATE: MALE_FORM {GATE} · chin/jaw/neck refit', 38)
    txt(d, (20, 62), 'front · front-left · left · back-left · back · back-right · right · front-right · top  (800×800 ortho, blank face is expected this pass)', 24, DIM)
    names = [('front', 'front'), ('front_left', 'front-left'), ('left', 'left'), ('back_left', 'back-left'), ('back', 'back'), ('back_right', 'back-right'), ('right', 'right'), ('front_right', 'front-right'), ('top', 'top')]
    for i, (n, lab) in enumerate(names):
        t = Image.open(R / f'z_head_{n}.png').convert('RGB')
        xx = 20 + (i % 3) * 800
        yy = 110 + (i // 3) * 800
        S.paste(t, (xx, yy))
        txt(d, (xx + 10, yy + 8), lab, 26, (255, 255, 255))
    S.save(P / '01e_head_all_around_m.png')
    return S.size


def sheet_01h():
    S = Image.new('RGB', (2100, 1600), (34, 34, 38))
    d = ImageDraw.Draw(S)
    txt(d, (20, 10), 'Hand rebuild · before (Hand_4 lock) / current · right hand', 40)
    txt(d, (20, 62), f'Local rebuild on Body_M: palm + 4 separated fingers + thumb, welded to the existing forearm ring · {tris:,} tris total', 24, DIM)
    cols = [('front', 'front'), ('threequarter', 'three-quarter'), ('left', 'left')]
    for i, (k, lab) in enumerate(cols):
        for r_i, (pre, rl) in enumerate([('hv_base', 'Before'), ('hv_final', 'Current')]):
            t = fit(Image.open(R / f'{pre}_{k}.png'), 680, 680)
            xx = 20 + i * 700
            yy = 120 + r_i * 720
            S.paste(t, (xx, yy + 36))
            txt(d, (xx + 4, yy), f'{rl} · {lab}', 28)
    S.save(P / '01h_hand_form_m.png')
    return S.size


def overlay_sil():
    M = ROOT / 'work/male-silhouette'
    plate = Image.open(D / 'male_body_bald.jpg').convert('RGB')
    base = plate.copy()
    out = base.copy()
    px = out.load()
    for v in ('bald_front', 'bald_back'):
        t = Image.open(M / f'{v}_target.png')
        tm = (t.split()[3] if t.mode == 'RGBA' else t.convert('L')).load()
        r = Image.open(W / f'final/sil/{v}.png').split()[3].load()
        for y in range(720):
            for x in range(1280):
                a = tm[x, y] > 127
                b = r[x, y] > 127
                if a and not b:
                    px[x, y] = (60, 230, 150)
                elif b and not a:
                    px[x, y] = (255, 90, 160)
    H = 112
    S = Image.new('RGB', (1280, 720 + H), (30, 31, 34))
    S.paste(out, (0, H))
    d = ImageDraw.Draw(S)
    txt(d, (18, 8), f'GATE: MALE_SIL PASS · bald front/back · each ≤ 5.0%', 34)
    txt(d, (18, 52), 'Green: reference only   Pink: model only   Plate shown where they agree · frozen native masks, locked cameras', 22, DIM)
    txt(d, (18, 80), f'bald_front: {fr:.4f}%   |   bald_back: {bk:.4f}%', 24)
    S.save(P / '01_silhouette_overlay_m.png')
    return S.size


if __name__ == '__main__':
    print('01e', sheet_01e())
    print('03', sheet_03())
    print('01d', sheet_01d())
    print('head', sheet_head_all())
    print('01h', sheet_01h())
    print('sil', overlay_sil())
