from pathlib import Path
import json,hashlib,subprocess,shutil,os,sys
w=Path('work/character-finish32/native');merged=w/'merged';target=Path('GolfArcade/Unity/CharacterAssets');backup=w/'pre-adoption';backup.mkdir(exist_ok=True)
for stem in sys.argv[1:]:
 report=json.loads((merged/(stem+'-merge-proof.json')).read_text());manifest=target/(stem+'.json');assert hashlib.sha256(manifest.read_bytes()).hexdigest()==report['sourceManifestSha256'],'Native manifest changed since garment merge; rebase required'
 names=[stem,stem+'_Rig']+json.loads(manifest.read_text())['swingFrames']
 for n in names:
  check=merged/'raw'/('current-'+n+'.bin');subprocess.run([str(w.resolve()/'cloth-codec'),'decode',str(target/(n+'.lzfse')),str(check)],check=True);assert check.read_bytes()==(merged/'raw'/('old-'+n+'.bin')).read_bytes(),'Native bytes changed since garment merge: '+n
 for name in [n+'.lzfse' for n in names]+[stem+'.json']:
  assert not (backup/name).exists(),'Backup already exists; do not overwrite'
  shutil.copy2(target/name,backup/name)
 for name in [n+'.lzfse' for n in names]+[stem+'.json']:
  temporary=target/(name+'.cloth-tmp');shutil.copy2(merged/name,temporary);os.replace(temporary,target/name)
 print('Adopted garment-only package',stem,flush=True)
