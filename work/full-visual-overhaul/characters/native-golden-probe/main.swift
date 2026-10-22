import Foundation
import SceneKit
import simd
let repo="/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
struct Golden:Decodable { struct Sample:Decodable { let clip:String; let frame:Int; let part:String; let vertices:[[Double]] }; let samples:[Sample] }
func floats(_ s:SCNGeometrySource)->[Float] { s.data.withUnsafeBytes{r in (0..<s.vectorCount*s.componentsPerVector).map{k in r.loadUnaligned(fromByteOffset:s.dataOffset+k/s.componentsPerVector*s.dataStride+k%s.componentsPerVector*s.bytesPerComponent,as:Float.self)}} }
func indices(_ s:SCNGeometrySource)->[Int] { s.data.withUnsafeBytes { r in (0..<s.vectorCount*s.componentsPerVector).map { k in let o=s.dataOffset+k/s.componentsPerVector*s.dataStride+k%s.componentsPerVector*s.bytesPerComponent; switch s.bytesPerComponent { case 1:return Int(r.loadUnaligned(fromByteOffset:o,as:UInt8.self)); case 2:return Int(r.loadUnaligned(fromByteOffset:o,as:UInt16.self)); case 4:return Int(r.loadUnaligned(fromByteOffset:o,as:UInt32.self)); default: fatalError("Unsupported index stride") } } } }
@MainActor func run() throws {
 MatchHeroData.locate={n,e in let u=URL(fileURLWithPath:repo+"/GolfArcade/Unity/CharacterAssets/"+n+"."+e);return FileManager.default.fileExists(atPath:u.path) ? u:nil}
 for golf in [false,true] { for female in [false,true] { for distance in golf ? [false] : [false,true] {
  let name=(golf ? "GolfKitHero_":"MatchHero_")+(female ? "Female":"Male")+(distance ? "_Distance":"")
  let asset=MatchHeroData.asset(female:female,golf:golf,distance:distance)!,root=MatchHeroData.buildHero(asset,picks:MatchHeroData.Picks(colour:{_ in nil})),rig=HeroRig(root:root,asset:asset)!;rig.attach()
  let golden=try JSONDecoder().decode(Golden.self,from:Data(contentsOf:URL(fileURLWithPath:repo+"/proof/full-visual-overhaul/native-golden-provisional-2/"+name+"_golden.json")))
  var worst:Float=0, checked=0, failed=0; var worstAt=""
  for sample in golden.samples {
   let clip=rig.data.clips[sample.clip]!,time=clip.info.times?.count==clip.frames ? Double(clip.info.times![sample.frame]):Double(sample.frame)*clip.length/Double(clip.frames-1)
   rig.apply(clip.pose(at:time,loop:false)); rig.data.applyMorphWeights(clip.morphWeights(at:time,loop:false),to:root)
   let node=root.childNode(withName:sample.part,recursively:true)!,g=node.geometry!,bind=floats(g.sources(for:.vertex)[0]),targets=node.morpher?.targets.map{floats($0.sources(for:.vertex)[0])} ?? [],w=node.skinner.map{floats($0.boneWeights)} ?? [],ids=node.skinner.map{indices($0.boneIndices)} ?? []
   for v in sample.vertices {
    let i=Int(v[0]);var p=SIMD3(bind[3*i],bind[3*i+1],bind[3*i+2]);for(k,t) in targets.enumerated(){p+=Float(node.morpher!.weight(forTargetAt:k))*SIMD3(t[3*i],t[3*i+1],t[3*i+2])}
    var got=SIMD4<Float>(repeating:0)
    if let skin=node.skinner { for k in 0..<4 where w[4*i+k]>0 { let b=ids[4*i+k], inv=simd_float4x4(skin.boneInverseBindTransforms![b].scnMatrix4Value);got+=w[4*i+k]*(root.simdWorldTransform.inverse*skin.bones[b].simdWorldTransform*inv*SIMD4(p,1)) } }
    else { got=root.simdWorldTransform.inverse*node.simdWorldTransform*SIMD4(p,1) }
    let want=SIMD3<Float>(Float(v[1]),Float(v[2]),Float(v[3])),e=simd_distance(SIMD3(got.x,got.y,got.z),want);checked+=1
    if e>worst {worst=e;worstAt="\(sample.clip) frame\(sample.frame) \(sample.part) v\(i)"}
    if e>0.0005 {failed+=1;if failed<4 {print("FAIL",name,sample.clip,sample.frame,sample.part,i,e*1000)}}
   }
  }
  print("LIVE_GRAPH",name,"checked",checked,"failures",failed,"worst_mm",worst*1000,"at",worstAt,"bones",rig.data.boneCount,"actualIndexBytes",rig.root.childNode(withName:"Body",recursively:true)!.skinner!.boneIndices.bytesPerComponent)
  rig.detach()
 } } }
}
MainActor.assumeIsolated { try! run() }
