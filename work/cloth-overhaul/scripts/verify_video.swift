import Foundation
import AVFoundation
let paths = CommandLine.arguments.dropFirst()
var records:[[String:Any]]=[]
for path in paths {
 let asset=AVURLAsset(url:URL(fileURLWithPath:path))
 let duration=try await asset.load(.duration)
 let tracks=try await asset.loadTracks(withMediaType:.video)
 guard let track=tracks.first else { fatalError("No video track: \(path)") }
 let size=try await track.load(.naturalSize)
 let generator=AVAssetImageGenerator(asset:asset)
 var decoded=0
 for time in [0.0,duration.seconds/2,max(0,duration.seconds-0.05)] {
  let image=try await generator.image(at:CMTime(seconds:time,preferredTimescale:600))
  guard image.image.width>0 else { fatalError("Empty image") };decoded+=1
 }
 records.append(["path":path,"duration_s":duration.seconds,"width":size.width,"height":size.height,"decoded_samples":decoded])
}
let data=try JSONSerialization.data(withJSONObject:records,options:[.prettyPrinted,.sortedKeys]);print(String(data:data,encoding:.utf8)!)
