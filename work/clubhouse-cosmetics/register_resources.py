"""Register offline cosmetic resources in both existing Xcode projects (no source regrouping)."""
from pathlib import Path
import hashlib,re
R=Path(__file__).resolve().parents[2]
files=sorted(p.name for p in (R/'GolfArcade/Unity/CharacterAssets').iterdir() if p.name.startswith(('NativeGolfEquipment_hockey_','NativeGolfEquipment_slugger_','NativeGolfEquipment_balloon_','NativeGolfEquipment_candy_','Cosmetic_','ball_')))
for project in ['GolfArcade','GolfArcadeUnity']:
 p=R/f'{project}.xcodeproj/project.pbxproj';s=p.read_text()
 builds=[];refs=[];children=[];resources=[]
 for name in files:
  if f'path = {name};' in s:continue
  fid=hashlib.sha256((project+'ref'+name).encode()).hexdigest()[:24].upper();bid=hashlib.sha256((project+'build'+name).encode()).hexdigest()[:24].upper()
  builds.append(f'\t\t{bid} /* {name} in Resources */ = {{isa = PBXBuildFile; fileRef = {fid} /* {name} */; }};')
  refs.append(f'\t\t{fid} /* {name} */ = {{isa = PBXFileReference; lastKnownFileType = {"image.png" if name.endswith("png") else "text.json"}; path = {name}; sourceTree = "<group>"; }};')
  children.append(f'\t\t\t\t{fid} /* {name} */,');resources.append(f'\t\t\t\t{bid} /* {name} in Resources */,')
 s=s.replace('/* End PBXBuildFile section */','\n'.join(builds)+'\n/* End PBXBuildFile section */')
 s=s.replace('/* End PBXFileReference section */','\n'.join(refs)+'\n/* End PBXFileReference section */')
 # CharacterAssets group's children end immediately before its path.
 marker='\t\t\t);\n\t\t\tpath = CharacterAssets;';assert marker in s
 s=s.replace(marker,'\n'.join(children)+'\n'+marker)
 # Insert into the app phase containing an existing NativeGolfEquipment resource.
 s=re.sub(r'(\t{4}[A-F0-9]+ /\* NativeGolfEquipment_Iron.json in Resources \*/,)',lambda m:m[0]+'\n'+'\n'.join(resources),s)
 p.write_text(s)
print('Registered',len(files),'resources in both projects')
