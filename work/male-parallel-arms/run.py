"""Build a hand variant, patch it into the current mesh, report metrics, optionally render proofs.
usage: py.sh run.py <tag> '<json overrides>' [render]"""
import sys, json, subprocess, os
from pathlib import Path
import numpy as np
W=Path(__file__).resolve().parent
sys.path[:0]=[str(W/'hand'),str(W),str(W.parent/'male-micro1e')]
import hand_build as HB0, hand_build2 as HB2, assemble2 as A
from zonelib import load
import handobj, quality
P0=dict(HB2.P); Q0=dict(HB0.P)
V0,T0,polys=load()
IDX=np.load(W/'data/map_mf2cur.npy'); SH=np.load(W/'data/shell_mf.npy')
ZR=np.load(W/'data/zone_R.npy'); ZL=np.load(W/'data/zone_L.npy'); SHC=np.load(W/'data/shell_cur.npy')
BASEP=json.load(open(W/'hand/params_m1f_final.json'))
ARM=(np.abs(V0[:,0])>0.2)&(V0[:,2]>0.78)&(V0[:,2]<1.40); SEL=ARM[T0].all(1)
SHM=SH  # shell mask in micro1f space
MF0=np.load(W.parent/'male-micro1f/final/k5_verts.npy')
ZONE_MF=np.zeros(len(MF0),bool)
_ok=IDX>=0
ZONE_MF[_ok]=(ZR|ZL)[IDX[_ok]]
def build(over):
    HB2.P.clear(); HB2.P.update(P0); HB0.P.clear(); HB0.P.update(Q0)
    p=dict(BASEP); p.update(over)
    v,f,info=A.assemble(p,HB2)
    v=polish(v,f,over)
    return v
def polish(v,faces,over):
    """extra localized Taubin passes on the freshly built hand (micro1f space). keys: pol_thumb=[radius,iters], pol_web=[iters] ..."""
    import hand_sdf as H
    v=v.copy()
    E=None
    def edges():
        nonlocal E
        if E is None:
            S=set()
            for f in faces:
                for k in range(len(f)):
                    a,b=f[k],f[(k+1)%len(f)]; S.add((min(a,b),max(a,b)))
            E=np.array(sorted(S))
        return E
    from zonelib import taubin
    if 'pol_arm' in over:
        it=int(over['pol_arm'][0]); lam=over['pol_arm'][1] if len(over['pol_arm'])>1 else 0.5; mu=over['pol_arm'][2] if len(over['pol_arm'])>2 else -0.53; t0=over['pol_arm'][3] if len(over['pol_arm'])>3 else -0.02; rmp=over['pol_arm'][4] if len(over['pol_arm'])>4 else 0.05
        w=np.zeros(len(v))
        sm=lambda x: (lambda y: y*y*(3-2*y))(np.clip(x,0,1))
        for side in (+1,-1):
            Lc=H.to_local(v,side); lw=Lc[:,2]
            t=quality.arm_t(v,side)
            zone=ZONE_MF&(side*v[:,0]>0)
            ww=np.where(SHM,1-sm((lw-0.0)/0.025),sm((t-t0)/rmp))
            w[zone]=np.maximum(w[zone],ww[zone])
        v=taubin(v,edges(),w,it,lam,mu)
    if 'pol_roles' in over:
        import re, roles as RL
        RM=RL.roles(BASEP)       # (side, mf index) -> role string (topology only, independent of the parameters)
        spec,it=over['pol_roles']
        w=np.zeros(len(v))
        for (side,fi),r in RM.items():
            for pat,wt in spec:
                if re.fullmatch(pat,r): w[fi]=max(w[fi],wt)
        v=taubin(v,edges(),w,int(it))
    if 'pol_thumb' in over:
        R_,it=over['pol_thumb'][:2]; cen=np.array(over.get('pol_thumb_c',[0.0433,-0.0067,0.0369]))
        w=np.zeros(len(v))
        for side in (+1,-1):
            Lc=H.to_local(v,side); d=np.linalg.norm(Lc-cen,axis=1)
            m=(side*v[:,0]>0.30)&(v[:,2]<1.10)&SH
            t=np.clip(1-d/R_,0,1); t=t*t*(3-2*t)
            w[m]=np.maximum(w[m],t[m])
        v=taubin(v,edges(),w,int(it))
    return v
def patch(newmf):
    moved=np.abs(newmf.astype(np.float32)-MF0.astype(np.float32)).max(1)>0
    assert (IDX[moved]>=0).all(), 'moved vertex outside mapped area'
    V=V0.copy().astype(np.float64); V[IDX[moved]]=newmf[moved]; V=V.astype(np.float32)
    zone=ZR|ZL; mv=np.nonzero((V!=V0).any(1))[0]
    assert zone[mv].all(), 'moved vertex outside arm zone: %d'%(~zone[mv]).sum()
    return V
_PL={}
def fullsil(V):
    import lockcam as L
    from PIL import Image
    out={}
    for v in ('bald_front','bald_back'):
        if v not in _PL: _PL[v]=np.array(Image.open(W.parent/'male-silhouette'/f'{v}_target.png').convert('L'))>127
        m=L.raster(V,T0,v,ss=2); p=_PL[v]; out[v]=int((m^p).sum())
    return out
def evaluate(V,verbose=False):
    tot,res=handobj.xor_report(V,T0,SEL,verbose)
    q=quality.metrics(V,T0,polys,ZR,ZL,SHC)
    return tot,res,q
def folds(V,thr=100):
    ef=quality.edge_faces(polys); Fn=quality.face_normals(V,polys); out=[]
    zz=ZR|ZL
    for (a,b),fs in ef.items():
        if len(fs)==2 and zz[a] and zz[b]:
            ang=np.degrees(np.arccos(np.clip((Fn[fs[0]]*Fn[fs[1]]).sum(),-1,1)))
            if ang>thr: out.append((ang,a,b))
    return out
def render(tag,coords_path,extra_views=None):
    env=dict(os.environ); env['COORDS']=str(coords_path); env['CLIP']='0.15'
    B='/Applications/Blender.app/Contents/MacOS/Blender'
    T="0.60,-0.105,0.89"
    views=["back:%s:0.768,0,0.642:0.30:55:-40"%T,"palm3qb:%s:-0.55,0.7,-0.45:0.30:55:-40"%T,"thumbside:%s:-0.07,-1,0.09:0.30:55:-40"%T,"back3q:%s:0.55,-0.7,0.45:0.30:55:-40"%T,
           "palmfront:%s:-0.6,-0.8,-0.3:0.30:60:-20"%T,"pinkyside:%s:0.07,1,-0.09:0.30:55:-40"%T,
           "thumbroot_a:0.5852,-0.1434,0.8939:-0.768,-0.1,-0.642:0.10:55:-40","thumbroot_b:0.5852,-0.1434,0.8939:-0.07,-1,0.09:0.10:55:-40"]
    out=W/f'proof/it/{tag}'; out.mkdir(parents=True,exist_ok=True)
    subprocess.run([B,'-b',str(W/'baseline/HeroBase_Male_Silhouette.blend'),'--python',str(W/'closeup.py'),'--',str(out)]+views,env=env,capture_output=True)
    from PIL import Image
    names=[v.split(':')[0] for v in views]
    S=Image.new('RGB',(4*450,2*450))
    for i,n in enumerate(names):
        S.paste(Image.open(out/f'{n}.png').convert('RGB').resize((450,450)),((i%4)*450,(i//4)*450))
    S.save(W/f'proof/it/{tag}_sheet.png'); return W/f'proof/it/{tag}_sheet.png'
if __name__=='__main__':
    tag=sys.argv[1]; over=json.loads(sys.argv[2]) if len(sys.argv)>2 else {}
    mf=build(over); V=patch(mf)
    (W/'data/it').mkdir(exist_ok=True); np.save(W/f'data/it/{tag}_cur.npy',V)
    tot,res,q=evaluate(V)
    fo=folds(V); fs=fullsil(V); fs0=fullsil(V0)
    print(json.dumps(dict(tag=tag,roi_xor_total=tot,per_roi={f'{k[0]}_{k[1]}':v[0] for k,v in res.items()},
          wristhand_hf_rms=[q['R_wristhand_hf_rms_mm'],q['L_wristhand_hf_rms_mm']],dih30=q['dihedral_gt30'],dih45=q['dihedral_gt45'],dih60=q['dihedral_gt60'],dihmax=q['dihedral_max'],folds_gt100=len(fo),fullbody_xor=fs,fullbody_xor_start=fs0),indent=None))
    if len(sys.argv)>3 and sys.argv[3]=='render': print(render(tag,W/f'data/it/{tag}_cur.npy'))
