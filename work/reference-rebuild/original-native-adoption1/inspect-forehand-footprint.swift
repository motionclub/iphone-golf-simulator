import Foundation
let task=URL(fileURLWithPath:CommandLine.arguments[1])
var rows:[[String:Any]]=[]
for stem in ["MatchHero_Male","MatchHero_Female","MatchHero_Male_Distance","MatchHero_Female_Distance"] {
 let d=try JSONSerialization.jsonObject(with:Data(contentsOf:task.appendingPathComponent("export/"+stem+".json"))) as! [String:Any]
 let rig=d["rig"] as! [String:Any],clips=rig["clips"] as! [[String:Any]]
 let clip=clips.first(where:{$0["id"] as? String=="forehand"})!
 let file=task.appendingPathComponent("export/"+(rig["file"] as! String)+".lzfse")
 let packed=try Data(contentsOf:file),raw=try (packed as NSData).decompressed(using:.lzfse) as Data
 let offset=clip["offset"] as! Int
 let tail=raw.subdata(in:offset..<raw.count)
 let encodedTail=try (tail as NSData).compressed(using:.lzfse) as Data
 rows.append(["manifest":stem,"frames":clip["frames"]!,"lengthSeconds":clip["length"]!,"proofTrackOffset":offset,"rigDecodedBytes":raw.count,"extraTailDecodedBytes":tail.count,"tailAloneLzfseBytes":encodedTail.count,"rigPackedBytes":packed.count,"lastClipIsForehand":clips.last!["id"] as? String=="forehand","tennisPracticeFrameCount":(d["swingFrames"] as! [String]).count])
}
let output=try JSONSerialization.data(withJSONObject:rows,options:[.prettyPrinted,.sortedKeys]);try output.write(to:task.appendingPathComponent("forehand-footprint.json"));print(String(data:output,encoding:.utf8)!)
