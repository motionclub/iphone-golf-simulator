"""03_unity_m.png for Micro1h: Unity head close-ups + authority plates + body context + stats.  python3 compose_03h.py <checks.json> <out.png>"""
import sys, json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
R = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
U = R / 'work/male-micro1l-head/proof/unity_captures_k11'; FL = R / 'ArtDir/hero/base_lock/face_lock'
st = json.load(open(sys.argv[1])); out = Path(sys.argv[2])
f = lambda s: ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', s)
FG = (236, 236, 240); DIM = (170, 170, 178)


def fit(im, w, h, bg=(40, 40, 44)):
    im = im.convert('RGB'); s = min(w / im.width, h / im.height); r = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    o = Image.new('RGB', (w, h), bg); o.paste(r, ((w - r.width) // 2, (h - r.height) // 2)); return o


def fig(name, pad=30, aspect=0.8):
    im = Image.open(U / f'{name}.png').convert('RGB'); mk = Image.open(U / f'{name}_mask.png').convert('L').point(lambda v: 255 if v > 127 else 0)
    x0, y0, x1, y1 = mk.getbbox(); h = (y1 - y0) + 2 * pad; w = int(h * aspect); cx = (x0 + x1) // 2; cy = (y0 + y1) // 2
    return im.crop((cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2))


def cc(im, w, h): return im.crop(((im.width - w) // 2, (im.height - h) // 2, (im.width + w) // 2, (im.height + h) // 2))


Wd = 2000; m = 16; S = Image.new('RGB', (Wd, 2470), (36, 36, 40)); d = ImageDraw.Draw(S)
d.text((m, 12), f"Male Micro1k · unity · {st['gate_line']} · saved FBX {st['fbx_sha256'][:8]}…", font=f(34), fill=FG)
d.text((m, 56), f"bald front {st['sil_front']:.4f}% / back {st['sil_back']:.4f}% (Body_M; with Face_M {st['sil_front_face']:.4f}% / {st['sil_back_face']:.4f}%) · required each ≤ 5.0% · Body_M {st['body_tris']:,} tris (~60k approved) + Face_M {st['face_tris']:,} tris · face-zone edge mean {st['face_edge_mean_mm']:.2f} mm", font=f(21), fill=DIM)
y = 96
d.text((m, y), 'head close-ups (actual Unity captures, locked studio)', font=f(26), fill=FG); y += 36
tiles = [('face_front', 'front'), ('face_threequarter', 'three-quarter'), ('face_profile', 'profile'), ('face_threequarter_back', '3/4 back')]
tw = (Wd - 2 * m) // 4
for i, (v, lab) in enumerate(tiles):
    im = Image.open(U / f'{v}.png').convert('RGB'); c = cc(im, 760, 720)
    S.paste(fit(c, tw - 8, int((tw - 8) * 720 / 760)), (m + i * tw + 4, y + 30)); d.text((m + i * tw + 8, y + 4), lab, font=f(20), fill=DIM)
y += 30 + int((tw - 8) * 720 / 760) + 14
d.text((m, y), 'whole head (Unity) and ear / eye close-ups', font=f(26), fill=FG); y += 36
tiles = [('head_front', 'head front'), ('head_threequarter', 'head 3/4'), ('ear_side', 'ear side'), ('eye_front', 'eyes')]
for i, (v, lab) in enumerate(tiles):
    im = Image.open(U / f'{v}.png').convert('RGB'); c = cc(im, 760, 720)
    S.paste(fit(c, tw - 8, int((tw - 8) * 720 / 760)), (m + i * tw + 4, y + 30)); d.text((m + i * tw + 8, y + 4), lab, font=f(20), fill=DIM)
y += 30 + int((tw - 8) * 720 / 760) + 14
d.text((m, y), 'authority plates (face_lock crops)', font=f(26), fill=FG); y += 36
refs = [('01_front_face.png', 'plate front'), ('04_threequarter_front_left.png', 'plate 3/4'), ('02_left_profile.png', 'plate profile'), ('15_ma_threequarter_back_left.png', 'plate 3/4 back')]
for i, (fn, lab) in enumerate(refs):
    im = Image.open(FL / fn).convert('RGB')
    S.paste(fit(im, tw - 8, 330), (m + i * tw + 4, y + 28)); d.text((m + i * tw + 8, y + 2), lab, font=f(20), fill=DIM)
y += 28 + 330 + 14
d.text((m, y), 'body context', font=f(26), fill=FG); y += 36
views = [('front', 'front'), ('back', 'back'), ('left', 'left'), ('threequarter', 'three-quarter'), ('head_side', 'head side')]
colw = (Wd - 2 * m) // 5
for i, (v, lab) in enumerate(views):
    c = fig(v) if v != 'head_side' else cc(Image.open(U / 'head_side.png').convert('RGB'), 720, 720)
    S.paste(fit(c, colw - 8, 520), (m + i * colw + 4, y + 30)); d.text((m + i * colw + 4, y + 2), lab, font=f(22), fill=DIM)
y += 30 + 520 + 14
d.text((m, y), 'Micro1k: head+neck zone + nape strip (z 1.36-1.40, 20 verts, <= 2 mm): neck crease undone, mandible edge, softer cheeks. Else bit-identical. No hair.', font=f(21), fill=DIM)
S = S.crop((0, 0, Wd, y + 44)); S.save(out); print(out, S.size)
