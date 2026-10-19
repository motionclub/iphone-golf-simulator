"""python3 tools/rough_map.py out.jpg params.json : offline front + 3/4 render coloured by local roughness (mean dihedral of a vertex's edges, deg)."""
import sys, os, json; OUT=os.path.abspath(sys.argv[1]); PJ=os.path.abspath(sys.argv[2]); sys.argv=['x']
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, nose_off as NO, render_off as RO
from PIL import Image
G=NO.head(json.load(open(PJ))); t=NO.h.tri
fn=np.cross(G[t[:,1]]-G[t[:,0]],G[t[:,2]]-G[t[:,0]]); fn/=np.maximum(np.linalg.norm(fn,axis=1),1e-12)[:,None]
e={}
for k,(a,b,c) in enumerate(t):
    for u,v in ((a,b),(b,c),(c,a)): e.setdefault((min(u,v),max(u,v)),[]).append(k)
acc=np.zeros(len(G)); cnt=np.zeros(len(G))
for (u,v),ks in e.items():
    if len(ks)==2:
        ang=np.degrees(np.arccos(np.clip(fn[ks[0]]@fn[ks[1]],-1,1))); acc[[u,v]]+=ang; cnt[[u,v]]+=1
r=acc/np.maximum(cnt,1)
# colour: render twice, mix shading with a heat colour where roughness is high
keep=G[t][:,:,1].min(1)>-175
ims=[]
for yaw in (0,-40):
    img,A=RO.render(G,t,yaw,keep=keep,res=520,half=95,centre=(0,-45,0))
    ims.append(img)
# per-pixel roughness: rasterise r as colour via a fake colour render (reuse renderer with color per vertex is not supported) -> instead overlay vertex dots
out=[]
for yaw,img in zip((0,-40),ims):
    a=np.radians(yaw); R=np.array([[np.cos(a),0,np.sin(a)],[0,1,0],[-np.sin(a),0,np.cos(a)]])
    P=(G-np.array([0,-45,0]))@R.T; s=520/190; px=(P[:,0]*s+260).astype(int); py=(260-P[:,1]*s).astype(int)
    im=img.copy(); front=P[:,2]>np.percentile(P[:,2],40)
    vis=(px>=0)&(px<520)&(py>=0)&(py<520)&front&(r>14)&(G[:,1]>-150)
    nm=RO.vnormals(G,t)@R.T; vis&=nm[:,2]>0.2
    for x,y,v in zip(px[vis],py[vis],r[vis]):
        c=(255,int(max(0,255-(v-14)*12)),0); im[max(y-1,0):y+2,max(x-1,0):x+2]=c
    out.append(Image.fromarray(im))
o=Image.new('RGB',(1040,520)); o.paste(out[0],(0,0)); o.paste(out[1],(520,0)); o.save(OUT,quality=90)
print('vertices r>14:',int(((r>14)&(G[:,1]>-150)&(G[:,1]<20)).sum()), ' r>20:',int(((r>20)&(G[:,1]>-150)&(G[:,1]<20)).sum()))
