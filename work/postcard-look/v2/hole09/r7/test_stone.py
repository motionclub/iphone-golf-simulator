import sys, time, random, math
sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/blender/scripts')
import numpy as np
import hole09_stone as S
import importlib
# box corners like hole09_masonry._box_corners
def box_corners(rng, sx, sy, sz, top_rag=0.0):
    tx, ty = rng.uniform(-0.04, 0.05), rng.uniform(-0.05, 0.05)
    shx, shy = rng.uniform(-0.05, 0.05) * sz, rng.uniform(-0.05, 0.05) * sz
    twist = rng.uniform(-0.03, 0.03)
    sl_x, sl_y = rng.uniform(-0.06, 0.06), rng.uniform(-0.06, 0.06)
    drop = rng.uniform(0.0, 0.04) + top_rag * rng.uniform(0.15, 0.45)
    rag_x, rag_y = top_rag * rng.uniform(-1.1, 1.1), top_rag * rng.uniform(-0.8, 0.8)
    C = {}
    for ix in (0, 1):
        for iy in (0, 1):
            for iz in (0, 1):
                u, v = (ix - 0.5), (iy - 0.5)
                x, y = u * sx * (1.0 + tx * (iz * 2 - 1)), v * sy * (1.0 + ty * (iz * 2 - 1))
                if iz:
                    c, sn = math.cos(twist), math.sin(twist)
                    x, y = c * x - sn * y, sn * x + c * y
                    x, y = x + shx, y + shy
                    z = sz * (1.0 - drop - (sl_x + rag_x) * u - (sl_y + rag_y) * v)
                    z = max(z, 0.18 * sz)
                else:
                    z = sz * 0.012 * (u + v)
                C[(ix, iy, iz)] = np.array([x, y, z])
    return C
rng = random.Random(5)
t=time.time(); nf=[]; nv=[]; nt=[]; fails=0; maxdev=0
for k in range(400):
    sx=rng.uniform(0.4,1.6); sy=1.1; sz=rng.uniform(0.27,0.8)
    C=box_corners(rng,sx,sy,sz, 0.0 if k%3 else 0.5)
    r=S.build_stone(rng,C,top_chip=0.03 if k%2 else None)
    if r is None: fails+=1; continue
    P,F,Nn=r
    nf.append(len(F)); nv.append(len(P)); nt.append(sum(len(f)-2 for f in F))
    for f,n in zip(F,Nn):
        d=np.abs((P[f]-P[f][0])@n).max(); maxdev=max(maxdev,d)
print('time',time.time()-t,'fails',fails,'faces',np.mean(nf),max(nf),'verts',np.mean(nv),'tris',np.mean(nt),max(nt),'planarity max dev',maxdev)
