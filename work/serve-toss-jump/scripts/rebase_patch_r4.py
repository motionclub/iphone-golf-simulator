from pathlib import Path
import difflib,json,hashlib,subprocess
W=Path(__file__).resolve().parents[1];P=W.parents[1];R=W/'r4';C=W/'UnityClone';T=R/'rebased_source'
own=[];foreign={};guards={}
for name in ['HeroTennisDriver.cs','TennisGame.cs','TennisServeRoutine.cs']:
 rel=Path('Unity/Assets/Scripts/Tennis')/name;old=(R/'production_input'/rel).read_text();ours=(C/'Assets/Scripts/Tennis'/name).read_text();current=(P/rel).read_text()
 own.extend(difflib.unified_diff(old.splitlines(True),ours.splitlines(True),fromfile='a/'+str(rel),tofile='b/'+str(rel)))
 foreign[str(rel)]=''.join(difflib.unified_diff(old.splitlines(True),current.splitlines(True),fromfile='saved-production',tofile='current-production'))
 out=T/rel;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(current);guards[str(rel)]=hashlib.sha256(current.encode()).hexdigest()
(R/'OWNED_CHANGES.patch').write_text(''.join(own))
args=['git','apply','--directory=work/serve-toss-jump/r4/rebased_source',str(R/'OWNED_CHANGES.patch')]
subprocess.run(args[:2]+['--check']+args[2:],cwd=P,check=True);subprocess.run(args,cwd=P,check=True)
final=[]
for name in ['HeroTennisDriver.cs','TennisGame.cs','TennisServeRoutine.cs']:
 rel=Path('Unity/Assets/Scripts/Tennis')/name;current=(P/rel).read_text();merged=(T/rel).read_text()
 final.extend(difflib.unified_diff(current.splitlines(True),merged.splitlines(True),fromfile='a/'+str(rel),tofile='b/'+str(rel)))
 if name=='HeroTennisDriver.cs':
  assert 'public bool HasEmote(Clip c)' in merged and 'public float EmoteDuration(Clip c)' in merged
  assert '// Celebrations are selected from the equipped controller slots.' in merged
(R/'PREVIEW.patch').write_text(''.join(final));subprocess.run(['git','apply','--check',str(R/'PREVIEW.patch')],cwd=P,check=True)
(R/'FOREIGN_PRODUCTION_EDITS.json').write_text(json.dumps({'foreign_diffs':foreign,'foreign_edits_preserved':True,'production_modified_by_this_work':False,'current_base_hashes':guards,'rebased_runtime_source':str(T)},indent=2));(R/'PRODUCTION_INPUT_FINAL.json').write_text(json.dumps(guards,indent=2))
print('Current celebration edits preserved; fresh install hunk passes git apply --check.')
