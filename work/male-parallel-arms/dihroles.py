import sys, json, numpy as np
sys.path.insert(0,'hand'); sys.path.insert(0,'../male-micro1e')
import roles, run, quality
P=json.load(open('hand/params_m1f_final.json')); R=roles.roles(P)
tag=sys.argv[1]; thr=float(sys.argv[2])
V=np.load(f'data/it/{tag}_cur.npy') if tag!='base' else run.V0.astype(np.float32)
inv={}  # cur index -> (side, role)
for (s,fi),r in R.items():
    if run.IDX[fi]>=0: inv[int(run.IDX[fi])]=(s,r)
ef=quality.edge_faces(run.polys); Fn=quality.face_normals(V.astype(float),run.polys); zz=run.ZR|run.ZL
rows=[]
for (a,b),fs in ef.items():
    if len(fs)==2 and zz[a] and zz[b] and V[a,0]>0:
        ang=np.degrees(np.arccos(np.clip((Fn[fs[0]]*Fn[fs[1]]).sum(),-1,1)))
        if ang>thr: rows.append((ang,a,b))
rows.sort(reverse=True)
print(len(rows),'edges >',thr,'(right side)')
from collections import Counter
for ang,a,b in rows[:40]: print(f'{ang:6.1f}',inv.get(a,('-','forearm')),inv.get(b,('-','forearm')))
