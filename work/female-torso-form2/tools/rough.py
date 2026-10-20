"""surface roughness maps: umbrella-Laplacian magnitude (mm) per zone vertex, new vs original (denoised PS = the smooth reference)"""
import sys; sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-torso-form2/tools')
from torso2 import *
from fieldmap import plot
from PIL import Image
def lap_mag(co):
    s=np.zeros_like(co); np.add.at(s,EA,co[EB]); np.add.at(s,EB,co[EA])
    m=s/np.maximum(DEG,1)[:,None]
    return np.linalg.norm(m-co,axis=1)
def lap_vec(co):
    s=np.zeros_like(co); np.add.at(s,EA,co[EB]); np.add.at(s,EB,co[EA])
    return s/np.maximum(DEG,1)[:,None]-co
def second_diff_noise(co):
    """roughness = |L(co)| minus smooth part: use L of the Laplacian (bi-Laplacian) magnitude: sensitive to bumps/jitter, insensitive to curvature"""
    L=lap_vec(co); s=np.zeros_like(L); np.add.at(s,EA,L[EB]); np.add.at(s,EB,L[EA])
    return np.linalg.norm(s/np.maximum(DEG,1)[:,None]-L,axis=1)
if __name__=='__main__':
    new=np.load(WD/sys.argv[1]); 
    ref_o=CO0; ref_c=np.load(WD/'data/cand.npz')['co'].astype(np.float64)
    bn=second_diff_noise(new); bo=second_diff_noise(ref_o); bc=second_diff_noise(ref_c)
    inner=T&(D_ARM>0.012)&(D_LEG>0.012)&(D_TOP>0.012)
    print('bi-Laplacian noise (mm) on zone interior: orig mean %.3f p95 %.3f max %.3f | chat7 mean %.3f p95 %.3f max %.3f | new mean %.3f p95 %.3f max %.3f'%tuple(np.r_[bo[inner].mean()*1000,np.percentile(bo[inner],95)*1000,bo[inner].max()*1000,bc[inner].mean()*1000,np.percentile(bc[inner],95)*1000,bc[inner].max()*1000,bn[inner].mean()*1000,np.percentile(bn[inner],95)*1000,bn[inner].max()*1000]))
    zz,xx=new[:,2],new[:,0]
    fr=new[:,1]<0
    a=plot(xx,zz,bn,T&fr,(-0.19,0.19),(0.80,1.37),scale=1500,vr=(0,0.006),title='FRONT bi-Laplacian noise (new)')
    b=plot(xx,zz,bn,T&~fr,(-0.19,0.19),(0.80,1.37),scale=1500,vr=(0,0.006),title='BACK bi-Laplacian noise (new)')
    c=plot(xx,zz,bo,T&fr,(-0.19,0.19),(0.80,1.37),scale=1500,vr=(0,0.006),title='FRONT noise (original)')
    Wd=a.width
    S=Image.new('RGB',(Wd*3,a.height)); S.paste(c,(0,0)); S.paste(a,(Wd,0)); S.paste(b,(2*Wd,0)); S.save(WD/'proof/scratch/rough_map.png'); print(S.size)
