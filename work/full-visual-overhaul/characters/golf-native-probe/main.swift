import Foundation
import SceneKit
import AppKit
import Metal
import simd
let repo="/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
@MainActor func run(){
 let output=repo+"/proof/full-visual-overhaul/characters/native-golf-bind-probe";try! FileManager.default.createDirectory(atPath:output,withIntermediateDirectories:true)
 MatchHeroData.locate={n,e in let u=URL(fileURLWithPath:repo+"/GolfArcade/Unity/CharacterAssets/"+n+"."+e);return FileManager.default.fileExists(atPath:u.path) ? u:nil}
 let device=MTLCreateSystemDefaultDevice()!
 for female in [false,true]{
  let asset=MatchHeroData.asset(female:female,golf:true)!,data=asset.rig()!
  var maxSum:Float=0
  for clip in data.clips.values{for tracks in clip.morphSamples.values{for f in 0..<clip.frames{maxSum=max(maxSum,tracks.values[(f*tracks.count)..<((f+1)*tracks.count)].reduce(0,+))}}}
  print("ACTUAL_CLIP_MAX_MORPH_SUM",female,maxSum)
  for (mode,clipId,fraction) in [("productionReady","ready",0.25),("productionDrive","golfDrive",0.34),("productionIron","golfIron",0.25),("productionChip","golfChip",0.5),("productionPutt","golfPutt",0.5),("productionBlink","ready",0.0)]{
   let scene=SCNScene();scene.background.contents=NSColor(calibratedWhite:0.9,alpha:1)
   let hero=MatchHeroData.buildHero(asset,picks:MatchHeroData.Picks(colour:{_ in nil}));scene.rootNode.addChildNode(hero)
   let rig=HeroRig(root:hero,asset:asset)!;rig.attach();let clip=data.clips[clipId]!,t=clip.length*fraction
   rig.apply(clip.pose(at:t,loop:false));rig.data.applyMorphWeights(clip.morphWeights(at:t,loop:false),to:hero)
   MatchHeroSurfaces.performFace(on:hero,blink:mode=="productionBlink" ? 1:0)
   let camera=SCNNode();camera.camera=SCNCamera();camera.camera!.usesOrthographicProjection=true;camera.camera!.orthographicScale=0.83;camera.camera!.zNear=0.01;camera.camera!.zFar=100;camera.position=SCNVector3(0,0.74,3);camera.look(at:SCNVector3(0,0.74,0));scene.rootNode.addChildNode(camera)
   let key=SCNNode();key.light=SCNLight();key.light!.type = .directional;key.light!.intensity=900;key.eulerAngles=SCNVector3(-0.6,-0.6,0);scene.rootNode.addChildNode(key);let ambient=SCNNode();ambient.light=SCNLight();ambient.light!.type = .ambient;ambient.light!.intensity=400;scene.rootNode.addChildNode(ambient)
   let renderer=SCNRenderer(device:device,options:nil);renderer.scene=scene;renderer.pointOfView=camera
   let image=renderer.snapshot(atTime:0.5,with:CGSize(width:700,height:900),antialiasingMode:.multisampling4X);let rep=NSBitmapImageRep(data:image.tiffRepresentation!)!;try! rep.representation(using:.png,properties:[:])!.write(to:URL(fileURLWithPath:output+"/"+(female ? "Female":"Male")+"_"+mode+".png"))
   print("RENDERED_PRODUCTION",female,mode,"bones",rig.data.boneCount,"morphTargets",rig.data.skinned.map{$0.morphTargets.count}.reduce(0,+))
  }
 }
 print("GOLF_NATIVE_BIND_PROBE_COMPLETE",output)
}
MainActor.assumeIsolated{run()}
