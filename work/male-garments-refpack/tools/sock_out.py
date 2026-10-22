import numpy as np, sys
def check(S, P, T, zlab, up=2):
    c=P[T].mean(1); n=np.cross(P[T[:,1]]-P[T[:,0]],P[T[:,2]]-P[T[:,0]]); n/=np.linalg.norm(n,axis=1,keepdims=True)+1e-12
    res=[]
    for i in range(0,len(S),400):
        d=np.linalg.norm(S[i:i+400,None,:]-c[None],axis=2); j=d.argmin(1); res.append(np.stack([d.min(1),((S[i:i+400]-c[j])*n[j]).sum(1),S[i:i+400,up]],1))
    o=np.concatenate(res); top=P[:,up].max()
    low=o[:,2]<top-.04            # well below the shoe's top: must be inside
    bad=low&(o[:,1]>.0005)&(o[:,0]<.02)
    print(zlab,'low sock verts',low.sum(),'outside the shoe:',bad.sum(),'max out %.1f mm'%(1000*o[bad,1].max() if bad.any() else 0))
    return bad
if __name__=='__main__':
    for sd in 'LR':
        s=np.load(f'out/MatchHero_Male/unity/Kit_Sock_{sd}_final.npz'); h=np.load(f'out/MatchHero_Male/unity/Kit_Shoe_{sd}_final.npz')
        check(s['pos'],h['pos'],h['tri'],'export '+sd,2)
        R='../clothing-v2/pipeline/runs/MG_MT/MatchHero_Male/'
        s=np.load(R+f'Kit_Sock_{sd}.npz'); h=np.load(R+f'Kit_Shoe_{sd}.npz'); check(s['P'],h['P'],h['tri'],'fitted '+sd,1)
