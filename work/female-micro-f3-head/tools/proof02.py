"""proof/02_match_f_head.png : plate vs mesh for the 16 face_lock_f crops (plate | Unity-like render | overlay with silhouette edges).
python3.13 proof02.py <assembled.blend> <out.png> [rerender 1|0]
01-06: head-detail panels with the calibrated cameras;  07-08: body plate front/back (0.0025954 m/px);  09-16: multi-angle plate (angle/placement only; yaw chosen by silhouette IoU)."""
import sys, os, json, math, subprocess
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f3-head/tools')
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1i/pylib')
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import fl
blend, out = sys.argv[1], sys.argv[2]; rerender = (sys.argv[3] != '0') if len(sys.argv) > 3 else True
B = '/Applications/Blender.app/Contents/MacOS/Blender'
RD = fl.W / 'renders/p02'; RD.mkdir(exist_ok=True, parents=True)
SB = 0.0025954; ZT = 1.7044; SM = 0.00575
UP = 4
crops = json.load(open(fl.PLATES / 'face_lock_f/crop_boxes.json'))
names = sorted(crops)
# ---------------------------------------------------------------------------------------------------------------- render list
views = ['front', 'left', 'right', 'q3L', 'q3R', 'top']
spec = {}
cen_front, top_front = 440.1, 23; cen_back, top_back = 845.3, 24
def sq(box, S): return max(box[2] - box[0], box[3] - box[1]) * S
b7, b8 = crops['07_body_front_head.png']['box'], crops['08_body_back_head.png']['box']
spec['07'] = f"c:0:0:{((b7[0] + b7[2]) / 2 - cen_front) * SB:.5f}:0.0:{ZT - ((b7[1] + b7[3]) / 2 - top_front) * SB:.5f}:{sq(b7, SB):.5f}:{max(b7[2] - b7[0], b7[3] - b7[1]) * 3}"
spec['08'] = f"c:180:0:{-((b8[0] + b8[2]) / 2 - cen_back) * SB:.5f}:0.0:{ZT - ((b8[1] + b8[3]) / 2 - top_back) * SB:.5f}:{sq(b8, SB):.5f}:{max(b8[2] - b8[0], b8[3] - b8[1]) * 3}"
# multi-angle head tops / centres measured on the plate skin mask (crop name -> (top row, centre col))
MA = {'09_ma_front.png': (48, 169.15), '10_ma_back.png': (50, 485.65), '11_ma_left_profile.png': (50, 789.2), '12_ma_right_profile.png': (51, 1092.7),
      '13_ma_threequarter_front_left.png': (378, 168.3), '14_ma_threequarter_front_right.png': (378, 480.95), '15_ma_threequarter_back_left.png': (378, 785.3), '16_ma_threequarter_back_right.png': (379, 1088.55)}
YAWS = {'09': [0], '10': [180], '11': [90], '12': [-90], '13': [-50, -40, -30, -20, 20, 30, 40, 50], '14': [-50, -40, -30, -20, 20, 30, 40, 50],
        '15': [130, 140, 150, 160, 200, 210, 220, 230], '16': [130, 140, 150, 160, 200, 210, 220, 230]}
def ma_spec(name, az):
    box = crops[name]['box']; top, cen = MA[name]
    tz = ZT - ((box[1] + box[3]) / 2 - top) * SM
    d = ((box[0] + box[2]) / 2 - cen) * SM; a = math.radians(az)
    return f"c:{az}:0:{d * math.cos(a):.5f}:{0.003 + d * math.sin(a):.5f}:{tz:.5f}:{sq(box, SM):.5f}:{max(box[2] - box[0], box[3] - box[1]) * 3}"
ma_names = [n for n in names if int(n[:2]) >= 9]
for n in ma_names:
    k = n[:2]
    for az in YAWS[k]: spec[f'{k}_{az}'] = ma_spec(n, az)
allv = views + list(spec.values())
if rerender:
    subprocess.run([B, '-b', '--factory-startup', '--python', str(fl.W / 'tools/ul.py'), '--', blend, str(RD), ','.join(allv), 'p'], check=True, capture_output=True)
def rpath(v): return RD / (f'p_{v}.png' if not v.startswith('c:') else 'p_' + v.replace(':', '_') + '.png')
# ---------------------------------------------------------------------------------------------------------------- helpers
def edge(m):
    m = m.astype(np.uint8); e = np.zeros_like(m)
    e[1:-1, 1:-1] = ((m[1:-1, 1:-1] != m[:-2, 1:-1]) | (m[1:-1, 1:-1] != m[2:, 1:-1]) | (m[1:-1, 1:-1] != m[1:-1, :-2]) | (m[1:-1, 1:-1] != m[1:-1, 2:]))
    return e.astype(bool)
def dil(m, k=1):
    o = m.copy()
    for _ in range(k):
        p = o.copy(); p[1:] |= o[:-1]; p[:-1] |= o[1:]; p[:, 1:] |= o[:, :-1]; p[:, :-1] |= o[:, 1:]; o = p
    return o
def skin_mask(a):
    R, G, B_ = a[..., 0], a[..., 1], a[..., 2]
    return (R - B_ > 18) & (R > G + 4) & (G > B_) & (R > 110)
def fgm(a):
    sat = a.max(axis=2) - a.min(axis=2); V = a.mean(axis=2)
    return ~((sat < 16) & (V > 150))
try: font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 20)
except Exception: font = ImageFont.load_default()
def load_render(path, size):
    r = Image.open(path).convert('RGBA'); r = r.resize(size, Image.LANCZOS); al = np.asarray(r)[..., 3].astype(float) / 255
    rgb = np.asarray(r.convert('RGB')).astype(float); bg = np.array([40.0, 40.0, 42.0])
    return Image.fromarray((rgb * al[..., None] + bg * (1 - al[..., None])).astype(np.uint8)), al > 0.5
def crop_render(path, box, S, rs_px):
    """render is a square of side max(w,h)*S centred on the crop centre -> crop to w x h"""
    w, h = box[2] - box[0], box[3] - box[1]; m = max(w, h)
    r = Image.open(path).convert('RGBA'); sq_px = r.size[0]
    cx0 = int(round((sq_px - w * sq_px / m) / 2)); cy0 = int(round((sq_px - h * sq_px / m) / 2))
    r = r.crop((cx0, cy0, sq_px - cx0, sq_px - cy0))
    return r
sheets = []
plate_cache = {}
def plate_of(name):
    c = crops[name]; src = fl.PLATES / c['source']
    if src not in plate_cache: plate_cache[src] = Image.open(src).convert('RGB')
    return plate_cache[src].crop(tuple(c['box']))
def tile(name, render_rgba, label, plate_mask_fn, cut=None):
    pl = plate_of(name); w, h = pl.size
    tw, th = w * UP, h * UP
    pl_big = pl.resize((tw, th), Image.LANCZOS)
    r, rm = load_render_img(render_rgba, (tw, th))
    pa = np.asarray(pl_big).astype(float); pm = plate_mask_fn(pa)
    if cut is not None:
        rm = rm.copy(); pm = pm.copy(); rm[int(cut * UP):] = False; pm[int(cut * UP):] = False       # head + upper neck only (the body is not this chat's zone)
    if name.startswith('06'):
        rm = skin_mask(np.asarray(r).astype(float)); pm = skin_mask(pa)                                    # top view: head only (skin-coloured pixels), the shoulders are not this chat's zone
    ov = (0.5 * pa + 0.5 * np.asarray(r).astype(float)).astype(np.uint8); ov[dil(edge(rm), 1)] = (255, 40, 40); ov[dil(edge(pm), 1)] = (30, 220, 60)
    iou = (rm & pm).sum() / max((rm | pm).sum(), 1)
    if cut is not None:
        d0 = ImageDraw.Draw(Image.new('RGB', (1, 1)))
    row = Image.new('RGB', (tw * 3, th), (20, 20, 22)); row.paste(pl_big, (0, 0)); row.paste(r, (tw, 0)); row.paste(Image.fromarray(ov), (tw * 2, 0))
    d = ImageDraw.Draw(row); d.rectangle([0, 0, 360, 28], fill=(0, 0, 0)); d.text((6, 3), f'{label}   head-region silhouette IoU {iou:.3f}', fill=(255, 255, 255), font=font)
    return row, iou
def load_render_img(img, size):
    r = img.resize(size, Image.LANCZOS); al = np.asarray(r)[..., 3].astype(float) / 255; rgb = np.asarray(r.convert('RGB')).astype(float); bg = np.array([40.0, 40.0, 42.0])
    return Image.fromarray((rgb * al[..., None] + bg * (1 - al[..., None])).astype(np.uint8)), al > 0.5
CUT = {'01_front_face.png': 55 + 0, '02_left_profile.png': 0, '03_right_profile.png': 0, '04_threequarter_front_left.png': 0, '05_threequarter_front_right.png': 0}
def chin_cut(name):
    box = crops[name]['box']; k = int(name[:2])
    if k <= 3: return float(fl.rowz(1.4255 - 0.004)) - box[1] + 8          # head-detail panels (K = 1.537 mm/px)
    if k == 4: return 563 + 6 - box[1]
    if k == 5: return 562 + 6 - box[1]
    if k in (7, 8): return top_front + (ZT - 1.4255 + 0.004) / SB + 6 - box[1]
    if k >= 9: return MA[name][0] - box[1] + (ZT - 1.4255) / SM + 4
    return None
rows = {}; info = {}
for n in names:
    k = int(n[:2]); lab = n[:-4]
    if k <= 6:
        v = ['front', 'left', 'right', 'q3L', 'q3R', 'top'][k - 1]; img = Image.open(rpath(v)).convert('RGBA')
        rows[n], iou = tile(n, img, lab, fgm, None if k == 6 else chin_cut(n)); info[n] = dict(iou=float(iou))
    elif k in (7, 8):
        key = '07' if k == 7 else '08'; S_, box = SB, crops[n]['box']
        img = crop_render(rpath(spec[key]), box, S_, 0); rows[n], iou = tile(n, img, lab, skin_mask, chin_cut(n)); info[n] = dict(iou=float(iou))
    else:
        key = n[:2]; best = None
        for az in YAWS[key]:
            img = crop_render(rpath(spec[f'{key}_{az}']), crops[n]['box'], SM, 0)
            pl = plate_of(n); a = np.asarray(pl.resize((pl.size[0] * UP, pl.size[1] * UP), Image.LANCZOS)).astype(float)
            _, rm = load_render_img(img, (pl.size[0] * UP, pl.size[1] * UP)); pm = skin_mask(a)
            hh = int(pm.any(1).argmax()) + 38 * UP     # head rows only (skin below is neck/arms)
            iou_h = (rm[:hh] & pm[:hh]).sum() / max((rm[:hh] | pm[:hh]).sum(), 1)
            if best is None or iou_h > best[0]: best = (iou_h, az, img)
        rows[n], iou = tile(n, best[2], f'{lab}  yaw {best[1]}', skin_mask, chin_cut(n)); info[n] = dict(iou=float(iou), yaw=best[1], head_iou=float(best[0]))
json.dump(info, open(fl.W / 'data/proof02_info.json', 'w'), indent=1)
# ---------------------------------------------------------------------------------------------------------------- assemble: 2 columns
cols = [[n for n in names if int(n[:2]) % 2 == 1], [n for n in names if int(n[:2]) % 2 == 0]]
colimgs = []
for c in cols:
    h = sum(rows[n].height for n in c); w = max(rows[n].width for n in c)
    im = Image.new('RGB', (w, h), (20, 20, 22)); y = 0
    for n in c: im.paste(rows[n], (0, y)); y += rows[n].height
    colimgs.append(im)
W_ = sum(i.width for i in colimgs); H_ = max(i.height for i in colimgs)
S = Image.new('RGB', (W_, H_ + 44), (20, 20, 22)); d = ImageDraw.Draw(S)
d.text((10, 10), 'FEMALE HEAD MicroF3 - plate | mesh (Unity-like lighting) | overlay   (red = mesh silhouette, green = plate silhouette)   crops 01-16 of face_lock_f', fill=(255, 255, 255), font=font)
x = 0
for i in colimgs: S.paste(i, (x, 44)); x += i.width
S.thumbnail((5200, 5200), Image.LANCZOS)
S.save(out); print('saved', out, S.size)
for n in names: print(n, info[n])
