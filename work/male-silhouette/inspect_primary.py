from pathlib import Path
from PIL import Image
import numpy as np,json
W=Path(__file__).parent;R=W.parents[1];P=R/'ArtDir/hero/base_lock/proof/male_silhouette'
views=json.loads((W/'reference-cameras.json').read_text())['views'][:2]
s=1.7/593
def spans(mask,v,y):
    py=round(v['sole_y']-(654-y)*s/v['metres_per_pixel'])
    xs=np.where(mask[py])[0]
    if not len(xs):return []
    x=(xs-v['centre_x'])*v['metres_per_pixel']/s
    if v['angle_degrees']==180:x=-x
    x=np.sort(x)
    cuts=np.where(np.diff(x)>4)[0]+1
    return [[round(a[0],2),round(a[-1],2)] for a in np.split(x,cuts)]
for v in views:
    t=np.array(Image.open(W/(v['name']+'_target.png')))>127
    m=np.array(Image.open(P/(v['name']+'.png')).getchannel('A'))>127
    print(v['name'])
    for y in [60,65,75,90,110,145,165,175,185,195,205,215,225,235,245,255,275,300,325,345,365,375,385,395,410,430,460,500,560,600,620,635,645,650,653]:
        print(y,'ref',spans(t,v,y),'mesh',spans(m,v,y))
