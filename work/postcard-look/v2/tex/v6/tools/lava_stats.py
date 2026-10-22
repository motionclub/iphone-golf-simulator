import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rawio import load
from wall_stats import hsv
def stats(d, n='hole10_3_lavarim', box=(330,700,900,1600)):
    a = load(f'{d}/{n}')[box[1]:box[3], box[0]:box[2], :3].reshape(-1, 3)
    h, s, v = hsv(a)
    lava = (h < 40) & (s > .55) & (v > .22)                     # orange / red-brown pixels (not grass, not the grey-black rock)
    # remove the rock shadow side: keep only pixels in the lava floor box (x >= 330)
    al = a[lava]; hl, sl, vl = h[lava], s[lava], v[lava]
    inb = ((hl >= 8) & (hl <= 28) & (sl >= .75) & (vl >= .70)).mean()
    dark = (vl < .40).mean()
    lum = 0.2126*al[:,0]+0.7152*al[:,1]+0.0722*al[:,2]
    # blobs: dark components >= 400 px
    return dict(px=int(lava.sum()), mean=tuple(al.mean(0).round(0)), in_band=round(float(inb)*100,1), dark_v40=round(float(dark)*100,2), lum_sd=round(float(lum.std()),1), p10_p90=(round(float(np.percentile(lum,10))), round(float(np.percentile(lum,90)))), hot=round(float((al[:,1] > 120).mean())*100,1))
if __name__ == '__main__':
    for d in sys.argv[1:]: print(d, stats(d))
