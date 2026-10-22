import Foundation
import AVFoundation
import AppKit

let args=Array(CommandLine.arguments.dropFirst())
let out=URL(fileURLWithPath:args[0],isDirectory:true)
try FileManager.default.createDirectory(at:out,withIntermediateDirectories:true)
var results:[[String:Any]]=[]
for path in args.dropFirst() {
    let url=URL(fileURLWithPath:path)
    let asset=AVURLAsset(url:url)
    let duration=try await asset.load(.duration)
    let tracks=try await asset.loadTracks(withMediaType:.video)
    let track=tracks[0]
    let size=try await track.load(.naturalSize)
    let fps=try await track.load(.nominalFrameRate)
    let generator=AVAssetImageGenerator(asset:asset)
    generator.appliesPreferredTrackTransform=true
    generator.requestedTimeToleranceBefore = .zero
    generator.requestedTimeToleranceAfter = .zero
    let sec=duration.seconds
    var decoded=0
    for (i,t) in [0.0,sec*0.5,max(0,sec-0.1)].enumerated() {
        let (cg,_)=try await generator.image(at:CMTime(seconds:t,preferredTimescale:600))
        let rep=NSBitmapImageRep(cgImage:cg)
        let png=rep.representation(using:.png,properties:[:])!
        try png.write(to:out.appendingPathComponent(url.deletingPathExtension().lastPathComponent+"_\(i).png"))
        decoded+=1
    }
    results.append(["file":path,"duration_s":sec,"width":size.width,"height":size.height,"fps":fps,"decoded_samples":decoded])
}
let data=try JSONSerialization.data(withJSONObject:results,options:[.prettyPrinted,.sortedKeys])
try data.write(to:out.appendingPathComponent("movie_audit.json"))
print(String(data:data,encoding:.utf8)!)
