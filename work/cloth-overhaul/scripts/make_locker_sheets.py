from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import shutil,json,hashlib
W=Path(__file__).resolve().parents[1];R=W.parents[1];D=R/'ArtDir/screenshots/cloth_overhaul'
font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',22)
for sex in ['male','female']:
 out=Image.new('RGB',(1800,1800),'#eef0f3');draw=ImageDraw.Draw(out)
 for row,(label,u,s) in enumerate([('Polo',W/'after_final'/f'{sex}_collar.png',W/'locker/proof'/f'cloth_{sex}_collar.png'),('Shoe side',W/'after_final'/f'{sex}_shoe_side.png',W/'locker/proof'/f'cloth_{sex}_shoe_side.png')]):
  for col,(p,renderer) in enumerate([(u,'Unity'),(s,'SceneKit')]):
   im=Image.open(p);im.thumbnail((900,850));out.paste(im,(col*900,row*900+50));draw.text((col*900+15,row*900+12),f'{sex} {label} — {renderer}',fill='black',font=font)
 out.save(D/f'LOCKER_PARITY_{sex}.png')
 shutil.copy2(W/'locker/proof'/f'cloth_{sex}_shirt_dummy.png',D/f'SPEC_REUSE_{sex}.png')
files=[W/'locker/render',*sorted((W/'locker/src').glob('*.swift')),W/'locker/main.swift',*sorted((W/'locker/assets').glob('*.lzfse'))]
(W/'locker/spec_reuse_proof.json').write_text(json.dumps({'method':'Same executable, sources and packed assets for default vs DUMMY_POLO.json; only environment-selected data changed. Top cloned as Dummy_Polo_Duplicate, same mesh/maps/rig.','data':json.loads((W/'locker/DUMMY_POLO.json').read_text()),'sha256':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}},indent=2))
