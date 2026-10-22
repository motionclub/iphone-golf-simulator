"""Tiny SDF + marching-tetrahedra mesher (numpy only). Units metres. Inside = negative."""
import numpy as np
def smin(a,b,k):
    if k<=0: return np.minimum(a,b)
    h=np.clip(0.5+0.5*(b-a)/k,0,1); return b*(1-h)+a*h-k*h*(1-h)
def smax(a,b,k):
    return -smin(-a,-b,k)
class Shape:
    def __init__(self): self.parts=[]   # (kind,params,blend)
    def capsule(self,a,b,r0,r1=None,k=0.0):
        self.parts.append(('cap',(np.array(a,float),np.array(b,float),r0,r0 if r1 is None else r1),k)); return self
    def ellipsoid(self,c,radii,k=0.0,rot=None):
        self.parts.append(('ell',(np.array(c,float),np.array(radii,float),rot),k)); return self
    def ecyl(self,c,a,b,z0,z1,k=0.0):
        self.parts.append(('ecyl',(np.array(c,float),a,b,z0,z1),k)); return self
    def loft(self,stations,pivot=None,R=None,n=2.5,k=0.0):
        """stations: array rows (y, halfwidth, zbot, ztop, xoff); superellipse sections along y; flat end caps."""
        self.parts.append(('loft',(np.array(stations,float),pivot,R,n),k)); return self
    def econe(self,z0,c0,a0,b0,z1,c1,a1,b1,k=0.0):
        """elliptic cone between z0 and z1 (linear centre/radii), flat ends."""
        self.parts.append(('econe',(z0,np.array(c0,float),a0,b0,z1,np.array(c1,float),a1,b1),k)); return self
    def eval(self,P):
        d=None
        for kind,p,k in self.parts:
            if kind=='cap':
                a,b,r0,r1=p; ab=b-a; t=np.clip(((P-a)@ab)/(ab@ab),0,1)
                q=a+t[:,None]*ab; di=np.linalg.norm(P-q,axis=1)-(r0+(r1-r0)*t)
            elif kind=='loft':
                st,piv,R,n=p
                Q=P if R is None else (P-piv)@R+piv           # world->local when R maps local->world
                if not hasattr(self,'_lf'):
                    o=np.argsort(st[:,0]); ys_=st[o,0]; yf=np.arange(ys_.min(),ys_.max()+1e-9,0.0005)
                    cols=[np.interp(yf,ys_,st[o,j]) for j in range(1,5)]
                    wn=13; ker=np.ones(wn)/wn
                    cols=[np.convolve(np.pad(c,(wn//2,wn//2),mode='edge'),ker,mode='valid') for c in cols]
                    self._lf=(yf,cols)
                yf,cols=self._lf
                y=Q[:,1]; yc=np.clip(y,yf.min(),yf.max())
                w,zb,zt,xo=[np.interp(yc,yf,c) for c in cols]
                w=np.maximum(w,1e-3); hh=np.maximum((zt-zb)/2,1e-3); zc=(zt+zb)/2
                q=(np.abs((Q[:,0]-xo)/w)**n+np.abs((Q[:,2]-zc)/hh)**n)**(1.0/n)
                d2=(q-1)*np.minimum(w,hh)
                over=np.maximum(yf.min()-y,y-yf.max())
                di=np.where(over>0,np.hypot(np.maximum(d2,0),over),d2)
            elif kind=='econe':
                z0,c0,a0,b0,z1,c1,a1,b1=p; t=(P[:,2]-z0)/(z1-z0)
                cx=c0[0]+(c1[0]-c0[0])*t; cy=c0[1]+(c1[1]-c0[1])*t; a=a0+(a1-a0)*t; b=b0+(b1-b0)*t
                q=np.sqrt(((P[:,0]-cx)/a)**2+((P[:,1]-cy)/b)**2); dxy=(q-1)*np.minimum(a,b)
                di=np.maximum(dxy,np.maximum(z0-P[:,2],P[:,2]-z1))
            elif kind=='ecyl':
                c,a,b,z0,z1=p; q=np.sqrt(((P[:,0]-c[0])/a)**2+((P[:,1]-c[1])/b)**2)
                dxy=(q-1)*min(a,b); dz=np.maximum(z0-P[:,2],P[:,2]-z1)
                di=np.maximum(dxy,dz)
            else:
                c,r,rot=p; Q=P-c
                if rot is not None: Q=Q@rot
                kk=np.linalg.norm(Q/r,axis=1); k1=np.linalg.norm(Q/(r*r),axis=1)
                di=kk*(kk-1)/np.maximum(k1,1e-9)
            d=di if d is None else smin(d,di,k)
        return d
def mesh(shape,lo,hi,h):
    lo=np.array(lo,float); hi=np.array(hi,float)
    n=np.ceil((hi-lo)/h).astype(int)+1
    xs=[lo[i]+np.arange(n[i])*h for i in range(3)]
    G=np.stack(np.meshgrid(*xs,indexing='ij'),-1).reshape(-1,3)
    f=shape.eval(G).reshape(n)
    idx=np.arange(n[0]*n[1]*n[2]).reshape(n)
    cs=[(0,0,0),(1,0,0),(1,1,0),(0,1,0),(0,0,1),(1,0,1),(1,1,1),(0,1,1)]
    def corner(c): 
        return idx[c[0]:n[0]-1+c[0],c[1]:n[1]-1+c[1],c[2]:n[2]-1+c[2]].ravel()
    C=[corner(c) for c in cs]
    tets=[(0,5,1,6),(0,1,2,6),(0,2,3,6),(0,3,7,6),(0,7,4,6),(0,4,5,6)]
    F=f.ravel(); 
    tri_chunks=[]
    for t in tets:
        ids=np.stack([C[i] for i in t],1)    # (m,4)
        vals=F[ids]
        ins=vals<0
        cnt=ins.sum(1); keep=(cnt>0)&(cnt<4)
        ids=ids[keep]; vals=vals[keep]; ins=ins[keep]
        # edges of tet
        E=[(0,1),(0,2),(0,3),(1,2),(1,3),(2,3)]
        crossing=np.stack([ins[:,a]!=ins[:,b] for a,b in E],1)
        for m_,(cnt_) in []: pass
        for case in (1,2,3):
            sel=np.where(ins.sum(1)==case)[0]
            if not len(sel): continue
            I=ids[sel]; Ins=ins[sel]
            for row in range(len(sel)):
                pass
        tri_chunks.append((ids,vals,ins))
    # vectorised triangle emission
    verts_edge={}; out_tris=[]
    def evert(a,b):   # arrays of global node idx -> edge key
        lo_=np.minimum(a,b); hi_=np.maximum(a,b); return lo_*np.int64(F.size)+hi_
    Gp=G
    all_keys=[]; all_tri_keys=[]
    for ids,vals,ins in tri_chunks:
        if not len(ids): continue
        cnt=ins.sum(1)
        for case in (1,2,3):
            sel=np.where(cnt==case)[0]
            if not len(sel): continue
            I=ids[sel]; N=ins[sel]
            if case in (1,3):
                lone=(N if case==1 else ~N)
                li=np.argmax(lone,1)             # lone vertex local idx
                others=[]
                for j in range(3):
                    # j-th of the other three vertices
                    mask=np.ones((len(sel),4),bool); mask[np.arange(len(sel)),li]=False
                    oi=np.argsort(~mask,1,kind='stable')[:,j]
                    others.append(oi)
                a=I[np.arange(len(sel)),li]
                tris=[]
                for j in range(3): tris.append((a,I[np.arange(len(sel)),others[j]]))
                keys=[evert(x,y) for x,y in tris]
                inside_c=np.where((N if case==1 else ~N)[:,:,None],Gp[I],0).sum(1)  # lone vertex position
                lone_pos=Gp[a]
                # oriented: normal away from the "inside" side
                sign_in=(1 if case==1 else -1)
                pts=[]
                for (x,y) in tris:
                    fx=F[x]; fy=F[y]; t=(fx/(fx-fy))[:,None]; pts.append(Gp[x]+t*(Gp[y]-Gp[x]))
                n_=np.cross(pts[1]-pts[0],pts[2]-pts[0])
                # direction from inside-vertex-set to outside: for case1 outside = others centroid; inside=lone
                oc=np.mean([Gp[y] for _,y in tris],axis=0)
                dirv=(oc-lone_pos)*sign_in
                flip=(n_*dirv).sum(1)<0
                T=np.stack(pts,1)
                T[flip]=T[flip][:,[0,2,1]]
                K=np.stack(keys,1); K[flip]=K[flip][:,[0,2,1]]
                out_tris.append((T,K))
            else:
                # 2 inside / 2 outside -> quad
                for r in range(len(sel)):
                    pass
                inn=np.argsort(~N,1,kind='stable')[:,:2]; out=np.argsort(N,1,kind='stable')[:,:2]
                ar=np.arange(len(sel))
                i0,i1=I[ar,inn[:,0]],I[ar,inn[:,1]]; o0,o1=I[ar,out[:,0]],I[ar,out[:,1]]
                pairs=[(i0,o0),(i0,o1),(i1,o1),(i1,o0)]   # ring order around the quad
                pts=[];keys=[]
                for x,y in pairs:
                    fx=F[x]; fy=F[y]; t=(fx/(fx-fy))[:,None]; pts.append(Gp[x]+t*(Gp[y]-Gp[x])); keys.append(evert(x,y))
                ic=(Gp[i0]+Gp[i1])/2; oc=(Gp[o0]+Gp[o1])/2
                for tri in ((0,1,2),(0,2,3)):
                    T=np.stack([pts[j] for j in tri],1); K=np.stack([keys[j] for j in tri],1)
                    n_=np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0]); flip=(n_*(oc-ic)).sum(1)<0
                    T[flip]=T[flip][:,[0,2,1]]; K[flip]=K[flip][:,[0,2,1]]
                    out_tris.append((T,K))
    T=np.concatenate([t for t,_ in out_tris]); K=np.concatenate([k for _,k in out_tris])
    uk,inv=np.unique(K.ravel(),return_inverse=True)
    V=np.zeros((len(uk),3)); V[inv]=T.reshape(-1,3)
    Fc=inv.reshape(-1,3)
    ok=(Fc[:,0]!=Fc[:,1])&(Fc[:,1]!=Fc[:,2])&(Fc[:,0]!=Fc[:,2]); Fc=Fc[ok]
    return V,Fc
if __name__=='__main__':
    s=Shape().capsule((0,0,0),(0,0,0.1),0.02,0.015).ellipsoid((0.03,0,0.03),(0.02,0.015,0.03),k=0.01)
    V,Fc=mesh(s,(-0.06,-0.06,-0.04),(0.08,0.06,0.16),0.004)
    print(V.shape,Fc.shape)
    # watertight check
    e=np.sort(np.concatenate([Fc[:,[0,1]],Fc[:,[1,2]],Fc[:,[2,0]]]),1)
    u,c=np.unique(e,axis=0,return_counts=True); print('edge counts',np.bincount(c))
