import AVFoundation
import AppKit
// usage: frames <video.mp4> <outPrefix> <t0> <t1> <count>   - writes <count> frames evenly between t0 and t1 seconds as <outPrefix>_NN.png
let a = CommandLine.arguments
guard a.count >= 6, let t0 = Double(a[3]), let t1 = Double(a[4]), let n = Int(a[5]) else { print("usage: frames video outPrefix t0 t1 count"); exit(1) }
let asset = AVURLAsset(url: URL(fileURLWithPath: a[1]))
let gen = AVAssetImageGenerator(asset: asset); gen.requestedTimeToleranceBefore = .zero; gen.requestedTimeToleranceAfter = .zero; gen.appliesPreferredTrackTransform = true
for i in 0..<n {
    let t = n == 1 ? t0 : t0 + (t1 - t0) * Double(i) / Double(n - 1)
    do {
        let cg = try gen.copyCGImage(at: CMTime(seconds: t, preferredTimescale: 600), actualTime: nil)
        let rep = NSBitmapImageRep(cgImage: cg)
        try rep.representation(using: .png, properties: [:])!.write(to: URL(fileURLWithPath: String(format: "%@_%02d.png", a[2], i)))
    } catch { print("frame \(i) at \(t): \(error)") }
}
