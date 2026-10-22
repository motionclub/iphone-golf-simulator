import AVFoundation
import ImageIO
import Foundation
let dir = CommandLine.arguments[1], out = CommandLine.arguments[2]
let files = try! FileManager.default.contentsOfDirectory(atPath: dir).filter{$0.hasSuffix(".png")}.sorted()
try? FileManager.default.removeItem(atPath: out)
let w = try! AVAssetWriter(url: URL(fileURLWithPath: out), fileType: .mp4)
let inp = AVAssetWriterInput(mediaType: .video, outputSettings: [AVVideoCodecKey: AVVideoCodecType.h264, AVVideoWidthKey: 450, AVVideoHeightKey: 800, AVVideoCompressionPropertiesKey:[AVVideoAverageBitRateKey: 8_000_000]])
let ad = AVAssetWriterInputPixelBufferAdaptor(assetWriterInput: inp, sourcePixelBufferAttributes: [kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32ARGB, kCVPixelBufferWidthKey as String:450, kCVPixelBufferHeightKey as String:800])
w.add(inp); guard w.startWriting() else { fatalError("Video writer: \(String(describing:w.error))") }; w.startSession(atSourceTime: .zero)
for (i,f) in files.enumerated() {
  while !inp.isReadyForMoreMediaData { usleep(2000) }
  let img = CGImageSourceCreateImageAtIndex(CGImageSourceCreateWithURL(URL(fileURLWithPath: dir+"/"+f) as CFURL, nil)!, 0, nil)!
  var pb: CVPixelBuffer?; CVPixelBufferPoolCreatePixelBuffer(nil, ad.pixelBufferPool!, &pb)
  CVPixelBufferLockBaseAddress(pb!, [])
  let ctx = CGContext(data: CVPixelBufferGetBaseAddress(pb!), width: 450, height: 800, bitsPerComponent: 8, bytesPerRow: CVPixelBufferGetBytesPerRow(pb!), space: CGColorSpaceCreateDeviceRGB(), bitmapInfo: CGImageAlphaInfo.noneSkipFirst.rawValue)!
  ctx.draw(img, in: CGRect(x:0,y:0,width:450,height:800))
  CVPixelBufferUnlockBaseAddress(pb!, [])
  ad.append(pb!, withPresentationTime: CMTime(value: Int64(i), timescale: 24))
}
inp.markAsFinished(); let s = DispatchSemaphore(value: 0); w.finishWriting { s.signal() }; s.wait(); print(w.status.rawValue, files.count)
