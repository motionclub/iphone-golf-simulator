from pathlib import Path
import json,hashlib
root=Path('Unity/Assets');mirror=Path('work/character-finish32/review-project/Unity/Assets');w=Path('work/character-female33');files=['Scripts/Tennis/MatchHeroLook.cs','Scripts/Tennis/HeroGarmentTailoring.cs','Scripts/Tennis/HeroGarmentLOD.cs','Scripts/Tennis/HeroTennisDriver.cs','Scripts/Tennis/TailoredPoloDeformation.cs','Editor/MatchHeroLockerExport.cs','Editor/TailoredPoloAssetBake.cs','Resources/Tennis/GarmentCoverage/Tennis_Male.json','Resources/Tennis/GarmentCoverage/Tennis_Female.json']
for stem in ['Male','MaleDistance','Female','FemaleDistance','FemaleSkirt','FemaleSkirtDistance']:files.append('Resources/Tennis/KitsTailored/'+stem+'.fbx')
for sex in ['Male','Female']:
 for suffix in ['Full','Distance']:
  for ending in ['.asset','Controls.json']:files.append('Resources/Tennis/KitsTailored/'+sex+'Polo'+suffix+ending)
files += [name+'.meta' for name in list(files) if (mirror/(name+'.meta')).exists()]
rows=[{'path':name,'beforeSha256':hashlib.sha256((root/name).read_bytes()).hexdigest() if (root/name).exists() else None} for name in files];(w/'adoption-inputs.json').write_text(json.dumps(rows,indent=2));print('Prepared guarded clothing adoption for',len(rows),'files')
