from pathlib import Path
import hashlib,json,shutil
p=Path(__file__).parent;repo=Path(__file__).parents[4]
changed=[]
def record(relative):
 target=repo/relative;changed.append({'path':relative,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'bytes':target.stat().st_size})
def method(text,signature):
 start=text.index(signature);brace=text.index('{',start);level=1;i=brace+1
 while level:
  level += (text[i]=='{')-(text[i]=='}');i+=1
 return start,i,text[start:i]
# Mixed ownership file: merge only the two owned world functions into the latest peer source.
relative='Unity/Assets/Scripts/Tennis/TennisLook.cs';target=repo/relative;s=target.read_text();staged=(p/relative).read_text()
for name in ['public static void LightScene(Light sun)','public static void StyleArena(GameObject arena)']:
 a,b,_=method(s,name);_,_,new=method(staged,name);s=s[:a]+new+s[b:]
target.write_text(s);record(relative)
files=['Unity/Assets/Resources/Tennis/Shaders/TennisWorldSurface.shader','Unity/Assets/Resources/Tennis/Shaders/TennisCoastalSky.shader','Unity/Assets/Resources/Tennis/Shaders/TennisRooftopSky.shader','Unity/Assets/Resources/Tennis/Shaders/TennisVolcanicSky.shader','Unity/Assets/Resources/Tennis/Shaders/TennisTowerAtmosphere.shader','Unity/Assets/Scripts/Tennis/TennisVenueBuilder.Skyscraper.cs','Unity/Assets/Scripts/Tennis/TennisVenueBuilder.Volcano.cs','Unity/Assets/Editor/TennisVenueCapture.cs','Unity/Assets/Resources/Tennis/Premium/AcrylicAggregate.png','Unity/Assets/Resources/Tennis/Premium/AcrylicAggregate.png.meta']
for relative in files:
 target=repo/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p/relative,target);record(relative)
manifest={'checkpoint':'World19 material/atmosphere candidate','status':'installed; actual Unity art comparison pending','invariants':['court/net/collision geometry untouched','gameplay contacts/toss/actor transforms untouched','quality settings/cascades/shadow distance untouched','world/foliage density untouched'],'files':changed}
proof=repo/'proof/full-visual-overhaul/tennis/world19-installed-manifest.json';proof.write_text(json.dumps(manifest,indent=2)+'\n')
canonical=repo/'ArtDir/tennis/venues/materials';canonical.mkdir(parents=True,exist_ok=True)
s=(p/'build-acrylic-aggregate.py').read_text();s=s.replace("out=Path(__file__).parent/'Unity/Assets/Resources/Tennis/Premium';out.mkdir(parents=True,exist_ok=True)","import argparse\nparser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,default=Path(__file__).parents[4]/'Unity/Assets/Resources/Tennis/Premium');args=parser.parse_args()\nout=args.out;out.mkdir(parents=True,exist_ok=True)")
(canonical/'build-acrylic-aggregate.py').write_text(s)
(canonical/'README.md').write_text('''# Tennis physical surface details

AcrylicAggregate is a deterministic 512² periodic aggregate texture. RGB encodes an unpacked micro normal and alpha holds pigment-height variation; one tile spans one metre. Import as linear Default, uncompressed RGBA, repeat, mipmaps, anisotropic8. It is not a standard packed normal map because alpha is retained.

Regenerate with `python3 ArtDir/tennis/venues/materials/build-acrylic-aggregate.py` (NumPy, Pillow). Use `--out` to stage outside Assets. The shader bounds court pigment to 2.8%, uses .19 normal strength, and mipmaps integrate distant aggregate. The court's plane, height, lines and collision are unchanged.

World19 candidate adds actual imported normal-map triplanar relief to basalt, normalizes the already-charcoal albedo before modulation, preserves cloud highlights while calibrating coastal clear blue, uses only the upper sky part of SkyRooftop above the existing horizontal cloud plane, and reflects that sky on a facade alpha glazing mask. Actual capture comparison remains required.
''')
print(json.dumps({'installed':len(changed),'manifest':str(proof)},indent=2))
