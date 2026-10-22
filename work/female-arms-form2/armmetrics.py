"""python3 armmetrics.py prefix_K1 -> json of arm silhouette metrics (front+back at plate framing, K=1 renders with alpha)."""
import sys, json, numpy as np
sys.path.insert(0,'../../Tools/HeroBase')
from plate_profiles import FEMALE as F
from PIL import Image, ImageDraw
H,W=720,1280; S=0.0025954198473282443
def poly(p): im=Image.new('L',(W,H),0); ImageDraw.Draw(im).polygon(p,fill=255); return np.array(im)>0
PF=poly(F['front_outline']); PB=poly(F['back_outline'])
yy,xx=np.mgrid[0:H,0:W]
def half(P,cx,sd): return P[:,np.clip(np.round(cx+sd*np.arange(0,140)).astype(int),0,W-1)]
dx=np.arange(0,140)[None,:].repeat(H,0); y=yy[:,:140]
Z=(y>=165)&(y<372)&(dx>=58)          # chat-8 'arms' zone
Zs=(y>=165)&(y<345)&(dx>=40)         # strict deltoid->wrist rows
pv={'frontL':half(PF,440,-1),'frontR':half(PF,440,1),'backL':half(PB,847,-1),'backR':half(PB,847,1)}
T=np.mean([m.astype(float) for m in pv.values()],0)
def err(a,b,z):
    a=a.astype(float);b=b.astype(float);u=np.maximum(a,b)[z].sum();return float(np.abs(a-b)[z].sum()/u)
def run(pre):
    mm={v:np.array(Image.open(f'{pre}_{v}.png'))[:,:,3]>127 for v in('front','back')}
    out={}
    for v,P,cx in(('front',PF,440),('back',PB,847)):
        M=mm[v]; z=(yy>=165)&(yy<372)&(np.abs(xx-cx)>=58); u=((P|M)&z).sum(); out[f'{v}_arms_xor_pct']=round(float((P^M)[z].sum()/u*100),2)
    Mh=(half(mm['front'],440,-1).astype(float)+half(mm['front'],440,1).astype(float))/2
    Mb=(half(mm['back'],847,-1).astype(float)+half(mm['back'],847,1).astype(float))/2
    Mf=(Mh+Mb)/2
    for nm,m in(('front',Mh),('mean_fb',Mf)):
        e=err(m,T,Z); ev=np.mean([err(q,T,Z) for q in pv.values()])
        out[f'consensus_{nm}']={'model':round(e,4),'plate_self':round(float(ev),4),'ratio':round(e/float(ev),3)}
    # outer-edge per row (mm): model vs plate consensus outer edge, rows 175..340
    def outer(m):  # m: (H,140) mask half -> outermost True col
        return np.array([ (np.where(m[r]>0.5)[0].max() if (m[r]>0.5).any() else -1) for r in range(H)],float)
    po=outer(T>0.5); mo=outer(Mf>0.5)
    rows=np.arange(175,341); d=(mo[rows]-po[rows])*S*1000
    out['outer_edge_dev_mm']={'mean_abs':round(float(np.abs(d).mean()),2),'max_abs':round(float(np.abs(d).max()),2),'mean_signed':round(float(d.mean()),2)}
    return out
if __name__=='__main__':
    print(json.dumps(run(sys.argv[1]),indent=1))
