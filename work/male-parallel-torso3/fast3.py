"""Batch builder with cached solver state: python3.13 fast3.py <spec.json>  (spec = {tag: cfg overrides}); writes data/V_<tag>.npy for each; prints dy stats."""
import sys, json, copy
import numpy as np
sys.path.insert(0, '.')
import form3
from form3 import *
V0 = np.load('data/V_base.npy'); T0 = Torso3(V0); _cache = {}
def build_fast(cfg):
    R = cfg['rbf']; key = json.dumps(R, sort_keys=True)
    if key not in _cache: _cache[key] = rbf_stage(V0.copy(), T0, R, V0) if not R.get('skip') else (V0.copy(), None)
    V = _cache[key][0].copy(); V = clamp_extremes(V, V0, T0, cfg['clamp_tol'])
    steps = [s for s in (['struct'] if cfg['order'] == 'rbf_first' else []) if s]
    V, P = struct_stage(V, T0, cfg['struct'], cfg['only_struct']); V = clamp_extremes(V, V0, T0, cfg['clamp_tol'], cfg.get('allow_back'))
    Vg, dF, dB = deficit_guard(V, V0, T0, sigma=cfg['guard_sigma'], n=cfg['guard_n'], zhi=cfg['guard_zhi'], zlo=cfg.get('guard_zlo', 0.80))
    return Vg, P
if __name__ == '__main__':
    spec = json.load(open(sys.argv[1])); base = json.load(open(sys.argv[2])) if len(sys.argv) > 2 else {}
    for tag, over in spec.items():
        cfg = copy.deepcopy(DEF); merge(cfg, base); merge(cfg, over); Vg, P = build_fast(cfg); np.save(f'data/V_{tag}.npy', Vg); json.dump(cfg, open(f'data/cfg_{tag}.json', 'w'), indent=1)
        d = (Vg[:, 1] - V0[:, 1]) * 1000; print(tag, 'dy [%.1f, %.1f] mm' % (d.min(), d.max()))
