from pathlib import Path
p=Path('GolfArcade/Unity/MatchHeroData.swift');s=p.read_text()
s=s.replace('let specularStrength: Float?, environmentStrength: Float?','let specularStrength: Float?, environmentStrength: Float?, metallic: Float?')
s=s.replace('    struct RigPartInfo: Decodable {','    struct MorphShapeInfo: Decodable { let name: String; let positionOffset: Int; let normalOffset: Int }\n    struct MorphTrackInfo: Decodable { let part: String; let offset: Int; let count: Int }\n    struct RigPartInfo: Decodable {')
s=s.replace('        let bones: [Int]\n    }\n    struct ClipInfo:', '        let bones: [Int]\n        let morphs: [MorphShapeInfo]?\n    }\n    struct ClipInfo:')
s=s.replace('        let times: [Float]?\n    }\n    struct RigInfo:', '        let times: [Float]?\n        let morphWeights: [MorphTrackInfo]?\n        let equipment: String?\n    }\n    struct RigInfo:')
s=s.replace('            if part.name == "Kit_Glove_R" { node.isHidden = true }','            if part.name == "Kit_Glove_R" || (part.kind == "equipment" && part.name != "Club_Iron") { node.isHidden = true }')
s=s.replace('        let bones: [Int]\n    }\n    /// One clip:', '        let bones: [Int]\n        let morphTargets: [SCNGeometry]\n    }\n    struct MorphSamples { let count: Int; let values: [Float] }\n    /// One clip:')
s=s.replace('        let data: [Float]\n        var frames:', '        let data: [Float]\n        let morphSamples: [Int: MorphSamples]\n        var frames:')
# Preserve the existing skeletal sampler and add corrective samples using the exact same time/frame interpolation.
marker='''        /// Every track at clip time `time`, interpolated between the two surrounding samples (a loop wraps; otherwise the time is clamped to the clip).'''
new='''        func morphWeights(at time: Double, loop: Bool) -> [Int: [Float]] {
            guard frames > 0, length > 0 else { return [:] }
            let n = frames - 1
            var t = loop ? time.truncatingRemainder(dividingBy: length) : min(max(time,0),length)
            if t < 0 { t += length }
            let frame = t / length * Double(n)
            var i0 = min(n,Int(frame.rounded(.down))), i1 = min(n,i0+1), weight = Float(frame-Double(i0))
            if let times = info.times, times.count == frames {
                var low = 0, high = n
                while low < high { let mid = (low+high+1)/2; if times[mid] <= Float(t) { low=mid } else { high=mid-1 } }
                i0=low; i1=min(n,low+1); weight=i0 == i1 ? 0 : (Float(t)-times[i0])/max(0.000001,times[i1]-times[i0])
            }
            return morphSamples.mapValues { sample in (0..<sample.count).map { shape in
                let a=sample.values[i0*sample.count+shape], b=sample.values[i1*sample.count+shape]
                return a+(b-a)*weight
            }}
        }
'''+marker
s=s.replace(marker,new)
s=s.replace('            skinned.append(Skinned(partIndex: pi, name: rp.part, geometry: geometry, weights: weights, indices: indices, inverseBinds: binds, bones: rp.bones))','''            var targets: [SCNGeometry] = []
            for shape in rp.morphs ?? [] {
                guard shape.positionOffset >= 0, shape.normalOffset >= 0,
                      shape.positionOffset + v*12 <= blob.count, shape.normalOffset + v*12 <= blob.count else { return nil }
                targets.append(SCNGeometry(sources: [src(shape.positionOffset,.vertex),src(shape.normalOffset,.normal)]+base.sources(for:.texcoord),elements:base.elements))
            }
            skinned.append(Skinned(partIndex: pi, name: rp.part, geometry: geometry, weights: weights, indices: indices, inverseBinds: binds, bones: rp.bones, morphTargets: targets))''')
s=s.replace('            clips[c.id] = Clip(info: c, trackCount: info.trackCount, data: d)','''            var morphSamples: [Int: MorphSamples] = [:]
            for track in c.morphWeights ?? [] {
                guard let pi=asset.partIndex(track.part), let part=skinned.first(where:{$0.partIndex==pi}), track.count==part.morphTargets.count,
                      let values=floats(track.offset,c.frames*track.count) else { return nil }
                morphSamples[pi]=MorphSamples(count:track.count,values:values)
            }
            clips[c.id] = Clip(info: c, trackCount: info.trackCount, data: d, morphSamples: morphSamples)''')
marker='''    /// Blend of two poses (same track count): `w` = 0 is `a`, 1 is `b`.'''
s=s.replace(marker,'''    /// Corrective targets are in the original bind space, so SceneKit morphs them before skinning.
    func attachMorphers(to root: SCNNode) {
        for part in skinned where !part.morphTargets.isEmpty {
            guard let node=root.childNode(withName:part.name,recursively:false) else { continue }
            let morpher=SCNMorpher(); morpher.calculationMode = .additive; morpher.unifiesNormals = false
            morpher.targets=part.morphTargets; node.morpher=morpher
        }
    }
    func applyMorphWeights(_ weights: [Int:[Float]], to root: SCNNode) {
        for part in skinned where !part.morphTargets.isEmpty {
            guard let morpher=root.childNode(withName:part.name,recursively:false)?.morpher else { continue }
            let values=weights[part.partIndex] ?? []
            for shape in part.morphTargets.indices { morpher.setWeight(CGFloat(shape<values.count ? values[shape]:0),forTargetAt:shape) }
        }
    }
    static func blendMorphs(_ a: [Int:[Float]], _ b: [Int:[Float]], _ weight: Float) -> [Int:[Float]] {
        var result: [Int:[Float]] = [:]
        for part in Set(a.keys).union(b.keys) {
            let aa=a[part] ?? [], bb=b[part] ?? []
            result[part]=(0..<max(aa.count,bb.count)).map { shape in
                let from=shape<aa.count ? aa[shape]:0, to=shape<bb.count ? bb[shape]:0
                return from+(to-from)*weight
            }
        }
        return result
    }

'''+marker)
s+='''
// Follows MenuMotion.pose's identical clock, easing and settle semantics for cloth fit.
extension MenuMotion {
    @MainActor func morphWeights(_ rig: RigData, at time: Double) -> [Int:[Float]] {
        func ease(_ value: Double) -> Float { let x=min(1,max(0,value)); return Float(x*x*(3-2*x)) }
        func playing(_ t: Double) -> [Int:[Float]] {
            guard let ready=rig.clips["ready"] else { return [:] }
            let base=ready.morphWeights(at:t+idleOffset,loop:true)
            if case .clipOnce(let id)=kind, let clip=rig.clips[id] {
                let elapsed=t-lead; if elapsed<0 { return base }
                let weight=elapsed<=clip.length ? ease(elapsed/max(.001,fadeIn)):1-ease((elapsed-clip.length)/max(.001,fadeOut))
                return RigData.blendMorphs(base,clip.morphWeights(at:elapsed,loop:false),weight)
            }
            let weight=serveWeight(rig,at:t)
            guard weight>0,let serve=rig.clips["serve"] else { return base }
            return RigData.blendMorphs(base,serve.morphWeights(at:t-lead,loop:false),weight)
        }
        guard let from=settleFrom,let ready=rig.clips["ready"] else { return playing(time) }
        return RigData.blendMorphs(playing(from),ready.morphWeights(at:0,loop:true),ease((time-from)/settleDuration))
    }
}
'''
p.write_text(s)
p=Path('GolfArcade/Unity/MatchHeroSurfaces.swift');s=p.read_text()
s=s.replace('mat = look.isCloth ? cloth(look, tint: tint, sceneScale: sceneScale, trim: trimColour) : character(look, tint: tint)','''if look.shader == "Universal Render Pipeline/Lit" {
                mat=SCNMaterial();mat.lightingModel = .physicallyBased;mat.diffuse.contents=flatColour(tint)
                mat.metalness.contents=look.metallic ?? 0;mat.roughness.contents=1-look.smoothness
            } else {
                mat = look.isCloth ? cloth(look, tint: tint, sceneScale: sceneScale, trim: trimColour) : character(look, tint: tint)
            }''')
p.write_text(s)
