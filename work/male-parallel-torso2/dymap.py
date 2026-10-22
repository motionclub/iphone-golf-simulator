"""Displacement map: outward (+) / inward (-) mm per vertex, front and back, splatted at plate resolution. python3.13 dymap.py out.png tag [tag2 ...] [--vs basetag]"""
import sys; sys.path.insert(0, '.')
from plateview import *
from zone import zone_mask
from PIL import Image, ImageDraw
out = sys.argv[1]; tags = [a for a in sys.argv[2:]]; V0 = np.load('data/V_base.npy'); Z = zone_mask(V0)
def tomap(dy_out, view, box, Zm=3, vmax=6.0):
    vw = View(view); col, row = vw.project(V0); img = np.full((box[3] - box[1], box[2] - box[0], 3), 30, np.uint8)
    face = (V0[:, 1] < -0.04) if view == 'front' else (V0[:, 1] > -0.04)
    for i in np.where(Z & face)[0]:
        c = int(round(col[i])) - box[0]; r = int(round(row[i])) - box[1]
        if 2 <= c < img.shape[1] - 2 and 2 <= r < img.shape[0] - 2:
            t = np.clip(dy_out[i] / vmax, -1, 1); rgb = (255, int(255 * (1 - t)), int(255 * (1 - t))) if t > 0 else (int(255 * (1 + t)), int(255 * (1 + t)), 255)
            img[r - 2:r + 2, c - 2:c + 2] = rgb
    return Image.fromarray(img).resize(((box[2] - box[0]) * Zm, (box[3] - box[1]) * Zm), Image.NEAREST)
BOX = {'front': (225, 140, 485, 440), 'back': (790, 140, 1050, 440)}
rows = []
for t in tags:
    V1 = np.load(f'data/V_{t}.npy'); dy = (V1[:, 1] - V0[:, 1]) * 1000.0
    fr = tomap(-dy, 'front', BOX['front']); bk = tomap(dy, 'back', BOX['back']); rows.append((t, fr, bk))
W_ = rows[0][1].width; H_ = rows[0][1].height
s = Image.new('RGB', (W_ * 2 + 8, (H_ + 24) * len(rows)), (0, 0, 0)); d = ImageDraw.Draw(s)
for k, (t, fr, bk) in enumerate(rows):
    s.paste(fr, (0, k * (H_ + 24) + 24)); s.paste(bk, (W_ + 8, k * (H_ + 24) + 24)); d.text((6, k * (H_ + 24) + 4), f'{t}: front outward(+red)/inward(-blue) +-6mm | back', fill=(255, 255, 255))
s.save(out); print(out, s.size)
