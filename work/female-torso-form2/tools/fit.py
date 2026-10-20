"""Nelder-Mead fit of the feature parameters against the plate side-profile envelope, with plausibility constraints.
python3 tools/fit.py bust|glute|both"""
import sys, json; sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-torso-form2/tools')
from torso2 import *

def strip_extents(co, zs, xmax):
    fe,be=section_extents(co,strip=(0,xmax),zg=zs)
    return fillnan(fe),fillnan(be)

def nm(f,x0,step,iters=400,tol=1e-6):
    n=len(x0); sim=[np.array(x0,float)]
    for i in range(n):
        x=np.array(x0,float); x[i]+=step[i]; sim.append(x)
    fs=[f(x) for x in sim]
    for it in range(iters):
        o=np.argsort(fs); sim=[sim[i] for i in o]; fs=[fs[i] for i in o]
        if abs(fs[-1]-fs[0])<tol: break
        c=np.mean(sim[:-1],axis=0); xr=c+(c-sim[-1]); fr=f(xr)
        if fr<fs[0]:
            xe=c+2*(c-sim[-1]); fe=f(xe)
            if fe<fr: sim[-1],fs[-1]=xe,fe
            else: sim[-1],fs[-1]=xr,fr
        elif fr<fs[-2]: sim[-1],fs[-1]=xr,fr
        else:
            xc=c+0.5*(sim[-1]-c); fc=f(xc)
            if fc<fs[-1]: sim[-1],fs[-1]=xc,fc
            else:
                for i in range(1,n+1): sim[i]=sim[0]+0.5*(sim[i]-sim[0]); fs[i]=f(sim[i])
    o=np.argsort(fs); return sim[o[0]],fs[o[0]]

BUST_KEYS=['b_zc','b_Rzd','b_Rzu','b_Ry','b_e','st_R','b_xc','b_Rxm','b_Rxl']
BUST_BOUNDS={'b_zc':(1.214,1.228),'b_Rzd':(0.054,0.066),'b_Rzu':(0.054,0.068),'b_Ry':(0.044,0.062),'b_ya':(-0.133,-0.129),'b_e':(0.010,0.034),'st_R':(0.006,0.024),'b_tilt':(0.0,0.5),'b_xc':(0.072,0.082),'b_Rxm':(0.046,0.056),'b_Rxl':(0.040,0.050)}
GLUTE_KEYS=['g_zc','g_Rzd','g_Rzu','g_Ry','g_ya','gr_C','gr_z1','gr_w','g_xc','g_Rxm','g_Rxl']
GLUTE_BOUNDS={'g_zc':(0.855,0.905),'g_Rzd':(0.070,0.100),'g_Rzu':(0.085,0.130),'g_Ry':(0.060,0.090),'g_ya':(0.114,0.119),'gr_C':(0.016,0.032),'gr_z1':(0.925,0.965),'gr_w':(0.035,0.085),'g_xc':(0.062,0.082),'g_Rxm':(0.075,0.100),'g_Rxl':(0.066,0.090)}

def penalty(x,keys,bounds):
    p=0.0
    for v,k in zip(x,keys):
        lo,hi=bounds[k]
        if v<lo: p+=((lo-v)/(hi-lo))**2*400
        if v>hi: p+=((v-hi)/(hi-lo))**2*400
    return p

def bust_obj(x,P0):
    P={**P0,**dict(zip(BUST_KEYS,x))}
    co=build2(P)
    zs=np.arange(1.14,1.321,0.01)
    fe,_=strip_extents(co,zs,0.20)
    err=1000*(fe-np.array([plate_front(z) for z in zs]))
    w=np.where((zs>=1.17)&(zs<=1.27),2.0,1.0)
    e=np.sqrt((w*err**2).sum()/w.sum())
    # sternum recess: the front extent on the central strip must not exceed apex by >16 mm nor be forward of it
    fs,_=strip_extents(co,np.array([1.20,1.23,1.26]),0.015)
    fa,_=strip_extents(co,np.array([1.20,1.23,1.26]),0.20)
    valley=1000*(fs-fa)             # + = sternum recessed behind the apex
    pv=0.0
    for v in valley[:2]:
        if v<8: pv+=(8-v)**2*0.15
        if v>20: pv+=(v-20)**2*0.15
    A=P['b_Ry']-P['b_e']
    pa=0.0
    if A<0.022: pa+=((0.022-A)*1000)**2*0.3
    if A>0.034: pa+=((A-0.034)*1000)**2*0.3
    return e+pv+pa+penalty(x,BUST_KEYS,BUST_BOUNDS)

def glute_obj(x,P0):
    P={**P0,**dict(zip(GLUTE_KEYS,x))}
    co=build2(P)
    zs=np.arange(0.82,1.041,0.01)
    _,be=strip_extents(co,zs,0.20)
    err=1000*(be-np.array([plate_back_soft(z) for z in zs]))
    w=np.where((zs>=0.84)&(zs<=1.0),2.0,1.0)
    e=np.sqrt((w*err**2).sum()/w.sum())
    # cleft depth: apex envelope vs central strip
    zc=np.array([0.86,0.88,0.90,0.93,0.96])
    _,bc=strip_extents(co,zc,0.012); _,ba=strip_extents(co,zc,0.20)
    depth=1000*(ba-bc)
    pd=0.0
    for z,d in zip(zc,depth):
        lo,hi={0.86:(22,32),0.88:(22,32),0.90:(18,30),0.93:(3,14),0.96:(0,6)}[z]
        if d<lo: pd+=(lo-d)**2*0.2
        if d>hi: pd+=(d-hi)**2*0.2
    return e+pd+penalty(x,GLUTE_KEYS,GLUTE_BOUNDS)

def fit(kind,P0):
    if kind=='bust':
        keys,obj=BUST_KEYS,bust_obj
    else:
        keys,obj=GLUTE_KEYS,glute_obj
    best=None
    x0=np.array([P0[k] for k in keys]); step=np.array([0.01*abs(v)+0.002 for v in x0])
    for rep in range(4):
        x,f=nm(lambda x:obj(x,P0),x0,step,iters=300)
        if best is None or f<best[1]: best=(x,f)
        x0=best[0]; step=step*0.6
        P0={**P0,**dict(zip(keys,best[0]))}
    return dict(zip(keys,[float(v) for v in best[0]])),best[1]

if __name__=='__main__':
    kind=sys.argv[1]
    P0={**DEFAULT2,**dict(b_Rzu=0.062,b_zc=1.232,b_Rxm=0.062,b_Rxl=0.050,b_Rzd=0.047,b_Ry=0.054,b_k=0.016,st_R=0.016,g_k=0.016,gr_C=0.022,g_Rzu=0.112,b_xc=0.072,b_tilt=0.25,g_ktop=0.045)}
    out={}
    if kind in ('bust','both'):
        r,f=fit('bust',P0); out.update(r); P0.update(r); print('bust fit obj %.3f'%f,{k:round(v,4) for k,v in r.items()})
    if kind in ('glute','both'):
        r,f=fit('glute',P0); out.update(r); P0.update(r); print('glute fit obj %.3f'%f,{k:round(v,4) for k,v in r.items()})
    json.dump(out,open(WD/f'data/fit_{kind}.json','w'),indent=1)
    co=build2(P0); np.save(WD/f'data/co_fit_{kind}.npy',co)
    r=envelope_report(co); print('front err',np.round(1000*(r[:,1]-r[:,3]),1)[(r[:,0]>=1.1)&(r[:,0]<=1.33)]); print('back err',np.round(1000*(r[:,2]-r[:,4]),1)[(r[:,0]>=0.80)&(r[:,0]<=1.1)])
