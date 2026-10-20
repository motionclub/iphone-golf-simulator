"""Conservative masks of the source crowd atlas's existing teal/white/orange kit.
Skin/hair are deliberately excluded. This changes existing garment palette only.
"""
from pathlib import Path
from PIL import Image
import numpy as np, json
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'Unity/Assets/Resources/Tennis/Characters'
report=[]
for sex in ['Male','Female']:
 source=Image.open(OUT/f'Higgs{sex}_Color.png').convert('RGB')
 rgb=np.asarray(source,dtype=np.float32)/255
 hsv=np.asarray(source.convert('HSV'),dtype=np.float32)/255
 h,s,v=hsv[:,:,0],hsv[:,:,1],hsv[:,:,2]
 def edge(x,a,b):return np.clip((x-a)/(b-a),0,1)
 # The source white shirt and teal shorts/lining are strongly separated in colour.
 shirt=(1-edge(s,.11,.18))*edge(v,.48,.65)
 shorts=edge(h,.47,.52)*(1-edge(h,.63,.68))*edge(s,.35,.5)
 accent=(1-edge(h,.10,.14))*edge(h,.015,.035)*edge(s,.78,.90)
 mask=np.stack([shirt,shorts,accent,np.zeros_like(h)],axis=-1)
 Image.fromarray(np.uint8(np.clip(mask,0,1)*255),'RGBA').save(OUT/f'Higgs{sex}_Mask.png')
 linear=np.where(rgb<.04045,rgb/12.92,((rgb+.055)/1.055)**2.4)
 lum=linear@np.array([.2126,.7152,.0722])
 refs=[]
 for channel in [shirt,shorts,accent]:refs.append(float(np.sum(lum*channel)/max(1,np.sum(channel))))
 values=dict(shirt=refs[0],shorts=refs[1],accent=refs[2],skin=.27)
 (OUT/f'Higgs{sex}_Mask.json').write_text(json.dumps(values,indent=2))
 report.append(dict(sex=sex,maskedPixelFraction=[float(c.mean()) for c in [shirt,shorts,accent]],skinMasked=0,references=values))
(ROOT/'proof/full-visual-overhaul/characters/crowd-palette-source.json').write_text(json.dumps(report,indent=2))
print('CROWD_KIT_MASKS',report)
