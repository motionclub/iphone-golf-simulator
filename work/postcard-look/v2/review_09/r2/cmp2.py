import numpy as np, sys
b=np.load(sys.argv[1],allow_pickle=True).item(); s=np.load(sys.argv[2],allow_pickle=True).item()
print('names equal',sorted(b)==sorted(s), len(b))
mx=0;nv=0;bad=0;upbad=0;nup=0
for k in b:
    if k not in s: print('missing',k); continue
    vb,vs=b[k]['v'],s[k]['v']
    if vb.shape!=vs.shape: print('shape',k); bad+=1; continue
    mx=max(mx,abs(vb-vs).max()); nv+=len(vb)
    if b[k]['polys']!=s[k]['polys']: print('polys differ',k); bad+=1
    nb=np.array(b[k]['nup']); ns=np.array(s[k]['nup'])
    up=nb[:,2]>0.3; nup+=up.sum()
    if abs(nb-ns).max()>1e-6: upbad+=1
    # up-facing face centroid height compare
    cb=np.array([vb[p].mean(0) for p in b[k]['polys']]); cs=np.array([vs[p].mean(0) for p in s[k]['polys']])
    if abs(cb-cs).max()>0: print('centroid diff',k)
print('verts',nv,'max delta',mx,'bad',bad,'normal mismatch objs',upbad,'upfaces',nup)
