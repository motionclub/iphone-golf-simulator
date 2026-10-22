import Foundation
import AVFoundation
import CoreGraphics
import ImageIO
import CoreVideo
import UniformTypeIdentifiers

enum CaptureError: Error { case failed(String) }
@main struct Encode {
 static func main() async throws {
  let args=CommandLine.arguments
  guard args.count==4 else {throw CaptureError.failed("encode <frames> <out.mp4> <probe-dir>")}
  let dir=URL(fileURLWithPath:args[1]), out=URL(fileURLWithPath:args[2]), probes=URL(fileURLWithPath:args[3])
  try FileManager.default.createDirectory(at:probes,withIntermediateDirectories:true)
  let files=try FileManager.default.contentsOfDirectory(at:dir,includingPropertiesForKeys:nil).filter{$0.lastPathComponent.hasPrefix("f_") && $0.pathExtension=="jpg"}.sorted{$0.lastPathComponent<$1.lastPathComponent}
  guard files.count==600 else {throw CaptureError.failed("Expected 600 frames, got \(files.count)")}
  guard !FileManager.default.fileExists(atPath:out.path) else {throw CaptureError.failed("Refuse overwrite")}
  let width=1600,height=900
  let writer=try AVAssetWriter(outputURL:out,fileType:.mp4)
  let input=AVAssetWriterInput(mediaType:.video,outputSettings:[AVVideoCodecKey:AVVideoCodecType.h264,AVVideoWidthKey:width,AVVideoHeightKey:height,AVVideoCompressionPropertiesKey:[AVVideoAverageBitRateKey:10000000,AVVideoProfileLevelKey:AVVideoProfileLevelH264HighAutoLevel,AVVideoMaxKeyFrameIntervalKey:60]])
  input.expectsMediaDataInRealTime=false
  let adaptor=AVAssetWriterInputPixelBufferAdaptor(assetWriterInput:input,sourcePixelBufferAttributes:[kCVPixelBufferPixelFormatTypeKey as String:kCVPixelFormatType_32BGRA,kCVPixelBufferWidthKey as String:width,kCVPixelBufferHeightKey as String:height,kCVPixelBufferCGImageCompatibilityKey as String:true,kCVPixelBufferCGBitmapContextCompatibilityKey as String:true])
  writer.add(input)
  guard writer.startWriting() else {throw writer.error ?? CaptureError.failed("Start writing")}
  writer.startSession(atSourceTime:.zero)
  for (i,file) in files.enumerated() {
   while !input.isReadyForMoreMediaData {if writer.status == .failed {throw writer.error!};try await Task.sleep(nanoseconds:2_000_000)}
   try autoreleasepool {
    guard let source=CGImageSourceCreateWithURL(file as CFURL,nil),let image=CGImageSourceCreateImageAtIndex(source,0,nil),image.width==width,image.height==height else {throw CaptureError.failed("Invalid frame \(file.path)")}
    var buffer:CVPixelBuffer?
    guard let pool=adaptor.pixelBufferPool,CVPixelBufferPoolCreatePixelBuffer(nil,pool,&buffer)==kCVReturnSuccess,let buffer=buffer else {throw CaptureError.failed("Pixel buffer")}
    CVPixelBufferLockBaseAddress(buffer,[])
    defer {CVPixelBufferUnlockBaseAddress(buffer,[])}
    guard let ctx=CGContext(data:CVPixelBufferGetBaseAddress(buffer),width:width,height:height,bitsPerComponent:8,bytesPerRow:CVPixelBufferGetBytesPerRow(buffer),space:CGColorSpaceCreateDeviceRGB(),bitmapInfo:CGBitmapInfo.byteOrder32Little.rawValue | CGImageAlphaInfo.premultipliedFirst.rawValue) else {throw CaptureError.failed("Bitmap context")}
    ctx.draw(image,in:CGRect(x:0,y:0,width:width,height:height))
    guard adaptor.append(buffer,withPresentationTime:CMTime(value:Int64(i),timescale:30)) else {throw writer.error ?? CaptureError.failed("Append")}
   }
   if i%120==0 {print("Encoded \(i)/600")}
  }
  input.markAsFinished()
  writer.endSession(atSourceTime:CMTime(value:600,timescale:30))
  await writer.finishWriting()
  guard writer.status == .completed else {throw writer.error ?? CaptureError.failed("Finish")}
  let asset=AVURLAsset(url:out)
  let duration=try await asset.load(.duration)
  let tracks=try await asset.loadTracks(withMediaType:.video)
  guard let track=tracks.first else {throw CaptureError.failed("No video track")}
  let size=try await track.load(.naturalSize), fps=try await track.load(.nominalFrameRate)
  let reader=try AVAssetReader(asset:asset)
  let readerOut=AVAssetReaderTrackOutput(track:track,outputSettings:[kCVPixelBufferPixelFormatTypeKey as String:kCVPixelFormatType_32BGRA])
  reader.add(readerOut);reader.startReading()
  var count = 0, first = -1.0, last = -1.0
  while let sample=readerOut.copyNextSampleBuffer() {let pts=CMTimeGetSeconds(CMSampleBufferGetPresentationTimeStamp(sample));if count==0 {first=pts};last=pts;count += 1}
  guard reader.status == .completed && count==600 && abs(CMTimeGetSeconds(duration)-20)<0.01 && abs(fps-30)<0.01 && size.width==1600 && size.height==900 else {throw CaptureError.failed("Video validation failed")}
  let generator=AVAssetImageGenerator(asset:asset);generator.appliesPreferredTrackTransform=true;generator.requestedTimeToleranceBefore = .zero;generator.requestedTimeToleranceAfter = .zero
  for (label,seconds) in [("start",0.0),("middle",10.0),("end",599.0/30.0)] {
   let image=try generator.copyCGImage(at:CMTime(seconds:seconds,preferredTimescale:600),actualTime:nil)
   let dest=CGImageDestinationCreateWithURL(probes.appendingPathComponent(label+".png") as CFURL,UTType.png.identifier as CFString,1,nil)!
   CGImageDestinationAddImage(dest,image,nil);guard CGImageDestinationFinalize(dest) else {throw CaptureError.failed("Probe PNG")}
  }
  let info:[String:Any]=["file":out.path,"frames":count,"duration_seconds":CMTimeGetSeconds(duration),"width":size.width,"height":size.height,"fps":fps,"first_pts":first,"last_pts":last,"codec":"H.264","decoded_all_frames":true]
  try JSONSerialization.data(withJSONObject:info,options:[.prettyPrinted,.sortedKeys]).write(to:probes.appendingPathComponent("verified.json"))
  print(String(data:try JSONSerialization.data(withJSONObject:info,options:.sortedKeys),encoding:.utf8)!)
 }
}

