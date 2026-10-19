#!/usr/bin/env python3
"""Offline replica of RenderedSky.BuildLut + the shader's sky colour, to tune profiles fast.
   tools/sky_tune.py out.png sunEl exposure turbidity mieG saturation [ms_lift]"""
import sys,numpy as np
from PIL import Image
out=sys.argv[1];sel,EXP,T,G,SAT=map(float,sys.argv[2:7]);MS=float(sys.argv[7]) if len(sys.argv)>7 else .08
Re,Ra,Hr,Hm=6360e3,6420e3,8000.,1200.
bR=np.array([5.802e-6,13.558e-6,33.1e-6]);bO=np.array([.65e-6,1.881e-6,.085e-6]);bMs,bMe=3.996e-6,4.4e-6
def rs(o,d,r):
    b=(o*d).sum(-1);c=(o*o).sum(-1)-r*r;h=b*b-c;sh=np.sqrt(np.maximum(h,0));t1=-b-sh;t2=-b+sh
    return np.where(h<0,-1,np.where(t1>0,t1,np.where(t2>0,t2,-1)))
def oz(h):return np.maximum(0,1-np.abs(h-25000)/15000)
def sky(dirs,sun):
    o=np.array([0,Re+2,0.]);n=len(dirs)
    tmax=rs(o[None],dirs,Ra);tg=rs(o[None],dirs,Re);tmax=np.where(tg>0,np.minimum(tmax,tg),tmax)
    sumR=np.zeros((n,3));sumM=np.zeros((n,3));od=np.zeros((n,3))
    VS,LS=20,8
    for i in range(VS):
        u0,u1=i/VS,(i+1)/VS;t0,t1=u0*u0*tmax,u1*u1*tmax;ds=t1-t0;tm=(t0+t1)/2
        p=o+dirs*tm[:,None];h=np.linalg.norm(p,axis=1)-Re
        dr=np.exp(-h/Hr)*ds;dm=np.exp(-h/Hm)*ds;dO=oz(h)*ds
        od+=bR*dr[:,None]+(bMe*T*dm)[:,None]+bO*dO[:,None]
        tl=rs(p,np.broadcast_to(sun,p.shape),Ra);blk=rs(p,np.broadcast_to(sun,p.shape),Re)>0
        odl=np.zeros((n,3));dsl=tl/LS
        for j in range(LS):
            q=p+sun*((j+.5)*dsl)[:,None];hl=np.linalg.norm(q,axis=1)-Re
            odl+=bR*(np.exp(-hl/Hr)*dsl)[:,None]+(bMe*T*np.exp(-hl/Hm)*dsl)[:,None]+bO*(oz(hl)*dsl)[:,None]
        tr=np.exp(-(od+odl));tr[blk]=0
        sumR+=tr*bR*dr[:,None];sumM+=tr*(bMs*T*dm)[:,None]
    mu=(dirs*sun).sum(1);pR=3/(16*np.pi)*(1+mu*mu)
    pM=3/(8*np.pi)*((1-G*G)*(1+mu*mu))/((2+G*G)*np.power(1+G*G-2*G*mu,1.5))
    return (sumR*pR[:,None]+sumR*MS/(4*np.pi)+sumM*pM[:,None])*EXP
se=np.radians(sel);sun=np.array([np.cos(se),np.sin(se),0])
W,H=720,240
az=np.linspace(-np.pi,np.pi,W);el=np.linspace(np.radians(60),np.radians(.3),H)
A,E=np.meshgrid(az,el);d=np.stack([np.cos(E)*np.cos(A),np.sin(E),np.cos(E)*np.sin(A)],-1).reshape(-1,3)
c=sky(d,sun).reshape(H,W,3)
l=(c*np.array([.2126,.7152,.0722])).sum(-1,keepdims=True);c=l+(c-l)*SAT
s=np.where(c<=.0031308,c*12.92,1.055*np.power(np.clip(c,0,None),1/2.4)-.055)
Image.fromarray((np.clip(s,0,1)*255).astype(np.uint8)).save(out)
print('zenith-ish',c[0,W//2].round(3),'horizon sun',c[-1,W//2].round(3),'horizon away',c[-1,0].round(3))
