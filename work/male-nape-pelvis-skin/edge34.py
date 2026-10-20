"""3/4-back panel outline comparison per row (z): plate mask vs render alpha. python3 edge34.py <tag...>
panel boxes (sheet px): q3BL cols 690-890 rows 440-700 ; q3BR cols 980-1180. Prints (render_edge - plate_edge) in mm along the sheet's horizontal axis for the left and right outline of the lower body (rows z .70..1.05)."""
import sys, numpy as np
from PIL import Image
R='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/hero/base_lock/'
L=np.asarray(Image.open(R+'male_multiangle_body.jpg').convert('L')).astype(float)
BOX={'q3BL':(690,890,440,700,(676,690,884,898)),'q3BR':(980,1180,440,700,(1000,1008,1146,1154))}
MPP=0.00582; SOLE=673.5
def plate_edges(panel):
    c0,c1,r0,r1,(b0,b1,b2,b3)=BOX[panel]; out={}
    for r in range(r0,r1):
        bg=np.median(np.concatenate([L[r,b0:b1],L[r,b2:b3]])); m=L[r,c0:c1]>bg+9
        out[r]=m
    return out
def runs(m):
    idx=np.where(m)[0]
    if len(idx)==0: return []
    br=np.where(np.diff(idx)>1)[0]; st=[idx[0]]+[idx[b+1] for b in br]; en=[idx[b] for b in br]+[idx[-1]]; return list(zip(st,en))
pan=sys.argv[1]; tags=sys.argv[2:]
c0,c1,r0,r1,_=BOX[pan]; pm=plate_edges(pan)
res={}
for t in tags:
    a=np.asarray(Image.open(f'r/{t}_s34/reg_{pan}_{c0}_{c1}_{r0}_{r1}_4.png'))[...,3]>127
    # render is 4x of the panel box: columns (c1-c0)*4
    res[t]=a
print(f'{pan}: outline (render - plate) mm per z; L=left outline of body (outer edge), R=right outline; only rows where both masks have a single outer run')
print('   z    '+'  '.join(f'{t:>14s}' for t in tags))
for z in np.arange(0.70,1.06,0.03):
    r=int(round(SOLE-z/MPP)); pr=runs(pm[r])
    if not pr: continue
    # outermost left/right edges of the plate within the panel (cols relative c0); exclude arms by taking runs that overlap the central 120 px of the panel
    cen=(c1-c0)//2; body=[(s,e) for s,e in pr if e>=cen-40 and s<=cen+40]
    if not body: continue
    pl=min(s for s,e in body); prr=max(e for s,e in body); row=f'{z:.2f} '
    for t in tags:
        a=res[t]; ra=a[(r-r0)*4:(r-r0)*4+4].any(0); rr=runs(ra); rb=[(s/4,e/4) for s,e in rr if e/4>=cen-40 and s/4<=cen+40]
        if not rb: row+='  '+'-'.rjust(14); continue
        rl=min(s for s,e in rb); rrt=max(e for s,e in rb)
        row+='  '+f'L{(rl-pl)*MPP*1000:+5.1f} R{(rrt-prr)*MPP*1000:+5.1f}'.rjust(14)
    print(row)
