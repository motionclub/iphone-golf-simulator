from pathlib import Path
import hashlib,json,re,shutil,subprocess,difflib
W=Path(__file__).resolve().parents[1];R=W.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
names=sorted(p.name for p in (W/'locker/assets').glob('*.ktx'))
assert len(names)==25
def patch_project(text):
    assert all(n not in text for n in names),'Already patched'
    ids={n:(hashlib.sha256(('cloth29-file-'+n).encode()).hexdigest()[:24].upper(),hashlib.sha256(('cloth29-build-'+n).encode()).hexdigest()[:24].upper()) for n in names}
    builds=''.join(f'\t\t{b} /* {n} in Resources */ = {{isa = PBXBuildFile; fileRef = {f} /* {n} */; }};\n' for n,(f,b) in ids.items())
    refs=''.join(f'\t\t{f} /* {n} */ = {{isa = PBXFileReference; lastKnownFileType = file; path = {n}; sourceTree = "<group>"; }};\n' for n,(f,b) in ids.items())
    text=text.replace('/* Begin PBXBuildFile section */\n','/* Begin PBXBuildFile section */\n'+builds,1)
    text=text.replace('/* Begin PBXFileReference section */\n','/* Begin PBXFileReference section */\n'+refs,1)
    pat=r'([A-F0-9]{24} /\* CharacterAssets \*/ = \{\n\s+isa = PBXGroup;\n\s+children = \(\n)'
    text,count=re.subn(pat,lambda m:m[1]+''.join(f'\t\t\t\t{f} /* {n} */,\n' for n,(f,b) in ids.items()),text,count=1);assert count==1
    pat=r'([A-F0-9]{24} /\* Resources \*/ = \{\n\s+isa = PBXResourcesBuildPhase;\n\s+buildActionMask = \d+;\n\s+files = \(\n)(.*?)(\n\s+\);)'
    def resource(m):
        if 'MatchHero_Male.json in Resources' not in m[2]:return m[0]
        return m[1]+''.join(f'\t\t\t\t{b} /* {n} in Resources */,\n' for n,(f,b) in ids.items())+m[2]+m[3]
    text,count=re.subn(pat,resource,text,flags=re.S);assert count>=1
    assert all(text.count(n+' in Resources')==2 for n in names)
    return text
if __name__=='__main__':
    baseline=json.loads((W/'p5_preinstall.json').read_text())
    changed=[rel for rel,row in baseline.items() if sha(R/rel)!=row['sha256']]
    assert not changed,changed
    replacements={
      'GolfArcade/Unity/MatchHeroData.swift':W/'locker/src/MatchHeroData.swift',
      'Unity/Assets/Editor/MatchHeroLockerExport.cs':W/'isolation/Unity/Assets/Editor/MatchHeroLockerExport.cs'}
    surface=(W/'locker/src/MatchHeroSurfaces.swift').read_text()+'\n'+'\n'.join(l for l in (W/'locker/src/GarmentSurface.swift').read_text().splitlines() if not l.startswith('import '))+'\n'
    merged=W/'locker/MatchHeroSurfaces.integrated.swift';merged.write_text(surface)
    replacements['GolfArcade/Unity/MatchHeroSurfaces.swift']=merged
    for p in (W/'locker/assets').iterdir():
        if p.suffix in ['.json','.lzfse','.ktx'] and p.name.startswith('MatchHero_'):replacements['GolfArcade/Unity/CharacterAssets/'+p.name]=p
    installed=[]
    for rel,src in replacements.items():
        dst=R/rel
        if dst.exists() and rel not in baseline:
            raise RuntimeError('Unbacked replacement: '+rel)
        shutil.copy2(src,dst);installed.append({'path':rel,'sha256':sha(dst),'rollback':baseline.get(rel,{}).get('rollback','NEW')})
    for rel in ['GolfArcade.xcodeproj/project.pbxproj','GolfArcadeUnity.xcodeproj/project.pbxproj']:
        path=R/rel;before=path.read_text();after=patch_project(before);path.write_text(after)
        (W/'locker'/ (Path(rel).parent.name+'.cloth.patch')).write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/'+rel,tofile='b/'+rel)))
        # Preserve unrelated staged/unstaged project edits: prepare only our addition on the existing index version.
        index=subprocess.check_output(['git','show',':'+rel],cwd=R,text=True)
        target=W/'locker'/ (Path(rel).parent.name+'.index.pbxproj');target.write_text(patch_project(index))
        installed.append({'path':rel,'sha256':sha(path),'rollback':baseline[rel]['rollback'],'index_candidate':str(target)})
    (W/'locker/installed_files.json').write_text(json.dumps(installed,indent=2))
    print('Installed locker files:',len(installed))
