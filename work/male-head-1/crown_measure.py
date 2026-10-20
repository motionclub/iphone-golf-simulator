import numpy as np
from PIL import Image
from pathlib import Path
R=Path('.'); S=R/'work/male-silhouette'
s=1.7/593
for r in range(59,156,3):
 vals=[]
 for name,cx,sole,h in [('bald_front',353,654,593),('bald_back',915.75,651,589)]:
  q=np.array(Image.open(S/(name+'_target.png')).convert('L'))>127; row=round(sole-(654-r)/593*h); xx=np.where(q[row])[0]
  vals.append(tuple(np.round(((xx[0]-cx)*593/h,(xx[-1]-cx)*593/h),1)) if len(xx) else None)
 print(r,vals)
