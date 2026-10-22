import AVFoundation
import AppKit
import CoreVideo
let args=CommandLine.arguments
let dir=URL(fileURLWithPath:args[1]),out=URL(fileURLWithPath:args[2]);let width=1170,height=2532,fps:Int32=30
let writer=try AVAssetWriter(outputURL:out,fileType:.mov)
let input=AVAssetWriterInput(mediaType:.video,outputSettings:[AVVideoCodecKey:AVVideoCodecType.h264,AVVideoWidthKey:width,AVVideoHeightKey:height,AVVideoCompressionPropertiesKey:[AVVideoAverageBitRateKey:12_000_000,AVVideoMaxKeyFrameIntervalKey:30]])
let adaptor=AVAssetWriterInputPixelBufferAdaptor(assetWriterInput:input,sourcePixelBufferAttributes:[kCVPixelBufferPixelFormatTypeKey as String:kCVPixelFormatType_32ARGB,kCVPixelBufferWidthKey as String:width,kCVPixelBufferHeightKey as String:height])
writer.add(input);writer.startWriting();writer.startSession(atSourceTime:.zero)
for i in 0..<90 {
 let name=String(format:"f_%03d.png",i),data=try Data(contentsOf:dir.appendingPathComponent(name));let bitmap=NSBitmapImageRep(data:data)!,image=bitmap.cgImage!
 var optional:CVPixelBuffer?;CVPixelBufferPoolCreatePixelBuffer(nil,adaptor.pixelBufferPool!,&optional);let buffer=optional!
 CVPixelBufferLockBaseAddress(buffer,[])
 let ctx=CGContext(data:CVPixelBufferGetBaseAddress(buffer),width:width,height:height,bitsPerComponent:8,bytesPerRow:CVPixelBufferGetBytesPerRow(buffer),space:CGColorSpaceCreateDeviceRGB(),bitmapInfo:CGImageAlphaInfo.noneSkipFirst.rawValue)!
 ctx.draw(image,in:CGRect(x:0,y:0,width:width,height:height));CVPixelBufferUnlockBaseAddress(buffer,[])
 while !input.isReadyForMoreMediaData {Thread.sleep(forTimeInterval:0.005)}
 guard adaptor.append(buffer,withPresentationTime:CMTime(value:Int64(i),timescale:fps)) else{fatalError(writer.error?.localizedDescription ?? "append failed")}
}
writer.endSession(atSourceTime:CMTime(value:90,timescale:fps));input.markAsFinished();let group=DispatchGroup();group.enter();writer.finishWriting{group.leave()};group.wait()
guard writer.status == .completed else{fatalError(writer.error?.localizedDescription ?? "encode failed")};print(out.path)
