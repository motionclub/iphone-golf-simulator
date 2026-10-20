import numpy as np, sys
sys.path.insert(0,'.')
from common import V0
A = np.load('data/preF3_mesh.npz')['co']      # pre-FORM3 (torso FORM2)  == legs/feet FORM2 state
d = V0 - A; m = np.linalg.norm(d,axis=1) > 1e-7
print('moved by FORM3:', int(m.sum()), 'z range', V0[m,2].min().round(3), V0[m,2].max().round(3))
# displacement profile vs z for rear vertices (y>0.0) at different |x|
X,Y,Z = V0[:,0],V0[:,1],V0[:,2]
for u0,u1 in ((0,0.03),(0.03,0.06),(0.06,0.09),(0.09,0.12),(0.12,0.16)):
    print(f'|x| in [{u0},{u1}] rear dy by z (mm):')
    row=[]
    for z in np.arange(0.76,0.90,0.01):
        sel=(np.abs(X)>=u0)&(np.abs(X)<u1)&(np.abs(Z-z)<0.005)&(Y>0.02)
        row.append(f'{z:.2f}:{(d[sel,1].mean()*1000 if sel.any() else float("nan")):6.1f}')
    print('  '+' '.join(row))
print('FRONT dy (y<-0.05):')
for u0,u1 in ((0,0.03),(0.03,0.06),(0.06,0.09),(0.09,0.12),(0.12,0.16)):
    row=[]
    for z in np.arange(0.76,0.90,0.01):
        sel=(np.abs(X)>=u0)&(np.abs(X)<u1)&(np.abs(Z-z)<0.005)&(Y<-0.05)
        row.append(f'{z:.2f}:{(d[sel,1].mean()*1000 if sel.any() else float("nan")):6.1f}')
    print(f' u[{u0},{u1}] '+' '.join(row))
