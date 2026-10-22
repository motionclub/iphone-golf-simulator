import AVFoundation
import CoreImage
// usage: shrink <in.mp4> <out.mp4> [width] [bitrateKbps] [maxSeconds]  - re-encodes video at a given width (aspect kept) and bitrate, keeping every frame (60 fps stays 60 fps)
let a = CommandLine.arguments
guard a.count >= 3 else { print("usage: shrink in out [width] [kbps] [maxSeconds]"); exit(1) }
let width = a.count > 3 ? Double(a[3]) ?? 540 : 540, kbps = a.count > 4 ? Int(a[4]) ?? 3000 : 3000, maxSeconds = a.count > 5 ? Double(a[5]) ?? 1e9 : 1e9
let asset = AVURLAsset(url: URL(fileURLWithPath: a[1]))
let sem = DispatchSemaphore(value: 0)
Task {
    do {
        let track = try await asset.loadTracks(withMediaType: .video)[0]
        let size = try await track.load(.naturalSize); let duration = try await asset.load(.duration)
        let w = Int(width) / 2 * 2, h = Int(width * Double(size.height / size.width)) / 2 * 2
        let reader = try AVAssetReader(asset: asset)
        let out = AVAssetReaderTrackOutput(track: track, outputSettings: [kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA])
        reader.add(out)
        try? FileManager.default.removeItem(atPath: a[2])
        let writer = try AVAssetWriter(outputURL: URL(fileURLWithPath: a[2]), fileType: .mp4)
        let input = AVAssetWriterInput(mediaType: .video, outputSettings: [AVVideoCodecKey: AVVideoCodecType.h264, AVVideoWidthKey: w, AVVideoHeightKey: h, AVVideoCompressionPropertiesKey: [AVVideoAverageBitRateKey: kbps * 1000]])
        let adapter = AVAssetWriterInputPixelBufferAdaptor(assetWriterInput: input, sourcePixelBufferAttributes: [kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA, kCVPixelBufferWidthKey as String: w, kCVPixelBufferHeightKey as String: h])
        writer.add(input); reader.startReading(); writer.startWriting(); writer.startSession(atSourceTime: .zero)
        let ctx = CIContext()
        var first: CMTime?
        while let sample = out.copyNextSampleBuffer() {
            let t = CMSampleBufferGetPresentationTimeStamp(sample); if first == nil { first = t }
            let rel = CMTimeSubtract(t, first!)
            if rel.seconds > maxSeconds { break }
            guard let px = CMSampleBufferGetImageBuffer(sample) else { continue }
            var dst: CVPixelBuffer?; CVPixelBufferPoolCreatePixelBuffer(nil, adapter.pixelBufferPool!, &dst)
            let img = CIImage(cvPixelBuffer: px).transformed(by: CGAffineTransform(scaleX: Double(w) / size.width, y: Double(h) / size.height))
            ctx.render(img, to: dst!)
            while !input.isReadyForMoreMediaData { try await Task.sleep(nanoseconds: 2_000_000) }
            adapter.append(dst!, withPresentationTime: rel)
        }
        input.markAsFinished(); await writer.finishWriting()
        print("done", writer.status.rawValue, "from", duration.seconds, "s")
    } catch { print("error \(error)") }
    sem.signal()
}
sem.wait()
