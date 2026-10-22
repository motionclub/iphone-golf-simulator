import numpy as np, collections
L=lambda n: np.load(f'data/{n}.npz',allow_pickle=True)
FIN,B,F3,A=L('final_body'),L('base_body'),L('f3_body'),L('artdir_body')
D=np.load('export/full_merge_delta.npz'); nkeep=13224; NLOW=12421
VF=FIN['V']; VB=B['V']; V3=F3['V']
# (a) exact-position matching using void views (robust hashing)
def keyarr(V): 
    V=np.ascontiguousarray(V.astype(np.float32)); return V.view([('x','f4'),('y','f4'),('z','f4')]).ravel()
k3=keyarr(V3[:NLOW]); kf=keyarr(VF[:nkeep])
s3=set(k3.tolist()); m=np.array([t in s3 for t in kf.tolist()])
print('(a) final retained verts at an F3-lower position:', m.sum(), 'of', nkeep, ' not:', (~m).sum())
# older approach used tuple(np.float32 row)
kmap={tuple(p):i for i,p in enumerate(V3[:NLOW])}
m2=np.array([tuple(VF[i]) in kmap for i in range(nkeep)]); print('   tuple approach matched', m2.sum(), '(this was the buggy count if small)')
print('   dtype F3 V', V3.dtype, 'final V', VF.dtype)
# (c) loose vertices
def used(d,n):
    u=np.zeros(n,bool); u[d['corner_verts']]=True; return u
uf=used(FIN,len(VF)); ub=used(B,len(VB))
print('(c) loose verts: final', (~uf).sum(), ' base', (~ub).sum())
lf=np.nonzero(~uf)[0]; print('   final loose idx range', lf.min(), lf.max(), ' < nkeep:', (lf<nkeep).sum())
bi=np.nonzero(~ub)[0]; print('   base loose idx range', bi.min(), bi.max(), ' z range', VB[bi,2].min(), VB[bi,2].max(), ' x range', VB[bi,0].min(), VB[bi,0].max())
# are base loose verts in the hand slots?
hd=np.load('start/hands_delta.npz'); slots=set(hd['slots'].tolist()); print('   base loose verts that are reused hand slots:', sum(1 for i in bi if i in slots), ' in appended range:', int((bi>=22419).sum()))
# final loose = base loose retained?
keep_v=np.ones(len(VB),bool); keep_v[D['old_head_idx']]=False
print('   base loose verts retained in final:', int(keep_v[bi].sum()), ' base loose verts in old head (removed):', int((~keep_v[bi]).sum()))
# ArtDir loose verts?
ua=used(A,len(A['V'])); print('   ArtDir loose verts:', (~ua).sum())
