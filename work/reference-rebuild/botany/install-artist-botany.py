from pathlib import Path
import shutil,json,uuid,re,hashlib
R=Path(__file__).resolve().parents[3];S=R/'work/reference-rebuild/botany/artist3';A=R/'Unity/Assets';written=[]
def put(src,dest):
 dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest);written.append(dest)
put(S/'CoastalBotany.fbx',A/'Resources/Course/Resort/CoastalBotany.fbx')
put(S/'GolfCoastalBotany.cs',A/'Scripts/Course/GolfCoastalBotany.cs')
put(S/'GolfCoastalFoliage.shader',A/'Resources/Course/Shaders/GolfCoastalFoliage.shader')
shaderMeta=A/'Resources/Course/Shaders/GolfCoastalFoliage.shader.meta'
if not shaderMeta.exists():shaderMeta.write_text('fileFormatVersion: 2\nguid: '+uuid.uuid4().hex+'\nShaderImporter:\n  externalObjects: {}\n  defaultTextures: []\n  nonModifiableTextures: []\n  userData: \n  assetBundleName: \n  assetBundleVariant: \n')
written.append(shaderMeta)
maps=A/'Resources/Course/Resort/CoastalBotanyMaps';maps.mkdir(exist_ok=True)
folder=Path(str(maps)+'.meta')
if not folder.exists():folder.write_text('fileFormatVersion: 2\nguid: '+uuid.uuid4().hex+'\nfolderAsset: yes\nDefaultImporter:\n  externalObjects: {}\n  userData: \n  assetBundleName: \n  assetBundleVariant: \n')
for source in S.glob('maps/*_[CN].png'):
 dest=maps/source.name;put(source,dest);normal=source.stem.endswith('_N');template=(A/'Resources/Course/Resort'/('Limestone_N.png.meta' if normal else 'Limestone_C.png.meta')).read_text()
 meta=Path(str(dest)+'.meta')
 if meta.exists():guid=re.search(r'guid: (\w+)',meta.read_text()).group(1)
 else:guid=uuid.uuid4().hex
 template=re.sub(r'guid: \w+','guid: '+guid,template);template=template.replace('aniso: 8','aniso: 4');template=template.replace('maxTextureSize: 512','maxTextureSize: 2048')
 if not normal:
  template=template.replace('alphaIsTransparency: 0','alphaIsTransparency: 1').replace('mipMapsPreserveCoverage: 0','mipMapsPreserveCoverage: 1').replace('alphaTestReferenceValue: 0.5','alphaTestReferenceValue: 0.3')
 meta.write_text(template);written.append(meta)
put(S/'CoastalBotany.blend',R/'ArtDir/golf/source/CoastalBotany.blend')
put(S/'source-manifest.json',R/'ArtDir/golf/coastal-botany-source-manifest.json')
manifest={'status':'artist candidate installed, actual Unity art/material/cost pending','sourceProofs':[str(S/n) for n in ['artist-final-near.png','artist-final-far.png','artist-final-understory.png','artist-fir-branch-close.png']],'files':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in written}}
(R/'ArtDir/golf/coastal-botany-manifest.json').write_text(json.dumps(manifest,indent=2))
print('Installed artist botanical candidate. Files:',len(written),'maps:',len(list(maps.glob('*.png'))))
print('Manifest: ArtDir/golf/coastal-botany-manifest.json')
