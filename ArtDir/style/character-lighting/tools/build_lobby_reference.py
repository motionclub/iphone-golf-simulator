"""Compile a scratch SceneKit comparison using the app's renderer and §15 rig.
Input is hero-colours.tsv from the Unity capture; no application files are edited.
"""
from pathlib import Path
import sys,subprocess,json
repo=Path(__file__).resolve().parents[4];work=Path(sys.argv[1]);work.mkdir(parents=True,exist_ok=True)
rows={}
for line in Path(sys.argv[2]).read_text().splitlines():
 a=line.split('\t');name=a[0].split('__')[0]
 if name.startswith(('MatchHero','GolfKitHero')):rows.setdefault(name,[float(x) for x in a[1:]])
(work/'colours.json').write_text(json.dumps(rows))
base=(repo/'work/lobby-parity/harness/main.swift').read_text();base=base[:base.index('@MainActor\nfunc run()')]
body=r'''
@MainActor func run() {
 let out=CommandLine.arguments[1];try? FileManager.default.createDirectory(atPath:out,withIntermediateDirectories:true)
 let input=try! Data(contentsOf:URL(fileURLWithPath:CommandLine.arguments[2]));let rows=try! JSONDecoder().decode([String:[Float]].self,from:input)
 MatchHeroData.locate={name,ext in let u=URL(fileURLWithPath:assetsDir+"/"+name+"."+ext);return FileManager.default.fileExists(atPath:u.path) ? u:nil}
 let device=MTLCreateSystemDefaultDevice()!
 for (id,c) in rows.sorted(by:{$0.key<$1.key}) {
  let female=id.contains("Female"),golf=id.contains("GolfKit")
  guard let asset=MatchHeroData.asset(female:female,golf:golf) else { fatalError("Missing "+id) }
  let picks=MatchHeroData.Picks(colour:{name in if name=="Skin" {return SIMD3(c[0],c[1],c[2])};if name=="Kit_Shirt" {return SIMD3(c[3],c[4],c[5])};return nil})
  for framing in ["body","head"] {
   let st=Stage(cameraDistance:3.25);st.frame(framing,cameraDistance:3.25,headCentre:asset.manifest.headCentreY*asset.scale)
   let hero=MatchHeroData.buildHero(asset,picks:picks);st.character.addChildNode(hero);if let rig=HeroRig(root:hero,asset:asset){rig.attach()}
   png(st.snapshot(CGSize(width:720,height:1000),device:device),out+"/"+id+"_"+framing+".png")
   st.scene.background.contents=NSColor.black
   hero.enumerateChildNodes{node,_ in guard let geo=node.geometry else{return};geo.materials=geo.materials.map{src in let m=SCNMaterial();m.lightingModel = .constant;m.isDoubleSided=true;let name=src.name ?? "";m.diffuse.contents=name=="Skin" ? NSColor.red : name=="Kit_Shirt" ? NSColor.green : NSColor.blue;return m}}
   png(st.snapshot(CGSize(width:720,height:1000),device:device),out+"/"+id+"_"+framing+".mask.png")
  }
 }
}
MainActor.assumeIsolated { run() }
'''
(work/'main.swift').write_text(base+body)
subprocess.run(['swiftc','-swift-version','6','-O','-module-cache-path',str(work/'cache'),str(work/'main.swift'),*[str(repo/'GolfArcade/Unity'/n) for n in ['MatchHeroData.swift','MatchHeroSurfaces.swift','MatchHeroMotion.swift']],'-framework','SceneKit','-framework','AppKit','-framework','Metal','-o',str(work/'capture')],check=True)
print(work/'capture')
