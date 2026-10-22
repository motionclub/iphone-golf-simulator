#!/usr/bin/env python3
"""Prepare a faithful device build sandbox. Does not export/build/launch anything."""
import argparse, hashlib, json, os, shutil
from pathlib import Path

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--export',type=Path);a=p.parse_args();root=a.root.resolve();v3=root/'work/postcard-look/v3';device=v3/'ios/device';export=(a.export or v3/'ios/export').resolve()
if not export.is_relative_to(v3):raise SystemExit('Export must be physical scratch beneath v3')
script=root/'Unity/Tools/build-integrated-ios.sh';target=device/'Unity/Tools/build-integrated-ios.sh';target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(script,target)
base=(root/'project.yml').read_text()
for old in ('      - path: GolfArcade\n','      - path: GolfArcadeTests\n','      - path: GolfArcadeUITests\n'):
 name=old.split(': ',1)[1].strip();new='      - path: '+json.dumps(str(root/name))+'\n'
 if base.count(old)!=1:raise SystemExit('Source specification changed; review instead of guessing '+name)
 base=base.replace(old,new)
for key,path in [('CODE_SIGN_ENTITLEMENTS','GolfArcade/Multiplayer/GolfArcade.entitlements'),('INFOPLIST_FILE','GolfArcade/Unity/SportsInfo.plist'),('SWIFT_OBJC_BRIDGING_HEADER','GolfArcade/Unity/GolfArcade-Bridging-Header.h')]:
 old=f'        {key}: {path}\n'
 if base.count(old)!=1:raise SystemExit('Native path setting changed: '+key)
 base=base.replace(old,f'        {key}: '+json.dumps(str(root/path))+'\n')
(device/'project.yml').write_text(base)
# The overlay is byte identical. Its existing relative Unity paths resolve through
# a scratch-only link to the exact current export, never the stale installed export.
shutil.copy2(root/'project-unity.yml',device/'project-unity.yml')
link=device/'Unity/Builds/iOS';link.parent.mkdir(parents=True,exist_ok=True)
if os.path.lexists(link):
 if not link.is_symlink() or link.resolve()!=export:raise SystemExit('Refusing to replace existing different export link')
else:link.symlink_to(export,target_is_directory=True)
manifest={'status':'PREPARED_NOT_BUILT','sourceScript':str(script),'invokedScript':str(target),'sourceSha256':sha(script),'copySha256':sha(target),'scriptsByteIdentical':script.read_bytes()==target.read_bytes(),'actualCurrentExport':str(export),'exportLink':str(link),'projectOverlayByteIdentical':(root/'project-unity.yml').read_bytes()==(device/'project-unity.yml').read_bytes(),'sourceProjectSha256':sha(root/'project.yml'),'adaptedProjectSha256':sha(device/'project.yml'),'adaptation':'Native source/plist/bridging-header/entitlement paths absolute; original values and dependencies unchanged. Overlay and invoked shell script byte-identical. Generated Xcode project and DerivedData remain under v3.'}
(device/'build_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(manifest,indent=2))
