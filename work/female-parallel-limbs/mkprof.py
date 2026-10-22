"""Per-row symmetric target (px, plate scale) for arms+legs from plate polygons (front+back averaged), and current profile from model silhouette.
python3 mkprof.py prefix out.json"""
import sys, json, numpy as np
sys.path.insert(0,'../../Tools/HeroBase')
from plate_profiles import FEMALE as F
from PIL import Image, ImageDraw
def poly(pts):
    im=Image.new('L',(1280,720),0); ImageDraw.Draw(im).polygon(pts,fill=255); return np.array(im)>0
def runs(row):
    d=np.diff(np.concatenate([[0],row.astype(np.int8),[0]])); s=np.where(d==1)[0]; e=np.where(d==-1)[0]
    return list(zip(s.tolist(),e.tolist()))
def merge(r,gap=2):
    out=[]
    for a,b in r:
        if out and a-out[-1][1]<=gap: out[-1]=(out[-1][0],b)
        else: out.append((a,b))
    return out
def measure(mask,y):
    """-> dict of arm_out,arm_in,leg_in,leg_out (px, symmetric means) or None parts"""
    r=merge(runs(mask[y]),2)
    res={}
    if y<165 or not r: return res
    if y<226:
        a,b=r[0][0],r[-1][1]; res['arm_out']=(b-a)/2.0; return res
    # armpit-separated rows: arms = runs with centre far outboard
    c0=(r[0][0]+r[-1][1])/2.0
    if y<372 and len(r)>=3:
        res['arm_out']=(r[-1][1]-r[0][0])/2.0
        res['arm_in']=((c0-r[0][1])+(r[-1][0]-c0))/2.0
        mid=r[1:-1]; res['torso_out']=((c0-mid[0][0])+(mid[-1][1]-c0))/2.0
    elif y>=372:
        arms=[x for x in r if abs((x[0]+x[1])/2-c0)>74]
        legs=[x for x in r if abs((x[0]+x[1])/2-c0)<=74]
        if len(arms)==2 and y<430:
            res['arm_out']=((c0-arms[0][0])+(arms[1][1]-c0))/2.0
            res['arm_in']=((c0-arms[0][1])+(arms[1][0]-c0))/2.0
        if y>=380:
            # legs may be one run (hips) or two; get overall outer and inner gap
            if len(legs)>=1:
                lo=c0-legs[0][0]; ro=legs[-1][1]-c0
                res['leg_out']=(lo+ro)/2.0
                # inner gap: find gap between consecutive leg runs
                if len(legs)>=2:
                    g=[ (legs[i][1],legs[i+1][0]) for i in range(len(legs)-1)]
                    gl,gr=g[0]; res['leg_in']=((c0-gl)+(gr-c0))/2.0
                    res['leg_in']=abs(gr-gl)/2.0
    return res
pre=sys.argv[1]; res={}
views={'front':(poly(F['front_outline']),440),'back':(poly(F['back_outline']),847)}
rows=range(150,680)
tar={};cur={}
for y in rows:
    for view,(P,cx) in views.items():
        M=np.array(Image.open(f'{pre}_{view}.png'))[:,:,3]>127
        for name,mask,store in(('p',P,tar),('m',M,cur)):
            for k,v in measure(mask,y).items(): store.setdefault(k,{}).setdefault(y,[]).append(v)
def avg(store):
    out={}
    for k,d in store.items():
        ys=sorted(d); vals=np.array([np.mean(d[y]) for y in ys],float)
        # smooth with 9-row moving mean
        n=9; pad=np.pad(vals,(n//2,n//2),mode='edge'); sm=np.convolve(pad,np.ones(n)/n,mode='valid')
        out[k]={'y':ys,'v':sm.tolist()}
    return out
json.dump({'target':avg(tar),'current':avg(cur)},open(sys.argv[2],'w'))
for k in ('arm_out','arm_in','leg_out','leg_in'):
    t=avg(tar)[k]; c=avg(cur).get(k)
    print(k, 'rows',t['y'][0],t['y'][-1])
    for y in range(max(t['y'][0],150),t['y'][-1],40):
        i=t['y'].index(y) if y in t['y'] else None
        if i is None: continue
        ci=c['y'].index(y) if c and y in c['y'] else None
        print('  ',y,round(t['v'][i],1),'cur',round(c['v'][ci],1) if ci is not None else None)
