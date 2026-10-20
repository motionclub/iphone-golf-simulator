"""build a jaw variant from a contour-fit json and render it with analytic normals:  python3 variant_fit.py name fitfile"""
import sys, subprocess
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f3-head/tools')
import numpy as np
import trial, anorm_variant
name, fitfile = sys.argv[1], sys.argv[2]
kw = dict(nf_smooth=1, ztop=1.540, protect_eyes_ears=1, s5=1, smin=2, fit=1, fitfile=fitfile)
Vn, ctx, H = trial.build_variant(name, **kw)
anorm_variant.normals_for(name, Vn, ctx, H)
subprocess.run([trial.B, '-b', '--factory-startup', '--python', trial.W3 + 'tools/ul.py', '--', trial.W3 + f'data/var_{name}.npz', trial.W3 + 'renders/trial', trial.VIEWS, name + 'N', trial.W3 + f'data/anorm_{name}.npz'], check=True, capture_output=True)
print('built + rendered', name + 'N')
