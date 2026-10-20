import AVFoundation
import AppKit
// enc <out.mp4> <fps> <w> <h> <frame1.png> <frame2.png> ...   (H.264, 30 fps video from stills)
let a = CommandLine.arguments
let out = URL(fileURLWithPath: a[1]); let fps = Int32(a[2])!; let w = Int(a[3])!; let h = Int(a[4])!
try? FileManager.default.removeItem(at: out)
let wr = try! AVAssetWriter(outputURL: out, fileType: .mp4)
let inp = AVAssetWriterInput(mediaType: .video, outputSettings: [AVVideoCodecKey: AVVideoCodecType.h264, AVVideoWidthKey: w, AVVideoHeightKey: h, AVVideoCompressionPropertiesKey: [AVVideoAverageBitRateKey: 6_000_000]])
let ad = AVAssetWriterInputPixelBufferAdaptor(assetWriterInput: inp, sourcePixelBufferAttributes: [kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32ARGB, kCVPixelBufferWidthKey as String: w, kCVPixelBufferHeightKey as String: h])
wr.add(inp)
guard wr.startWriting() else { fatalError("Cannot start encoder: \(String(describing: wr.error))") }
wr.startSession(atSourceTime: .zero)
for (i, p) in a[5...].enumerated() {
  guard let img = NSImage(contentsOfFile: p), let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else { fatalError("Cannot read frame \(p)") }
  var pb: CVPixelBuffer?; CVPixelBufferCreate(nil, w, h, kCVPixelFormatType_32ARGB, nil, &pb)
  CVPixelBufferLockBaseAddress(pb!, [])
  let ctx = CGContext(data: CVPixelBufferGetBaseAddress(pb!), width: w, height: h, bitsPerComponent: 8, bytesPerRow: CVPixelBufferGetBytesPerRow(pb!), space: CGColorSpaceCreateDeviceRGB(), bitmapInfo: CGImageAlphaInfo.noneSkipFirst.rawValue)!
  ctx.draw(cg, in: CGRect(x: 0, y: 0, width: w, height: h))
  CVPixelBufferUnlockBaseAddress(pb!, [])
  while !inp.isReadyForMoreMediaData {
    if wr.status == .failed { fatalError("Encoder failed: \(String(describing: wr.error))") }
    Thread.sleep(forTimeInterval: 0.005)
  }
  guard ad.append(pb!, withPresentationTime: CMTime(value: CMTimeValue(i), timescale: fps)) else { fatalError("Frame append failed: \(String(describing: wr.error))") }
}
inp.markAsFinished(); let sem = DispatchSemaphore(value: 0); wr.finishWriting { sem.signal() }; sem.wait()
guard wr.status == .completed else { fatalError("Finish failed: \(String(describing: wr.error))") }
print("wrote", a[1], "frames", a.count-5, "fps", fps, "status completed")
