"""iter3.py <tag> [params.json|-] [--nofit] [--parts chest,pelvis]  : build -> render -> compare images.
writes data/co_<tag>.npy and scratch/r/it_<tag>_{chest,pelvis}.png (plate | form2 | this: soft + bandpass)"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from torso3 import *
from rr import *
import viz3

def run(tag, P=None, fit=True, parts=('chest', 'pelvis'), cmp_form2=True, looks=('soft',), iters=4, zhi=1.30):
    t0 = time.time()
    P = {**DEFAULT3, **(P or {})}
    if fit:
        H, zc = fit_bust(P, verbose=True)
        P['bm_H'], P['bm_zc'] = H, zc
        dF, dB = fit_walls(P, iters=iters, zhi=zhi, verbose=False)
    else:
        dF = dB = None
    co = build3(P, dF, dB)
    np.save(f'{HERE}/data/co_{tag}.npy', co)
    json.dump({k: (float(v) if isinstance(v, (float, np.floating)) else v) for k, v in P.items()}, open(f'{HERE}/data/P_{tag}.json', 'w'), indent=1)
    if dF is not None:
        np.save(f'{HERE}/data/dFB_{tag}.npy', np.stack([dF, dB]))
    outs = []
    for roi in parts:
        f2 = f'{HERE}/scratch/r/rr_form2_{roi}.png'
        if not os.path.exists(f2):
            render([roi], f'{HERE}/data/co_start_f2.npy', f'rr_form2', 'matcap:soft')
        p = render([roi], f'{HERE}/data/co_{tag}.npy', f'rd_{tag}', 'matcap:soft')[0]
        files = ([f2] if cmp_form2 else []) + [p]
        labs = (['form2'] if cmp_form2 else []) + [tag]
        a = strip([plate_crop(roi, 1.0)] + files, ['PLATE'] + labs, scale=0.6)
        b = viz3.structure_strip(roi, files, labs, scale_out=0.6)
        W = Image.new('RGB', (max(a.width, b.width), a.height + b.height))
        W.paste(a, (0, 0)); W.paste(b, (0, a.height))
        q = f'{HERE}/scratch/r/it_{tag}_{roi}.png'
        W.save(q); outs.append(q)
    print(f'[{tag}] {time.time()-t0:.1f}s', *outs)
    return co, outs

if __name__ == '__main__':
    tag = sys.argv[1]
    P = json.load(open(sys.argv[2])) if len(sys.argv) > 2 and sys.argv[2] != '-' else {}
    run(tag, P, fit='--nofit' not in sys.argv)
