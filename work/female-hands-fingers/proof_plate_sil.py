"""python3 proof_plate_sil.py <after_tag> <out.png> [before_tag=base] : plate | before | after silhouettes for the 8 hand ROIs (XOR colours) + numbers"""
import sys, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from femlib import *
import sil_f
after = sys.argv[1]; outp = sys.argv[2]; before = sys.argv[3] if len(sys.argv) > 3 else 'base'
B = str(W) + '/../../ArtDir/hero/base_lock/'
bald = Image.open(B + 'female_body_bald.jpg').convert('RGB'); multi = Image.open(B + 'female_multiangle_body.jpg').convert('RGB')
PM = np.load(W / 'data/plate_masks.npz')
def fnt(sz):
    try: return ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', sz)
    except Exception: return ImageFont.load_default()
cands = {}
for tag in (before, after):
    V, polys = sil_f.load(tag); hm = sil_f.hand_mask_for(V)
    T = Mesh(V.astype(np.float32), polys).tris(); cands[tag] = (V, T, sil_f.evaluate(V, polys, hm))
# display windows (plate px): wider/taller than the cost ROI so the wrist is visible
DISP = {'bald_front': {+1: (495, 340, 560, 424), -1: (320, 340, 385, 424)}, 'bald_back': {+1: (728, 340, 793, 424), -1: (908, 340, 973, 424)}}
zc = lambda z: int(round(Z0_SHEET - z / S_SHEET))
for v, sg in (('sheet_front', +1), ('sheet_back', -1)):
    cx = SHEET_X0[v]; xs = lambda x: cx + sg * x / S_SHEET
    DISP[v] = {+1: (int(min(xs(0.165), xs(0.285))), zc(0.86), int(max(xs(0.165), xs(0.285))), zc(0.66)), -1: (int(min(xs(-0.165), xs(-0.285))), zc(0.86), int(max(xs(-0.165), xs(-0.285))), zc(0.66))}
tiles = []
for view in ('bald_front', 'bald_back', 'sheet_front', 'sheet_back'):
    for sd in (+1, -1):
        box = DISP[view][sd]; x0, y0, x1, y1 = box; sc = 7 if view.startswith('bald') else 11
        src = bald if view.startswith('bald') else multi
        plate_img = src.crop(box).resize(((x1 - x0) * sc, (y1 - y0) * sc), Image.LANCZOS)
        pl = PM[view][y0:y1, x0:x1]
        panels = [plate_img]
        for tag in (before, after):
            V, T, ev = cands[tag]
            mh = raster(V, T, view, box, ss=3)
            rgb = np.zeros((y1 - y0, x1 - x0, 3), np.uint8)
            rgb[pl & mh] = (95, 190, 95); rgb[pl & ~mh] = (225, 60, 60); rgb[~pl & mh] = (60, 120, 255)
            im = Image.fromarray(rgb).resize(((x1 - x0) * sc, (y1 - y0) * sc), Image.NEAREST)
            d = ImageDraw.Draw(im)
            roi = sil_f.ROI[view][sd]; ry0 = (roi[1] - y0) * sc
            d.line([(0, ry0), (im.width, ry0)], fill=(255, 255, 0), width=1)
            key = f'{view}_{"p" if sd > 0 else "m"}'; x = ev['per'][key]
            d.text((6, im.height - 22), f'{"before" if tag == before else "after"}  XOR {x["xor"]} px (cost ROI below yellow line)', fill=(255, 255, 255), font=fnt(15))
            panels.append(im)
        W3 = sum(p.width for p in panels) + 12; H3 = panels[0].height + 26
        T3 = Image.new('RGB', (W3, H3), (20, 20, 24)); xx = 0
        for p in panels: T3.paste(p, (xx, 26)); xx += p.width + 6
        ImageDraw.Draw(T3).text((6, 4), f'{view}  {"+x hand (anat. left)" if sd > 0 else "-x hand (anat. right)"}   plate | BEFORE | AFTER   (green both, red plate-only, blue model-only)', fill=(255, 230, 120), font=fnt(16))
        tiles.append(T3)
cols = 2; rows = (len(tiles) + 1) // 2
cw = max(t.width for t in tiles); chs = [max(t.height for t in tiles[r * 2:(r + 1) * 2]) for r in range(rows)]
S = Image.new('RGB', (cols * (cw + 8), sum(chs) + 8 * rows + 40), (20, 20, 24)); d = ImageDraw.Draw(S)
tb = cands[before][2]['total']; ta = cands[after][2]['total']
d.text((8, 8), f'Hand ROI silhouette XOR (weighted total, 8 ROIs): {before} {tb:.0f} -> {after} {ta:.0f}', fill=(255, 230, 120), font=fnt(22))
y = 40
for r in range(rows):
    for c in range(cols):
        i = r * 2 + c
        if i < len(tiles): S.paste(tiles[i], (c * (cw + 8), y))
    y += chs[r] + 8
S.save(outp); print(outp, S.size, 'before', tb, 'after', ta)
