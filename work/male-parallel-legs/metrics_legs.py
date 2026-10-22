"""before/after fidelity metrics for the legs/feet zone.  python metrics_legs.py <base.npy> <new.npy> <out.json>"""
import sys, json
sys.path.insert(0,'.')
import numpy as np
from PIL import Image, ImageDraw
from leglib import *
from edges import spans
base=np.load(sys.argv[1]); new=np.load(sys.argv[2]); outj=sys.argv[3]
C_NEW=np.array([(-0.2235,0.030),(-0.2215,0.045),(-0.2150,0.054),(-0.2000,0.061),(-0.1800,0.067),(-0.1600,0.0705),(-0.1400,0.079),(-0.1200,0.0905),(-0.1000,0.099),(-0.0850,0.110),(-0.0720,0.124),(-0.0640,0.140),(-0.0620,0.160),(-0.0640,0.190),(-0.0620,0.220),(-0.0620,0.250),(-0.0660,0.300)])
def sag_contour(V):
    """upper-front boundary of the left leg's (y,z) silhouette: for each z>=0.09 min y, for each y the max z for z<0.14  -> dense polyline pts"""
    sel=LEFT&(V[:,2]<0.40); faces=[p for p in F if all(sel[i] for i in p)]
    S=2000.0; y0,z0=-0.30,-0.01; W=int(0.45*S); H=int(0.42*S)
    img=Image.new('L',(W,H),0); d=ImageDraw.Draw(img)
    for p in faces: d.polygon([((V[i,1]-y0)*S,(V[i,2]-z0)*S) for i in p],fill=1)
    m=np.array(img,bool)
    e=m&~(np.roll(m,1,0)&np.roll(m,-1,0)&np.roll(m,1,1)&np.roll(m,-1,1))
    zs,ys=np.nonzero(e); P=np.stack([ys/S+y0,zs/S+z0],1); return P
def contour_error(V):
    P=sag_contour(V)
    # sample the plate polyline densely
    t=np.linspace(0,1,400); seg=np.cumsum(np.r_[0,np.linalg.norm(np.diff(C_NEW,axis=0),axis=1)]); seg/=seg[-1]
    Q=np.stack([np.interp(t,seg,C_NEW[:,0]),np.interp(t,seg,C_NEW[:,1])],1)
    d=np.array([np.min(np.linalg.norm(P-q,axis=1)) for q in Q])*1000
    # restrict to the instep part (y<-0.075) to report separately
    inst=Q[:,0]<-0.075
    return dict(mean_mm=float(d.mean()),max_mm=float(d.max()),instep_mean_mm=float(d[inst].mean()),instep_max_mm=float(d[inst].max()))
def extents(V):
    out={}
    for z in (0.015,0.025,0.035,0.045,0.055):
        s=ZONE&(np.abs(V[:,2]-z)<0.006); out[f'{z:.3f}']=(float(V[s,1].min()),float(V[s,1].max()))
    return out
def plate_extents():
    out={}
    for z in (0.015,0.025,0.035,0.045,0.055):
        fr=[];bk=[]
        for v in ('left','right'):
            sp=spans(v,z); fr.append(sp[0][0]); bk.append(sp[-1][1])
        out[f'{z:.3f}']=(float(np.mean(fr)),float(np.mean(bk)))
    return out
def ankle_center(V):
    out={}
    for z in (0.16,0.19,0.22):
        s=ZONE&(np.abs(V[:,2]-z)<0.006); out[f'{z:.2f}']=(float(V[s,1].min()),float(V[s,1].max()),float(0.5*(V[s,1].min()+V[s,1].max())))
    return out
def plate_ankle():
    out={}
    for z in (0.16,0.19,0.22):
        a=[];b=[]
        for v in ('left','right'):
            sp=spans(v,z); a.append(sp[0][0]); b.append(sp[-1][1])
        out[f'{z:.2f}']=(float(np.mean(a)),float(np.mean(b)),float(0.5*(np.mean(a)+np.mean(b))))
    return out
def banding(V):
    """z-banding / ripple: rms (micrometres) of the normal component of (V - vertical-anisotropic-Taubin(V, 40 it)) over the leg tube z 0.2..0.7"""
    w=np.zeros(N); w[ZONE]=1
    S=taubin_aniso(V,w,iters=40); n=normals(V); d=((S-V)*n).sum(1)
    sel=ZONE&(V[:,2]>0.2)&(V[:,2]<0.7); return float(np.sqrt((d[sel]**2).mean())*1e6)
def normal_roughness(V):
    """rms of (vertex - 25x Taubin-smoothed vertex) along the normal for the leg tube z 0.2..0.7, micrometres"""
    w=np.zeros(N); w[ZONE]=1
    S=taubin(V,w,iters=25); n=normals(V); d=((S-V)*n).sum(1)
    sel=ZONE&(V[:,2]>0.2)&(V[:,2]<0.7); return float(np.sqrt((d[sel]**2).mean())*1e6)
def consensus_dev(V):
    devs_x=[];devs_y=[]
    for z in np.arange(0.18,0.70,0.02):
        ins=[];outs=[]
        for v,w in (('bald_front',2),('sheet_front',1),('bald_back',2),('sheet_back',1)):
            sp=[s for s in spans(v,z) if s[0]>=0.0 and s[1]>0.05]
            if sp: ins+=[sp[0][0]]*w; outs+=[sp[0][1]]*w
        s=LEFT&(np.abs(V[:,2]-z)<0.006); s2=RIGHT&(np.abs(V[:,2]-z)<0.006)
        mi=0.5*(V[s,0].min()+(-V[s2,0].max())); mo=0.5*(V[s,0].max()+(-V[s2,0].min()))
        devs_x+= [abs(mi-np.mean(ins)),abs(mo-np.mean(outs))]
        yf=[];yb=[]
        for v in ('left','right'):
            sp=spans(v,z); yf.append(sp[0][0]); yb.append(sp[-1][1])
        sy=ZONE&(np.abs(V[:,2]-z)<0.006)
        devs_y+=[abs(V[sy,1].min()-np.mean(yf)),abs(V[sy,1].max()-np.mean(yb))]
    return dict(x_edge_mean_abs_mm=float(np.mean(devs_x)*1000),y_edge_mean_abs_mm=float(np.mean(devs_y)*1000))
def knee_relief(V):
    """front-surface y at the knee centre line minus the mean of the y 5 cm above and below (mm; positive = proud)"""
    out=[]
    for sel0,side in ((LEFT,1),(RIGHT,-1)):
        def fy(z):
            s=sel0&(np.abs(V[:,2]-z)<0.006)&(np.abs(V[:,0]-side*0.136)<0.02); return V[s,1].min()
        out.append((np.mean([fy(0.47),fy(0.58)])-fy(0.52))*1000)
    return float(np.mean(out))
res={}
for tag,V in (('base',base),('new',new)):
    res[tag]=dict(near_foot_sagittal_contour_vs_plate=contour_error(V),foot_y_extents=extents(V),ankle_y=ankle_center(V),band_residual_um=banding(V),normal_roughness_um=normal_roughness(V),consensus_edge_dev=consensus_dev(V),knee_front_relief_mm=knee_relief(V))
res['plate_foot_y_extents']=plate_extents(); res['plate_ankle_y']=plate_ankle()
json.dump(res,open(outj,'w'),indent=1)
for tag in ('base','new'):
    r=res[tag]; print(tag,'| near-foot contour err mean %.1f max %.1f | instep mean %.1f max %.1f mm'%(r['near_foot_sagittal_contour_vs_plate']['mean_mm'],r['near_foot_sagittal_contour_vs_plate']['max_mm'],r['near_foot_sagittal_contour_vs_plate']['instep_mean_mm'],r['near_foot_sagittal_contour_vs_plate']['instep_max_mm']),
      '| banding %.0f um  roughness %.0f um | edge dev x %.2f y %.2f mm | knee relief %.1f mm'%(r['band_residual_um'],r['normal_roughness_um'],r['consensus_edge_dev']['x_edge_mean_abs_mm'],r['consensus_edge_dev']['y_edge_mean_abs_mm'],r['knee_front_relief_mm']))
print('plate foot y extents',res['plate_foot_y_extents']); print('base',res['base']['foot_y_extents']); print('new ',res['new']['foot_y_extents'])
print('plate ankle y',res['plate_ankle_y']); print('base',res['base']['ankle_y']); print('new ',res['new']['ankle_y'])
