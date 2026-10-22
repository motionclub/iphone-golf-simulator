import Foundation
import AVFoundation
import CoreGraphics
import ImageIO
import CoreVideo
import AppKit
let frames=URL(fileURLWithPath:CommandLine.arguments[1],isDirectory:true)
let destination=URL(fileURLWithPath:CommandLine.arguments[2])
let urls=try FileManager.default.contentsOfDirectory(at:frames,includingPropertiesForKeys:nil).filter{$0.pathExtension=="png" && $0.deletingPathExtension().lastPathComponent.count==4 && Int($0.deletingPathExtension().lastPathComponent) != nil}.sorted{$0.lastPathComponent<$1.lastPathComponent}
let w=1800,h=1080
if FileManager.default.fileExists(atPath:destination.path){try FileManager.default.removeItem(at:destination)}
let writer=try AVAssetWriter(outputURL:destination,fileType:.mp4)
let input=AVAssetWriterInput(mediaType:.video,outputSettings:[AVVideoCodecKey:AVVideoCodecType.h264,AVVideoWidthKey:w,AVVideoHeightKey:h,AVVideoCompressionPropertiesKey:[AVVideoAverageBitRateKey:8_000_000,AVVideoExpectedSourceFrameRateKey:30]])
input.expectsMediaDataInRealTime=false
let adaptor=AVAssetWriterInputPixelBufferAdaptor(assetWriterInput:input,sourcePixelBufferAttributes:[kCVPixelBufferPixelFormatTypeKey as String:kCVPixelFormatType_32BGRA,kCVPixelBufferWidthKey as String:w,kCVPixelBufferHeightKey as String:h,kCVPixelBufferCGImageCompatibilityKey as String:true,kCVPixelBufferCGBitmapContextCompatibilityKey as String:true])
writer.add(input);writer.shouldOptimizeForNetworkUse=true
if !writer.startWriting(){fatalError("Writer start: \(String(describing:writer.error))")};writer.startSession(atSourceTime:.zero)
for (index,url) in urls.enumerated(){
 while !input.isReadyForMoreMediaData{if writer.status == .failed{fatalError("\(String(describing:writer.error))")};Thread.sleep(forTimeInterval:0.001)}
 try autoreleasepool {
  guard let source=CGImageSourceCreateWithURL(url as CFURL,nil),let image=CGImageSourceCreateImageAtIndex(source,0,nil) else{fatalError("Missing frame")}
  var pixel:CVPixelBuffer?;CVPixelBufferPoolCreatePixelBuffer(nil,adaptor.pixelBufferPool!,&pixel);let buffer=pixel!
  CVPixelBufferLockBaseAddress(buffer,[])
  let context=CGContext(data:CVPixelBufferGetBaseAddress(buffer),width:w,height:h,bitsPerComponent:8,bytesPerRow:CVPixelBufferGetBytesPerRow(buffer),space:CGColorSpaceCreateDeviceRGB(),bitmapInfo:CGImageAlphaInfo.premultipliedFirst.rawValue|CGBitmapInfo.byteOrder32Little.rawValue)!
  context.draw(image,in:CGRect(x:0,y:0,width:w,height:h));CVPixelBufferUnlockBaseAddress(buffer,[])
  if !adaptor.append(buffer,withPresentationTime:CMTime(value:Int64(index),timescale:30)){throw writer.error ?? NSError(domain:"VideoAppend",code:1)}
 }
}
input.markAsFinished();let done=DispatchSemaphore(value:0);writer.finishWriting{done.signal()};done.wait()
guard writer.status == .completed else{fatalError("\(String(describing:writer.error))")}
let asset=AVURLAsset(url:destination);let generator=AVAssetImageGenerator(asset:asset);generator.appliesPreferredTrackTransform=true
let test=try generator.copyCGImage(at:CMTime(value:68,timescale:30),actualTime:nil)
let png=NSBitmapImageRep(cgImage:test).representation(using:.png,properties:[:])!
try png.write(to:frames.appendingPathComponent("encoded_check.png"))
print("ENCODED \(urls.count) frames at 30 fps to \(destination.path)")
