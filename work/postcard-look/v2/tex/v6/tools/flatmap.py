import sys, numpy as np
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/postcard-look/v2/tex/v6/tools')
from rawio import load, save_raw
import os
RAWDIR = os.environ.get('RAWDIR', 'raw')
def lum(a): a = a[..., :3].astype(np.float64) / 255; return 0.2126*a[...,0]+0.7152*a[...,1]+0.0722*a[...,2]
def flatmask(l, win=8, flat_sd=0.006, block_sd=0.003):
    H, W = l.shape; h2, w2 = H//win, W//win
    a = l[:h2*win, :w2*win].reshape(h2, win, w2, win)
    sd = a.std(axis=(1,3)); b = a.reshape(h2, win//4, 4, w2, win//4, 4).mean(axis=(2,5)); bsd = b.std(axis=(1,3))
    return (sd < flat_sd) | (bsd < block_sd), sd
if __name__ == '__main__':
    for n in sys.argv[1:]:
        a = load(f'{RAWDIR}/{n}'); l = lum(a)
        rows = int(l.shape[0]*0.6); low = l[l.shape[0]-rows:]   # bottom 60 % of frame
        m, sd = flatmask(low)
        print(n, 'flat share', round(m.mean(), 4), 'median wsd', round(float(np.median(sd)), 4))
        # bands of 160 px rows (top-down in image coordinates)
        H = l.shape[0]
        for y0 in range(H - rows, H, 160):
            mm, ss = flatmask(l[y0:y0+160])
            print('   rows', y0, '-', y0+160, 'flat', round(float(mm.mean()), 3), 'median wsd', round(float(np.median(ss)), 4), 'mean lum', round(float(l[y0:y0+160].mean())*255,1))
