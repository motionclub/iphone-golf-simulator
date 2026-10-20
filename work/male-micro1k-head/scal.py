"""normal-displacement scalar (mm) between two variants: python3.13 scal.py <Vnew.npy> <Vbase.npy> <out.npy>"""
import sys, pickle
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1k-head')
from j_edit import *
Vn = np.load(sys.argv[1]); Vb = np.load(sys.argv[2])
F = pickle.load(open(W / 'data/F_start.pkl', 'rb'))
Nb = vertex_normals(Vb, F)
S = ((Vn - Vb) * Nb).sum(1) * 1000
np.save(sys.argv[3], S); print('max', S.max(), 'min', S.min(), 'n>0.05', int((np.abs(S) > 0.05).sum()))
