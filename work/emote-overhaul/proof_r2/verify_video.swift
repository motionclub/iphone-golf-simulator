import AVFoundation
import Foundation
for path in CommandLine.arguments.dropFirst() {
 let asset = AVURLAsset(url: URL(fileURLWithPath: path))
 let track = asset.tracks(withMediaType: .video).first!
 let reader = try AVAssetReader(asset: asset)
 let output = AVAssetReaderTrackOutput(track: track, outputSettings: [kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA])
 reader.add(output)
 guard reader.startReading() else { fatalError("reader start failed") }
 var n = 0
 while output.copyNextSampleBuffer() != nil { n += 1 }
 guard reader.status == .completed && n > 0 else { fatalError("decode failed: \(reader.error?.localizedDescription ?? "unknown")") }
 print("VIDEO PASS", URL(fileURLWithPath: path).lastPathComponent, "frames=\(n)", "duration=\(CMTimeGetSeconds(asset.duration))", "size=\(track.naturalSize)")
}
