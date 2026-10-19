import sys, json, types; sys.modules.setdefault('bpy', types.ModuleType('bpy')); sys.path.insert(0, __file__.rsplit('/', 1)[0])
import numpy as np, off, render_off as RO
from PIL import Image, ImageDraw
h = off.Head(); rows = []
for spec in sys.argv[2:]:
    label, pj, dt = spec.split(':'); P = dict(off.DEFAULT)
    if pj != '-': d = json.load(open(pj)); P.update(d.get('warp', d))
    co = h.base + (np.load(f'eval/{dt}_delta.npy') if dt != '-' else 0); G = h.U(h.warp(co, P)) * 1000
    keep = G[h.tri][:, :, 1].min(1) > -175
    ims = [Image.fromarray(RO.render(G, h.tri, yaw, keep=keep, res=400, half=48, centre=(0, -82, 30))[0]) for yaw in (0, -35, 90)]
    row = Image.new('RGB', (1200, 400)); [row.paste(im, (400 * i, 0)) for i, im in enumerate(ims)]; ImageDraw.Draw(row).text((8, 8), label, fill=(0, 0, 0)); rows.append(row)
out = Image.new('RGB', (1200, 400 * len(rows))); [out.paste(r, (0, 400 * i)) for i, r in enumerate(rows)]; out.save(sys.argv[1], quality=88)
