import numpy as np, sys
sys.path.insert(0,'../male-micro1e')
import hand_sdf as H
from zonelib import *
from quality import *
V,T,polys=load(); zR=np.load('data/zone_R.npy'); sh=np.load('data/shell_cur.npy')
ef=edge_faces(polys); Fn=face_normals(V,polys)
rows=[]
for (a,b),fs in ef.items():
    if len(fs)==2 and zR[a] and zR[b]:
        ang=np.degrees(np.arccos(np.clip((Fn[fs[0]]*Fn[fs[1]]).sum(),-1,1)))
        if ang>50:
            m=(V[a]+V[b])/2; l=H.to_local(m[None],+1)[0]
            rows.append((ang,l[0],l[1],l[2],bool(sh[a]),bool(sh[b]),np.linalg.norm(V[a]-V[b])*1000,a,b))
rows.sort(reverse=True)
print(len(rows))
for r in rows[:60]: print(f'ang {r[0]:6.1f}  local a\'={r[1]:+.3f} n={r[2]:+.3f} w={r[3]:+.3f} shell={r[4]},{r[5]} len={r[6]:.1f}mm ({r[7]},{r[8]})')
