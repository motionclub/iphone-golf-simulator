"""3/4 panel silhouette comparison: plate mask (bg-subtracted from the sheet) vs registered render alpha.
python3 sil34.py <panel q3BL|q3BR> <render png> <out png>  (box fixed per panel)"""
import sys, numpy as np
from PIL import Image
R = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/hero/base_lock/'
BOX = {'q3BL': (730, 860, 480, 620, 8, (676, 690, 884, 898)), 'q3BR': (1010, 1140, 480, 620, 8, (1000, 1008, 1146, 1154))}
def plate_mask(panel):
    c0, c1, r0, r1, mag, (b0, b1, b2, b3) = BOX[panel]
    L = np.asarray(Image.open(R + 'male_multiangle_body.jpg').convert('L')).astype(float)
    m = np.zeros(L.shape, bool)
    for r in range(r0 - 2, r1 + 2):
        bg = np.median(np.concatenate([L[r, b0:b1], L[r, b2:b3]]))
        m[r] = L[r] > bg + 9
    return m[r0:r1, c0:c1]
def main():
    panel, rend, out = sys.argv[1:4]; c0, c1, r0, r1, mag, _ = BOX[panel]
    pm = plate_mask(panel)
    pmu = np.asarray(Image.fromarray((pm * 255).astype(np.uint8)).resize(((c1 - c0) * mag, (r1 - r0) * mag), Image.BILINEAR)) > 127
    a = np.asarray(Image.open(rend)); rm = a[..., 3] > 127
    if rm.shape != pmu.shape: print('shape mismatch', rm.shape, pmu.shape); rm = np.asarray(Image.fromarray((rm * 255).astype(np.uint8)).resize(pmu.shape[::-1])) > 127
    img = np.zeros(rm.shape + (3,), np.uint8); img[pmu & rm] = (90, 90, 90); img[pmu & ~rm] = (255, 70, 70); img[~pmu & rm] = (70, 220, 255)
    Image.fromarray(img).save(out)
    print(panel, 'union', int((pmu | rm).sum()), 'diff', int((pmu ^ rm).sum()), 'pct', round(100.0 * (pmu ^ rm).sum() / (pmu | rm).sum(), 2))
main()
