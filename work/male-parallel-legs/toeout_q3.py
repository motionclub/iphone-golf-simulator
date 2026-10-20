import sys; sys.path.insert(0,'.')
import json, numpy as np
from PIL import Image, ImageDraw
from leglib import *
Vf=np.load('data/V_final.npy')
Q3=json.load(open('data/q3cams.json'))
masks={k:np.array(Image.open(f'data/plate_mask_{k}.png').convert('L'))>127 for k in Q3}
zonefaces=[p for p in F if all(ZONE[i] and V0[i,2]<0.30 for i in p)]
def rot_feet(V,alpha_deg,xp=0.19,yp=0.0):
    Vn=V.copy()
    for sel0,side in ((LEFT,1),(RIGHT,-1)):
        sel=sel0&(V[:,2]<0.16); P=V[sel]; x=P[:,0]*side; y=P[:,1]; z=P[:,2]
        th=np.radians(alpha_deg)*smoothstep(0.15,0.07,z); dx=x-xp; dy=y-yp
        x3=xp+dx*np.cos(th)-dy*np.sin(th); y3=yp+dx*np.sin(th)+dy*np.cos(th)
        Vn[sel]=np.stack([x3*side,y3,z],1)
    return Vn
def render(V,az,ox,sole,mpp):
    a=np.radians(az); R=np.array([np.cos(a),np.sin(a),0.0])
    px=ox+(V@R)/mpp; py=sole-V[:,2]/mpp
    img=Image.new('L',(1280,720),0); d=ImageDraw.Draw(img)
    for p in zonefaces: d.polygon([(px[i],py[i]) for i in p],fill=1)
    return np.array(img,bool)
def best_iou(V,k):
    c=Q3[k]; mpp=c['mpp']; m=masks[k]
    r0=int(c['sole']-0.14/mpp)
    best=(0,None)
    for az in np.arange(c['az']-14,c['az']+14.1,2):
        for dox in range(-10,11,2):
            r=render(V,az,c['ox']+dox,c['sole'],mpp)
            for dy in (-2,0,2):
                rr=np.roll(r,dy,axis=0)
                inter=(rr[r0:]&m[r0:]).sum(); uni=(rr[r0:]|m[r0:]).sum(); iou=inter/max(uni,1)
                if iou>best[0]: best=(iou,(az,dox,dy))
    return best
print('extra toe-out (deg)  IoU of feet rows (z<0.14) per q3 view [FL FR BL BR] and mean')
for al in (-3,0,3,6,10,14,18):
    V=rot_feet(Vf,al)
    ious=[best_iou(V,k) for k in ('q3FL','q3FR','q3BL','q3BR')]
    print('%3d  '%al,' '.join('%.3f(az%+.0f)'%(b[0],b[1][0]) for b in ious),' mean %.3f'%np.mean([b[0] for b in ious]))
