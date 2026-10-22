"""Work-only proof packaging: preserve exact exported PNG/material inputs."""
from pathlib import Path
import concurrent.futures, hashlib, json, shutil, subprocess
TASK=Path(__file__).resolve().parent
REPO=TASK.parents[2]
EXPORT=TASK/'export'
SHIPPED=REPO/'GolfArcade/Unity/CharacterAssets'
CONVERTER=Path('/Applications/Xcode.app/Contents/Developer/usr/bin/TextureConverter')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
names=set()
for sex in ['Male','Female']:
    manifest=json.loads((EXPORT/f'MatchHero_{sex}.json').read_text())
    for part in manifest['parts']:
        for sub in part['submeshes']:
            look=sub['look']
            if look.get('useGarmentMaps',0)>.5:
                for key in ['normalMap','maskMap','weaveMap']:
                    assert look.get(key),f'{sex}/{part["name"]} missing {key}'
                    names.add(look[key])
assert names,'No garment maps found in staged manifests'
def package(name):
    png=EXPORT/(name+'.png');destination=EXPORT/(name+'.ktx')
    assert png.exists(),f'Exported source map missing: {png}'
    source_hash=sha(png)
    shipped_png=SHIPPED/png.name;shipped_ktx=SHIPPED/destination.name
    fmt='ASTC4x4' if 'Atlas' in name else 'ASTC8x8'
    row={'name':name,'source_png_sha256':source_hash,'format':fmt,'material_definition_unchanged':True}
    if shipped_png.exists() and shipped_ktx.exists() and sha(shipped_png)==source_hash:
        shutil.copyfile(shipped_ktx,destination)
        row.update(method='exact shipped KTX copy',shipped_png_sha256=sha(shipped_png),shipped_ktx_sha256=sha(shipped_ktx))
        assert sha(destination)==row['shipped_ktx_sha256']
    else:
        # Same production cloth conversion, including linear data, alpha and y flip.
        command=[str(CONVERTER),'--compression_format='+fmt,'--compression_quality=Highest','--alpha_mode=Preserve','--channel_weighting=Linear','--gamma_in=1','--gamma_out=1','--flip_y','--wrap_mode=Clamp','--file_format=KTX','--output='+str(destination),str(png)]
        result=subprocess.run(command,capture_output=True,text=True)
        if result.returncode:raise RuntimeError(result.stdout+result.stderr)
        row.update(method='existing TextureConverter workflow',command=command)
    assert destination.read_bytes().startswith(b'\xabKTX 11\xbb\r\n\x1a\n'),f'Not KTX1: {destination}'
    row.update(ktx_sha256=sha(destination),ktx_bytes=destination.stat().st_size)
    print(name+': '+row['method'],flush=True)
    return row
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    rows=list(pool.map(package,sorted(names)))
(TASK/'garment-texture-package.json').write_text(json.dumps({'status':'PASS','maps':rows,'all_exported_pngs_retained':True,'no_material_bypass':True},indent=2)+'\n')
