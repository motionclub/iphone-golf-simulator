from pathlib import Path
import shutil,uuid,json
R=Path.cwd();W=R/'work/full-visual-overhaul/tennis';S=R/'Unity/Assets/Scripts/Tennis';H=R/'Unity/Assets/Resources/Tennis/Shaders';A=R/'Unity/Assets/Resources/Tennis/Premium'
for n in ['TennisVenueArt.cs','TennisVenueBuilder.Skyscraper.cs','TennisVenueBuilder.Volcano.cs','TennisStandsCrowd.cs']:
 shutil.copyfile(W/(n+'.stage6'),S/n)
# Peer owns other portions of TennisLook; only our resort lighting strings change.
p=S/'TennisLook.cs';s=p.read_text().replace('"Course/Shaders/GolfResortSky"','"Tennis/Shaders/TennisCoastalSky"').replace('"Course/Resort/SkyCoastal"','"Course/Resort/SkyCoastalSmall"').replace('resortSky.SetFloat("_CloudCompression", .85f)','resortSky.SetFloat("_CloudCompression", 1.35f)');p.write_text(s)
for n in ['TennisWater.shader','TennisCloudAtmosphere.shader','TennisRooftopSky.shader','TennisCoastalSky.shader','TennisSpectator.shader','TennisBotanical.shader']:
 shutil.copyfile(W/(n+'.stage6'),H/n)
 if not (H/(n+'.meta')).exists():(H/(n+'.meta')).write_text('fileFormatVersion: 2\nguid: '+uuid.uuid4().hex+'\nShaderImporter:\n  externalObjects: {}\n  defaultTextures: []\n  nonModifiableTextures: []\n  userData: \n  assetBundleName: \n  assetBundleVariant: \n')
for a,b in [('TennisCoast-v3.fbx','TennisCoast.fbx'),('TennisBotanicalKit-v2.fbx','TennisBotanicalKit.fbx'),('CoastShallows-v3.png','CoastShallows.png'),('TennisSpectators.fbx','TennisSpectators.fbx')]:shutil.copyfile(W/a,A/b)
meta=(A/'TennisBotanicalKit.fbx.meta').read_text();meta=meta.replace(meta.split('guid: ')[1].split('\n')[0],uuid.uuid4().hex).replace('  importAnimation: 1','  importAnimation: 0');(A/'TennisSpectators.fbx.meta').write_text(meta)
source=Path('/Users/adnanyonathan/.codex/generated_images/01a114cb-8312-7363-a7bc-a81a6ff7ce35/exec-c5e23f4e-7ca6-4743-a8da-5a31bf4c4af8.png')
shutil.copyfile(source,A/'CloudTops.png');meta=(A/'SkyRooftop.png.meta').read_text();meta=meta.replace(meta.split('guid: ')[1].split('\n')[0],uuid.uuid4().hex);(A/'CloudTops.png.meta').write_text(meta)
(R/'proof/full-visual-overhaul/tennis/cloud-tops-provenance.json').write_text(json.dumps({'method':'GPT Image authored opaque horizontal cloud material; native imagegen tool','source':str(source),'runtime':str(A/'CloudTops.png'),'mapping':'world XZ repeating horizontal cloud sea, no panorama-to-ground projection'},indent=2)+'\n')
print('WORLD6_CROWD_INSTALLED')
