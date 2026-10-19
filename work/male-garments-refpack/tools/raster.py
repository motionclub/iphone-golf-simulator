"""Tiny numpy/PIL flat-shaded orthographic rasterizer for dump meshes (painter's algorithm)."""
import numpy as np, os
from PIL import Image, ImageDraw
DUMP='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/clothing-v2/dump'
def part(hero, tag, dump=DUMP):
    d=os.path.join(dump,hero)
    P=np.fromfile(f'{d}/{tag}_pos.f32',np.float32).reshape(-1,3).astype(float)
    T=np.fromfile(f'{d}/{tag}_tri.i32',np.int32).reshape(-1,3)
    return P,T
def render(items, view, scale, origin, size, light=(0.3,-0.5,0.8), img=None):
    """items: list of (P,T,rgb). view: 3x3 rows = screen x, screen y(up), depth(toward viewer). origin: world point at image centre."""
    W,H=size; img=img or Image.new('RGB',size,(205,205,205)); d=ImageDraw.Draw(img)
    polys=[]
    L=np.array(light,float); L/=np.linalg.norm(L)
    for P,T,col in items:
        Q=(P-origin)@np.asarray(view).T
        n=np.cross(P[T[:,1]]-P[T[:,0]],P[T[:,2]]-P[T[:,0]]); n/=np.linalg.norm(n,axis=1,keepdims=True)+1e-12
        nv=n@np.asarray(view).T
        sh=np.clip(np.abs(n@L),0,1)*.65+.35
        dep=Q[T,2].mean(1)
        xs=W/2+Q[T,0]*scale; ys=H/2-Q[T,1]*scale
        for i in range(len(T)):
            polys.append((dep[i],[(xs[i,0],ys[i,0]),(xs[i,1],ys[i,1]),(xs[i,2],ys[i,2])],tuple(int(c*sh[i]) for c in col)))
    polys.sort(key=lambda p:p[0])
    for _,pts,c in polys: d.polygon(pts,fill=c)
    return img
