import Foundation
import AVFoundation
import AppKit

let args = CommandLine.arguments
let movie = URL(fileURLWithPath: args[1])
let output = URL(fileURLWithPath: args[2])
try FileManager.default.createDirectory(at: output, withIntermediateDirectories: true)
let asset = AVURLAsset(url: movie)
let generator = AVAssetImageGenerator(asset: asset)
generator.appliesPreferredTrackTransform = true
generator.requestedTimeToleranceBefore = .zero
generator.requestedTimeToleranceAfter = .zero
print("duration=\(CMTimeGetSeconds(asset.duration))")
for text in args.dropFirst(3) {
    let seconds = Double(text)!
    let frame = try generator.copyCGImage(at: CMTime(seconds: seconds, preferredTimescale: 600), actualTime: nil)
    let bitmap = NSBitmapImageRep(cgImage: frame)
    try bitmap.representation(using: .png, properties: [:])!.write(to: output.appendingPathComponent("frame-\(text).png"))
}
