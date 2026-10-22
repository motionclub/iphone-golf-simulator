from pathlib import Path
import plistlib,subprocess,json,hashlib
folder=Path(__file__).resolve().parent
archive=folder/'MotionClub-online-0.1.2-5-f24cfcb0fe.xcarchive'
r=folder.parent/'phone-build-20261014/root'
info=plistlib.loads((archive/'Info.plist').read_bytes())
app=archive/'Products'/info['ApplicationProperties']['ApplicationPath']
p=plistlib.loads((app/'Info.plist').read_bytes())
assert p['CFBundleIdentifier']=='com.adnanandrew.motionsports',p
assert p['CFBundleShortVersionString']=='0.1.2',p
assert p['CFBundleVersion']=='5',p
ent=subprocess.run(['codesign','-d','--entitlements','-','--xml',str(app)],capture_output=True,check=True).stdout
e=plistlib.loads(ent);assert e['com.apple.developer.game-center'] is True,e
subprocess.run(['codesign','--verify','--deep','--strict',str(app)],capture_output=True,check=True)
binary=app/p['CFBundleExecutable'];strings=subprocess.check_output(['strings',str(binary)],text=True)
markers=['Join my Motion Club lobby','Single-player is locked while friends are in your lobby','Choose a map, then start','Game Center connected']
for marker in markers:assert marker in strings,marker
unity=app/'Frameworks/UnityFramework.framework/UnityFramework'
uuid=subprocess.check_output(['xcrun','dwarfdump','--uuid',str(unity)],text=True).split()[1]
dsym=archive/'dSYMs/UnityFramework.framework.dSYM'
assert uuid in subprocess.check_output(['xcrun','dwarfdump','--uuid',str(dsym)],text=True)
manifest=folder/'build-provenance.json';d=json.loads(manifest.read_text())
for path,digest in d['source_sha256'].items():assert hashlib.sha256((r/path).read_bytes()).hexdigest()==digest,path
d.update(archive_succeeded=True,archive_path=str(archive),game_center_entitlement=True,signature_verified=True,online_binary_markers_verified=markers,unity_dsym_uuid=uuid,app_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),temporary_build_recovery='Removed redundant Unity object cache after static-library link; retained matching complete dSYM; restored generated project after archive.')
manifest.write_text(json.dumps(d,indent=2)+'\n')
(folder/'signed-entitlements.plist').write_bytes(ent)
print(json.dumps({k:v for k,v in d.items() if k!='source_sha256'},indent=2))
