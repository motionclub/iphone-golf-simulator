import sys, numpy as np
from PIL import Image, ImageDraw
tag, view = sys.argv[1], sys.argv[2]
d = np.load(f'eval/{tag}_mesh.npz'); G = d['G']; tri = d['tri']
S = 14; W, H = 70 * S, 90 * S     # x -35..35 mm, y -140..-50
img = Image.new('RGB', (W, H), (255, 255, 255)); dr = ImageDraw.Draw(img)
if view == 'front':
    keep = (G[tri][:, :, 2] > -15).all(1) & (G[tri][:, :, 1] < -50).all(1) & (G[tri][:, :, 1] > -140).all(1) & (np.abs(G[tri][:, :, 0]) < 36).all(1)
    def P(v): return ((v[0] + 35) * S, (-50 - v[1]) * S)
else:   # side: z horizontal (forward to the right), only x>=0 half
    keep = (G[tri][:, :, 0] > -1).all(1) & (G[tri][:, :, 1] < -50).all(1) & (G[tri][:, :, 1] > -140).all(1) & (G[tri][:, :, 2] > -40).all(1)
    def P(v): return ((v[2] + 45) * S, (-50 - v[1]) * S)
for t in tri[keep]:
    pts = [P(G[i]) for i in t]
    dr.polygon(pts, outline=(60, 60, 60))
for yy in range(-140, -49, 10): dr.text((4, (-50 - yy) * S), str(yy), fill=(200, 0, 0))
img.save(f'scratch/wire_{tag}_{view}.png')
