"""Apply optional golf-v3 support to a fresh shared-file snapshot; preserve tennis paths."""
from pathlib import Path
import shutil,json,hashlib,re
W=Path(__file__).resolve().parents[1];R=W.parents[1];D=W/'candidate/GolfArcade/Unity';D.mkdir(parents=True,exist_ok=True)
for name in ['MatchHeroData.swift','MatchHeroMotion.swift']:
 p=R/'GolfArcade/Unity'/name;shutil.copy2(p,D/name)
p=D/'MatchHeroData.swift';s=p.read_text()
s=s.replace('struct Part: Decodable {','struct Part: Decodable {\n        let variantHand: String?, equipment: String?')
s=s.replace('struct RigPartInfo: Decodable {','struct CorrectiveInfo: Decodable { let name: String; let positionOffset: Int; let normalOffset: Int? }\n    struct RigPartInfo: Decodable {\n        let correctives: [CorrectiveInfo]?')
s=s.replace('struct ClipInfo: Decodable {','struct ClipInfo: Decodable {\n        let file: String?, motion: String?, handedness: String?, equipment: String?, correctiveFile: String?\n        let impact: Float?, backswingTop: Float?, recovery: Float?, clubLength: Float?')
s=s.replace('struct Manifest: Decodable {','struct Manifest: Decodable {\n        let version: Int?, sport: String?\n        var isGolf: Bool { sport == "golf" && (version ?? 0) >= 3 }')
s=s.replace('root.setValue(asset.female, forKey: "heroFemale")','root.setValue(asset.female, forKey: "heroFemale")\n        root.setValue(m.isGolf, forKey: "heroGolf")\n        root.setValue(picks.leftHanded, forKey: "heroLeft")')
s=s.replace('if part.name == "Kit_Glove_R" { node.isHidden = true }','if part.name == "Kit_Glove_R" { node.isHidden = true }\n            if let hand = part.variantHand { node.isHidden = hand != (picks.leftHanded ? "left" : "right") }\n            if let equipment = part.equipment { node.isHidden = equipment != "iron" }')
s=s.replace('if picks.leftHanded { root.scale.x = -root.scale.x }','if picks.leftHanded && !m.isGolf { root.scale.x = -root.scale.x }')
s=s.replace('let inverseBinds: [NSValue]','let inverseBinds: [NSValue]\n        let correctives: [String: SCNGeometry]')
s=s.replace('let info: MatchHeroData.RigInfo\n','let info: MatchHeroData.RigInfo\n    let isGolf: Bool, sex: String\n    private var correctiveCache: [String: GolfCoefficients] = [:]\n    struct GolfCoefficients: Decodable { let fps: Float; let names: [String]; let values: [[Float]]; let trailRelease: [Float]?\n        func sample(_ time: Double) -> [Float] { guard let first = values.first else { return [] }; let f=min(max(Float(time)*fps,0),Float(values.count-1)), a=Int(f), b=min(a+1,values.count-1); return first.indices.map { values[a][$0]+(values[b][$0]-values[a][$0])*(f-Float(a)) } }\n    }\n    func coefficients(_ clip: Clip) -> GolfCoefficients? { guard let file=clip.info.correctiveFile else { return nil }; if let c=correctiveCache[file] { return c }; guard let u=MatchHeroData.locate(file,"json"),let d=try? Data(contentsOf:u),let c=try? JSONDecoder().decode(GolfCoefficients.self,from:d) else { return nil }; correctiveCache[file]=c;return c }\n    func clip(_ id: String, left: Bool = false) -> Clip? {\n        var key=id\n        if isGolf { let aliases=["ready":"AddressIron","serve":"IronSwing","golfPractice":"Drive","wave":"GoodShot","celebrate":"GoodShot","good-shot":"GoodShot","disappointed":"Disappointed"]; if let family=aliases[id] { key="\\(family)_\\(sex)_\\(left ? "LH" : "RH")" } }\n        if let clip=clips[key] { return clip }\n        guard let c=info.clips.first(where:{$0.id==key}),let file=c.file,let blob=MatchHeroData.data(file),blob.count>=c.frames*info.trackCount*40 else { return nil }\n        var values=[Float](repeating:0,count:c.frames*info.trackCount*10);values.withUnsafeMutableBytes{$0.copyBytes(from:blob.prefix(values.count*4))}\n        let result=Clip(info:c,trackCount:info.trackCount,data:values);if isGolf && clips.count>=4 { clips.removeAll() };clips[key]=result;return result\n    }\n')
s=s.replace('self.info = info','self.info = info; isGolf = asset.manifest.isGolf; sex = asset.manifest.sex')
s=s.replace('skinned.append(Skinned(partIndex:', '''var correctiveGeometry: [String: SCNGeometry] = [:]
            for c in rp.correctives ?? [] {
                guard c.positionOffset >= 0, c.positionOffset + v * 12 <= blob.count else { return nil }
                let position=SCNGeometrySource(data:blob.subdata(in:c.positionOffset ..< c.positionOffset+v*12),semantic:.vertex,vectorCount:v,usesFloatComponents:true,componentsPerVector:3,bytesPerComponent:4,dataOffset:0,dataStride:12)
                var normals=geometry.sources(for:.normal)
            if let offset=c.normalOffset,offset>=0,offset+v*12<=blob.count { normals=[SCNGeometrySource(data:blob.subdata(in:offset ..< offset+v*12),semantic:.normal,vectorCount:v,usesFloatComponents:true,componentsPerVector:3,bytesPerComponent:4,dataOffset:0,dataStride:12)] }
            correctiveGeometry[c.name]=SCNGeometry(sources:[position]+normals+geometry.sources(for:.texcoord),elements:geometry.elements)
            }
            skinned.append(Skinned(partIndex:''')
s=s.replace('inverseBinds: binds, bones: rp.bones))','inverseBinds: binds, correctives: correctiveGeometry, bones: rp.bones))')
s=s.replace('for c in info.clips {\n            guard let d','for c in info.clips where c.file == nil {\n            guard let d')
s=s.replace('guard clips["ready"] != nil else { return nil }','guard clip("ready") != nil else { return nil }')
# Avoid overlapping inout access when filling lazily loaded buffers.
s=s.replace('var values=[Float](repeating:0,count:c.frames*info.trackCount*10);values.withUnsafeMutableBytes{$0.copyBytes(from:blob.prefix(values.count*4))}','let count=c.frames*info.trackCount*10;var values=[Float](repeating:0,count:count);values.withUnsafeMutableBytes{$0.copyBytes(from:blob.prefix(count*4))}')
s=s.replace('struct RigInfo: Decodable {','struct RigInfo: Decodable {\n        let golfWristRH: [[Float]]?, golfWristLH: [[Float]]?')
pos=s.index('    func coefficients(');s=s[:pos]+"    func golfAnchors(left:Bool)->[SIMD3<Float>]? { guard let rows=left ? info.golfWristLH:info.golfWristRH,rows.count==2,rows.allSatisfy({$0.count==3}) else { return nil };return rows.map{SIMD3($0[0],$0[1],$0[2])} }\n"+s[pos:]
s=s.replace('Bundle.main.url(forResource: name, withExtension: ext)','Bundle.main.url(forResource: name, withExtension: ext) ?? Bundle.main.url(forResource: name, withExtension: ext, subdirectory: "GolfAnimations")')
p.write_text(s)
p=D/'MatchHeroMotion.swift' ;s=p.read_text();s=s.replace('private var staticGeometry: [String: SCNGeometry] = [:]','private var staticGeometry: [String: SCNGeometry] = [:]\n    private var morphers: [(morpher: SCNMorpher, names: [String])] = []\n    var leftHanded: Bool { root.value(forKey:"heroLeft") as? Bool ?? false }')
s=s.replace('node.skinner = skinner','node.skinner = skinner\n            if !part.correctives.isEmpty { let names=part.correctives.keys.sorted();let morpher=SCNMorpher();morpher.calculationMode = .additive;morpher.targets=names.compactMap{part.correctives[$0]};morpher.unifiesNormals=false;node.morpher=morpher;morphers.append((morpher,names)) }')
s=s.replace('if let ready = data.clips["ready"]','if let ready = data.clip("ready", left:leftHanded)')
s=s.replace('node.skinner = nil','node.skinner = nil; node.morpher = nil')
s=s.replace('boneNodes = []; rigid = []; staticGeometry = [:]','boneNodes = []; rigid = []; staticGeometry = [:]; morphers = []')
s=s.replace('func apply(_ motion: MenuMotion, at time: Double) { apply(motion.pose(data, at: time)) }','''func apply(_ motion: MenuMotion, at time: Double) {
        var motion=motion;motion.leftHanded=leftHanded;apply(motion.pose(data,at:time))
        let samples=motion.samples(data,at:time)
        var coefficients: [String: Float]=[:]
        for (clip,t,weight) in samples { if let data=self.data.coefficients(clip) { for (name,value) in zip(data.names,data.sample(t)) { coefficients[name,default:0]+=value*weight } } }
        for entry in morphers { for (i,name) in entry.names.enumerated() { entry.morpher.setWeight(CGFloat(coefficients[name] ?? 0),forTargetAt:i) } }
        // Current hero clips are coupled at authoring. The last stage keeps both
        // hands on that shared handle after any menu cross-fade.
        if data.isGolf { restoreGolfContacts(samples) }
    }
    private func restoreGolfContacts(_ samples: [(RigData.Clip,Double,Float)]) {
        guard let clubPart=data.info.rigid.firstIndex(of:"GolfHandle"),let handle=rigid.first(where:{$0.track==data.boneCount+clubPart})?.node else { return }
        // Exported wrist anchors are stored in each manifest's optional golf data.
        guard let anchors=data.golfAnchors(left:leftHanded) else { return }
        var released:Float=0
        for (clip,t,w) in samples { if let c=data.coefficients(clip),let r=c.trailRelease,!r.isEmpty { let i=min(r.count-1,max(0,Int(t*Double(c.fps))));released+=r[i]*w } }
        var shift=SIMD3<Float>(repeating:0)
        for _ in 0..<24 { for (side,anchor) in zip(["Left","Right"],anchors) {
            if released>0.000001 && side==(leftHanded ? "Left":"Right") { continue }
            guard let ui=data.info.bones.firstIndex(of:side+"UpperArm"),let ei=data.info.bones.firstIndex(of:side+"LowerArm"),let hi=data.info.bones.firstIndex(of:side+"Hand") else { continue }
            let u=boneNodes[ui].simdPosition,e=boneNodes[ei].simdPosition,h=boneNodes[hi].simdPosition
            let a=simd_distance(u,e),b=simd_distance(e,h),point=handle.simdTransform*SIMD4(anchor,1)
            let target=SIMD3(point.x,point.y,point.z)+shift,ray=target-u,d=simd_length(ray)
            if d>0.000001 { let allowed=min(max(d,abs(a-b)+0.00001),(a+b)*0.99999);shift+=(ray/d)*(allowed-d) }
        } }
        if simd_length(shift)>0 { for part in rigid { let index=part.track-data.boneCount;if index>=0 && index<data.info.rigid.count && data.info.rigid[index].hasPrefix("Golf") { part.node.simdPosition+=shift } } }
        for (side,anchor) in zip(["Left","Right"],anchors) {
            let indices=data.info.bones.enumerated().filter{$0.element==side+"Hand" || $0.element.hasPrefix(side+"Thumb") || $0.element.hasPrefix(side+"Index") || $0.element.hasPrefix(side+"Middle") || $0.element.hasPrefix(side+"Ring") || $0.element.hasPrefix(side+"Little")}.map(\\.offset)
            guard let hi=data.info.bones.firstIndex(of:side+"Hand"),let ui=data.info.bones.firstIndex(of:side+"UpperArm"),let ei=data.info.bones.firstIndex(of:side+"LowerArm") else { continue }
            var released:Float=0
            for (clip,t,w) in samples { if let c=data.coefficients(clip),let r=c.trailRelease,!r.isEmpty { let i=min(r.count-1,max(0,Int(t*Double(c.fps))));released+=r[i]*w } }
            if released>0.000001 && side==(leftHanded ? "Left":"Right") { continue }
            let target=(handle.simdTransform*SIMD4(anchor,1)).xyz
            let u=boneNodes[ui].simdPosition,e=boneNodes[ei].simdPosition,h=boneNodes[hi].simdPosition
            let a=simd_distance(u,e),b=simd_distance(e,h),d=simd_distance(u,target)
            if d<0.000001 || d>a+b+0.0001 { continue }
            let axis=simd_normalize(target-u),along=(a*a-b*b+d*d)/(2*d)
            var pole=e-u-axis*simd_dot(e-u,axis);if simd_length(pole)<0.000001 { pole=simd_cross(axis,SIMD3<Float>(0,0,1)) }
            let elbow=u+axis*along+simd_normalize(pole)*sqrt(max(0,a*a-along*along))
            boneNodes[ui].simdOrientation=simd_quatf(from:simd_normalize(e-u),to:simd_normalize(elbow-u))*boneNodes[ui].simdOrientation
            boneNodes[ei].simdOrientation=simd_quatf(from:simd_normalize(h-e),to:simd_normalize(target-elbow))*boneNodes[ei].simdOrientation;boneNodes[ei].simdPosition=elbow
            let delta=target-h;for i in indices { boneNodes[i].simdPosition+=delta }
        }
    }''')
s=s.replace('var idleOffset = 0.0','var idleOffset = 0.0\n    var leftHanded = false',1)
# All menu lookups are lazy and handedness-aware; tennis key names are unchanged.
s=re.sub(r'rig\.clips\["([^\"]+)"\]',r'rig.clip("\1", left:leftHanded)',s)
s=s.replace('rig.clips[id]','rig.clip(id, left:leftHanded)')
# Add the same weights used for skeletal fading to the garment coefficients.
pos=s.index('\n}\n\n/// A lobby hero owns')
s=s[:pos]+'''
    @MainActor func samples(_ rig:RigData,at t:Double)->[(RigData.Clip,Double,Float)] {
        guard let ready=rig.clip("ready",left:leftHanded) else { return [] }
        if let from=settleFrom { var m=self;m.settleFrom=nil;let w=Self.smooth((t-from)/settleDuration);return m.samples(rig,at:from).map{($0.0,$0.1,$0.2*(1-w))}+[(ready,0,w)] }
        let id:String?;switch kind { case .ready:id=nil;case .serveOnce:id="serve";case .clipOnce(let name):id=name }
        guard let id,let clip=rig.clip(id,left:leftHanded) else { return [(ready,t+idleOffset,1)] }
        let elapsed=t-lead;let w:Float
        if kind == .serveOnce { w=serveWeight(rig,at:t) } else { w=elapsed<0 ? 0:elapsed<=clip.length ? Self.smooth(elapsed/max(.001,fadeIn)):1-Self.smooth((elapsed-clip.length)/max(.001,fadeOut)) }
        return [(ready,t+idleOffset,1-w),(clip,min(max(elapsed,0),clip.length),w)]
    }
'''+s[pos:]
# Lobby methods are outside MenuMotion; use the hero's handedness.
start=s.index('@MainActor final class LobbyHeroMotion');a=s[:start];b=s[start:].replace('left:leftHanded','left:rig.leftHanded').replace('rig.data.clips[id]','rig.data.clip(id,left:rig.leftHanded)').replace('rig.data.clips[$0]','rig.data.clip($0,left:rig.leftHanded)');s=a+b
s=s.replace('max(.001','max(0.001').replace('let target=(handle.simdTransform*SIMD4(anchor,1)).xyz','let point=handle.simdTransform*SIMD4(anchor,1);let target=SIMD3(point.x,point.y,point.z)')
p.write_text(s)
print('NATIVE_CANDIDATE_READY')
