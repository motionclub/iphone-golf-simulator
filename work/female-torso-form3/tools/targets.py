"""Plate-derived side-profile targets (m), anchored on knee-center (X0=791.5 left panel / 1095.0 right panel).
Front/back y at height z. Averaged left+right profile panels (female_multiangle_body.jpg), gradient-edge extraction."""
import numpy as np
def sm(z,v,sigma=0.009,step=0.002):
    zg=np.arange(z[0],z[-1]+1e-9,step); vg=np.interp(zg,z,v)
    k=np.arange(-int(4*sigma/step),int(4*sigma/step)+1)*step; ker=np.exp(-0.5*(k/sigma)**2); ker/=ker.sum()
    pad=len(k)//2; vp=np.pad(vg,(pad,pad),mode='edge'); out=np.convolve(vp,ker,mode='valid')
    return zg,out
# (z, front y (negative = forward), back y)
FRONT=[(0.70,-0.1015),(0.735,-0.1075),(0.77,-0.1075),(0.806,-0.1075),(0.842,-0.1075),(0.877,-0.1100),(0.912,-0.1140),
       (0.948,-0.118),(0.983,-0.1194),(1.02,-0.1194),(1.054,-0.1194),(1.09,-0.1194),(1.125,-0.122),(1.161,-0.1255),
       (1.196,-0.131),(1.231,-0.131),(1.267,-0.1135),(1.302,-0.084),(1.338,-0.0605),(1.38,-0.040)]
BACK=[(0.70,0.080),(0.735,0.0813),(0.77,0.0825),(0.80,0.096),(0.83,0.111),(0.86,0.1175),(0.89,0.1160),(0.92,0.1085),(0.94,0.1015),
      (0.96,0.0895),(0.975,0.0770),(0.99,0.0685),(1.02,0.0675),(1.05,0.0722),(1.08,0.0745),(1.12,0.0755),(1.16,0.0785),(1.20,0.083),(1.23,0.090),(1.267,0.0931),
      (1.30,0.0931),(1.338,0.0931),(1.38,0.078)]
def curves():
    fz,f=sm(np.array([a for a,b in FRONT]),np.array([b for a,b in FRONT]))
    bz,b=sm(np.array([a for a,b in BACK]),np.array([b for a,b in BACK]))
    return (fz,f),(bz,b)
if __name__=='__main__':
    (fz,f),(bz,b)=curves()
    for z in np.arange(0.80,1.38,0.04): print(f"{z:.2f} front {np.interp(z,fz,f):+.4f} back {np.interp(z,bz,b):+.4f}")
