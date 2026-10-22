"""Ceiling: correlation between the two independent plate renders (plain plate vs multi-angle sheet) in the torso regions, matched physical scale."""
import sys, json
import numpy as np
from PIL import Image
sys.path.insert(0, '.')
from relcorr import blur
R = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/'
CAM = {c['name']: c for c in json.load(open(R + 'work/male-silhouette/reference-cameras.json'))['views']}
PL = np.asarray(Image.open(R + 'ArtDir/hero/base_lock/male_body_plain.jpg').convert('L')).astype('float32')
SH = np.asarray(Image.open(R + 'ArtDir/hero/base_lock/male_multiangle_body.jpg').convert('L')).astype('float32')
def sample(img, cam, xs, zs, back):
    c = CAM[cam]; mpp = c['metres_per_pixel']
    col = c['centre_x'] + (-xs if back else xs) / mpp; row = c['sole_y'] - zs / mpp
    c0 = np.clip(np.floor(col).astype(int), 0, img.shape[1] - 2); r0 = np.clip(np.floor(row).astype(int), 0, img.shape[0] - 2); fc = col - c0; fr = row - r0
    return img[r0, c0] * (1 - fc) * (1 - fr) + img[r0, c0 + 1] * fc * (1 - fr) + img[r0 + 1, c0] * (1 - fc) * fr + img[r0 + 1, c0 + 1] * fc * fr
REG = {'chest': (1.15, 1.32), 'abdomen': (0.90, 1.15), 'pelvis': (0.80, 0.90)}
# resample both to a common grid of 5 mm
step = 0.005
for back, v_pl, v_sh in ((False, 'bald_front', 'sheet_front'), (True, 'bald_back', 'sheet_back')):
    xs = np.arange(-0.17, 0.17 + 1e-9, step); zs = np.arange(0.76, 1.40, step)
    X, Z = np.meshgrid(xs, zs)
    # pre-blur each source to its own pixel scale so the common-grid sample is alias free
    a = sample(blur(PL, 1.0), v_pl, X, Z, back); b = sample(blur(SH, 0.5), v_sh, X, Z, back)
    # band-pass on the common grid: sigma in grid px (5 mm): DoG(0.7, 2.8) ~ (3.4mm, 14mm)
    da = blur(a, 0.7) - blur(a, 2.8); db = blur(b, 0.7) - blur(b, 2.8)
    out = []
    for rn, (z0, z1) in REG.items():
        m = (np.abs(X) < 0.12) & (Z >= z0) & (Z < z1)
        out.append(f'{rn} {np.corrcoef(da[m], db[m])[0,1]:+.3f}')
    da2 = blur(a, 1.2) - blur(a, 4.5); db2 = blur(b, 1.2) - blur(b, 4.5)
    out2 = []
    for rn, (z0, z1) in REG.items():
        m = (np.abs(X) < 0.12) & (Z >= z0) & (Z < z1); out2.append(f'{rn} {np.corrcoef(da2[m], db2[m])[0,1]:+.3f}')
    print(('back ' if back else 'front'), 'plate-vs-sheet r (DoG ~3.5/14 mm):', ' | '.join(out), '   (DoG ~6/22 mm):', ' | '.join(out2))
