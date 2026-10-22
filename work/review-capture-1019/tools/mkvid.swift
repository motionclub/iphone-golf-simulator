// mkvid: JPEG sequence -> H.264 mp4 (no ffmpeg on this Mac). Review capture 10-19.
//   mkvid single <out.mp4> <fps> <width> <dir>                 every *.jpg in <dir>, sorted, scaled to <width>
//   mkvid grid <out.mp4> <fps> <cols> <tileW> <label=dir>...   tiles in a grid (frame i of each dir), each tile labelled
// Bit rate is chosen so the file stays <= ~36 MB (capped at 8 Mbit/s).
import AVFoundation
import AppKit
import CoreGraphics
import ImageIO

func jpgs(_ dir: String) -> [String] {
    let files = (try? FileManager.default.contentsOfDirectory(atPath: dir)) ?? []
    return files.filter { $0.lowercased().hasSuffix(".jpg") }.sorted().map { dir + "/" + $0 }
}
func load(_ path: String) -> CGImage? {
    guard let src = CGImageSourceCreateWithURL(URL(fileURLWithPath: path) as CFURL, nil) else { return nil }
    return CGImageSourceCreateImageAtIndex(src, 0, nil)
}
func even(_ v: Int) -> Int { v & ~1 }

let a = CommandLine.arguments
guard a.count >= 6 else { print("usage: mkvid single <out> <fps> <width> <dir> | grid <out> <fps> <cols> <tileW> <label=dir>..."); exit(2) }
let mode = a[1], out = a[2], fps = Int32(a[3])!
var W = 0, H = 0, count = 0
var tiles: [(String, [String])] = []
var cols = 1, tileW = 0, tileH = 0
if mode == "single" {
    let files = jpgs(a[5]); guard let first = files.first.flatMap(load) else { print("no frames in \(a[5])"); exit(1) }
    W = even(Int(a[4])!); H = even(Int(Double(W) * Double(first.height) / Double(first.width)))
    tiles = [("", files)]; count = files.count; tileW = W; tileH = H
} else {
    cols = Int(a[4])!; tileW = even(Int(a[5])!); tileH = even(tileW * 9 / 16)
    for spec in a[6...] { let p = spec.split(separator: "=", maxSplits: 1).map(String.init); tiles.append((p[0], jpgs(p[1]))) }
    count = tiles.map { $0.1.count }.filter { $0 > 0 }.min() ?? 0
    let rows = (tiles.count + cols - 1) / cols
    W = cols * tileW; H = rows * tileH
}
guard count > 0 else { print("no frames"); exit(1) }
let seconds = Double(count) / Double(fps)
let bitrate = min(8_000_000.0, 36.0 * 1_000_000 * 8 / seconds)
try? FileManager.default.removeItem(atPath: out)
let writer = try! AVAssetWriter(outputURL: URL(fileURLWithPath: out), fileType: .mp4)
let input = AVAssetWriterInput(mediaType: .video, outputSettings: [
    AVVideoCodecKey: AVVideoCodecType.h264, AVVideoWidthKey: W, AVVideoHeightKey: H,
    AVVideoCompressionPropertiesKey: [AVVideoAverageBitRateKey: Int(bitrate), AVVideoProfileLevelKey: AVVideoProfileLevelH264HighAutoLevel, AVVideoMaxKeyFrameIntervalKey: Int(fps) * 2]])
input.expectsMediaDataInRealTime = false
let adaptor = AVAssetWriterInputPixelBufferAdaptor(assetWriterInput: input, sourcePixelBufferAttributes: [
    kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA, kCVPixelBufferWidthKey as String: W, kCVPixelBufferHeightKey as String: H])
writer.add(input); writer.startWriting(); writer.startSession(atSourceTime: .zero)
let font = NSFont.boldSystemFont(ofSize: CGFloat(max(14, tileW / 30)))
func label(_ ctx: CGContext, _ text: String, x: Int, y: Int) {
    guard !text.isEmpty else { return }
    let attr = NSAttributedString(string: text, attributes: [.font: font, .foregroundColor: NSColor.white])
    let line = CTLineCreateWithAttributedString(attr)
    let b = CTLineGetBoundsWithOptions(line, [])
    let pad = 6.0, h = b.height + pad * 2
    // y is the tile's top in CG (bottom-left origin) coordinates
    ctx.setFillColor(CGColor(red: 0, green: 0, blue: 0, alpha: 0.6))
    ctx.fill(CGRect(x: Double(x), y: Double(y) - h, width: b.width + pad * 2, height: h))
    ctx.textPosition = CGPoint(x: Double(x) + pad, y: Double(y) - h + pad - b.minY)
    CTLineDraw(line, ctx)
}
for i in 0..<count {
    autoreleasepool {
        while !input.isReadyForMoreMediaData { usleep(2000) }
        var pb: CVPixelBuffer?
        CVPixelBufferPoolCreatePixelBuffer(nil, adaptor.pixelBufferPool!, &pb)
        let buf = pb!
        CVPixelBufferLockBaseAddress(buf, [])
        let ctx = CGContext(data: CVPixelBufferGetBaseAddress(buf), width: W, height: H, bitsPerComponent: 8, bytesPerRow: CVPixelBufferGetBytesPerRow(buf),
                            space: CGColorSpaceCreateDeviceRGB(), bitmapInfo: CGImageAlphaInfo.premultipliedFirst.rawValue | CGBitmapInfo.byteOrder32Little.rawValue)!
        ctx.setFillColor(CGColor(red: 0.08, green: 0.08, blue: 0.1, alpha: 1)); ctx.fill(CGRect(x: 0, y: 0, width: W, height: H))
        ctx.interpolationQuality = .high
        for (t, tile) in tiles.enumerated() {
            let files = tile.1; guard !files.isEmpty else { continue }
            let col = t % cols, row = t / cols
            let x = col * tileW, yTop = H - row * tileH
            if let img = load(files[min(i, files.count - 1)]) { ctx.draw(img, in: CGRect(x: x, y: yTop - tileH, width: tileW, height: tileH)) }
            label(ctx, tile.0, x: x + 4, y: yTop - 4)
        }
        CVPixelBufferUnlockBaseAddress(buf, [])
        adaptor.append(buf, withPresentationTime: CMTime(value: CMTimeValue(i), timescale: fps))
    }
}
input.markAsFinished()
let done = DispatchSemaphore(value: 0)
writer.finishWriting { done.signal() }
done.wait()
let size = ((try? FileManager.default.attributesOfItem(atPath: out)[.size]) as? Int) ?? 0
print("\(out): \(count) frames \(W)x\(H) \(String(format: "%.1f", seconds)) s \(size / 1_000_000) MB status \(writer.status.rawValue) \(writer.error?.localizedDescription ?? "")")
