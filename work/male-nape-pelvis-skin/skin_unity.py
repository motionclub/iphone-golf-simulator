"""Build unity_cases.json from a python list, run the Unity proof harness, measure skinish S/V/H per case (head region).
usage: python3 skin_unity.py <cases.py>   (cases.py defines CASES=[{...}], VIEWS=[...])"""
import sys, json, subprocess, glob, os, runpy
import numpy as np
from PIL import Image
R = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'; S = R + '/work/male-nape-pelvis-skin/skin'
UNITY = '/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity'
def hsv(a):
    mx=a.max(-1); mn=a.min(-1); d=mx-mn; s=np.where(mx>0,d/np.maximum(mx,1e-9),0)
    r,g,b=a[...,0],a[...,1],a[...,2]; h=np.zeros_like(mx); m=d>1e-9
    rc=(mx==r)&m; gc=(mx==g)&m&~rc; bc=m&~rc&~gc
    h[rc]=((g-b)[rc]/d[rc])%6; h[gc]=((b-r)[gc]/d[gc])+2; h[bc]=((r-g)[bc]/d[bc])+4
    return h*60,s,mx
def measure(files, crop_rows=600):
    P=[]
    for f in files:
        a=np.asarray(Image.open(f).convert('RGB')).astype(float)[:crop_rows]/255; H,Sa,V=hsv(a)
        m=(H>8)&(H<45)&(Sa>0.2)&(V>0.3); P.append(np.stack([Sa[m],V[m],H[m]],1))
    p=np.concatenate(P) if P else np.zeros((0,3)); return p
def run(cases_py, tag):
    ns = runpy.run_path(cases_py); cases = ns['CASES']; views = ns.get('VIEWS', ['head_front','head_side','head_q','head_back'])
    json.dump(dict(cases=cases, views=views), open(S + '/unity_cases.json', 'w'), indent=1)
    for f in glob.glob(S + '/unity/*.png'): os.remove(f)
    for f in (S + '/unity_done.txt', S + '/unity_error.txt'):
        if os.path.exists(f): os.remove(f)
    subprocess.run([UNITY, '-batchmode', '-projectPath', R + '/Unity', '-executeMethod', 'GolfArcade.EditorTools.HeroBaseSkinProof.Run', '-logFile', S + f'/unity_{tag}.log'], capture_output=True)
    if os.path.exists(S + '/unity_error.txt'): print(open(S + '/unity_error.txt').read()[:1500]); sys.exit(1)
    out = {}
    for c in cases:
        fs = sorted(glob.glob(S + f'/unity/{c["name"]}__head_*.png')); p = measure(fs)
        out[c['name']] = dict(n=int(len(p)), S=float(p[:,0].mean()) if len(p) else 0, V=float(p[:,1].mean()) if len(p) else 0, H=float(p[:,2].mean()) if len(p) else 0)
        print(f'{c["name"]:22s} n={len(p):7d} S={out[c["name"]]["S"]:.3f} V={out[c["name"]]["V"]:.3f} H={out[c["name"]]["H"]:.1f}')
    json.dump(out, open(S + f'/measure_{tag}.json', 'w'), indent=1)
if __name__ == '__main__': run(sys.argv[1], os.path.splitext(os.path.basename(sys.argv[1]))[0])
