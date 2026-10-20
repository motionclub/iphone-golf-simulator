import sys, numpy as np
sys.path.insert(0, '../../Tools/HeroBase')
from plate_profiles import FEMALE as F
from PIL import Image, ImageDraw
from femlib import *
import asm_f
def poly(pts):
    im = Image.new('L', (1280, 720), 0); ImageDraw.Draw(im).polygon(pts, fill=255); return np.array(im) > 0
PF, PB = poly(F['front_outline']), poly(F['back_outline'])
PM = np.load('data/plate_masks.npz')
xpx = np.arange(64, 118, 1.0); ypx = np.arange(352, 422, 1)
T4 = []
for P_, cx in ((PF, 440), (PB, 847)):
    for sd in (-1, 1):
        cols = np.clip(np.round(cx + sd * xpx).astype(int), 0, 1279); T4.append(P_[np.ix_(ypx, cols)].astype(float))
Tm = np.mean(T4, axis=0)
# image-based masks mirrored the same way
I4 = []
for nm, cx in (('bald_front', 440), ('bald_back', 847)):
    for sd in (-1, 1):
        cols = np.clip(np.round(cx + sd * xpx).astype(int), 0, 1279); I4.append(PM[nm][np.ix_(ypx, cols)].astype(float))
Im = np.mean(I4, axis=0)
def model_mean(tag):
    M = Mesh.from_npz(W / ('data/mesh_start.npz' if tag == 'base' else f'data/cand_{tag}.npz')); V = M.V.astype(np.float64); Tr = M.tris()
    ms = []
    for view, cx in (('bald_front', 440), ('bald_back', 847)):
        full = raster(V, Tr, view, (0, 0, 1280, 720), ss=2).astype(float)
        for sd in (-1, 1):
            cols = np.clip(np.round(cx + sd * xpx).astype(int), 0, 1279); ms.append(full[np.ix_(ypx, cols)])
    return np.mean(ms, axis=0), ms
Mb, _ = model_mean('base'); Mc, _ = model_mean('final')
def up(a): return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).resize((a.shape[1] * 8, a.shape[0] * 8), Image.NEAREST)
tiles = [up(Tm), up(Im), up(Mb), up(Mc)]
S = Image.new('L', (sum(t.width for t in tiles) + 18, tiles[0].height), 40); x = 0
for t in tiles: S.paste(t, (x, 0)); x += t.width + 6
S.save('proof/_consensus_dbg.png'); print(S.size)
keep = np.ones_like(Tm, bool)
for j, y in enumerate(ypx):
    if y >= 372: keep[j, xpx < 76] = False
    else: keep[j, xpx < 60] = False
err = lambda M, T: np.abs(M - T)[keep].sum() / np.maximum(M, T)[keep].sum()
print('target poly vs image-mean err', round(err(Im, Tm), 3))
print('start vs poly-mean %.3f   new vs poly-mean %.3f' % (err(Mb, Tm), err(Mc, Tm)))
print('start vs image-mean %.3f   new vs image-mean %.3f' % (err(Mb, Im), err(Mc, Im)))
