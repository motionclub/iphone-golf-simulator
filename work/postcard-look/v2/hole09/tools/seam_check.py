"""seam_check.py - measures the straight full-width seam in a tee preview (Blender EEVEE render, NOT a Game-view still): the step in the row-mean colour across the TEE_BOX / FAIRWAY boundary
(found from the geometry: the tee box far edge, projected into the frame = row ~556 of the 1600 px frame) against the typical row-to-row step of the 60 rows round it.
usage: Blender -b --python seam_check.py -- [--row 556] a.png [b.png ...]"""
import sys, numpy as np, bpy
A = sys.argv[sys.argv.index("--") + 1:]
row0 = 556
if "--row" in A:
    row0 = int(A[A.index("--row") + 1]); A = [x for x in A if x not in ("--row", str(row0))]
for pth in A:
    im = bpy.data.images.load(pth)
    w, h = im.size
    a = np.array(im.pixels[:]).reshape(h, w, 4)[::-1, :, :3] * 255.0      # row 0 = top
    rows = a[:, 20:w - 20, :].mean(axis=1)
    # step across each candidate row: mean of 3 rows below minus 3 rows above (rows grow downwards = nearer the camera)
    prof = {y: float(np.abs(rows[y:y + 3].mean(axis=0) - rows[y - 3:y].mean(axis=0)).max()) for y in range(row0 - 40, row0 + 41)}
    near = [v for y, v in prof.items() if abs(y - row0) <= 4]
    far = [v for y, v in prof.items() if abs(y - row0) > 12]
    print(f"SEAM {pth.split('/')[-3]}/{pth.split('/')[-1]}: step across rows {row0 - 4}..{row0 + 4}: max {max(near):.2f} levels; the other rows of rows {row0 - 40}..{row0 + 40}: median {np.median(far):.2f}, max {max(far):.2f}; ratio seam / typical-max {max(near) / max(max(far), 1e-6):.2f}")
