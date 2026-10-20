"""All six staged manifests: exact garment-map packaging, original LUTs remain PNG."""
from pathlib import Path
import argparse,concurrent.futures,hashlib,json,shutil,subprocess
TASK=Path(__file__).resolve().parent;REPO=TASK.parents[2]
p=argparse.ArgumentParser();p.add_argument('--assets',type=Path,default=TASK/'export');p.add_argument('--manifest',action='append');args=p.parse_args();EXPORT=args.assets.resolve();assert EXPORT.is_relative_to(TASK),'Work output only'
SHIPPED=REPO/'GolfArcade/Unity/CharacterAssets';CONVERTER='/Applications/Xcode.app/Contents/Developer/usr/bin/TextureConverter'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
names=set();manifests=[]
for stem in args.manifest or [prefix+sex+suffix for prefix,suffix in [('MatchHero_',''),('MatchHero_','_Distance'),('GolfKitHero_','')] for sex in ['Male','Female']]:
  d=json.loads((EXPORT/(stem+'.json')).read_text());manifests.append(stem)
  for part in d['parts']:
   for sub in part['submeshes']:
    l=sub['look']
    if l.get('useGarmentMaps',0)>.5:
     for key in ['normalMap','maskMap','weaveMap']:
      assert l.get(key),f'{stem}/{part["name"]}: missing {key}';names.add(l[key])
assert names,'No garment maps'
if not args.manifest:assert len(names)==50,'Unexpected complete garment map count; review before adoption'
def package(name):
 png=EXPORT/(name+'.png');destination=EXPORT/(name+'.ktx');assert png.is_file(),png
 source_hash=sha(png);shipped_png=SHIPPED/png.name;shipped_ktx=SHIPPED/destination.name
 fmt='ASTC4x4' if 'Atlas' in name else 'ASTC8x8';row={'name':name,'source_png_sha256':source_hash,'format':fmt}
 if shipped_png.is_file() and shipped_ktx.is_file() and sha(shipped_png)==source_hash:
  shutil.copyfile(shipped_ktx,destination);row.update(method='exact shipped KTX copy',shipped_ktx_sha256=sha(shipped_ktx));assert sha(destination)==sha(shipped_ktx)
 else:
  command=[CONVERTER,'--compression_format='+fmt,'--compression_quality=Highest','--alpha_mode=Preserve','--channel_weighting=Linear','--gamma_in=1','--gamma_out=1','--flip_y','--wrap_mode=Clamp','--file_format=KTX','--output='+str(destination),str(png)]
  result=subprocess.run(command,capture_output=True,text=True);row.update(method='existing production converter workflow',command=command)
  if result.returncode:raise RuntimeError(result.stdout+result.stderr)
 assert destination.read_bytes().startswith(b'\xabKTX 11\xbb\r\n\x1a\n'),destination
 row.update(ktx_sha256=sha(destination),ktx_bytes=destination.stat().st_size);print(name+': '+row['method'],flush=True);return row
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:rows=list(pool.map(package,sorted(names)))
(TASK/'resource-package.json').write_text(json.dumps({'status':'PASS','manifests':manifests,'maps':rows,'linear_face_luts_preserved_uncompressed_png':True,'no_material_bypass':True},indent=2)+'\n')
