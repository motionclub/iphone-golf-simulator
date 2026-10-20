import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f1-head')
import numpy as np, fl, loftf
rows,hw,yf,yb=loftf.plate_rows()
for r in range(66,253,6):
    i=r-66; print(r, round(hw[i]*1000,1) if not np.isnan(hw[i]) else None, round(yf[i]*1000,1) if not np.isnan(yf[i]) else None, round(yb[i]*1000,1) if not np.isnan(yb[i]) else None)
L=loftf.Loft()
for z in np.arange(1.43,1.71,0.02):
    p=L.at(np.array([z])); print(round(z,3), {k:round(float(v[0])*1000,1) for k,v in p.items() if k in('a','yf','yb','yw')}, round(float(p['nf'][0]),2))
