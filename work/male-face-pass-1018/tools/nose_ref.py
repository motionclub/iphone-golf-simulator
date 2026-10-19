"""Ref nose curves from sheet 17 (crown-chin 253.8 mm => .692 mm/px, eye line y=316 px -> 0):
profile: front-most skin per row (right profile, face toward -x), front: nose half-width per row (edge of the nose against the cheek is
not a silhouette, so the front width is taken from the dark alar edge where visible: ala outer edge by luminance minimum)."""
import numpy as np
from PIL import Image
S='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/style/alive/male-reference-pack-2026-10-17/sheets/17-face-detail-neutral.png'
A=np.asarray(Image.open(S).convert('RGB')).astype(float)
mm=.692
def profile():
    rows=[];
    for py in range(290,420):
        r=A[py,1400:1700]; bg=(np.abs(r-r[:5].mean(0)).sum(1)<30)   # grey background
        sk=np.where(~bg)[0]
        if len(sk): rows.append((-(py-316)*mm, -(1400+sk[0])*mm))   # z grows toward the face front (-x px)
    return np.array(rows)
if __name__=='__main__':
    P=profile(); np.save('nose/ref_profile.npy',P)
    for y,z in P[::5]: print(f'{y:7.1f} {z:8.1f}')
