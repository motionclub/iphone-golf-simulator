"""Plate side-profile contour (female_multiangle_body.jpg, LEFT + RIGHT profile panels), gradient-edge method.
For each even image row y (100..260) scan inward from outside the figure until |dL/dx| > 2.0, refine to the local gradient peak.
Panel calibration (skin landmarks): head top row 50, sole row 338  ->  S2 = 1.7039 m / 288.5 px, z = (338.5 - y) * S2.
Anchor: knee-centre (z=0.52) of each panel -> model y = 0:  left panel x0 = 791.5, right panel x0 = 1095.0.
Writes data/left_edges_grad.json, data/right_edges_grad.json  ({row: [[front_or_left_x, grad],[back_or_right_x, grad]]})."""
from PIL import Image
import numpy as np, json
L=np.asarray(Image.open('../../ArtDir/hero/base_lock/female_multiangle_body.jpg').convert('L')).astype(float)
def edge_scan(y,x_start,x_end,step,thr=2.0):
    row=L[y-1:y+2,:].mean(0); g=np.gradient(row)
    for x in range(x_start,x_end,step):
        if abs(g[x])>thr:
            best=x; bv=abs(g[x])
            for k in range(0,5):
                xx=x+k*step
                if abs(g[xx])>bv: bv=abs(g[xx]); best=xx
            return [float(best+0.5),float(bv)]
    return [None,0.0]
left={};right={}
for y in range(100,262,2):
    left[y]=[edge_scan(y,752,800,1),edge_scan(y,830,790,-1)]          # front edge scanned from the left, back edge from the right
    right[y]=[edge_scan(y,1125,1070,-1),edge_scan(y,1040,1085,1)]      # (right panel faces left too: its strong edge is the front on the LEFT side)
json.dump({str(k):v for k,v in left.items()},open('data/left_edges_grad.json','w'))
json.dump({str(k):v for k,v in right.items()},open('data/right_edges_grad.json','w'))
print("rows",len(left))
