"""./py.sh make_delta.py <cand.npz> <hands_delta.npz>   : express a hand candidate as a portable delta (see merge_hands_delta.py)"""
import sys
import numpy as np
from pathlib import Path
W = Path(__file__).resolve().parent
S = np.load(W / 'data/mesh_start.npz'); C = np.load(sys.argv[1])
N0 = len(S['V']); V0 = S['V']; V = C['V']
slots = np.sort(np.concatenate([np.load(W / f'data/start_hand_verts_{s}.npy') for s in (1, -1)]))
ring = np.sort(np.concatenate([np.load(W / f'data/start_hand_ring_{s}.npy') for s in (1, -1)]))
removed = C['removed_faces']; nkept = len(S['loop_total']) - len(removed)
cv, ls, lt = C['corner_verts'], C['loop_start'], C['loop_total']
new_ls = ls[nkept:]; start_c = new_ls[0]
np.savez(sys.argv[2], n_base=N0, slots=slots, ring=ring, ring_pos_start=V0[ring], slot_pos_start=V0[slots], slot_pos=V[slots], appended_pos=V[N0:],
         new_corner_verts=cv[start_c:], new_loop_start=(new_ls - start_c).astype(np.int32), new_loop_total=lt[nkept:])
print('delta: slots', len(slots), 'ring', len(ring), 'appended', len(V) - N0, 'new faces', len(lt) - nkept)
