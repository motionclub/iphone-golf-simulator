from pathlib import Path
import hashlib,json,shutil
R=Path(__file__).resolve().parents[3];W=R/'work/cloth-overhaul';C=W/'isolation/Unity';baseline=json.loads((W/'baseline_files.json').read_text());identity=json.loads((W/'prefab_identity_results.json').read_text())
assert all(all(v for k,v in h.items() if k!='kit_bones') and h['kit_bones']==[53] for h in identity.values())
rels=[f'Assets/Characters/MatchHeroKit/{s}_Kit.fbx' for s in ['Male','Female']]+[f'Assets/Resources/Tennis/Customization/Player{s}.prefab' for s in ['Male','Female']]
rels += [str(p.relative_to(C)) for p in (C/'Assets/Resources/Tennis/HeroDetail').glob('*') if p.name.startswith('Kit_') and ('_N.png' in p.name or '_M.png' in p.name) or p.name.startswith('Cloth_FabricAtlas.png')]
rels += [str(p.relative_to(C)) for p in (C/'Assets/Characters/MatchHeroes/Materials/Kit').glob('*.mat')]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for rel in rels:
 dst=R/'Unity'/rel;key='Unity/'+rel
 if dst.exists():
  assert key in baseline,(key,'unowned existing file')
  assert sha(dst)==baseline[key]['sha256'],(key,'changed concurrently')
rows=[]
for rel in rels:
 src=C/rel;dst=R/'Unity'/rel;key='Unity/'+rel;dst.parent.mkdir(parents=True,exist_ok=True)
 if dst.exists():
  rb=W/'rollback'/key;assert rb.exists() and sha(rb)==baseline[key]['sha256']
 else:rb=None
 shutil.copy2(src,dst);rows.append({'path':key,'sha256':sha(dst),'rollback':str(rb) if rb else 'NEW FILE — remove to roll back'})
(W/'installed_files.json').write_text(json.dumps(rows,indent=2));print('Installed',len(rows),'verified clothing-only files')
