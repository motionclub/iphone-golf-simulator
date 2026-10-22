import Foundation
import SceneKit
import simd
import AppKit
import Metal

@main @MainActor struct PoloNativeProof {
    static func trace(_ s:String) { FileHandle.standardError.write(Data((s+"\n").utf8)) }
    struct Sample: Decodable { let clip,part:String; let frame:Int; let vertices:[[Float]] }
    struct Proof: Decodable { let samples:[Sample] }
    static func vectors(_ source:SCNGeometrySource)->[SIMD3<Float>] {
        source.data.withUnsafeBytes { raw in (0..<source.vectorCount).map { i in
            let offset=source.dataOffset+i*source.dataStride
            return SIMD3(raw.loadUnaligned(fromByteOffset:offset,as:Float.self),raw.loadUnaligned(fromByteOffset:offset+4,as:Float.self),raw.loadUnaligned(fromByteOffset:offset+8,as:Float.self))
        } }
    }
    static func main() throws {
        let args=CommandLine.arguments
        guard args.count==4 else {fatalError("PoloNativeProof ASSETS GOLDENS OUTPUT")}
        let assets=URL(fileURLWithPath:args[1]),goldens=URL(fileURLWithPath:args[2]),output=URL(fileURLWithPath:args[3]);try FileManager.default.createDirectory(at:output,withIntermediateDirectories:true)
        MatchHeroData.locate={name,ext in let u=assets.appendingPathComponent(name+"."+ext);return FileManager.default.fileExists(atPath:u.path) ? u:nil}
        var reports:[[String:Any]]=[]
        for distance in [false,true] {
            let name="MatchHero_Male"+(distance ? "_Distance":"")
            guard FileManager.default.fileExists(atPath:assets.appendingPathComponent(name+".json").path) else {continue}
            guard let asset=MatchHeroData.asset(female:false,distance:distance),let data=asset.rig() else {fatalError("Candidate rig missing")}
            trace("Loaded \(name) bones=\(data.info.bones.count)"); precondition(data.info.bones.count==53)
            let root=MatchHeroData.buildHero(asset,picks:.init(colour:{$0=="Skin" ? SIMD3(0.8980,0.5529,0.3922):nil}));root.eulerAngles=SCNVector3Zero;root.scale=SCNVector3(1,1,1)
            let rig=HeroRig(root:root,asset:asset)!;rig.attach()
            let part=data.skinned.first(where:{$0.name=="Kit_Top"})!,node=root.childNode(withName:"Kit_Top",recursively:false)!
            trace("Rig attached"); let bind=vectors(part.geometry.sources(for:.vertex).first!),targets=part.morphTargets.map{vectors($0.sources(for:.vertex).first!)}
            let chest=part.bones.firstIndex(where:{data.info.bones[$0]=="Chest"})!
            for i in bind.indices {
                let w:Float=part.weights.data.withUnsafeBytes{$0.loadUnaligned(fromByteOffset:i*16,as:Float.self)}
                let b:Int=part.indices.data.withUnsafeBytes{(raw:UnsafeRawBufferPointer) in Int(raw[i*4])}
                precondition(w==1 && b==chest,"The exported polo must retain its fixed Chest basis")
            }
            trace("Bindings checked, targets=\(targets.count)"); let proof=try JSONDecoder().decode(Proof.self,from:Data(contentsOf:goldens.appendingPathComponent(name+"_golden.json")))
            var worst:Float=0,checked=0,minWeight:Float=0,maxWeight:Float=0
            for sample in proof.samples where sample.part=="Kit_Top" {
                trace("Checking \(sample.clip) frame \(sample.frame)")
                let clip=data.clips[sample.clip]!,info=data.info.clips.first(where:{$0.id==sample.clip})!
                let time=Double(info.times?.count == info.frames ? info.times![sample.frame] : (Float(sample.frame)*info.length/Float(info.frames-1)))
                let pose=clip.pose(at:time,loop:false),weights=clip.morphWeights(at:time,loop:false)
                rig.apply(pose);data.applyMorphWeights(weights,to:root)
                precondition(node.morpher?.targets.count==targets.count)
                var points=bind
                for k in targets.indices {
                    let w=Float(node.morpher!.weight(forTargetAt:k));minWeight=min(minWeight,w);maxWeight=max(maxWeight,w)
                    if abs(w)<1e-9 {continue}
                    for i in points.indices {points[i]+=targets[k][i]*w}
                }
                let matrix=pose[part.bones[chest]].matrix*simd_float4x4(part.inverseBinds[chest].scnMatrix4Value)
                for v in sample.vertices {
                    let i=Int(v[0]),q=matrix*SIMD4(points[i],1),want=SIMD3(v[1],v[2],v[3]);worst=max(worst,simd_distance(SIMD3(q.x,q.y,q.z),want));checked+=1
                }
            }
            trace("Parity max=\(worst*1000)mm checked=\(checked) weights=\(minWeight)...\(maxWeight)"); precondition(worst<0.0002,"Decoded polo differs from actual Unity cloth by more than 0.2mm")
            var times:[Double]=[]
            for (id,u) in [("ready",0.0),("wave",0.43),("serve",0.57),("scuba",0.71),("pushups",0.57)] {
                let clip=data.clips[id]!,info=data.info.clips.first(where:{$0.id==id})!,time=Double(info.length)*u
                rig.apply(clip.pose(at:time,loop:false));data.applyMorphWeights(clip.morphWeights(at:time,loop:false),to:root)
                let start=CFAbsoluteTimeGetCurrent();try snapshot(root,path:output.appendingPathComponent(name+"_"+id+".png"));times.append(CFAbsoluteTimeGetCurrent()-start)
            }
            reports.append(["manifest":name,"vertices":bind.count,"shapes":targets.count,"bones":data.info.bones.count,"verticesCompared":checked,"maxPositionErrorMm":worst*1000,"minMorphWeight":minWeight,"maxMorphWeight":maxWeight,"desktopSnapshotSeconds":times,"mobilePerformance":"Not measured by this desktop proof"])
        }
        try JSONSerialization.data(withJSONObject:reports,options:[.prettyPrinted,.sortedKeys]).write(to:output.appendingPathComponent("native-polo-proof.json"))
        print("Polo native parity passed",reports)
    }
    static func snapshot(_ root:SCNNode,path:URL) throws {
        let scene=SCNScene();scene.background.contents=NSColor(calibratedWhite:0.86,alpha:1);scene.rootNode.addChildNode(root)
        let target=SCNVector3(0,0.92,0),camera=SCNNode();camera.camera=SCNCamera();camera.camera!.fieldOfView=30;camera.camera!.zNear=0.03;camera.camera!.zFar=20;camera.position=SCNVector3(-0.45,1.05,-3.5);camera.look(at:target);scene.rootNode.addChildNode(camera)
        func light(_ intensity:CGFloat,_ position:SCNVector3,_ ambient:Bool=false) {let n=SCNNode();let l=SCNLight();l.type=ambient ? .ambient:.directional;l.intensity=intensity;l.color=NSColor.white;n.light=l;n.position=position;n.look(at:target);scene.rootNode.addChildNode(n)}
        light(1100,SCNVector3(-2,4,-3));light(350,SCNVector3(3,2,-2));light(300,SCNVector3Zero,true)
        let renderer=SCNRenderer(device:MTLCreateSystemDefaultDevice(),options:nil);renderer.scene=scene;renderer.pointOfView=camera
        let image=renderer.snapshot(atTime:0,with:CGSize(width:900,height:1200),antialiasingMode:.multisampling4X)
        guard let tiff=image.tiffRepresentation,let bitmap=NSBitmapImageRep(data:tiff),let png=bitmap.representation(using:.png,properties:[:]) else {fatalError("Native snapshot failed")}
        var pink=0
        for y in 0..<bitmap.pixelsHigh {for x in 0..<bitmap.pixelsWide {if let c=bitmap.colorAt(x:x,y:y)?.usingColorSpace(.sRGB),c.redComponent>0.75,c.blueComponent>0.75,c.greenComponent<0.30 {pink+=1}}}
        precondition(pink<=32,"Native shader fallback detected")
        try png.write(to:path);root.removeFromParentNode()
    }
}
