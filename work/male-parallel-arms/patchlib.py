"""Index mapping between the Micro1f vertex space (24,652 verts: pipeline output) and the current blend (30,296 verts, Micro1h/i head densification)."""
import numpy as np, sys
from pathlib import Path
W=Path(__file__).resolve().parent
E1=W.parent/'male-micro1e'; F1=W.parent/'male-micro1f'
def key(a): return np.ascontiguousarray(a.astype(np.float32)).view(np.dtype((np.void,12))).ravel()
def build_map(cur,mf,zmax=1.40):
    """returns idx[i] = index in cur of micro1f vertex i (or -1) for micro1f verts with z<zmax"""
    kc=key(cur); order=np.argsort(kc); ks=kc[order]
    km=key(mf)
    pos=np.searchsorted(ks,km); pos=np.clip(pos,0,len(ks)-1)
    hit=(ks[pos]==km)
    idx=np.where(hit,order[pos],-1)
    idx[mf[:,2]>=zmax]=-1
    # uniqueness check on cur keys
    dup=len(ks)-len(np.unique(ks))
    return idx,dup
def shell_mask_mf():
    """hand shell in micro1f index space (freed slots of both hands + appended vertices)"""
    sys.path.insert(0,str(E1))
    import hand_topo as T
    BASE=np.load(E1/'baseline/mesh.npz')['co'].astype(float); F0=np.load(E1/'faces.npy')
    n=24652; sh=np.zeros(n,bool)
    for s in (+1,-1): sh[:len(BASE)]|=T.extract_cut(BASE,F0,s,-0.055)['Hmask']
    sh[len(BASE):]=True
    return sh
if __name__=='__main__':
    D=np.load(W/'data/mesh_start.npz'); cur=D['V']
    mf=np.load(F1/'final/k5_verts.npy')
    idx,dup=build_map(cur,mf)
    low=mf[:,2]<1.40
    print('mf verts',len(mf),'below z1.40',low.sum(),'matched',(idx>=0).sum(),'dup coords in cur',dup)
    assert (idx[low]>=0).all()
    assert len(np.unique(idx[low]))==low.sum()
    sh=shell_mask_mf(); print('shell',sh.sum(),'in map',(idx[sh]>=0).all())
    np.save(W/'data/map_mf2cur.npy',idx); np.save(W/'data/shell_mf.npy',sh)
    # also reverse: which cur verts are not covered (head) and hand shell in cur indices
    covered=np.zeros(len(cur),bool); covered[idx[idx>=0]]=True
    print('cur verts not in micro1f map',(~covered).sum(),'z range',cur[~covered,2].min(),cur[~covered,2].max())
    shell_cur=np.zeros(len(cur),bool); shell_cur[idx[sh]]=True; np.save(W/'data/shell_cur.npy',shell_cur)
    print('shell_cur',shell_cur.sum(),'x range',cur[shell_cur,0].min(),cur[shell_cur,0].max(),'z',cur[shell_cur,2].min(),cur[shell_cur,2].max())
