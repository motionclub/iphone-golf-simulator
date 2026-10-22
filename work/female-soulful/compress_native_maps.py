"""Compress only the new female top and bottom maps for the native lobby."""
from pathlib import Path
import os,sys,subprocess,json,hashlib,shutil,tempfile
root=Path(__file__).resolve().parent;repo=root.parent.parent
source=Path('/private/tmp/female-soulful-UnityClone/Assets/Resources');dest=repo/'GolfArcade/Unity/CharacterAssets'
changed=json.loads((root/'native-changed-paths.json').read_text())
conv='/Applications/Xcode.app/Contents/Developer/usr/bin/TextureConverter'
for sport in sys.argv[1:] or ['Tennis','Golf']:
 for tag in os.environ.get('FEMALE_MAP_PIECES','Top,Bottom').split(','):
  for kind in ['N','M']:
   name=f'KitV2_{sport}_Female_{tag}_{kind}';src=source/sport/'KitsV2/Female'/(name+'.png');out=dest/('MatchHero_'+name+'.ktx')
   with tempfile.TemporaryDirectory(prefix='female-ktx-')as folder:
    tmp=Path(folder)/'map.ktx'
    p=subprocess.run([conv,'--compression_format=ASTC8x8','--compression_quality=Highest','--alpha_mode=Preserve','--channel_weighting=Linear','--gamma_in=1','--gamma_out=1','--flip_y','--wrap_mode=Clamp','--file_format=KTX','--output='+str(tmp),str(src)],capture_output=True,text=True)
    if p.returncode:raise RuntimeError(p.stdout+p.stderr)
    if not out.exists()or hashlib.sha256(out.read_bytes()).digest()!=hashlib.sha256(tmp.read_bytes()).digest():
     stage=out.with_suffix('.ktx.pending');shutil.copy2(tmp,stage);stage.replace(out);changed.append(str(out.relative_to(repo)))
   print(out.name,flush=True)
(root/'native-changed-paths.json').write_text(json.dumps(sorted(set(changed)),indent=2))
