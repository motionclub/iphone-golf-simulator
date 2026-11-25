"""Powered by Poly Haven. Offline runtime assets, CC0. Re-run to fetch pinned maps."""
import urllib.request,json,pathlib,hashlib
from PIL import Image,ImageOps
ROOT=pathlib.Path(__file__).resolve().parents[2]; OUT=ROOT/'work/clubhouse-cosmetics/sources'
DEST=ROOT/'Unity/Assets/Resources/Cosmetics'; DEST.mkdir(parents=True,exist_ok=True)
NATIVE=ROOT/'GolfArcade/Unity/CharacterAssets'
manifest=[]
for asset,key,name in [('fabric_pattern_07','col_1','woven'),('brown_leather','Diffuse','leather'),('metal_plate','Diffuse','metal'),('fine_grained_wood','Diffuse','wood')]:
 data=json.loads((OUT/(asset+'.json')).read_text()); options=data[key]['1k'];info=options.get('jpg',next(iter(options.values())))
 req=urllib.request.Request(info['url'],headers={'User-Agent':'PartySportsCosmetics/1.0'})
 raw=urllib.request.urlopen(req).read();src=OUT/(asset+'.jpg');src.write_bytes(raw)
 im=Image.open(src).convert('RGB').resize((512,512),Image.Resampling.LANCZOS)
 # Neutral detail preserves palette tint; high contrast grime suppressed for toy readability.
 im=ImageOps.grayscale(im); im=ImageOps.autocontrast(im); im=im.point(lambda x: int(140+x*0.45) if name=='wood' else int(210+x*0.176)).convert('RGB')
 for d in [DEST,NATIVE]: im.save(d/('Cosmetic_'+name+'.png'))
 manifest.append(dict(asset=asset,page='https://polyhaven.com/a/'+asset,url=info['url'],sha256=hashlib.sha256(raw).hexdigest(),license='CC0-1.0',derivation=('512px neutral luminance, range 140–255' if name=='wood' else '512px neutral luminance, range 210–255')))
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2))
print('Downloaded',len(manifest),'Poly Haven source maps')
