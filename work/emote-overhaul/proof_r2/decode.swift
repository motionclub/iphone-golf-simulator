import AVFoundation
import AppKit
let args = CommandLine.arguments
let asset = AVURLAsset(url: URL(fileURLWithPath: args[1]))
let gen = AVAssetImageGenerator(asset: asset)
gen.appliesPreferredTrackTransform = true
gen.requestedTimeToleranceBefore = .zero
gen.requestedTimeToleranceAfter = .zero
try FileManager.default.createDirectory(atPath: args[2], withIntermediateDirectories: true)
let duration = CMTimeGetSeconds(asset.duration)
for n in 0..<Int(duration * 12) {
 let t = Double(n) / 12
 let cg = try gen.copyCGImage(at: CMTime(seconds: t, preferredTimescale: 600), actualTime: nil)
 let rep = NSBitmapImageRep(cgImage: cg)
 try rep.representation(using: .png, properties: [:])!.write(to: URL(fileURLWithPath: args[2] + String(format: "/frame_%04d.png", n)))
}
print("DECODED", args[1], "duration",duration,"frames",Int(duration*12))
