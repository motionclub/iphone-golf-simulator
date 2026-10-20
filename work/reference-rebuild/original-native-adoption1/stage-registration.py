"""Stage exact PBX resource registrations; never mutate checked-in projects."""
from pathlib import Path
import difflib,hashlib,json,re,subprocess
TASK=Path(__file__).resolve().parent;REPO=TASK.parents[2]
LUTS=['MatchHero_OriginalEye_RelativeIris.png','MatchHero_OriginalEye_RelativeSclera.png','MatchHero_OriginalSeam_RelativeSkinPigment.png']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
rows=[];patches=[]
for project in ['GolfArcade','GolfArcadeUnity']:
 relative=project+'.xcodeproj/project.pbxproj';source=REPO/relative;text=source.read_text();old=text
 obj=json.loads(subprocess.check_output(['/usr/bin/plutil','-convert','json','-o','-',str(source)]))['objects']
 app=[o for o in obj.values() if o.get('isa')=='PBXNativeTarget' and o.get('name')=='GolfArcade'];assert len(app)==1
 phases=[i for i in app[0]['buildPhases'] if obj[i]['isa']=='PBXResourcesBuildPhase'];assert len(phases)==1;phase=phases[0]
 groups=[i for i,o in obj.items() if o.get('isa')=='PBXGroup' and o.get('path')=='CharacterAssets'];assert len(groups)==1;group=groups[0]
 refs=[];builds=[];children=[];resources=[]
 for name in LUTS:
  assert not any(o.get('path')==name for o in obj.values()),'Already registered: regenerate against new baseline'
  def uuid(kind):
   value=hashlib.sha1((project+'/OriginalSeam/'+name+'/'+kind).encode()).hexdigest()[:24].upper();assert value not in obj;return value
  ref=uuid('reference');build=uuid('build')
  refs.append(f'\t\t{ref} /* {name} */ = {{isa = PBXFileReference; lastKnownFileType = image.png; path = {name}; sourceTree = "<group>"; }};\n')
  builds.append(f'\t\t{build} /* {name} in Resources */ = {{isa = PBXBuildFile; fileRef = {ref} /* {name} */; }};\n')
  children.append(f'\t\t\t\t{ref} /* {name} */,\n');resources.append(f'\t\t\t\t{build} /* {name} in Resources */,\n')
 text=text.replace('/* End PBXBuildFile section */',''.join(builds)+'/* End PBXBuildFile section */',1)
 text=text.replace('/* End PBXFileReference section */',''.join(refs)+'/* End PBXFileReference section */',1)
 def insert(id,field,value):
  global text
  pattern=r'(\t\t'+id+r' /\* [^\n]+ \*/ = \{\n(?:(?!\t\t\};).)*?\b'+field+r' = \(\n)'
  text,count=re.subn(pattern,lambda m:m[1]+value,text,count=1,flags=re.S);assert count==1,(id,field)
 insert(group,'children',''.join(children));insert(phase,'files',''.join(resources))
 candidate=TASK/relative;candidate.parent.mkdir(parents=True,exist_ok=True);candidate.write_text(text)
 subprocess.run(['/usr/bin/plutil','-lint',str(candidate)],check=True)
 patches.extend(difflib.unified_diff(old.splitlines(True),text.splitlines(True),fromfile=relative,tofile=relative))
 rows.append({'project':project,'source_sha256':sha(source),'candidate_sha256':sha(candidate),'added_app_resources':LUTS,'app_resources_phase':phase,'character_assets_group':group})
(TASK/'resource-registration.patch').write_text(''.join(patches))
(TASK/'resource-registration.json').write_text(json.dumps({'status':'PASS staged plist syntax','projects':rows,'yaml':'project.yml recursively includes MatchHero_*; project-unity.yml inherits it; no YAML mutation required'},indent=2)+'\n')
