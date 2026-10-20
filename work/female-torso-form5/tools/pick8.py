"""pick8.py: robust re-evaluation of render-domain candidates.  python3 tools/pick8.py data/PP5_a.json data/PP5_b.json ...
For each parameter file: build, numpy screen, render the back panel soft AND clay in Blender, and print soft err/rise at hp sigma 8/10/12, clay rise + crest gradient, numpy trace rise."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import ImageFilter
import rampfit6 as rf, rampfit8 as r8, pelvis5 as pv, blbatch6 as bb, bandtrace_panel6 as bp, cnweight5 as cnw
from run4 import SOFT
CLAY = 'matcap:clay_studio.exr'
HERE = bb.HERE

def rows_sigma(panel, s):
    return {dx: v[0] for dx, v in bp.trace_panel(panel, s).items()}

def metrics(rows, plate_rows):
    r = bb.lr_avg(rows); p = bb.lr_avg(plate_rows)
    return float(np.sqrt(((r - p) ** 2).mean())), float(r[0] - r[-1])

if __name__ == '__main__':
    files = sys.argv[1:]
    cos = {}
    for i, f in enumerate(files):
        PP = json.load(open(f)); PP['rl0'] = 0.075; PP['rl1'] = 0.2
        co = pv.build_pelvis(rf.CO_MIX, PP); ok, st = r8.screen(co)
        path = f'{HERE}/scratch/r/pk8_{i}.npy'; np.save(path, co); wpath = f'{HERE}/scratch/r/pk8_{i}_w.npy'; np.save(wpath, cnw.cn_weight(co)); cos[f'p{i}'] = ((path, wpath), ok, st)
    soft = bb.render_panels({t: v[0] for t, v in cos.items()}, prefix='pk8s', look=SOFT)
    clay = bb.render_panels({t: v[0] for t, v in cos.items()}, prefix='pk8c', look=CLAY)
    plate = bb.plate_panel()
    print('file | screen | soft err/rise s8 | s10 | s12 | clay err/rise | clay crest')
    for i, f in enumerate(files):
        t = f'p{i}'
        line = []
        for s in (8, 10, 12):
            e, ri = metrics(rows_sigma(soft[t], s), rows_sigma(plate, s)); line.append(f'{e:5.1f}/{ri:5.1f}')
        e2, r2 = metrics(rows_sigma(clay[t], 10), rows_sigma(plate, 10))
        rows_c = rows_sigma(clay[t], 10)
        cg = bp.crest_grad(clay[t], rows_c)
        stt = cos[t][2]
        print(f"{os.path.basename(f):22s} | ok={cos[t][1]} env {stt['env']:.2f} dm {stt['dm']:.1f} di {stt['di']:.1f} du {stt['du']:.1f} ms {stt['ms']:.1f} | soft " + ' | '.join(line) + f' | clay {e2:5.1f}/{r2:5.1f} crest {cg:.1f}')
