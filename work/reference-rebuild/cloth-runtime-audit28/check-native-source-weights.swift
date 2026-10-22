import Foundation
let repo=URL(fileURLWithPath:CommandLine.arguments[1]),task=repo.appendingPathComponent("work/reference-rebuild/cloth-runtime-audit28")
var rows:[[String:Any]]=[]
for (stem,detail) in [("MatchHero_Female","Full"),("MatchHero_Female_Distance","LOD")] {
 let export=repo.appendingPathComponent("work/reference-rebuild/original-native-adoption1/export")
 let d=try JSONSerialization.jsonObject(with:Data(contentsOf:export.appendingPathComponent(stem+".json"))) as! [String:Any]
 let rig=d["rig"] as! [String:Any],bones=rig["bones"] as! [String],part=(rig["parts"] as! [[String:Any]]).first(where:{$0["part"] as? String=="Kit_Top"})!
 let source=try JSONSerialization.jsonObject(with:Data(contentsOf:repo.appendingPathComponent("Unity/Assets/Resources/Tennis/Correctives/UnderarmGusset_Female_"+detail+".json"))) as! [String:Any]
 let pb=source["bones"] as! [String],pi=source["boneIndices"] as! [Int],pw=source["weights"] as! [Double],map=part["bones"] as! [Int],count=part["vertexCount"] as! Int
 precondition(count==source["sourceVertexCount"] as! Int)
 let encoded=try Data(contentsOf:export.appendingPathComponent((rig["file"] as! String)+".lzfse")),raw=try (encoded as NSData).decompressed(using:.lzfse) as Data
 let off=part["weightOffset"] as! Int,index=part["indexOffset"] as! Int
 var changed=0,worst:Double=0
 raw.withUnsafeBytes { bytes in
  for v in 0..<count {
   var sourceW:[String:Double]=[:],liveW:[String:Double]=[:]
   for k in 0..<4 {
    sourceW[pb[pi[v*4+k]],default:0]+=pw[v*4+k]
    let b=Int(bytes.loadUnaligned(fromByteOffset:index+v*4+k,as:UInt8.self)),w=Double(bytes.loadUnaligned(fromByteOffset:off+v*16+k*4,as:Float.self))
    liveW[bones[map[b]],default:0]+=w
   }
   let error=Set(sourceW.keys).union(liveW.keys).reduce(0.0){$0+abs(sourceW[$1,default:0]-liveW[$1,default:0])}
   worst=max(worst,error);if error>0.000001 {changed+=1}
  }
 }
 rows.append(["manifest":stem,"detail":detail,"sourceVertices":count,"runtimeProfileChangedWeights":changed,"maxWeightL1":worst,"source":"fresh root native export, exact post OwnMaterials/geometry/axilla/pose-preparation weights; gusset disabled"])
}
let data=try JSONSerialization.data(withJSONObject:rows,options:[.prettyPrinted,.sortedKeys]);try data.write(to:task.appendingPathComponent("native-source-weight-contract.json"));print(String(data:data,encoding:.utf8)!)
