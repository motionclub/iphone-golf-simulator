"""Segment a shoe-sheet view: fg mask + class map (0 bg,1 white upper/midsole,2 navy trim,3 grey outsole,4 other)."""
import numpy as np
from PIL import Image
S='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/style/alive/male-reference-pack-2026-10-17/sheets/'
def load(n): return np.asarray(Image.open(S+n+'.png').convert('RGB')).astype(float)
def fill_holes(m):
    # flood fill background from the border (4-neigh) iteratively with numpy
    bg=np.zeros_like(m); bg[0,:]=~m[0,:]; bg[-1,:]=~m[-1,:]; bg[:,0]=~m[:,0]; bg[:,-1]=~m[:,-1]
    free=~m
    while True:
        n=bg.copy()
        n[1:]|=bg[:-1]; n[:-1]|=bg[1:]; n[:,1:]|=bg[:,:-1]; n[:,:-1]|=bg[:,1:]
        n&=free
        if (n==bg).all(): break
        bg=n
    return ~bg
def classify(im,bgc):
    d=np.abs(im-bgc).sum(2)
    r,g,b=im[...,0],im[...,1],im[...,2]
    lum=(r+g+b)/3; sat=im.max(2)-im.min(2)
    navy=(b-r>25)&(lum<150)
    white=(lum>222)&(sat<22)
    grey=(lum<=222)&(lum>120)&(sat<26)&~navy
    fg=fill_holes(d>22)
    cls=np.zeros(im.shape[:2],np.uint8)
    cls[fg]=4; cls[fg&white]=1; cls[fg&navy]=2; cls[fg&grey]=3
    return fg,cls
