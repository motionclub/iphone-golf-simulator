"""Switch only explicit female candidate paths in the disposable Unity clone."""
from pathlib import Path
import sys,shutil,json
root=Path(__file__).resolve().parent;repo=root.parent.parent;clone=Path('/private/tmp/female-soulful-UnityClone');snap=root/'candidate-snapshot'
if (root/'IMPLEMENTATION_MANIFEST.json').exists():
 raise RuntimeError('Production now contains the implementation. Use proof/before-final as the historical baseline; do not label current production as BEFORE.')
code=['Scripts/Tennis/'+n+'.cs' for n in ['HeroShoulderDeformation','HeroShoulderWeights','HeroOriginalSeamAnatomy']]
assets=['Characters/KitsV2/'+hero+'/'+piece+'.asset' for hero in ['MatchHero_Female','GolfKitHero_Female'] for piece in ['Kit_Top','Kit_Bottom']]
assets+=['Resources/Tennis/Customization/'+p+'.prefab' for p in ['PlayerFemale','PlayerFemaleGolfKit']]
for sport in ['Tennis','Golf']:
 folder=repo/'Unity/Assets/Resources'/sport/'KitsV2/Female'
 assets += [str(p.relative_to(repo/'Unity/Assets'))for p in folder.iterdir()if any('_'+tag+'_' in p.name for tag in ['Top','Bottom']) and not p.name.endswith('.meta')]
paths=code+assets
if sys.argv[1]=='baseline':
 for p in paths:
  dst=snap/p;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(clone/'Assets'/p,dst);shutil.copy2(repo/'Unity/Assets'/p,clone/'Assets'/p)
 (snap/'paths.json').write_text(json.dumps(paths,indent=2))
elif sys.argv[1]=='restore':
 for p in json.loads((snap/'paths.json').read_text()):
  if p in paths:shutil.copy2(snap/p,clone/'Assets'/p)
print(sys.argv[1],len(paths),'scoped files')
