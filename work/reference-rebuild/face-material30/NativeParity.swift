import Foundation
import SceneKit
import simd
import AppKit
import Metal

@main @MainActor struct NativeParity {
    struct Vertex: Decodable { let index: Int; let position: [Float] }
    struct Sample: Decodable { let clip,part: String; let time,blink: Float; let vertices: [Vertex] }
    struct Proof: Decodable { let samples: [Sample] }
    static func vector(_ source: SCNGeometrySource, _ index: Int) -> SIMD3<Float> {
        source.data.withUnsafeBytes { p in let o=source.dataOffset+index*source.dataStride
            return SIMD3(p.loadUnaligned(fromByteOffset:o,as:Float.self),p.loadUnaligned(fromByteOffset:o+4,as:Float.self),p.loadUnaligned(fromByteOffset:o+8,as:Float.self)) }
    }
    static func position(_ part: RigData.Skinned, _ node: SCNNode, _ pose: [HeroTrackPose], _ index: Int) -> SIMD3<Float> {
        var bind=vector(part.geometry.sources(for:.vertex).first!,index)
        if let morph=node.morpher { for (i,target) in morph.targets.enumerated() {
            let w=Float(morph.weight(forTargetAt:i)); if w != 0 { bind += vector(target.sources(for:.vertex).first!,index)*w }
        } }
        var result=SIMD3<Float>.zero
        for k in 0..<4 {
            let w:Float=part.weights.data.withUnsafeBytes { $0.loadUnaligned(fromByteOffset:index*16+k*4,as:Float.self) }
            if w == 0 { continue }
            let b:Int=part.indices.data.withUnsafeBytes { (raw:UnsafeRawBufferPointer) in Int(raw[index*4+k]) }
            let matrix=pose[part.bones[b]].matrix*simd_float4x4(part.inverseBinds[b].scnMatrix4Value)
            let p=matrix*SIMD4(bind,1); result += SIMD3(p.x,p.y,p.z)*w
        }
        return result
    }
    static func main() throws {
        guard CommandLine.arguments.count==4 else { fatalError("NativeParity ASSET_DIR GOLDEN_DIR OUTPUT_DIR") }
        let assets=URL(fileURLWithPath:CommandLine.arguments[1]),golden=URL(fileURLWithPath:CommandLine.arguments[2]),out=URL(fileURLWithPath:CommandLine.arguments[3])
        try FileManager.default.createDirectory(at:out,withIntermediateDirectories:true)
        MatchHeroData.locate={name,ext in let u=assets.appendingPathComponent(name+"."+ext); return FileManager.default.fileExists(atPath:u.path) ? u:nil }
        var report:[[String:Any]]=[]
        let variants: [(Bool,Bool)] = ProcessInfo.processInfo.environment["NATIVE_PROOF_PRIMARY_ONLY"] == "1" ? [(false,false)] : ProcessInfo.processInfo.environment["NATIVE_PROOF_TENNIS_ONLY"] == "1" ? [(false,false),(false,true)] : [(false,false),(false,true),(true,false)]
        for (golf,distance) in variants { for female in [false,true] {
            let sex=female ? "Female":"Male"
            let name=(golf ? "GolfKitHero_":"MatchHero_")+sex+(distance ? "_Distance":"")
            guard let asset=MatchHeroData.asset(female:female,golf:golf,distance:distance),let data=asset.rig() else { fatalError("Missing staged asset/rig "+sex) }
            precondition(data.info.bones.count==(golf ? 54:53),"53 character bones + existing golf Club")
            if golf { precondition(data.info.bones.last=="Club") }
            let tone:SIMD3<Float>
            if let hex=ProcessInfo.processInfo.environment[female ? "NATIVE_PROOF_SKIN_FEMALE":"NATIVE_PROOF_SKIN_MALE"] {
                guard hex.count==6,let colour=UInt32(hex,radix:16) else {fatalError("Proof skin must be six hex digits")}
                tone=SIMD3(Float((colour>>16)&255),Float((colour>>8)&255),Float(colour&255))/255
            }else{tone=female ? SIMD3(0.9608,0.6706,0.4980):SIMD3(0.8980,0.5529,0.3922)}
            let root=MatchHeroData.buildHero(asset,picks:.init(colour:{ $0=="Skin" ? tone:nil }))
            root.eulerAngles=SCNVector3Zero;root.scale=SCNVector3(1,1,1)
            let rig=HeroRig(root:root,asset:asset)!;rig.attach()
            for name in ["Body","Face"] {
                let part=data.skinned.first(where:{$0.name==name})!
                precondition(part.morphTargets.contains(where:{$0.name=="Hero_Blink_Half"}))
                precondition(part.morphTargets.contains(where:{$0.name=="Hero_Blink"}))
            }
            precondition(root.childNode(withName:"Body",recursively:false)!.geometry!.sources(for:.texcoord).count==3,"UV0 and immutable bind xy/z")
            let proof=try JSONDecoder().decode(Proof.self,from:Data(contentsOf:golden.appendingPathComponent(name+"_blink_parity.json")))
            var worst:Float=0,checked=0
            for sample in proof.samples {
                if ProcessInfo.processInfo.environment["NATIVE_PROOF_MATERIAL_ONLY"] == "1" && !(sample.part=="Face" && sample.clip=="ready" && sample.blink==0) { continue }
                let clip=data.clips[sample.clip]!,pose=clip.pose(at:Double(sample.time),loop:false)
                rig.apply(pose);data.applyMorphWeights(clip.morphWeights(at:Double(sample.time),loop:false),to:root,includeFaceBlink:false)
                MatchHeroSurfaces.performFace(on:root,blink:sample.blink)
                let part=data.skinned.first(where:{$0.name==sample.part})!,node=root.childNode(withName:sample.part,recursively:false)!
                for v in sample.vertices { let p=position(part,node,pose,v.index);worst=max(worst,simd_distance(p,SIMD3(v.position[0],v.position[1],v.position[2])));checked += 1 }
                // Snapshot once for each pose/stage; Body and Face goldens share the pose.
                if sample.part=="Face" && (ProcessInfo.processInfo.environment["NATIVE_PROOF_QUICK"] != "1" || (sample.clip=="ready" && (sample.blink==0 || sample.blink==1))) { try snapshot(root,asset:asset,rig:rig,pose:pose,path:out.appendingPathComponent("\(name)_\(sample.clip)_t\(Int(sample.time*1000))_blink_\(Int(sample.blink*100)).png")) }
            }
            precondition(worst<0.0002,"CPU decoded morph/weights parity > .2mm")
            report.append(["manifest":name,"sex":sex,"boneCount":data.info.bones.count,"samples":checked,"maxPositionErrorMm":worst*1000,"art":"PENDING actual snapshot inspection"])
        } }
        try JSONSerialization.data(withJSONObject:report,options:[.prettyPrinted,.sortedKeys]).write(to:out.appendingPathComponent("parity.json"))
    }
    static var pinkAudit:[[String:Any]]=[]
    static func snapshot(_ root:SCNNode,asset:MatchHeroData.Asset,rig:HeroRig,pose:[HeroTrackPose],path:URL) throws {
        root.childNode(withName:MatchHeroData.racketName,recursively:false)?.isHidden=true
        let scene=SCNScene();scene.background.contents=NSColor(calibratedWhite:0.86,alpha:1);scene.rootNode.addChildNode(root)
        let body=rig.data.skinned.first(where:{$0.name=="Body"})!,look=asset.manifest.parts.first(where:{$0.name=="Body"})!.submeshes.first!.look!
        let head=rig.data.info.bones.firstIndex(of:"Head")!,local=body.bones.firstIndex(of:head)!
        func v(_ a:[Float]?)->SIMD3<Float>{let a=a!;return SIMD3(a[0],a[1],a[2])}
        let origin=v(look.headOrigin),right=v(look.headRight),up=v(look.headUp),forward=v(look.headForward),eye=v(look.headEye)
        let p=origin+right*eye.x+up*eye.y+forward*eye.z
        let transform=pose[head].matrix*simd_float4x4(body.inverseBinds[local].scnMatrix4Value)
        func mapped(_ q:SIMD3<Float>,w:Float)->SIMD3<Float>{let a=transform*SIMD4(q.x,q.y,-q.z,w);return SIMD3(a.x,a.y,a.z)}
        let u=simd_normalize(mapped(up,w:0)),f=simd_normalize(mapped(forward,w:0)),r=simd_normalize(mapped(right,w:0)),target=mapped(p,w:1)-u*0.02
        let camera=SCNNode();camera.camera=SCNCamera();camera.camera!.usesOrthographicProjection=true;camera.camera!.orthographicScale=0.23;camera.camera!.zNear=0.01;camera.camera!.zFar=10
        camera.simdPosition=target+f*0.90+u*0.01+r*0.18;camera.look(at:SCNVector3(target),up:SCNVector3(u),localFront:SCNVector3(0,0,-1));scene.rootNode.addChildNode(camera)
        func light(_ intensity:CGFloat,_ position:SIMD3<Float>,_ ambient:Bool=false) {let n=SCNNode();let l=SCNLight();l.type=ambient ? .ambient:.directional;l.intensity=intensity;l.color=NSColor.white;n.light=l;n.simdPosition=position;n.look(at:SCNVector3(target));scene.rootNode.addChildNode(n)}
        if ProcessInfo.processInfo.environment["NATIVE_PROOF_LOBBY_LIGHT"] == "1" {
            // Exact CharacterModelPreview.Coordinator light recipe, not a new lobby look.
            func stageLight(_ intensity:CGFloat,_ colour:NSColor,_ elevation:Float,_ azimuth:Float,_ shadow:Bool=false) {
                let node=SCNNode(),l=SCNLight();l.type = .directional;l.intensity=intensity;l.color=colour
                if shadow {l.castsShadow=true;l.shadowRadius=6;l.shadowSampleCount=8;l.shadowMode = .deferred;l.shadowColor=NSColor(red:0.12,green:0.14,blue:0.24,alpha:0.35);l.orthographicScale=2.2}
                node.light=l;let e=elevation*Float.pi/180,a=azimuth*Float.pi/180
                node.position=SCNVector3(-sin(a)*cos(e)*6,sin(e)*6,cos(a)*cos(e)*6)
                node.look(at:SCNVector3(0,0.8,0));scene.rootNode.addChildNode(node)
            }
            stageLight(1050,NSColor(red:1,green:0.92,blue:0.82,alpha:1),40,38,true)
            stageLight(370,NSColor(red:0.84,green:0.9,blue:1,alpha:1),18,-55)
            stageLight(520,NSColor(red:1,green:0.96,blue:0.9,alpha:1),35,160)
            let amb=SCNNode();amb.light=SCNLight();amb.light!.type = .ambient;amb.light!.intensity=210
            amb.light!.color=NSColor(red:0.86,green:0.88,blue:0.96,alpha:1);scene.rootNode.addChildNode(amb)
        } else {
            light(1100,target-r*2+u*3+f*3);light(350,target+r*3+u*1+f*2);light(300,.zero,true)
        }
        let renderer=SCNRenderer(device:MTLCreateSystemDefaultDevice(),options:nil);renderer.scene=scene;renderer.pointOfView=camera
        let image=renderer.snapshot(atTime:0,with:CGSize(width:640,height:640),antialiasingMode:.multisampling4X)
        guard let tiff=image.tiffRepresentation,let bitmap=NSBitmapImageRep(data:tiff),let png=bitmap.representation(using:.png,properties:[:]) else {fatalError("snapshot PNG")}
        try png.write(to:path);root.removeFromParentNode()
        var pink=0
        for y in 0..<bitmap.pixelsHigh { for x in 0..<bitmap.pixelsWide {
            if let c=bitmap.colorAt(x:x,y:y)?.usingColorSpace(.sRGB),c.redComponent>0.75,c.blueComponent>0.75,c.greenComponent<0.30 { pink += 1 }
        } }
        pinkAudit.append(["file":path.lastPathComponent,"magentaPixels":pink,"pass":pink<=32])
        try JSONSerialization.data(withJSONObject:pinkAudit,options:[.prettyPrinted,.sortedKeys]).write(to:path.deletingLastPathComponent().appendingPathComponent("pink-audit.json"))
        if pink>32 { throw NSError(domain:"NativeParity",code:1,userInfo:[NSLocalizedDescriptionKey:"MAGENTA_SHADER_FALLBACK: \(path.lastPathComponent) has \(pink) magenta pixels"]) }
    }
}
