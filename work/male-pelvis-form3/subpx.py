"""Sub-pixel rear contour of the plate side views from the multiangle sheet (50% crossing between local background and body level per row).
python3 subpx.py -> data/plate_rear_subpx.json  (z, left_rear_y_m, right_rear_y_m) where y is measured like the renders (rear positive, origin = camera centre_x)"""
import json, numpy as np
from PIL import Image
R='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/'
L=np.asarray(Image.open(R+'ArtDir/hero/base_lock/male_multiangle_body.jpg').convert('L')).astype(float)
cams={c['name']:c for c in json.load(open(R+'work/male-silhouette/reference-cameras.json'))['views']}
def edge_row(row, cx, side, win=26):
    """row: 1-D intensities; find the rear edge near the silhouette: scan outward from the body centre in direction side (+1 right / -1 left) until intensity falls to the background"""
    n=len(row); i0=int(cx)
    # background level: median of 10 px far outside (cx +- 70..80 px)
    far=cx+side*70; bgs=row[int(far-5*side):int(far+5*side):side] if side>0 else row[int(far+5):int(far-5):-1]
    bg=np.median(row[int(cx+side*60):int(cx+side*75):side]) if side>0 else np.median(row[int(cx-75):int(cx-60)])
    return bg
res={'z':[], 'left':[], 'right':[]}
zs=np.arange(0.70,1.56,0.002)
for v,side in (('left',+1),('right',-1)):
    c=cams[v]; mpp=c['metres_per_pixel']; cx=c['centre_x']
    for z in zs:
        r=int(round(c['sole_y']-z/mpp)); row=L[r]
        # estimate local body level just inside the rear edge: take the mask-based edge as a starting guess
        x0=cx
        # search window for the edge: from cx - side*? to cx + side*80 ; rear is +col for 'left' view, -col for 'right' view
        cols=np.arange(int(cx-side*20), int(cx+side*90), side)
        prof=row[cols]
        bg=np.median(row[int(cx+side*80):int(cx+side*95):side]) if side>0 else np.median(row[int(cx-95):int(cx-80)])
        inside=np.median(row[int(cx+side*5):int(cx+side*12):side]) if side>0 else np.median(row[int(cx-12):int(cx-5)])
        # find the outermost crossing of the midpoint level scanning outward from the inside level
        thr=0.5*(bg+inside) if abs(bg-inside)>12 else None
        if thr is None: res[v].append(None); continue
        pos=None
        for k in range(len(cols)-1):
            a,b=prof[k],prof[k+1]
            if (a-thr)*(b-thr)<=0 and a!=b and abs(cols[k]-cx)>2:
                t=(thr-a)/(b-a); pos=cols[k]+t*(cols[k+1]-cols[k])
        # outermost crossing found last; ensure it lies beyond the inside region
        res[v].append(None if pos is None else float((pos-cx)*mpp*(1 if side>0 else -1)))
res['z']=[float(z) for z in zs]
json.dump(res,open('data/plate_rear_subpx.json','w'))
for z in np.arange(0.74,1.10,0.02):
    i=int(round((z-0.70)/0.002)); l=res['left'][i]; r=res['right'][i]
    print(f'z {z:.2f}  left {None if l is None else round(l*1000,1)}  right {None if r is None else round(r*1000,1)}')
