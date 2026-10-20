import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f1-head')
import numpy as np, fl, loftf
L=loftf.Loft()
i=np.argmax(L.a); print('max a',L.a[i]*1000,'at z',L.zk[i])
V=np.load(fl.W/'data/prev_loft.npz')['V']
j=np.argmax(np.abs(V[:,0])); print(V[j], L.at(np.array([V[j,2]]))['a']*1000)
