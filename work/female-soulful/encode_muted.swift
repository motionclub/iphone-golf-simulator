import Foundation
import AVFoundation
import AppKit
import CoreVideo
let a = CommandLine.arguments
guard a.count == 6 else { fatalError("encode <frames-directory> <output.mp4> <prefix> <extension> <fps>") }
let dir = URL(fileURLWithPath:a[1]); let output = URL(fileURLWithPath:a[2])
let frames = try FileManager.default.contentsOfDirectory(at:dir,includingPropertiesForKeys:nil).filter{$0.pathExtension == a[4] && $0.lastPathComponent.hasPrefix(a[3])}.sorted{$0.lastPathComponent < $1.lastPathComponent}
guard let first = frames.first,let source=CGImageSourceCreateWithURL(first as CFURL,nil),let image=CGImageSourceCreateImageAtIndex(source,0,nil) else { fatalError("no PNG frames") }
try FileManager.default.createDirectory(at:output.deletingLastPathComponent(),withIntermediateDirectories:true)
if FileManager.default.fileExists(atPath:output.path) { try FileManager.default.removeItem(at:output) }
let writer=try AVAssetWriter(outputURL:output,fileType:.mp4)
let w=image.width,h=image.height
let input=AVAssetWriterInput(mediaType:.video,outputSettings:[AVVideoCodecKey:AVVideoCodecType.h264,AVVideoWidthKey:w,AVVideoHeightKey:h,AVVideoCompressionPropertiesKey:[AVVideoAverageBitRateKey:10000000,AVVideoProfileLevelKey:AVVideoProfileLevelH264HighAutoLevel]])
input.expectsMediaDataInRealTime=false
let adaptor=AVAssetWriterInputPixelBufferAdaptor(assetWriterInput:input,sourcePixelBufferAttributes:[kCVPixelBufferPixelFormatTypeKey as String:kCVPixelFormatType_32ARGB,kCVPixelBufferWidthKey as String:w,kCVPixelBufferHeightKey as String:h,kCVPixelBufferCGImageCompatibilityKey as String:true,kCVPixelBufferCGBitmapContextCompatibilityKey as String:true])
writer.add(input);guard writer.startWriting() else { fatalError("\(String(describing:writer.error))") };writer.startSession(atSourceTime:.zero)
for (i,url) in frames.enumerated() {
 while !input.isReadyForMoreMediaData { if writer.status == .failed { fatalError("\(String(describing:writer.error))") };Thread.sleep(forTimeInterval:0.002) }
 autoreleasepool {
  guard let s=CGImageSourceCreateWithURL(url as CFURL,nil),let img=CGImageSourceCreateImageAtIndex(s,0,nil) else { fatalError("invalid PNG") }
  var buffer:CVPixelBuffer?;guard CVPixelBufferPoolCreatePixelBuffer(nil,adaptor.pixelBufferPool!,&buffer)==kCVReturnSuccess,let b=buffer else { fatalError("pixel buffer") }
  CVPixelBufferLockBaseAddress(b,[])
  let context=CGContext(data:CVPixelBufferGetBaseAddress(b),width:w,height:h,bitsPerComponent:8,bytesPerRow:CVPixelBufferGetBytesPerRow(b),space:CGColorSpaceCreateDeviceRGB(),bitmapInfo:CGImageAlphaInfo.noneSkipFirst.rawValue)!
  context.draw(img,in:CGRect(x:0,y:0,width:w,height:h));CVPixelBufferUnlockBaseAddress(b,[])
  guard adaptor.append(b,withPresentationTime:CMTime(value:Int64(i),timescale:Int32(a[5])!)) else { fatalError("\(String(describing:writer.error))") }
 }
}
input.markAsFinished();let sem=DispatchSemaphore(value:0);writer.finishWriting{sem.signal()};sem.wait()
guard writer.status == .completed else { fatalError("\(String(describing:writer.error))") };print("\(output.path): \(frames.count) frames / \(a[5]) fps")
