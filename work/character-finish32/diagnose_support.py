exec(open('work/character-finish32/solve_support.py').read().split("print('SUPPORT POSES'")[0])
for label,M,support,norm in poses:
 q=np.einsum('nij,nj->ni',M[:,:3,:3],P)+M[:,:3,3];sample=np.concatenate([q[ids],q[FT].mean(1)]);signed=((sample-support)*norm).sum(1);worst=np.argmin(signed)
 if signed[worst]<-.035:print(label,'depth',signed[worst],'rest',samples[worst],'support_rest',(BP[supportIds[worst]]*bary[worst,:,None]).sum(0),'restBodyDistance',np.linalg.norm(samples[worst]-(BP[supportIds[worst]]*bary[worst,:,None]).sum(0)),'posedDistance',np.linalg.norm(sample[worst]-support[worst]),flush=True)
