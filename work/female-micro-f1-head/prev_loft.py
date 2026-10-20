import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f1-head')
import numpy as np, fl, loftf
L = loftf.Loft()
V, F = loftf.preview_mesh(L)
loftf.save_npz(str(fl.W / 'data/prev_loft.npz'), V, F)
print(V.shape, len(F), V[:,2].min(), V[:,2].max(), V[:,1].min(), V[:,1].max(), V[:,0].min(), V[:,0].max())
