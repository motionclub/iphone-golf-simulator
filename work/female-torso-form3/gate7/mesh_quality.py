"""Mesh integrity checks old vs new: face normal flips, edge stretch, triangle area change (zone), degenerate faces."""
import numpy as np, sys, json
d=np.load('data/start.npz'); co0=d['co'].astype(np.float64); tri=d['tri']; ed=d['edges']
T=np.load('data/zone.npz')['torso']
def fnorm(co):
    v0,v1,v2=co[tri[:,0]],co[tri[:,1]],co[tri[:,2]]
    n=np.cross(v1-v0,v2-v0); a=np.linalg.norm(n,axis=1); return n/np.maximum(a,1e-18)[:,None],a/2
def run(path,label):
    co=np.load(path).astype(np.float64)
    n0,a0=fnorm(co0); n1,a1=fnorm(co)
    zone_tri=T[tri].any(1)
    dot=(n0*n1).sum(1)
    flipped=int(((dot<0)&zone_tri).sum()); big=int(((dot<0.5)&zone_tri).sum())
    ratio=a1[zone_tri]/np.maximum(a0[zone_tri],1e-18)
    el0=np.linalg.norm(co0[ed[:,0]]-co0[ed[:,1]],axis=1); el1=np.linalg.norm(co[ed[:,0]]-co[ed[:,1]],axis=1)
    ze=T[ed].any(1); er=el1[ze]/np.maximum(el0[ze],1e-12)
    res={'label':label,'zone_tris':int(zone_tri.sum()),'flipped_tris':flipped,'tris_normal_turn_gt60deg':big,
         'tri_area_ratio_min':float(ratio.min()),'tri_area_ratio_p1':float(np.percentile(ratio,1)),'tri_area_ratio_p99':float(np.percentile(ratio,99)),'tri_area_ratio_max':float(ratio.max()),
         'edge_stretch_min':float(er.min()),'edge_stretch_max':float(er.max()),'edge_len_new_min_mm':float(el1[ze].min()*1000),'edge_len_new_max_mm':float(el1[ze].max()*1000),
         'degenerate_tris(area<1e-9)':int((a1<1e-9).sum()),'total_tris':int(len(tri))}
    print(json.dumps(res,indent=1)); return res
if __name__=='__main__':
    for p in sys.argv[1:]: run(p,p)
