from pathlib import Path
from PIL import Image
import json,math
W=Path(__file__).resolve().parents[1];D=W/'maps';rows=[]
def astc(s,block):
 total=0
 while True:
  total+=math.ceil(s/block)**2*16
  if s==1:break
  s=max(1,s//2)
 return total
for p in sorted(D.glob('*.png')):
 size=Image.open(p).width;block=4 if p.name=='Cloth_FabricAtlas.png' else 8
 rows.append({'map':p.name,'size':size,'format':f'ASTC_{block}x{block}','mipmapped_bytes':astc(size,block),'MB':astc(size,block)/1e6})
shared=astc(512,4)+astc(256,4) # the old resource is currently loaded before the atlas replaces it
summ={sex:sum(x['mipmapped_bytes'] for x in rows if f'_{sex}_' in x['map'])+shared for sex in ['Male','Female']}
(W/'texture_budget.json').write_text(json.dumps({'maps':rows,'shared_atlas_and_legacy_weave_bytes':shared,'per_hero_total_bytes':summ,'limit_bytes':6000000,'pass':all(x<=6000000 for x in summ.values())},indent=2));print(summ)
