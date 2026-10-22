"""Game-view grass statistics of phone frames (900x1600): luminance sd of the lower 60 % (rows 640..1599), of the central lower third,
window sd (w=20 px, the probe's tile size) median / share >= .03 / share flat (<1.5/255), and the mean hue of the lower 60 %.
usage: gameview_grass.py <img> [<img> ...]    (run with Blender's python3.13)"""
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import imgnp
def stats(path):
    a = imgnp.load(path); H, W = a.shape[:2]
    y0 = int(round(H * 0.4)); lo = a[y0:]; l = imgnp.lum(lo)
    cy0, cy1 = int(H * 0.5), int(H * 0.83); cx0, cx1 = int(W * 0.25), int(W * 0.75)
    cl = imgnp.lum(a[cy0:cy1, cx0:cx1])
    s20 = imgnp.wsd(l, 20)
    h, s, v = imgnp.hsv_of_mean(lo.reshape(-1, 3).mean(0))
    return dict(f=os.path.basename(os.path.dirname(path)) + '/' + os.path.basename(path), sd60=l.std(), sd60_255=l.std() * 255, cl_sd=cl.std(), w20_med=float(np.median(s20)),
                w20_ge03=float(np.mean(s20 >= .03)), flat=float(np.mean(s20 < 1.5 / 255)), hue=h, S=s, V=v, rgb=np.round(lo.reshape(-1, 3).mean(0) * 255).astype(int).tolist())
if __name__ == '__main__':
    for p in sys.argv[1:]:
        d = stats(p)
        print(f"{d['f']:42s} lower60 sd {d['sd60']:.4f} ({d['sd60_255']:.1f}/255) | central-lower-third sd {d['cl_sd']:.4f} | w20 med {d['w20_med']:.4f} ge.03 {d['w20_ge03']:.0%} flat {d['flat']:.1%} | mean rgb {d['rgb']} h{d['hue']:.0f} S{d['S']:.2f} V{d['V']:.2f}")
