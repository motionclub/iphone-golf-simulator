"""py.sh volcmp.py base.json 'name={json overrides}' ...  -> palm volume, area, ROI, root dihedral, thenar mound"""
import sys, json, numpy as np
from pathlib import Path
W = Path(__file__).resolve().parent; sys.path.insert(0, str(W))
import asm3, evalp, allmetrics, palmvol_lib
base = json.load(open(sys.argv[1]))
v0 = palmvol_lib.vol({})
def run(name, p):
    v, _, _ = palmvol_lib.vol(p); r = evalp.evaluate(p)
    out, Vn, polys, si = allmetrics.all_metrics(p)
    pm = out['palm']['R']; ex = out['extra']['R']
    print('%-14s vol %+5.1f%%  area %+5.1f%% len %+5.1f%% web %+5.1f%% mid %+5.1f%% | roi %d bf %.2f bb %.2f | T5 %.1f max %.1f thenar %.1f' % (name, 100 * (v / v0[0] - 1), 100 * (pm['palm_planform_area_mm2'] / 9557.76 - 1), 100 * (pm['palm_length_mm'] / 104.05 - 1), 100 * (pm['palm_breadth_web_mm'] / 109.93 - 1), 100 * (pm['palm_breadth_mid_mm'] / 93.46 - 1), r['roi_total'], r['full']['bald_front'], r['full']['bald_back'], ex['T5_dihedral']['max'], out['dihedral_new_faces']['max'], ex['T1_thenar_mound_mm']))
run('base', base)
for a in sys.argv[2:]:
    n, js = a.split('=', 1); p = dict(base); p.update(json.loads(js)); run(n, p)
