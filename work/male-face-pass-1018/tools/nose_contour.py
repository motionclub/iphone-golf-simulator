"""python3 tools/nose_contour.py out.jpg label=params.json ... : front view with 2 mm depth contours (offline), to compare with the game's grid render."""
import sys, os, json; OUT=os.path.abspath(sys.argv[1]); SPEC=[(a.split('=')[0], os.path.abspath(a.split('=')[1])) for a in sys.argv[2:]]; sys.argv=['x']
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, nose_off as NO, render_off as RO
from PIL import Image, ImageDraw
def render_z(G, tri, yaw, out=None, half=130, res=700, centre=(0, -35, 0), keep=None, color=(.86, .66, .52)):
    a = np.radians(yaw); R = np.array([[np.cos(a), 0, np.sin(a)], [0, 1, 0], [-np.sin(a), 0, np.cos(a)]])
    P = (G - np.array(centre)) @ R.T; N = RO.vnormals(G, tri) @ R.T
    if keep is not None: tri = tri[keep]
    s = res / (2 * half); px = P[:, 0] * s + res / 2; py = res / 2 - P[:, 1] * s
    Z = np.full((res, res), -1e9); I = np.zeros((res, res, 3)); A = np.zeros((res, res), bool)
    T = tri[(P[tri][:, :, 2].max(1) > -1e8)]
    L = np.array([-.35, .45, .82]); L /= np.linalg.norm(L)
    for t in T:
        xs, ys = px[t], py[t]
        x0, x1 = int(max(xs.min(), 0)), int(min(xs.max() + 1, res - 1)); y0, y1 = int(max(ys.min(), 0)), int(min(ys.max() + 1, res - 1))
        if x1 < x0 or y1 < y0: continue
        X, Y = np.meshgrid(np.arange(x0, x1 + 1) + .5, np.arange(y0, y1 + 1) + .5)
        (ax, ay), (bx, by), (cx, cy) = zip(xs, ys)
        den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if abs(den) < 1e-12: continue
        l1 = ((by - cy) * (X - cx) + (cx - bx) * (Y - cy)) / den; l2 = ((cy - ay) * (X - cx) + (ax - cx) * (Y - cy)) / den; l3 = 1 - l1 - l2
        m = (l1 >= -1e-6) & (l2 >= -1e-6) & (l3 >= -1e-6)
        if not m.any(): continue
        z = l1 * P[t[0], 2] + l2 * P[t[1], 2] + l3 * P[t[2], 2]
        sub = Z[y0:y1 + 1, x0:x1 + 1]; upd = m & (z > sub)
        if not upd.any(): continue
        n = l1[..., None] * N[t[0]] + l2[..., None] * N[t[1]] + l3[..., None] * N[t[2]]; n /= np.maximum(np.linalg.norm(n, axis=-1), 1e-12)[..., None]
        sh = .30 + .70 * np.clip(n @ L, 0, 1) + .12 * np.clip(n[..., 2], 0, 1)
        sub[upd] = z[upd]; I[y0:y1 + 1, x0:x1 + 1][upd] = (np.array(color)[None, None] * sh[..., None])[upd]; A[y0:y1 + 1, x0:x1 + 1][upd] = True
    img = np.where(A[..., None], I, .88); img = (np.clip(img, 0, 1) * 255).astype(np.uint8)
    if out: Image.fromarray(img).save(out)
    return img, A, Z
rows=[]
for lab,p in SPEC:
    G=NO.head(json.load(open(p))); keep=G[NO.h.tri][:,:,1].min(1)>-175
    im,_,Zb=render_z(G,NO.h.tri,0,keep=keep,res=420,half=42,centre=(0,-36,30)); rest=[Zb+30]
    # depth image: re-render z as colour via a second pass with the renderer's z-buffer if available
    Z=rest[0] if rest else None
    img=Image.fromarray(im)
    if Z is not None:
        z=np.array(Z,float); m=z>-1e8; zz=np.where(m,z,np.nan)
        band=(np.abs(zz/2-np.round(zz/2))<.12)&m
        a=np.array(img).astype(float); a[band]*=.45; img=Image.fromarray(a.clip(0,255).astype(np.uint8))
    ImageDraw.Draw(img).text((6,6),lab,fill=(0,0,0)); rows.append(img)
out=Image.new('RGB',(420*len(rows),420)); [out.paste(r,(420*i,0)) for i,r in enumerate(rows)]; out.save(OUT,quality=90)
