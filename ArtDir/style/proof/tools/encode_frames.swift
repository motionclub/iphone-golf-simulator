// Encode the actual capture timestamps; no invented fixed-rate playback.
// Usage: swift encode_frames.swift FRAME_FOLDER OUTPUT.mp4
import Foundation
import AVFoundation
import CoreGraphics
import ImageIO

let folder=URL(fileURLWithPath:CommandLine.arguments[1])
let output=URL(fileURLWithPath:CommandLine.arguments[2])
let rows=try String(contentsOf:folder.appendingPathComponent("frames.tsv"),encoding:.utf8).split(separator:"\n").map { $0.split(separator:"\t").map(String.init) }
func source(_ index:String)->CGImage {
    let url=folder.appendingPathComponent(String(format:"%03d.jpg",Int(index)!))
    return CGImageSourceCreateImageAtIndex(CGImageSourceCreateWithURL(url as CFURL,nil)!,0,nil)!
}
let first=source(rows[0][0]);let width=first.width,height=first.height
if FileManager.default.fileExists(atPath:output.path) { try FileManager.default.removeItem(at:output) }
let writer=try AVAssetWriter(outputURL:output,fileType:.mp4)
let input=AVAssetWriterInput(mediaType:.video,outputSettings:[AVVideoCodecKey:AVVideoCodecType.h264,AVVideoWidthKey:width,AVVideoHeightKey:height,AVVideoCompressionPropertiesKey:[AVVideoAverageBitRateKey:6_000_000]])
input.expectsMediaDataInRealTime=false
let adaptor=AVAssetWriterInputPixelBufferAdaptor(assetWriterInput:input,sourcePixelBufferAttributes:[kCVPixelBufferPixelFormatTypeKey as String:kCVPixelFormatType_32ARGB,kCVPixelBufferWidthKey as String:width,kCVPixelBufferHeightKey as String:height,kCVPixelBufferCGImageCompatibilityKey as String:true,kCVPixelBufferCGBitmapContextCompatibilityKey as String:true])
writer.add(input);guard writer.startWriting() else { fatalError(String(describing:writer.error)) };writer.startSession(atSourceTime:.zero)
for row in rows {
    while !input.isReadyForMoreMediaData { if writer.status == .failed { fatalError(String(describing:writer.error)) };Thread.sleep(forTimeInterval:0.005) }
    var optional:CVPixelBuffer?;CVPixelBufferPoolCreatePixelBuffer(nil,adaptor.pixelBufferPool!,&optional);let buffer=optional!
    CVPixelBufferLockBaseAddress(buffer,[])
    let context=CGContext(data:CVPixelBufferGetBaseAddress(buffer),width:width,height:height,bitsPerComponent:8,bytesPerRow:CVPixelBufferGetBytesPerRow(buffer),space:CGColorSpaceCreateDeviceRGB(),bitmapInfo:CGImageAlphaInfo.noneSkipFirst.rawValue)!
    context.draw(source(row[0]),in:CGRect(x:0,y:0,width:width,height:height))
    CVPixelBufferUnlockBaseAddress(buffer,[])
    guard adaptor.append(buffer,withPresentationTime:CMTime(seconds:Double(row[1])!,preferredTimescale:60000)) else {fatalError(String(describing:writer.error))}
}
input.markAsFinished();let done=DispatchSemaphore(value:0);writer.finishWriting {done.signal()};done.wait()
guard writer.status == .completed else {fatalError(String(describing:writer.error))}
print(output.path)
