"""ncc4.py: band-pass NCC / amplitude ratio of model vs bald plate in the bust ROI, with a small x-registration search (the plate chest centre sits ~1.5 cm right of the model centre line).
python3 tools/ncc4.py tag=coords.npy ...   (visual aid, NOT a gate: FORM3's NCC soft-passed a flat chest)"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import photo3 as ph
from photo3 import roi_box, plate_bp, model_bp

def score(co, x0=-0.105, x1=0.105, z0=1.14, z1=1.30, s1=1.6, s2=9.0, shifts=(-4, -2, 0, 2, 4, 6, 8)):
    box = roi_box('front', x0, x1, z0, z1)
    c0, r0, c1, r1 = box
    pb_full = plate_bp('front', (c0 - 12, r0, c1 + 12, r1), s1, s2)          # plate patch with +-12 px margin for the shifts
    mb, mask, img = model_bp(co, 'front', box, s1, s2)
    from scipy_free import erode
    m = erode(mask, 6)
    best = None
    for sh in shifts:
        pb = pb_full[:, 12 + sh:12 + sh + (c1 - c0)]
        a, b = pb[m], mb[m]
        a0, b0 = a - a.mean(), b - b.mean()
        ncc = float((a0 * b0).sum() / np.sqrt((a0 ** 2).sum() * (b0 ** 2).sum() + 1e-12))
        amp = float(b0.std() / (a0.std() + 1e-12))
        if best is None or ncc > best[0]:
            best = (ncc, amp, sh)
    return best

if __name__ == '__main__':
    for a in sys.argv[1:]:
        tag, p = a.split('=', 1)
        co = np.load(p).astype(np.float64)
        n, amp, sh = score(co)
        n0, amp0, _ = score(co, shifts=(0,))
        print(f'{tag:10s} NCC {n:.3f} (shift {sh:+d}px)  amp_ratio {amp:.2f}   | no-shift NCC {n0:.3f} amp {amp0:.2f}')
