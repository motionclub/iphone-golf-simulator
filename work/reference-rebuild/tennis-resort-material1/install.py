from pathlib import Path
import hashlib,json,shutil,uuid
root=Path.cwd();stage=root/'work/reference-rebuild/tennis-resort-material1'
man=json.loads((stage/'manifest.json').read_text())
for rel,digest in man['baseline'].items():
 actual=hashlib.sha256((root/rel).read_bytes()).hexdigest()
 if actual!=digest:raise RuntimeError('Baseline changed; inspect before install: '+rel)
for rel in man['newFiles']:
 if(root/rel).exists():raise RuntimeError('New file exists; inspect before install: '+rel)
paths=list(man['baseline'])+man['newFiles']
for rel in paths:
 dst=root/rel
 if dst.exists():
  old=stage/'baseline'/rel;old.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(dst,old)
 dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(stage/rel,dst)
for rel in man['newFiles']:
 (root/(rel+'.meta')).write_text('fileFormatVersion: 2\nguid: '+uuid.uuid4().hex+'\n')
man['installed']={rel:hashlib.sha256((root/rel).read_bytes()).hexdigest() for rel in paths}
man['status']='installed stable candidate; root compilation and matched visual gate PENDING'
(stage/'manifest.json').write_text(json.dumps(man,indent=2)+'\n')
print('Installed six sources; root compile/art gate pending, renderer/geometry/shared lights unchanged.')
