from pathlib import Path
import hashlib,json,difflib
W=Path(__file__).resolve().parents[1];P=W.parents[1];rel=Path('Unity/Assets/Scripts/Tennis/HeroTennisDriver.cs');prod=(P/rel).read_text();clone=(W/'UnityClone/Assets/Scripts/Tennis/HeroTennisDriver.cs').read_text()
def region(s):
 a=s.index('        void LockFeet(float dt)');b=s.index('        static void TwoBone(',a);return a,b
pa,pb=region(prod);ca,cb=region(clone);final=prod[:pa]+clone[ca:cb]+prod[pb:];patch=''.join(difflib.unified_diff(prod.splitlines(True),final.splitlines(True),fromfile='a/'+str(rel),tofile='b/'+str(rel),n=3));(W/'r3/LOCKFEET.patch').write_text(patch);(W/'r3/LockFeet_staged.cs.txt').write_text(clone[ca:cb]);report={'production_sha':hashlib.sha256(prod.encode()).hexdigest(),'result_sha':hashlib.sha256(final.encode()).hexdigest(),'source_method_sha':hashlib.sha256(clone[ca:cb].encode()).hexdigest(),'onlyOwnedMethod':True,'crossfadeChanged':False}
# The integration copies must equal the frozen input after removing our method.
base=(W/'r3/28b_INPUT_DRIVER.cs').read_text();ba,bb=region(base)
for name in ['Integration28bInputClone','PhaseProofClone']:
 s=(W/name/'Assets/Scripts/Tennis/HeroTennisDriver.cs').read_text();a,b=region(s);restored=s[:a]+base[ba:bb]+s[b:];report[name]={'foreignInputUntouched':restored==base,'ownMethodIdentical':s[a:b]==clone[ca:cb]};assert all(report[name].values())
(W/'r3/PATCH_INPUT.json').write_text(json.dumps(report,indent=2));print(report)
