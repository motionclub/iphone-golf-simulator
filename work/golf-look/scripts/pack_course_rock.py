from pathlib import Path
import numpy as np
from PIL import Image
W=Path(__file__).resolve().parents[1];B=W/'inputs/post_cloth/Unity/Assets/Resources/Course/Look';D=W/'candidate/Unity/Assets/Resources/Course/Surface';D.mkdir(parents=True,exist_ok=True)
for name in ['Cliff','CliffDark','Rock','Masonry','Basalt']:
 p=B/(name+'_C.png')
 if not p.exists():continue
 a=np.array(Image.open(p).convert('RGBA'));e=B/(name+'_E.png')
 a[:,:,3]=0
 if e.exists():a[:,:,3]=np.array(Image.open(e).convert('RGB').resize((a.shape[1],a.shape[0]))).max(axis=2)
 Image.fromarray(a).save(D/(name+'_CE.png'))
print('Rock albedo/emission packing prepared in candidate; original maps unchanged')
