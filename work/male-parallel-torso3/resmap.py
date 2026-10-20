"""Unexplained shading: high-passed (plate - model) per vertex at the sample set, for baseline and a candidate.  python3.13 resmap.py out.png tag"""
import sys; sys.path.insert(0, '.')
from pmo_t import *
from PIL import Image, ImageDraw
out, tag = sys.argv[1], sys.argv[2]; V = np.load('data/V_base.npy'); P1 = np.load(f'data/V_{tag}.npy'); T = Torso(V); T.make_basis(0.012, 0.009)
BOX = {'front': (225, 140, 485, 440), 'back': (790, 140, 1050, 440)}; Zm = 3
def panel(P, view):
    v = T.views[view]; N = T.normals(P); M = v['basis'](N[v['sel']]) @ v['c']; r = T.hp(v['I'] - M, v['HP']); vw = v['vw']
    col, row = vw.project(T.V0[v['sel']]); box = BOX[view]; img = np.full((box[3] - box[1], box[2] - box[0], 3), 25, np.uint8)
    for k in range(len(r)):
        c = int(round(col[k])) - box[0]; rr = int(round(row[k])) - box[1]
        if 2 <= c < img.shape[1] - 2 and 2 <= rr < img.shape[0] - 2:
            t = np.clip(r[k] / 2.0, -1, 1); rgb = (255, int(255 * (1 - t)), int(255 * (1 - t))) if t > 0 else (int(255 * (1 + t)), int(255 * (1 + t)), 255); img[rr - 2:rr + 2, c - 2:c + 2] = rgb
    return Image.fromarray(img).resize((img.shape[1] * Zm, img.shape[0] * Zm), Image.NEAREST), float(np.sqrt((r ** 2).mean()))
rows = []
for view in ('front', 'back'):
    a, ra = panel(V, view); b, rb = panel(P1, view); rows.append((view, a, ra, b, rb))
W_ = rows[0][1].width; H_ = rows[0][1].height; s = Image.new('RGB', (W_ * 2 + 6, (H_ + 22) * 2), (0, 0, 0)); d = ImageDraw.Draw(s)
for k, (view, a, ra, b, rb) in enumerate(rows):
    s.paste(a, (0, k * (H_ + 22) + 22)); s.paste(b, (W_ + 6, k * (H_ + 22) + 22)); d.text((4, k * (H_ + 22) + 4), f'{view}: baseline residual (hp plate-model) rms {ra:.2f}  | red = plate brighter than model, blue = darker | {tag} rms {rb:.2f}', fill=(255, 255, 255))
s.save(out); print(out, s.size)
