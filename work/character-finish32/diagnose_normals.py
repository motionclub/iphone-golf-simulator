exec(open('work/character-finish32/diagnose_refined.py').read().split('for f in [')[0])
BN=np.array(b['normals']).reshape(-1,3);bn=BN[BT].mean(1);fn=np.cross(BP[BT[:,1]]-BP[BT[:,0]],BP[BT[:,2]]-BP[BT[:,0]]);dot=(fn*bn).sum(1);arm=(abs(BP[BT].mean(1)[:,0])>.18)&(BP[BT].mean(1)[:,2]>1.16);print('all winding',np.sum(dot<0),len(dot),'arm',np.sum(dot[arm]<0),sum(arm))
for v in [8134,18642,16036,7259,15287]:
 p=P[v];hit,n,fi,dist=rest.find_nearest(Vector(p));sm=BN[BT[fi]].mean(0);print(v,'point',p,'nearest',hit,'tri normal',n,'smoothnormal',sm,'windingdot',np.dot(n,sm),'signedTriangle',np.dot(p-hit,n),'signedSmooth',np.dot(p-hit,sm))
