import Foundation
import SceneKit
import AppKit
import Metal
import simd

let repo = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
@MainActor func run() {
    let before = CommandLine.arguments.contains("--before-lights")
    let forcedBlink:Float=CommandLine.arguments.contains("--blink") ? 1:0
    let out = repo + "/proof/full-visual-overhaul/characters/native/" + (forcedBlink > 0 ? "blink" : before ? "before-fill" : "after-fill")
    try! FileManager.default.createDirectory(atPath: out, withIntermediateDirectories: true)
    MatchHeroData.locate = { name, ext in
        let u=URL(fileURLWithPath:repo+"/GolfArcade/Unity/CharacterAssets/"+name+"."+ext)
        return FileManager.default.fileExists(atPath:u.path) ? u : nil
    }
    guard let device=MTLCreateSystemDefaultDevice() else { fatalError("No Metal device") }
    func rgb(_ hex:String)->SIMD3<Float>{let n=UInt32(hex,radix:16)!;return SIMD3(Float((n>>16)&255)/255,Float((n>>8)&255)/255,Float(n&255)/255)}
    for female in [false,true] {
        guard let asset=MatchHeroData.asset(female:female) else{fatalError("Missing production character")}
        for (tone,hex) in [("light","F3C9A6"),("medium","C47A4C"),("deep","603924")] {
            let scene=SCNScene();scene.background.contents=NSColor(calibratedRed:0.91,green:0.89,blue:0.84,alpha:1)
            let camera=SCNNode();camera.camera=SCNCamera();camera.camera!.fieldOfView=32;camera.camera!.zNear=0.05
            let h=CGFloat(asset.manifest.headCentreY*asset.scale);camera.position=SCNVector3(0.15,h+0.045,1.18);camera.look(at:SCNVector3(0,h,0));scene.rootNode.addChildNode(camera)
            func light(_ intensity:CGFloat,_ color:NSColor,_ elevation:Float,_ azimuth:Float,_ shadow:Bool=false){
                let node=SCNNode(),l=SCNLight();l.type = .directional;l.intensity=intensity;l.color=color
                if shadow{l.castsShadow=true;l.shadowRadius=6;l.shadowSampleCount=8;l.shadowMode = .deferred;l.shadowColor=NSColor(calibratedRed:0.12,green:0.14,blue:0.24,alpha:0.35);l.orthographicScale=2.2}
                node.light=l;let e=elevation*Float.pi/180,a=azimuth*Float.pi/180
                node.position=SCNVector3(CGFloat(-sin(a)*cos(e)*6),CGFloat(sin(e)*6),CGFloat(cos(a)*cos(e)*6));node.look(at:SCNVector3(0,0.8,0));scene.rootNode.addChildNode(node)
            }
            light(before ? 1050:1000,NSColor(calibratedRed:1,green:before ? 0.92:0.97,blue:before ? 0.82:0.92,alpha:1),40,38,true)
            light(before ? 370:620,NSColor(calibratedRed:before ? 0.84:0.95,green:before ? 0.90:0.97,blue:1,alpha:1),before ? 18:26,before ? -55:-38)
            light(before ? 520:400,NSColor(calibratedRed:1,green:0.97,blue:0.93,alpha:1),35,160)
            let ambient=SCNNode();ambient.light=SCNLight();ambient.light!.type = .ambient;ambient.light!.intensity=before ? 210:300;ambient.light!.color=NSColor(calibratedRed:0.95,green:0.97,blue:1,alpha:1);scene.rootNode.addChildNode(ambient)
            let picks=MatchHeroData.Picks(colour:{name in if name=="Skin" {return rgb(hex)};if name=="Kit_Shirt" {return rgb(female ? "C5D843":"E54D42")};return nil})
            let hero=MatchHeroData.buildHero(asset,picks:picks);hero.childNode(withName:"racket",recursively:true)?.isHidden=true;MatchHeroSurfaces.performFace(on:hero,blink:forcedBlink);scene.rootNode.addChildNode(hero)
            let renderer=SCNRenderer(device:device,options:nil);renderer.scene=scene;renderer.pointOfView=camera
            let image=renderer.snapshot(atTime:0,with:CGSize(width:800,height:900),antialiasingMode:.multisampling4X)
            guard let tiff=image.tiffRepresentation,let rep=NSBitmapImageRep(data:tiff),let png=rep.representation(using:.png,properties:[:]) else {fatalError("No PNG")}
            try! png.write(to:URL(fileURLWithPath:out+"/"+(female ? "female":"male")+"-"+tone+".png"))
        }
    }
    print("ATHLETE_NATIVE_LIGHT_PROOF "+out)
}
MainActor.assumeIsolated {run()}
