"""Scratch proposed P7 basalt network. No production files are modified.

Bounded connected fork trees retain an elongated geological envelope. Fine
cold grooves join neighboring trees; plain UV zones carry no hot emission.
The existing prism normal/albedo structure is preserved for this candidate.
"""
import numpy as np

def bounded_network(u,v,base,*,seed=311,variant=1):
    import golf_look_textures as T
    H,W=u.shape;rng=np.random.default_rng([seed,81])
    field=np.zeros((H,W),np.float32);depth=np.zeros_like(field)
    gx=np.zeros_like(field);gy=np.zeros_like(field)
    cold=np.zeros_like(field)
    centers=(.113,.435,.532,.728,.825,.946)
    zones=((.009,.061),(.165,.385),(.576,.685),(.772,.796),(.854,.893))
    segments=[];trees=[]
    def draw(a,b,hw,intensity=1.,hot=True):
        a=np.asarray(a);b=np.asarray(b);d=b-a;ln=np.linalg.norm(d)
        if ln<1e-7:return
        d=d/ln;pad=hw*2+3/max(H,W)
        x0=max(0,int((min(a[0],b[0])-pad)*W));x1=min(W,int(np.ceil((max(a[0],b[0])+pad)*W)))
        y0=max(0,int((1-max(a[1],b[1])-pad)*H));y1=min(H,int(np.ceil((1-min(a[1],b[1])+pad)*H)))
        if x1<=x0 or y1<=y0:return
        sl=np.s_[y0:y1,x0:x1];dx=u[sl]-a[0];dy=v[sl]-a[1]
        t=np.clip(dx*d[0]+dy*d[1],0,ln)
        perp=dx*(-d[1])+dy*d[0];dist=np.sqrt((dx-t*d[0])**2+(dy-t*d[1])**2)
        core=(1-T.sm(hw*.3,hw*1.1,dist))*intensity
        if hot:field[sl]=np.maximum(field[sl],core)
        else:cold[sl]=np.maximum(cold[sl],core)
        groove=(1-T.sm(hw*.35,hw*1.4,dist))
        depth[sl]=np.maximum(depth[sl],groove)
        walls=T.sm(hw*.2,hw*.6,dist)*(1-T.sm(hw,hw*1.75,dist))
        gx[sl]+=np.sign(perp)*(-d[1])*walls*.23
        gy[sl]+=np.sign(perp)*d[0]*walls*.23
        segments.append(dict(a=a.tolist(),b=b.tolist(),width=hw*2,hot=hot))
    for j,cx in enumerate(centers):
        available=.022 if j==4 else .028
        for k,cy0 in enumerate((.095,.340,.630,.890)):
            cy=cy0+rng.uniform(-.025,.025)
            # The long sparse ends give an elongated real envelope. Most heat
            # lies in its connected branching central fault, rather than lines.
            ys=np.array([-.067,-.033,-.012,0,.012,.033,.067])+cy
            xx=cx+rng.uniform(-.005,.005,len(ys));xx[0]=xx[-1]=cx
            path=np.stack([xx,ys],1)
            for a,b in zip(path[:-1],path[1:]):draw(a,b,.00175,1.)
            def fitted(pt):
                return np.array([np.clip(pt[0],cx-available,cx+available),np.clip(pt[1],cy-.025,cy+.025)])
            # Irregular connected fork paths replace the failed parallel fans.
            # Each actual turn has small Y branches; no repeated horizontal rung.
            for side in (-1,1):
                for yoff in (-.012,.001,.013):
                    start=np.array([float(np.interp(cy+yoff,ys,xx)),cy+yoff])
                    for step in range(3):
                        end=fitted(np.array([cx+side*available*(step+1)/3,
                                             cy+yoff+rng.uniform(-.013,.013)]))
                        draw(start,end,.00215,1.)
                        if step<2:
                            for sign in (-1,1):
                                twig=fitted(end+np.array([side*rng.uniform(.002,.006),sign*rng.uniform(.004,.008)]))
                                draw(end,twig,.00175,.98)
                        start=end
            trees.append(dict(center=[cx,cy],envelope=[cx-available,cy-.067,cx+available,cy+.067]))
    # These cooled fractures remain visible in the albedo/normal. Their glow is
    # explicitly below both inherited hard glow masks, not an erased network.
    for k in range(4):
        for j in range(len(centers)-1):
            a=trees[j*4+k]['center'];b=trees[(j+1)*4+k]['center']
            mid=[(a[0]+b[0])*.5,(a[1]+b[1])*.5+rng.uniform(-.035,.035)]
            draw(a,mid,.00125,.9,hot=False);draw(mid,b,.00125,.9,hot=False)
    # Heat fades toward the tile's middle; hotter lower/upper tile edges are
    # periodic, while the opposite emission edge samples stay identically dark.
    heat=.80+.20*((.5+.5*np.cos(2*np.pi*v))**1.3)
    field=np.clip(field*heat,0,1)
    keys=[0,.18,.45,.72,1]
    cols=np.array([[0,0,0],[70,8,0],[190,45,5],[250,100,16],[255,160,40]])/255
    E=np.stack([np.interp(field,keys,cols[:,i]) for i in range(3)],-1).astype(np.float32)
    E=np.maximum(E,cold[...,None]*np.array([7,1,0],np.float32)/255)
    for a,b in zones:
        # The hot tree envelopes were reserved outside these zones. Cooled
        # grooves cross them, but their7/255 maximum is a genuine plain chart.
        hot=(u>=a)&(u<=b)
        E[hot]=np.minimum(E[hot],np.array([7,1,0],np.float32)/255)
    E[0]=E[-1]=0;E[:,0]=E[:,-1]=0
    N=base['N'].copy()
    # Existing prism bevels and fracture normal walls stay intact. New grooves
    # occupy their front planes, adding no false block-fracture normal event.
    front=(np.abs(N[...,0])<.20)&(np.abs(N[...,1])<.20)
    N[...,0]+=np.clip(gx,-.22,.22)*front;N[...,1]+=np.clip(gy,-.22,.22)*front
    N[...,2]=np.sqrt(np.maximum(1-N[...,0]**2-N[...,1]**2,.03))
    N/=np.linalg.norm(N,axis=2,keepdims=True)
    C=base['C'].copy()
    return dict(C=C,N=N,E=E),dict(centers=centers,zones=zones,segments=segments,trees=trees,seed=seed,variant=variant)
