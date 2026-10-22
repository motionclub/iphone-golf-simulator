"""Compare the rear contour (mm) plate(sub-pixel) vs renders (4x alpha, sub-pixel): python3 rearcmp.py zlo zhi step tag..."""
import sys, json, numpy as np
from PIL import Image
R='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/'
cams={c['name']:c for c in json.load(open(R+'work/male-silhouette/reference-cameras.json'))['views']}
pl=json.load(open('data/plate_rear_subpx.json')); zsP=np.array(pl['z'])
def render_edge(tag, view, z):
    c=cams[view]; a=np.asarray(Image.open(f'r/{tag}_sil4/{view}@4.png'))[...,3].astype(float)/255; mpp=c['metres_per_pixel']
    r=int(round((c['sole_y']-z/mpp)*4)); row=a[r]; cx=c['centre_x']*4
    cols=np.where(row>0.5)[0]
    if len(cols)==0: return None
    if view=='left': e=cols.max()+ (row[cols.max()+1] if cols.max()+1<len(row) else 0)    # sub-pixel using partial coverage of the next pixel
    else: e=cols.min()- (row[cols.min()-1] if cols.min()>0 else 0)
    return (e-cx)/4*mpp*(1 if view=='left' else -1)+0.0
def table(zlo,zhi,step,tags):
    out=[]
    for z in np.arange(zlo,zhi+1e-9,step):
        i=int(round((z-0.70)/0.002)); pL=pl['left'][i]; pR=pl['right'][i]
        row=[z, pL, pR]
        for t in tags: row+= [render_edge(t,'left',z), render_edge(t,'right',z)]
        out.append(row)
    return out
if __name__=='__main__':
    zlo,zhi,st=float(sys.argv[1]),float(sys.argv[2]),float(sys.argv[3]); tags=sys.argv[4:]
    print('z    plate L/R (mm) | '+' | '.join(f'{t} L/R err(render-plate)' for t in tags))
    for r in table(zlo,zhi,st,tags):
        z,pL,pR=r[:3]; s=f'{z:.2f} {pL*1000 if pL else float("nan"):6.1f}/{pR*1000 if pR else float("nan"):6.1f} |'
        for k,t in enumerate(tags):
            eL,eR=r[3+2*k],r[4+2*k]
            s+=f'  {(eL-pL)*1000 if (eL is not None and pL) else float("nan"):+6.1f}/{(eR-pR)*1000 if (eR is not None and pR) else float("nan"):+6.1f} |'
        print(s)
