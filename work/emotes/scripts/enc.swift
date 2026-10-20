import AVFoundation
import AppKit
// enc <out.mp4> <fps> <w> <h> <frame1.png> <frame2.png> ...   (H.264, 30 fps video from stills)
let a = CommandLine.arguments
let out = URL(fileURLWithPath: a[1]); let fps = Int32(a[2])!; let w = Int(a[3])!; let h = Int(a[4])!
try? FileManager.default.removeItem(at: out)
let wr = try! AVAssetWriter(outputURL: out, fileType: .mp4)
let inp = AVAssetWriterInput(mediaType: .video, outputSettings: [AVVideoCodecKey: AVVideoCodecType.h264, AVVideoWidthKey: w, AVVideoHeightKey: h, AVVideoCompressionPropertiesKey: [AVVideoAverageBitRateKey: 6_000_000]])
let ad = AVAssetWriterInputPixelBufferAdaptor(assetWriterInput: inp, sourcePixelBufferAttributes: [kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32ARGB, kCVPixelBufferWidthKey as String: w, kCVPixelBufferHeightKey as String: h])
wr.add(inp); wr.startWriting(); wr.startSession(atSourceTime: .zero)
for (i, p) in a[5...].enumerated() {
  guard let img = NSImage(contentsOfFile: p), let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else { continue }
  var pb: CVPixelBuffer?; CVPixelBufferCreate(nil, w, h, kCVPixelFormatType_32ARGB, nil, &pb)
  CVPixelBufferLockBaseAddress(pb!, [])
  let ctx = CGContext(data: CVPixelBufferGetBaseAddress(pb!), width: w, height: h, bitsPerComponent: 8, bytesPerRow: CVPixelBufferGetBytesPerRow(pb!), space: CGColorSpaceCreateDeviceRGB(), bitmapInfo: CGImageAlphaInfo.noneSkipFirst.rawValue)!
  ctx.draw(cg, in: CGRect(x: 0, y: 0, width: w, height: h))
  CVPixelBufferUnlockBaseAddress(pb!, [])
  while !inp.isReadyForMoreMediaData { Thread.sleep(forTimeInterval: 0.005) }
  ad.append(pb!, withPresentationTime: CMTime(value: CMTimeValue(i), timescale: fps))
}
inp.markAsFinished(); let sem = DispatchSemaphore(value: 0); wr.finishWriting { sem.signal() }; sem.wait()
print("wrote", a[1], wr.status.rawValue)
