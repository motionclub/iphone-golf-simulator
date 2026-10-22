import sys, os, numpy as np, colorsys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rawio import load
BOX = {'hole10_1_tee': (0,135,560,300), 'hole10_2_approach': (0,20,900,310), 'hole10_3_lavarim': (0,345,900,640)}
def hsv(a):
    a = a.astype(np.float64)/255; mx = a.max(-1); mn = a.min(-1); d = mx-mn
    r,g,b = a[...,0],a[...,1],a[...,2]
    h = np.zeros_like(mx); m = d>1e-9
    rm = m&(mx==r); gm = m&(mx==g)&~rm; bm = m&~rm&~gm
    h[rm]=((g-b)[rm]/d[rm])%6; h[gm]=(b-r)[gm]/d[gm]+2; h[bm]=(r-g)[bm]/d[bm]+4
    return h*60, np.where(mx>1e-9,d/np.maximum(mx,1e-9),0), mx
def stats(d):
    for n,(x0,y0,x1,y1) in BOX.items():
        if not os.path.exists(f'{d}/{n}.raw'): continue
        a = load(f'{d}/{n}')[y0:y1, x0:x1,:3].reshape(-1,3)
        h,s,v = hsv(a); lum = 0.2126*a[:,0]+0.7152*a[:,1]+0.0722*a[:,2]
        wall = (v < 0.5)                                    # dark rock (sky is brighter)
        glow = wall & (a[:,0] > 110) & (s > .6) & (h > 5) & (h < 35)
        nw = wall & ~glow
        m = a[nw].mean(0); mh,ms,mv = hsv(m[None,:])
        print(f'  {n}: box {BOX[n]} wall px {int(nw.sum())} non-glow mean ({m[0]:.0f},{m[1]:.0f},{m[2]:.0f}) hue {mh[0]:.0f} S {ms[0]:.2f} V {mv[0]:.2f} median lum {np.median(lum[nw]):.1f} | glow {glow.sum()/max(wall.sum(),1)*100:.2f}% of wall')
if __name__ == '__main__': stats(sys.argv[1])
