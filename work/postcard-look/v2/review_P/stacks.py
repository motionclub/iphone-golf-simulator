import sys, os, math
R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, R + "/blender/scripts")
import bpy, numpy as np
import postcard_props_lib as PL
bpy.ops.wm.read_factory_settings(use_empty=True)
kinds=["ROCK_SEASTACK_A","ROCK_SEASTACK_B","ROCK_SEASTACK_C","ROCK_SPIRE_A"]
def tri_arrays(me):
    me.calc_loop_triangles()
    co=np.empty(len(me.vertices)*3); me.vertices.foreach_get("co",co); co=co.reshape(-1,3)
    t=np.array([lt.vertices[:] for lt in me.loop_triangles])
    return co,t
def raster(co,t,az,res=200):
    a=math.radians(az); c,s=math.cos(a),math.sin(a)
    u=co[:,0]*c+co[:,1]*s; v=co[:,2]
    return u,v
def fill(co,t,az):
    u,v=raster(co,t,az)
    zmin=v.min(); zmax=v.max()
    res=160
    H=zmax-zmin
    # sample grid in bbox
    umin,umax=u.min(),u.max()
    gx=np.linspace(umin,umax,res); gy=np.linspace(zmin,zmax,res)
    GX,GY=np.meshgrid(gx,gy)
    mask=np.zeros(GX.shape,bool)
    for tri in t:
        p=np.stack([u[tri],v[tri]],1)
        x0,y0=p.min(0);x1,y1=p.max(0)
        ix=(gx>=x0)&(gx<=x1); iy=(gy>=y0)&(gy<=y1)
        if not ix.any() or not iy.any(): continue
        sub=np.ix_(iy,ix)
        X=GX[sub];Y=GY[sub]
        d=(p[1,1]-p[2,1])*(p[0,0]-p[2,0])+(p[2,0]-p[1,0])*(p[0,1]-p[2,1])
        if abs(d)<1e-12: continue
        l1=((p[1,1]-p[2,1])*(X-p[2,0])+(p[2,0]-p[1,0])*(Y-p[2,1]))/d
        l2=((p[2,1]-p[0,1])*(X-p[2,0])+(p[0,0]-p[2,0])*(Y-p[2,1]))/d
        l3=1-l1-l2
        mask[sub]|=(l1>=0)&(l2>=0)&(l3>=0)
    return mask.mean(), mask, (umin,umax,zmin,zmax)
for k in kinds:
    ob=PL.library_object(k); me=ob.data
    co,t=tri_arrays(me)
    H=co[:,2].max()-co[:,2].min()
    fl=[]
    widths=[]
    for az in (0,45,90,135):
        f,m,_=fill(co,t,az); fl.append(f)
        # silhouette width at heights
        rows=m.shape[0]
        w=m.sum(1)/m.shape[1]
        # width in metres
        pass
    # width via silhouette horizontal extent at each height, over 4 azimuths: mean
    ws={}
    for az in (0,45,90,135):
        f,m,(u0,u1,z0,z1)=fill(co,t,az)
        res=m.shape[0]
        for h in (0.1,0.5,0.9):
            r=int(h*(res-1))
            band=m[max(0,r-3):r+4].any(0)
            idx=np.where(band)[0]
            ws.setdefault(h,[]).append((idx.max()-idx.min())/(res-1)*(u1-u0) if len(idx) else 0)
    wm={h:np.mean(v) for h,v in ws.items()}
    # flat cap: area of up-facing (nz>0.95) triangles / bbox footprint
    nz=[]; 
    tri=co[t]; n=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]); A=np.linalg.norm(n,axis=1)/2; nn=n/np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-12)
    flat=A[nn[:,2]>0.9].sum()
    foot=(co[:,0].max()-co[:,0].min())*(co[:,1].max()-co[:,1].min())
    # distinct heights of flat (upfacing) tris centroid
    print(k,"H %.1f"%H,"tris",len(t),"w10 %.2f w50 %.2f w90 %.2f taper90/10 %.2f"%(wm[.1],wm[.5],wm[.9],wm[.9]/wm[.1]),"fill",[round(x,2) for x in fl],"flat-up area/footprint %.2f"%(flat/foot), "welded",PL.welded_vertex_count(me))
