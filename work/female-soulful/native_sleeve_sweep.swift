import Foundation
import SceneKit
import simd

// Compile against the actual app sources (not a second implementation):
// xcrun swiftc -module-cache-path /private/tmp/female-soulful-swift-modules \
//   -parse-as-library GolfArcade/Unity/MatchHero{Data,Surfaces,Motion}.swift \
//   work/female-soulful/native_sleeve_sweep.swift -o /private/tmp/native-sleeve-check
// Usage: native-sleeve-check <CharacterAssets folder> <small proof output folder>
// Needs the reviewed JSON + sourceToHero beside the matching rig export.
@main struct NativeSleeveCheck {
    @MainActor static func main() throws {
        guard CommandLine.arguments.count == 3 else {
            print("usage: native-sleeve-check <assets> <proof-output>"); return
        }
        let directory = URL(fileURLWithPath:CommandLine.arguments[1],isDirectory:true)
        let output = URL(fileURLWithPath:CommandLine.arguments[2],isDirectory:true)
        try FileManager.default.createDirectory(at:output,withIntermediateDirectories:true)
        MatchHeroData.locate = { name,ext in
            let url = directory.appendingPathComponent(name).appendingPathExtension(ext)
            return FileManager.default.fileExists(atPath:url.path) ? url : nil
        }
        guard let asset = MatchHeroData.asset(female:true,golf:true), let rigData = asset.rig(),
              let part = rigData.skinned.first(where:{$0.name == "Kit_Top"}) else { throw Failure.message("missing female golf export") }
        let hero = MatchHeroData.buildHero(asset,picks:MatchHeroData.Picks(colour:{_ in nil}))
        guard let top = hero.childNode(withName:"Kit_Top",recursively:false), let rig = HeroRig(root:hero,asset:asset) else { throw Failure.message("missing female golf rig") }
        let original = top.geometry!, originalMaterials = original.materials
        rig.attach()
        if ProcessInfo.processInfo.environment["SLEEVE_EXPECT_FALLBACK"] == "1" {
            guard top.skinner != nil else { throw Failure.message("incompatible/missing field unexpectedly replaced skinner") }
            var unaffected = 0
            for (female,golf) in [(false,true),(true,false),(false,false)] {
                guard let other = MatchHeroData.asset(female:female,golf:golf),
                      let otherRig = HeroRig(root:MatchHeroData.buildHero(other,picks:MatchHeroData.Picks(colour:{_ in nil})),asset:other) else { continue }
                otherRig.attach()
                guard otherRig.root.childNode(withName:"Kit_Top",recursively:false)?.skinner != nil else { throw Failure.message("unrelated hero top lost skinner") }
                unaffected += 1
            }
            print("GATE: incompatible/missing field preserves ordinary female golf skinner PASS; unrelated heroes checked: \(unaffected)")
            return
        }
        guard top.skinner == nil else { throw Failure.message("field absent, incompatible or missing sourceToHero: ordinary skinner correctly retained; parity NOT verified") }
        let readyPoints = vectors(top.geometry!.sources(for:.vertex).first!)
        try floats(readyPoints).write(to:output.appendingPathComponent("ready_positions.f32"))
        try floats(vectors(top.geometry!.sources(for:.normal).first!)).write(to:output.appendingPathComponent("ready_normals.f32"))
        var pairedMaximumError: Float?
        // Optional paired Unity output: flip Z after converting its mesh-local
        // result through the SAME sourceToHero matrix exported in the field.
        if let path = ProcessInfo.processInfo.environment["SLEEVE_UNITY_READY"] {
            let bytes = try Data(contentsOf:URL(fileURLWithPath:path))
            guard bytes.count == readyPoints.count*12 else { throw Failure.message("paired Unity topology mismatch") }
            pairedMaximumError = bytes.withUnsafeBytes { raw in readyPoints.enumerated().reduce(Float(0)) { value,entry in
                let i=entry.offset*12
                let expected=SIMD3(raw.loadUnaligned(fromByteOffset:i,as:Float.self),raw.loadUnaligned(fromByteOffset:i+4,as:Float.self),raw.loadUnaligned(fromByteOffset:i+8,as:Float.self))
                return max(value,simd_distance(entry.element,expected))
            } }
            guard pairedMaximumError! < 0.0001 else { throw Failure.message("paired Unity ready differs by \(pairedMaximumError!) metres") }
        }
        let ready = rigData.clips["ready"]!.pose(at:0,loop:false)
        let clips = rigData.clips.values.sorted { $0.info.id < $1.info.id }
        // Pose labels are diagnostics only. The evaluator receives matrices only.
        // Include all exported motions and interpolated transitions between poses.
        var tested = 0, finite = true, maximumVertexStep:Float = 0
        var previous: [SIMD3<Float>]?
        for clip in clips {
            for sample in 0...4 {
                let target = clip.pose(at:clip.length*Double(sample)/4,loop:false)
                let pose = RigData.blend(ready,target,Float(sample)/4)
                rig.apply(pose)
                guard let geometry = top.geometry, let source = geometry.sources(for:.vertex).first,
                      let normalSource = geometry.sources(for:.normal).first else { throw Failure.message("missing evaluated geometry") }
                let positions = vectors(source), normals = vectors(normalSource)
                finite = finite && positions.allSatisfy { $0.x.isFinite && $0.y.isFinite && $0.z.isFinite }
                finite = finite && normals.allSatisfy { $0.x.isFinite && $0.y.isFinite && $0.z.isFinite }
                guard positions.count == part.geometry.sources(for:.vertex).first!.vectorCount,
                      geometry.elements.count == original.elements.count,
                      geometry.sources(for:.texcoord).count == original.sources(for:.texcoord).count,
                      geometry.materials.count == originalMaterials.count,
                      zip(geometry.materials,originalMaterials).allSatisfy({ $0 === $1 }) else { throw Failure.message("topology/UV/material identity changed") }
                // Save only the first, middle and final pose of the first motion,
                // keeping diagnostics bounded. Raw positions are native hero-local.
                if tested < 5 && sample % 2 == 0 {
                    try floats(positions).write(to:output.appendingPathComponent("pose_\(sample)_positions.f32"))
                    try floats(normals).write(to:output.appendingPathComponent("pose_\(sample)_normals.f32"))
                }
                tested += 1
            }
        }
        // Fine transition steps exercise the real HeroRig.apply integration.
        if let target = clips.last?.pose(at:(clips.last?.length ?? 0)*0.5,loop:false) {
            for sample in 0...80 {
                rig.apply(RigData.blend(ready,target,Float(sample)/80))
                let points = vectors(top.geometry!.sources(for:.vertex).first!)
                if let previous { for (a,b) in zip(points,previous) { maximumVertexStep = max(maximumVertexStep,simd_distance(a,b)) } }
                previous = points
            }
        }
        let evaluated = top.geometry!
        rig.detach()
        guard top.skinner == nil, top.geometry === original else { throw Failure.message("detach did not restore static geometry") }
        // Missing metadata must retain the ordinary skinner, even for this asset.
        let locate = MatchHeroData.locate
        MatchHeroData.locate = { name,ext in name == "golf_sleeve_field" ? nil : locate(name,ext) }
        let fallbackHero = MatchHeroData.buildHero(asset,picks:MatchHeroData.Picks(colour:{_ in nil}))
        let fallbackRig = HeroRig(root:fallbackHero,asset:asset)!
        fallbackRig.attach()
        let fallback = fallbackHero.childNode(withName:"Kit_Top",recursively:false)!.skinner != nil
        MatchHeroData.locate = locate
        guard fallback else { throw Failure.message("missing-field fallback disabled ordinary skinning") }
        guard finite else { throw Failure.message("nonfinite evaluated positions/normals") }
        var report: [String:Any] = ["productionSourcesCompiled":true,"poseSamples":tested,"transitionSamples":81,"allFinite":finite,"maximumTransitionVertexStepMetres":maximumVertexStep,"topologyUVAndMaterialIdentityPreserved":true,"missingFieldRetainsSkinner":fallback,"detachRestoresOriginal":true,"vertexCount":evaluated.sources(for:.vertex).first!.vectorCount,"actualUnityParity":"requires paired export proof; not asserted by this check"]
        if let error = pairedMaximumError { report["pairedUnityReadyMaximumErrorMetres"] = error }
        let json = try JSONSerialization.data(withJSONObject:report,options:[.prettyPrinted,.sortedKeys])
        try json.write(to:output.appendingPathComponent("NATIVE_SELF_CHECK.json"))
        print(String(data:json,encoding:.utf8)!)
    }
    enum Failure: Error { case message(String) }
    static func vectors(_ source: SCNGeometrySource) -> [SIMD3<Float>] {
        source.data.withUnsafeBytes { bytes in (0..<source.vectorCount).map { i in
            let offset=source.dataOffset+i*source.dataStride
            return SIMD3(bytes.loadUnaligned(fromByteOffset:offset,as:Float.self),bytes.loadUnaligned(fromByteOffset:offset+4,as:Float.self),bytes.loadUnaligned(fromByteOffset:offset+8,as:Float.self))
        } }
    }
    static func floats(_ vectors: [SIMD3<Float>]) -> Data {
        vectors.flatMap { [$0.x,$0.y,$0.z] }.withUnsafeBytes { Data($0) }
    }
}
