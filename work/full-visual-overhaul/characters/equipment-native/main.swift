import Foundation
import SceneKit
import AppKit
import Metal
import simd
let repo = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
@MainActor func run() {
    let out = repo + "/proof/full-visual-overhaul/characters/native-equipment"
    try! FileManager.default.createDirectory(atPath: out, withIntermediateDirectories: true)
    NativeGolfEquipment.locate = { n,e in URL(fileURLWithPath:repo+"/GolfArcade/Unity/CharacterAssets/"+n+"."+e) }
    guard let device = MTLCreateSystemDefaultDevice() else { fatalError("No Metal device") }
    let environment = NSImage(size: NSSize(width:512,height:256)); environment.lockFocus()
    NSGradient(colors:[NSColor(calibratedWhite:0.25,alpha:1),NSColor(calibratedWhite:0.9,alpha:1),NSColor(calibratedWhite:0.65,alpha:1)])!.draw(in:NSRect(x:0,y:0,width:512,height:256),angle:90)
    environment.unlockFocus()
    for id in ["Driver","Iron","Wedge","Putter"] {
        guard let asset = NativeGolfEquipment.asset(id), let club = NativeGolfEquipment.make(id) else { fatalError("Bad asset " + id) }
        let scene = SCNScene(); scene.background.contents = NSColor(calibratedWhite:0.91,alpha:1)
        scene.lightingEnvironment.contents = environment; scene.lightingEnvironment.intensity = 1
        club.position.y = 1.12; club.eulerAngles.y = -0.25; scene.rootNode.addChildNode(club)
        let floor = SCNNode(geometry:SCNFloor()); let fm=SCNMaterial();fm.diffuse.contents=NSColor(calibratedWhite:0.91,alpha:1);fm.lightingModel = .physicallyBased;fm.roughness.contents=1;floor.geometry!.materials=[fm];scene.rootNode.addChildNode(floor)
        for (pos,intensity) in [(SCNVector3(-2,3,4),1200.0),(SCNVector3(2,2,2),750.0),(SCNVector3(1,3,-3),700.0)] {
            let n=SCNNode();n.light=SCNLight();n.light!.type = .directional;n.light!.intensity=intensity;n.position=pos;n.look(at:SCNVector3(0,0.5,0));scene.rootNode.addChildNode(n)
        }
        let camera = SCNNode();camera.camera=SCNCamera();camera.camera!.fieldOfView=30;camera.camera!.zNear=0.005;scene.rootNode.addChildNode(camera)
        let renderer = SCNRenderer(device:device,options:nil);renderer.scene=scene;renderer.pointOfView=camera
        for detail in [false,true] {
            if detail {let h=CGFloat(asset.soleY+1.15); camera.position=SCNVector3(0.15,h + 0.10,0.45);camera.look(at:SCNVector3(0.04,h,0))}
            else {camera.position=SCNVector3(0.22,0.6,2.6);camera.look(at:SCNVector3(0.03,0.61,0))}
            let shot = renderer.snapshot(atTime:1,with:CGSize(width:700,height:900),antialiasingMode:.multisampling4X)
            let rep=NSBitmapImageRep(data:shot.tiffRepresentation!)!
            try! rep.representation(using:.png,properties:[:])!.write(to:URL(fileURLWithPath:out+"/"+id+(detail ? "-head":"-full")+".png"))
        }
    }
    print("NATIVE_GOLF_EQUIPMENT_PROOF " + out)
}
MainActor.assumeIsolated { run() }
