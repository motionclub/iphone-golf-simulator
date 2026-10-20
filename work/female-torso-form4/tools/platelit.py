"""plate-lit renders.  python3 tools/platelit.py fit              -> fits SH2 lighting per view on non-edited regions (data/sh_front.npy, sh_back.npy)
                      python3 tools/platelit.py render <coords.npy> <tag> -> proof/scratch/pl_<tag>_{front,back}.png (1280x720, plate-registered)"""
import sys, subprocess
sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-torso-form4/tools')
from fplate import *
B='/Applications/Blender.app/Contents/MacOS/Blender'
def fit():
    M=Mesh(); N=M.normals(); co=M.co
    legs=(co[:,2]<0.74)&(co[:,2]>0.14)&~M.T
    arms=(M.arm)&(co[:,2]>0.93)&(co[:,2]<1.30)&(np.abs(co[:,0])>0.15)&~M.T
    fitmask=legs|arms
    out={}
    for name in ('front','back'):
        vw=View(name); c,r2,nv=fit_sh(vw,co,N,fitmask,sigma=2.5,basis=sh2c_full)
        print(name,'R2',round(r2,3),'n',nv,'coef',np.round(c,1)); np.save(W/f'data/sh_{name}.npy',c)
def lum_arrays(co,tri):
    N=vertex_normals(co,tri)
    L={}
    for name in ('front','back'):
        vw=View(name); c=np.load(W/f'data/sh_{name}.npy'); L[name]=np.clip(sh2c_full(N,vw)@c,0,255)
    return L
def render(npy,tag,start=str(W/'START_torso_candidate.blend'),views='front,back'):
    co=np.load(npy) if isinstance(npy,str) else npy
    tri=np.load(W/'data/orig.npz')['tri']
    L=lum_arrays(co,tri); np.savez(W/f'proof/scratch/pl_{tag}_lum.npz',**L)
    cp=W/f'proof/scratch/pl_{tag}_co.npy'; np.save(cp,co)
    r=subprocess.run([B,'-b',start,'--python',str(W/'tools/vcrender_f.py'),'--',str(cp),str(W/f'proof/scratch/pl_{tag}_lum.npz'),str(W/f'proof/scratch/pl_{tag}'),views],capture_output=True,text=True)
    if 'VCRENDER_DONE' not in r.stdout: print(r.stdout[-600:],r.stderr[-600:]); raise SystemExit('render failed')
if __name__=='__main__':
    if sys.argv[1]=='fit': fit()
    else: render(sys.argv[2],sys.argv[3])
