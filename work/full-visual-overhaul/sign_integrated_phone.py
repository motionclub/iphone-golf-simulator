"""Sign a local integrated build with the existing paired-device profile."""
import argparse
import datetime as dt
import hashlib
import pathlib
import plistlib
import shutil
import subprocess

p = argparse.ArgumentParser()
p.add_argument('--app', type=pathlib.Path, required=True)
p.add_argument('--profile', type=pathlib.Path, required=True)
p.add_argument('--work', type=pathlib.Path, required=True)
a = p.parse_args()
if not a.app.is_dir():
    raise SystemExit('Integrated application is missing.')
a.work.mkdir(parents=True, exist_ok=True)
profile_bytes = subprocess.check_output(['security', 'cms', '-D', '-i', str(a.profile)])
profile = plistlib.loads(profile_bytes)
if profile['ExpirationDate'].replace(tzinfo=dt.timezone.utc) <= dt.datetime.now(dt.timezone.utc):
    raise SystemExit('Existing local development profile has expired.')
info = plistlib.loads((a.app / 'Info.plist').read_bytes())
bundle = info['CFBundleIdentifier']
expected = profile['Entitlements']['application-identifier']
if expected.split('.', 1)[1] != bundle:
    raise SystemExit('Profile does not authorize the integrated app bundle.')
identities = subprocess.check_output(['security', 'find-identity', '-v', '-p', 'codesigning'], text=True)
certificate = next((hashlib.sha1(c).hexdigest().upper() for c in profile['DeveloperCertificates']
                    if hashlib.sha1(c).hexdigest().upper() in identities), None)
if certificate is None:
    raise SystemExit('No local signing identity matches the existing profile.')
shutil.copy2(a.profile, a.app / 'embedded.mobileprovision')
entitlements = a.work / 'phone-entitlements.plist'
app_entitlements = dict(profile['Entitlements'])
# Profile wildcards authorize groups; a signed app uses its concrete group (Apple TN2415).
groups = app_entitlements.get('keychain-access-groups', [])
app_entitlements['keychain-access-groups'] = [
    expected if group == expected.split('.', 1)[0] + '.*' else group for group in groups]
if any('*' in group for group in app_entitlements['keychain-access-groups']):
    raise SystemExit('Unsupported wildcard keychain group requires explicit entitlement resolution.')
entitlements.write_bytes(plistlib.dumps(app_entitlements))
for path in sorted(a.app.rglob('*.dylib'), key=lambda path: len(path.parts), reverse=True):
    subprocess.run(['codesign', '--force', '--sign', certificate, str(path)], check=True)
for path in sorted(a.app.rglob('*.framework'), key=lambda path: len(path.parts), reverse=True):
    subprocess.run(['codesign', '--force', '--sign', certificate, str(path)], check=True)
subprocess.run(['codesign', '--force', '--sign', certificate, '--entitlements', str(entitlements),
                '--generate-entitlement-der', str(a.app)], check=True)
subprocess.run(['codesign', '--verify', '--deep', '--strict', '--verbose=2', str(a.app)], check=True)
print('Signed local app: ' + str(a.app), flush=True)
print('Profile expires: ' + str(profile['ExpirationDate']) + ' UTC', flush=True)
