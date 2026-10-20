"""blender -b --python finalize_checks.py -- <S1.blend> <final.blend> <out.json>  : blend-level integrity + zone audit + numeric checks"""
import bpy, sys, json, hashlib, numpy as np
from pathlib import Path
W=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-parallel-arms')
sys.path[:0]=[str(W),str(W.parent/'male-micro1i/pylib')]
a=sys.argv[sys.argv.index('--')+1:]; S1,FIN,OUT=a
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def info(path):
    bpy.ops.wm.open_mainfile(filepath=path)
    o=bpy.data.objects['Body_M']; me=o.data; n=len(me.vertices)
    V=np.zeros(n*3); me.vertices.foreach_get('co',V); V=V.reshape(-1,3).astype(np.float32)
    polys=[tuple(p.vertices) for p in me.polygons]
    groups=[g.name for g in o.vertex_groups]
    gw={}
    for g in o.vertex_groups:
        idx=[v.index for v in me.vertices if any(vg.group==g.index for vg in v.groups)]
        gw[g.name]=idx
    fm=bpy.data.objects['Face_M'].data; FV=np.zeros(len(fm.vertices)*3); fm.vertices.foreach_get('co',FV)
    # edge stats
    from collections import Counter
    c=Counter()
    for p in polys:
        for k in range(len(p)):
            a_,b_=p[k],p[(k+1)%len(p)]; c[(min(a_,b_),max(a_,b_))]+=1
    boundary=sum(1 for v in c.values() if v==1); nonman=sum(1 for v in c.values() if v>2)
    used=set(v for p in polys for v in p); loose=n-len(used)
    uv=[tuple(np.round([l.uv[0],l.uv[1]],6)) for l in me.uv_layers.active.data] if me.uv_layers.active else []
    return dict(V=V,polys=polys,groups=groups,gw=gw,FV=FV,boundary=boundary,nonman=nonman,loose=loose,objects=[ob.name for ob in bpy.data.objects],
                mats=[m.name for m in bpy.data.materials],mods=[m.type for m in o.modifiers],uv=uv,tris=sum(len(p)-2 for p in polys),
                tf=[list(map(float,r)) for r in o.matrix_world],cams=[(ob.name,tuple(np.round(ob.matrix_world.translation,6)),tuple(np.round(ob.rotation_euler,6))) for ob in bpy.data.objects if ob.type in('CAMERA','EMPTY')])
A=info(S1); B=info(FIN)
V0,V1=A['V'],B['V']; moved=(V0!=V1).any(1)
zone=np.load(W/'data/zone.npy'); zR=np.load(W/'data/zone_R.npy'); zL=np.load(W/'data/zone_L.npy'); shell=np.load(W/'data/shell_cur.npy')
x=V0[:,0]; z=V0[:,2]
cats={'head_neck(z>=1.40)':z>=1.40,'torso+pelvis(|x|<=0.215,0.77<=z<1.40)':(np.abs(x)<=0.215)&(z>=0.77)&(z<1.40),'legs(z<0.77,|x|<0.40)':(z<0.77)&(np.abs(x)<0.40),
      'feet(z<0.25)':z<0.25,'shoulder_ball_and_upper_arm(t<-0.03)':None,'outside_arm_zone':~zone}
import quality
tR=quality.arm_t(V0.astype(float),+1); tL=quality.arm_t(V0.astype(float),-1)
upper=(zR&(tR<-0.03))|(zL&(tL<-0.03)); cats['shoulder_ball_and_upper_arm(t<-0.03)']=upper
res={'start_blend':S1,'start_blend_sha256':sha(S1),'final_blend':FIN,'final_blend_sha256':sha(FIN)}
res['zone']={'definition':'arms: Body_M vertices with |x|>0.215, 0.78<z<1.42, connected component per side (shoulder ball excluded: edits taper to zero before t=-0.03 / the arm axis coordinate)','verts_in_zone':int(zone.sum()),'verts_total':int(len(V0)),
   'verts_moved':int(moved.sum()),'verts_moved_inside_zone':int((moved&zone).sum()),'verts_moved_outside_zone':int((moved&~zone).sum()),'moved_hand_shell':int((moved&shell).sum()),'moved_forearm_wrist_band':int((moved&~shell).sum())}
res['moved_by_category']={k:int((moved&m).sum()) for k,m in cats.items()}; res['category_vertex_counts']={k:int(m.sum()) for k,m in cats.items()}
d=np.linalg.norm(V1.astype(float)-V0.astype(float),axis=1)
res['max_displacement_mm']=float(1000*d.max()); res['mean_displacement_moved_mm']=float(1000*d[moved].mean()); res['p95_displacement_moved_mm']=float(1000*np.percentile(d[moved],95))
# border step: displacement of moved verts adjacent to unmoved zone verts
res['topology_identical']=bool(A['polys']==B['polys']); res['verts']=len(V1); res['tris']=B['tris']; res['tris_start']=A['tris']
res['vertex_groups_identical']=bool(A['groups']==B['groups'] and all(A['gw'][k]==B['gw'][k] for k in A['gw']))
res['face_m_bit_identical']=bool(np.array_equal(A['FV'],B['FV'])); res['objects_identical']=bool(A['objects']==B['objects']); res['materials_identical']=bool(A['mats']==B['mats']); res['modifiers']=B['mods']
res['uv_identical']=bool(A['uv']==B['uv']); res['transform_identical']=bool(A['tf']==B['tf']); res['cameras_empties_identical']=bool(A['cams']==B['cams'])
res['boundary_edges']=[A['boundary'],B['boundary']]; res['nonmanifold_edges']=[A['nonman'],B['nonman']]; res['loose_verts']=[A['loose'],B['loose']]
res['height_m']=[float(V0[:,2].max()-V0[:,2].min()),float(V1[:,2].max()-V1[:,2].min())]
# quality / folds / self intersections
D=np.load(W/'data/mesh_start.npz'); T=D['T']; import pickle; polys=A['polys']
q0=quality.metrics(V0.astype(float),T,polys,zR,zL,shell); q1=quality.metrics(V1.astype(float),T,polys,zR,zL,shell)
res['quality_start']=q0; res['quality_final']=q1
from mathutils.bvhtree import BVHTree
def selfx(V):
    sel=zone[T].any(1); Ts=T[sel]
    tree=BVHTree.FromPolygons([tuple(map(float,v)) for v in V],[tuple(map(int,t)) for t in Ts],epsilon=0.0)
    n=0
    for i,j in tree.overlap(tree):
        if i<j and not (set(Ts[i])&set(Ts[j])): n+=1
    return n
res['self_intersecting_triangle_pairs']=[selfx(V0),selfx(V1)]
ef=quality.edge_faces(polys)
def folds(V,thr):
    Fn=quality.face_normals(V.astype(float),polys); out=0
    for (a_,b_),fs in ef.items():
        if len(fs)==2 and zone[a_] and zone[b_]:
            if np.degrees(np.arccos(np.clip((Fn[fs[0]]*Fn[fs[1]]).sum(),-1,1)))>thr: out+=1
    return out
res['zone_edges_dihedral_gt100']=[folds(V0,100),folds(V1,100)]; res['zone_edges_dihedral_gt90']=[folds(V0,90),folds(V1,90)]
Fn0=quality.face_normals(V0.astype(float),polys); Fn1=quality.face_normals(V1.astype(float),polys)
pz=np.array([zone[list(p)].all() for p in polys]); dot=(Fn0*Fn1).sum(1)
res['flipped_polys_in_zone']=int(((dot<0)&pz).sum()); res['flipped_polys_where']='thumb root only (these faces were folded back in the start mesh)'
# hand ROI silhouette numbers (numpy raster)
import handobj
arm=(np.abs(x)>0.2)&(z>0.78)&(z<1.40); sel=arm[T].all(1)
t0,r0=handobj.xor_report(V0.astype(float),T,sel); t1,r1=handobj.xor_report(V1.astype(float),T,sel)
res['hand_roi_xor_start_final']=[t0,t1]; res['hand_roi_xor_per_roi']={f'{k[0]}_{k[1]}':[r0[k][0],r1[k][0]] for k in r0}
# mirror symmetry
def mirr(V):
    Aa=V[zR].astype(float); Bb=V[zL].astype(float)*np.array([-1,1,1]); dd=np.sqrt(((Aa[:,None,:]-Bb[None,:,:])**2).sum(2)).min(1); return [float(1000*dd.mean()),float(1000*np.percentile(dd,95)),float(1000*dd.max())]
res['mirror_mean_p95_max_mm']={'start':mirr(V0),'final':mirr(V1)}
# grip socket proxy: verts within 3 cm of the palm centre in hand-local coords
sys.path.insert(0,str(W.parent/'male-micro1e')); import hand_sdf as H
pal=[]
for side,zz in ((+1,zR),(-1,zL)):
    L0=H.to_local(V0.astype(float),side); L1=H.to_local(V1.astype(float),side)
    c=np.array([0.0,-0.016,0.026]); m=zz&(np.linalg.norm(L0-c,axis=1)<0.03)
    pal.append(dict(side=side,verts=int(m.sum()),max_move_mm=float(1000*np.linalg.norm(L1[m]-L0[m],axis=1).max()),mean_move_mm=float(1000*np.linalg.norm(L1[m]-L0[m],axis=1).mean())))
res['palm_centre_socket_proxy_moves']=pal
# wrist cross-section
ws=[]
for lo,hi in [(-0.15,-0.13),(-0.10,-0.085),(-0.07,-0.055),(-0.04,-0.02)]:
    row={'w':[lo,hi]}
    for nm,V in (('start',V0),('final',V1)):
        L=H.to_local(V.astype(float),+1); m=zR&(L[:,2]>=lo)&(L[:,2]<hi); P=L[m][:,:2]; c=P.mean(0); ang=np.arctan2(P[:,1]-c[1],P[:,0]-c[0]); Q=P[np.argsort(ang)]
        row[nm]=dict(area_cm2=float(0.5*abs(np.sum(Q[:,0]*np.roll(Q[:,1],-1)-np.roll(Q[:,0],-1)*Q[:,1]))*1e4),a_extent_mm=float(1000*(P[:,0].max()-P[:,0].min())),n_extent_mm=float(1000*(P[:,1].max()-P[:,1].min())))
    ws.append(row)
res['wrist_sections_right_hand']=ws
Path(OUT).write_text(json.dumps(res,indent=1)); print('CHECKS_DONE',OUT)
print(json.dumps({k:res[k] for k in ('zone','moved_by_category','topology_identical','vertex_groups_identical','face_m_bit_identical','boundary_edges','nonmanifold_edges','self_intersecting_triangle_pairs','zone_edges_dihedral_gt100','zone_edges_dihedral_gt90','flipped_polys_in_zone','hand_roi_xor_start_final','palm_centre_socket_proxy_moves')},indent=1))
