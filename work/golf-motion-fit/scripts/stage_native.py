"""Stage optional v3 assets and code into the isolated iOS project only."""
from pathlib import Path
import hashlib,re,shutil,subprocess
W=Path(__file__).resolve().parents[1];R=W.parents[1];I=W/'isolation';A=I/'GolfArcade/Unity/CharacterAssets';A.mkdir(parents=True,exist_ok=True)
for src in (W/'candidate/GolfArcade/Unity').glob('*.swift'):shutil.copy2(src,I/'GolfArcade/Unity'/src.name)
for name in ['LockerCatalog.swift','MatchHeroSurfaces.swift']:
 shutil.copy2(R/'GolfArcade/Unity'/name,I/'GolfArcade/Unity'/name)
(I/'GolfArcadeTests/LockerTests.swift').write_text((R/'GolfArcadeTests/LockerTests.swift').read_text()+(W/'candidate/GolfArcadeTests/GolfMotionRuntimeTests.fragment.swift').read_text())
raw=list((W/'native').glob('*.bin'))+list((W/'native/GolfAnimations').glob('*.bin'))
for i in range(0,len(raw),16):subprocess.run([str(W/'work/compress')]+[str(x) for x in raw[i:i+16]],check=True)
for src in (W/'native').iterdir():
 if src.is_file() and src.suffix in ['.json','.lzfse','.ktx']:shutil.copy2(src,A/src.name)
folder=A/'GolfAnimations';folder.mkdir(exist_ok=True)
for src in (W/'native/GolfAnimations').iterdir():
 if src.suffix in ['.lzfse','.json']:shutil.copy2(src,folder/src.name)
p=I/'GolfArcade.xcodeproj/project.pbxproj';s=(R/'GolfArcade.xcodeproj/project.pbxproj').read_text();files=[x.name for x in (W/'native').glob('*.ktx')]+['GolfAnimations']
for name in files:
 if re.search(r'path = '+re.escape(name)+r';',s):continue
 fid=hashlib.sha1(('golf-motion-ref:'+name).encode()).hexdigest()[:24].upper();bid=hashlib.sha1(('golf-motion-build:'+name).encode()).hexdigest()[:24].upper();typ='folder' if name=='GolfAnimations' else 'file'
 s=s.replace('/* End PBXBuildFile section */',f'\t\t{bid} /* {name} in Resources */ = {{isa = PBXBuildFile; fileRef = {fid} /* {name} */; }};\n/* End PBXBuildFile section */')
 s=s.replace('/* End PBXFileReference section */',f'\t\t{fid} /* {name} */ = {{isa = PBXFileReference; lastKnownFileType = {typ}; path = {name}; sourceTree = "<group>"; }};\n/* End PBXFileReference section */')
 end=s.index('path = CharacterAssets;');start=s.rfind('children = (',0,end)+len('children = (');s=s[:start]+f'\n\t\t\t\t{fid} /* {name} */,'+s[start:]
 start=s.index('files = (',s.index('/* Begin PBXResourcesBuildPhase section */'))+len('files = (');s=s[:start]+f'\n\t\t\t\t{bid} /* {name} in Resources */,'+s[start:]
p.write_text(s);(W/'candidate/GolfArcade.xcodeproj').mkdir(exist_ok=True);shutil.copy2(p,W/'candidate/GolfArcade.xcodeproj/project.pbxproj')
print('NATIVE_ISOLATION_STAGED',len(raw),'lazy animation/rig buffers')
