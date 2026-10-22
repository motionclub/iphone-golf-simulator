"""Hand-ROI silhouette evaluation vs the plate masks (bald front/back + multi-angle front/back).
python sil_f.py <tag|base> [--img out.png]"""
import sys, json
import numpy as np
from PIL import Image, ImageDraw
from femlib import *
PM = np.load(W / 'data/plate_masks.npz')
N0 = 22419
# hand ROIs in plate px (x0,y0,x1,y1); rows limited to the palm/finger part (z <= 0.82 -> avoids the lit-forearm holes in the masks)
ROI = {
 'bald_front':  {+1: (500, 372, 560, 424), -1: (320, 372, 380, 424)},
 'bald_back':   {+1: (730, 372, 790, 424), -1: (910, 372, 970, 424)},
}
def sheet_rois():
    zc = lambda z: int(round(Z0_SHEET - z / S_SHEET))
    r0, r1 = zc(0.80), zc(0.66)
    out = {}
    for v, sg in (('sheet_front', +1), ('sheet_back', -1)):
        cx = SHEET_X0[v]
        # +x hand is at x_px = cx + sg*x/S for front (sg=+1), cx - x/S for back
        xs = lambda x: cx + sg * x / S_SHEET
        out[v] = {+1: (int(xs(0.17)) if sg > 0 else int(xs(0.29)), r0, int(xs(0.29)) if sg > 0 else int(xs(0.17)), r1),
                  -1: (int(xs(-0.29)) if sg > 0 else int(xs(-0.17)), r0, int(xs(-0.17)) if sg > 0 else int(xs(-0.29)), r1)}
    return out
ROI.update(sheet_rois())
WT = {'bald_front': 1.0, 'bald_back': 1.0, 'sheet_front': 0.5, 'sheet_back': 0.5}

def hand_flag(nV, side_slots, extra_from):
    f = np.zeros(nV, bool)
    for s in (1, -1): f[side_slots[s]] = True
    f[extra_from:] = True
    return f

def evaluate(V, polys, hand_verts_mask, ss=3, return_masks=False):
    T = Mesh(V.astype(np.float32), polys).tris()
    hv = hand_verts_mask[T].any(1)                    # triangles that touch the hand shell
    res = {}; masks = {}
    for view, d in ROI.items():
        for sd, box in d.items():
            x0, y0, x1, y1 = box
            mh = raster(V, T, view, box, ss=ss)                           # whole body
            mo = raster(V, T, view, box, ss=ss, sel=~hv)                  # everything except the hand shell
            pl = PM[view][y0:y1, x0:x1]
            ign = mo & ~raster(V, T, view, box, ss=ss, sel=hv)            # pixels covered only by non-hand geometry (arm/thigh): hand cannot be judged there... keep simple: use whole-body compare
            xor = int((mh ^ pl).sum()); un = int((mh | pl).sum())
            res[(view, sd)] = dict(xor=xor, union=un, mesh_only=int((mh & ~pl).sum()), plate_only=int((pl & ~mh).sum()), plate=int(pl.sum()), mesh=int(mh.sum()))
            masks[(view, sd)] = (mh, pl)
    tot = sum(WT[k[0]] * v['xor'] for k, v in res.items())
    out = dict(total=tot, per={f'{k[0]}_{"p" if k[1] > 0 else "m"}': v for k, v in res.items()})
    if return_masks: return out, masks
    return out

def load(tag):
    path = W / ('data/mesh_start.npz' if tag == 'base' else f'data/cand_{tag}.npz')
    M = Mesh.from_npz(path)
    return M.V.astype(np.float64), M.polys

def hand_mask_for(V):
    slots = {s: np.load(W / f'data/start_hand_verts_{s}.npy') for s in (1, -1)}
    return hand_flag(len(V), slots, N0)

def overlay_img(masks, path, sc=6):
    tiles = []
    for (view, sd), (mh, pl) in masks.items():
        h, w = pl.shape
        rgb = np.zeros((h, w, 3), np.uint8)
        rgb[pl & mh] = (95, 190, 95); rgb[pl & ~mh] = (225, 60, 60); rgb[~pl & mh] = (60, 120, 255)
        im = Image.fromarray(rgb).resize((w * sc, h * sc), Image.NEAREST)
        ImageDraw.Draw(im).text((4, 2), f'{view} {"+x" if sd > 0 else "-x"}  green=both red=plate only blue=model only', fill=(255, 255, 0))
        tiles.append(im)
    cols = 4; rows = (len(tiles) + cols - 1) // cols
    cw = max(t.width for t in tiles); ch = max(t.height for t in tiles)
    S = Image.new('RGB', (cols * (cw + 6), rows * (ch + 6)), (20, 20, 24))
    for i, t in enumerate(tiles): S.paste(t, ((i % cols) * (cw + 6), (i // cols) * (ch + 6)))
    S.save(path); return S.size

if __name__ == '__main__':
    tag = sys.argv[1]
    V, polys = load(tag)
    out, masks = evaluate(V, polys, hand_mask_for(V), return_masks=True)
    print(json.dumps({'total': out['total'], **{k: (v['xor'], v['mesh_only'], v['plate_only']) for k, v in out['per'].items()}}))
    if '--img' in sys.argv:
        print(overlay_img(masks, sys.argv[sys.argv.index('--img') + 1]))
