import Foundation
import AVFoundation

let args = CommandLine.arguments
let asset = AVURLAsset(url:URL(fileURLWithPath:args[1]))
let exporter = AVAssetExportSession(asset:asset,presetName:AVAssetExportPreset1280x720)!
if args.count > 4 {
    exporter.timeRange = CMTimeRange(start:CMTime(seconds:Double(args[3])!,preferredTimescale:600),duration:CMTime(seconds:Double(args[4])!,preferredTimescale:600))
}
let output = URL(fileURLWithPath:args[2])
try? FileManager.default.removeItem(at:output)
exporter.shouldOptimizeForNetworkUse = true
try await exporter.export(to:output,as:.mp4)
print(output.path)
