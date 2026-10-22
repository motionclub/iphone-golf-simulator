import sys, math
R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, R + "/blender/scripts")
import bpy, numpy as np
import postcard_props_lib as PL
bpy.ops.wm.read_factory_settings(use_empty=True)
PL.ensure_library()
def sil(co,tris,az,res=120):
    a=math.radians(az); u=co[:,0]*math.cos(a)+co[:,1]*math.sin(a); v=co[:,2]
    u0,u1,v0,v1=u.min(),u.max(),v.min(),v.max()
    img=np.zeros((res,res),bool)
    gx=(u-u0)/(u1-u0+1e-9)*(res-1); gy=(v-v0)/(v1-v0+1e-9)*(res-1)
    for t in tris:
        P=np.stack([gx[t],gy[t]],1)
        mn=np.floor(P.min(0)).astype(int); mx=np.ceil(P.max(0)).astype(int)
        xs,ys=np.meshgrid(np.arange(mn[0],mx[0]+1),np.arange(mn[1],mx[1]+1))
        pts=np.stack([xs.ravel(),ys.ravel()],1).astype(float)
        a_,b_,c_=P
        d=(b_[1]-c_[1])*(a_[0]-c_[0])+(c_[0]-b_[0])*(a_[1]-c_[1])
        if abs(d)<1e-9: continue
        l1=((b_[1]-c_[1])*(pts[:,0]-c_[0])+(c_[0]-b_[0])*(pts[:,1]-c_[1]))/d
        l2=((c_[1]-a_[1])*(pts[:,0]-c_[0])+(a_[0]-c_[0])*(pts[:,1]-c_[1]))/d
        m=(l1>=-0.02)&(l2>=-0.02)&(1-l1-l2>=-0.02)
        p=pts[m].astype(int); img[np.clip(p[:,1],0,res-1),np.clip(p[:,0],0,res-1)]=True
    return img.mean(), img
for k in ["ROCK_SEASTACK_A","ROCK_SEASTACK_B","ROCK_SEASTACK_C","ROCK_SEASTACK_D","ROCK_SEASTACK_E","ROCK_SPIRE_A"]:
    ob=PL.library_object(k); me=ob.data; me.calc_loop_triangles()
    co=np.empty(len(me.vertices)*3); me.vertices.foreach_get("co",co); co=co.reshape(-1,3)
    tris=np.array([lt.vertices[:] for lt in me.loop_triangles])
    z0,z1=co[:,2].min(),co[:,2].max(); H=z1-z0
    def wid(f):
        z=z0+f*H; m=np.abs(co[:,2]-z)<0.04*H
        return (co[m,:2].max(0)-co[m,:2].min(0)).max() if m.any() else 0
    w10,w50,w90=wid(.1),wid(.5),wid(.9)
    # flat top area: faces with n.z>0.9 area / bbox plan area
    A=0;Af=0
    for p in me.polygons:
        A+=p.area
        if p.normal.z>0.9: Af+=p.area
    plan=(co[:,0].max()-co[:,0].min())*(co[:,1].max()-co[:,1].min())
    # widest "band widening": max over bands of width up vs below
    ws=[wid(f) for f in np.linspace(.05,.95,19)]
    wid_up=max(ws[i+1]/max(ws[i],1e-6) for i in range(len(ws)-1))
    fills=[sil(co,tris,az)[0] for az in (0,45,90,135)]
    print(f"{k:16s} H={H:5.1f} w10={w10:5.1f} w50={w50:5.1f} w90={w90:5.1f} taper90/10={w90/w10:.2f} maxStepUp={wid_up:.2f} flatTop%={100*Af/plan:.1f} fills={[round(f,2) for f in fills]} aspect={H/max(w10,1e-6):.1f}")
