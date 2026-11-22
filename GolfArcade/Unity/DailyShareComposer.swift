import AVFoundation
import CoreGraphics
import CoreText
import CoreVideo
import Foundation

// DAILY SHARE: cuts the day's filmed shots (DailyShareClips) into the clip a player shares (mockups:
// ArtDir/ui/daily-challenge-ui-mockups): a title card, each shot from its backswing to just after the ball stops with its
// distance and points stamped on, and an end card with the total and "Can you beat it?". Made in two shapes: wide (1280×720,
// the game as it looked) for Photos, Messages and X, and tall (1080×1920, the game uncropped in the middle) for TikTok,
// Reels and Stories. Only AVFoundation, CoreGraphics and CoreText, so it runs off the main thread and in tests.

/// What the cards say.
struct DailyShareCard: Sendable, Equatable {
    var number: Int          // #7
    var date: String         // "NOV 21"
    var total: Int
    var top: Int?            // Top X % in the world, once ranked
    var points: [Int]
    var feet: [Double]

    init(number: Int, date: String, total: Int, top: Int?, points: [Int], feet: [Double]) {
        self.number = number; self.date = date; self.total = total; self.top = top; self.points = points; self.feet = feet
    }
    init(_ result: HoleInOneResult, top: Int?) {
        self.init(number: DailyShareText.number(day: result.day), date: DailyShareText.shortDate(day: result.day), total: result.total,
                  top: top, points: result.shots, feet: result.feet)
    }
}

enum DailyShareShape: String, Sendable, CaseIterable {
    case wide, tall
    var size: (width: Int, height: Int) { self == .wide ? (1280, 720) : (1080, 1920) }
}

enum DailyShareComposer {
    static let fps: Int32 = 30
    static let titleSeconds = 1.6, endSeconds = 3.0

    enum Failure: Error { case noShots, writer(String) }

    /// The clip, written to `url`. `progress` gets 0–1 as frames are made.
    static func compose(clips: [DailyShotClip], card: DailyShareCard, shape: DailyShareShape, to url: URL,
                        progress: @Sendable (Double) -> Void = { _ in }) async throws -> URL {
        let shots = clips.sorted { $0.shot < $1.shot }
        guard !shots.isEmpty else { throw Failure.noShots }
        // the source frames of every shot, decoded one shot at a time
        var plans: [(clip: DailyShotClip, ranges: [ClosedRange<Double>], track: AVAssetTrack, asset: AVURLAsset)] = []
        for clip in shots {
            let asset = AVURLAsset(url: clip.url)
            guard let track = try await asset.loadTracks(withMediaType: .video).first else { continue }
            plans.append((clip, clip.keep(), track, asset))
        }
        guard !plans.isEmpty else { throw Failure.noShots }

        try? FileManager.default.removeItem(at: url)
        let (w, h) = shape.size
        let writer = try AVAssetWriter(outputURL: url, fileType: .mp4)
        let input = AVAssetWriterInput(mediaType: .video, outputSettings: [
            AVVideoCodecKey: AVVideoCodecType.h264, AVVideoWidthKey: w, AVVideoHeightKey: h,
            AVVideoCompressionPropertiesKey: [AVVideoAverageBitRateKey: shape == .wide ? 4_500_000 : 6_000_000,
                                              AVVideoExpectedSourceFrameRateKey: fps, AVVideoMaxKeyFrameIntervalKey: fps,
                                              AVVideoProfileLevelKey: AVVideoProfileLevelH264HighAutoLevel]])
        input.expectsMediaDataInRealTime = false
        let adaptor = AVAssetWriterInputPixelBufferAdaptor(assetWriterInput: input, sourcePixelBufferAttributes: [
            kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA,
            kCVPixelBufferWidthKey as String: w, kCVPixelBufferHeightKey as String: h,
            kCVPixelBufferIOSurfacePropertiesKey as String: [:]])
        writer.add(input)
        guard writer.startWriting() else { throw Failure.writer(writer.error?.localizedDescription ?? "start") }
        writer.startSession(atSourceTime: .zero)

        let painter = DailySharePainter(shape: shape, card: card)
        let total = Double(Int(titleSeconds * 30) + Int(endSeconds * 30)) + plans.reduce(0) { $0 + $1.clip.kept * 30 }
        var made: Int64 = 0
        func emit(_ draw: (CGContext) -> Void) throws {
            guard let pool = adaptor.pixelBufferPool else { throw Failure.writer("no pool") }
            var out: CVPixelBuffer?
            guard CVPixelBufferPoolCreatePixelBuffer(nil, pool, &out) == kCVReturnSuccess, let buffer = out else { throw Failure.writer("buffer") }
            CVPixelBufferLockBaseAddress(buffer, [])
            if let ctx = CGContext(data: CVPixelBufferGetBaseAddress(buffer), width: w, height: h, bitsPerComponent: 8,
                                   bytesPerRow: CVPixelBufferGetBytesPerRow(buffer), space: CGColorSpace(name: CGColorSpace.sRGB)!,
                                   bitmapInfo: CGImageAlphaInfo.premultipliedFirst.rawValue | CGBitmapInfo.byteOrder32Little.rawValue) {
                ctx.translateBy(x: 0, y: CGFloat(h)); ctx.scaleBy(x: 1, y: -1)   // top-left origin for the layout
                draw(ctx)
            }
            CVPixelBufferUnlockBaseAddress(buffer, [])
            while !input.isReadyForMoreMediaData { if writer.status != .writing { throw Failure.writer(writer.error?.localizedDescription ?? "writer") }; usleep(2000) }
            guard adaptor.append(buffer, withPresentationTime: CMTime(value: made, timescale: fps)) else { throw Failure.writer(writer.error?.localizedDescription ?? "append") }
            made += 1
            if made % 15 == 0 { progress(min(0.99, Double(made) / max(1, total))) }
        }

        // the title card, over the first shot's opening frame
        let opening = try firstFrame(plans[0].asset, track: plans[0].track, at: plans[0].ranges.first?.lowerBound ?? 0)
        for i in 0..<Int(titleSeconds * 30) { try emit { painter.title($0, background: opening, t: Double(i) / 30) } }
        // the shots
        for plan in plans {
            let restAt = plan.clip.rest
            for range in plan.ranges {
                try frames(plan.asset, track: plan.track, range: range) { image, time in
                    try emit { painter.shot($0, frame: image, clip: plan.clip, sinceRest: restAt.map { time - $0 }) }
                }
            }
        }
        // the end card
        for i in 0..<Int(endSeconds * 30) { try emit { painter.end($0, t: Double(i) / 30) } }

        input.markAsFinished()
        await writer.finishWriting()
        guard writer.status == .completed else { throw Failure.writer(writer.error?.localizedDescription ?? "finish") }
        progress(1)
        return url
    }

    /// Every frame of `track` in `range` (seconds), in order, with its time.
    private static func frames(_ asset: AVURLAsset, track: AVAssetTrack, range: ClosedRange<Double>, each: (CGImage, Double) throws -> Void) throws {
        let reader = try AVAssetReader(asset: asset)
        let output = AVAssetReaderTrackOutput(track: track, outputSettings: [kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA])
        output.alwaysCopiesSampleData = false
        reader.add(output)
        reader.timeRange = CMTimeRange(start: CMTime(seconds: range.lowerBound, preferredTimescale: 600),
                                       end: CMTime(seconds: range.upperBound, preferredTimescale: 600))
        guard reader.startReading() else { throw Failure.writer(reader.error?.localizedDescription ?? "read") }
        while let sample = output.copyNextSampleBuffer() {
            let time = CMSampleBufferGetPresentationTimeStamp(sample).seconds
            guard time <= range.upperBound + 0.001, let pixels = CMSampleBufferGetImageBuffer(sample), let image = cgImage(pixels) else { continue }
            try autoreleasepool { try each(image, time) }
        }
        if reader.status == .failed { throw Failure.writer(reader.error?.localizedDescription ?? "read") }
    }

    private static func firstFrame(_ asset: AVURLAsset, track: AVAssetTrack, at time: Double) throws -> CGImage? {
        var first: CGImage?
        struct Stop: Error {}
        do { try frames(asset, track: track, range: time...(time + 0.5)) { image, _ in first = image; throw Stop() } } catch is Stop {}
        return first
    }

    /// A BGRA pixel buffer as an image (copied: the buffer goes back to the reader).
    static func cgImage(_ pixels: CVPixelBuffer) -> CGImage? {
        CVPixelBufferLockBaseAddress(pixels, .readOnly); defer { CVPixelBufferUnlockBaseAddress(pixels, .readOnly) }
        return CGContext(data: CVPixelBufferGetBaseAddress(pixels), width: CVPixelBufferGetWidth(pixels), height: CVPixelBufferGetHeight(pixels),
                         bitsPerComponent: 8, bytesPerRow: CVPixelBufferGetBytesPerRow(pixels), space: CGColorSpace(name: CGColorSpace.sRGB)!,
                         bitmapInfo: CGImageAlphaInfo.premultipliedFirst.rawValue | CGBitmapInfo.byteOrder32Little.rawValue)?.makeImage()
    }
}

/// Draws the cards and the stamps, in the game's own look: Fredoka, white letters with a navy outline, gold for points.
struct DailySharePainter {
    let shape: DailyShareShape
    let card: DailyShareCard
    var size: CGSize { CGSize(width: shape.size.width, height: shape.size.height) }

    static let navy = CGColor(srgbRed: 0.059, green: 0.106, blue: 0.290, alpha: 1)
    static let navyTop = CGColor(srgbRed: 0.114, green: 0.196, blue: 0.522, alpha: 1)
    static let outline = CGColor(srgbRed: 0.075, green: 0.157, blue: 0.431, alpha: 1)
    static let gold = CGColor(srgbRed: 0.965, green: 0.761, blue: 0.243, alpha: 1)
    static let white = CGColor(srgbRed: 1, green: 1, blue: 1, alpha: 1)
    static let green = CGColor(srgbRed: 0.247, green: 0.698, blue: 0.310, alpha: 1)
    static let yellow = CGColor(srgbRed: 0.949, green: 0.761, blue: 0.188, alpha: 1)
    static let orange = CGColor(srgbRed: 0.941, green: 0.541, blue: 0.173, alpha: 1)
    static let red = CGColor(srgbRed: 0.886, green: 0.271, blue: 0.231, alpha: 1)

    /// Where the game picture goes: the whole frame (wide), or full width in the middle (tall).
    var video: CGRect {
        if shape == .wide { return CGRect(origin: .zero, size: size) }
        let h = size.width * 9 / 16
        return CGRect(x: 0, y: (size.height - h) / 2 - 40, width: size.width, height: h)
    }
    /// Letter sizes are given for the wide frame's 720-pixel height; the tall frame's middle picture scales them.
    private var k: CGFloat { video.height / 720 }

    // MARK: frames

    func title(_ ctx: CGContext, background: CGImage?, t: Double) {
        backdrop(ctx)
        if let background { image(ctx, background, in: video) }
        ctx.setFillColor(Self.navy.copy(alpha: 0.55)!); ctx.fill(video)
        let c = CGPoint(x: video.midX, y: video.midY)
        let rise = ease(min(1, t / 0.4))
        pill(ctx, "\(card.date)  ·  #\(card.number)", center: CGPoint(x: c.x, y: c.y - 120 * k), size: 30 * k)
        text(ctx, "DAILY HOLE IN ONE", center: CGPoint(x: c.x, y: c.y - 10 * k + (1 - rise) * 40 * k), size: 92 * k, fill: Self.white)
        text(ctx, "3 SHOTS  ·  \(DailyShareText.points(DailyHoleInOne.maxTotal)) UP FOR GRABS", center: CGPoint(x: c.x, y: c.y + 86 * k), size: 40 * k, fill: Self.gold)
        frame(ctx, shot: nil)
    }

    /// A shot's frame: the picture, which shot it is, and once the ball has stopped (`sinceRest` ≥ 0) what it scored.
    func shot(_ ctx: CGContext, frame picture: CGImage, clip: DailyShotClip, sinceRest: Double?) {
        backdrop(ctx)
        image(ctx, picture, in: video)
        // (the game's own HUD is in the picture: club and power on the left, wind and the map top right, so the stamps
        // keep to the top middle and the lower middle)
        let v = video, pad = 30 * k
        if shape == .wide { pill(ctx, "SHOT \(clip.shot + 1) OF \(DailyHoleInOne.shotCount)", center: CGPoint(x: v.midX, y: v.minY + pad + 21 * k), size: 26 * k) }
        if let s = sinceRest, s >= 0 {
            let pop = 1 + 0.35 * (1 - ease(min(1, s / 0.28)))   // a stamp that lands
            let points = "+\(DailyShareText.points(clip.points))"
            if clip.points >= DailyHoleInOne.maxShot {
                text(ctx, "HOLE IN ONE!", center: CGPoint(x: v.midX, y: v.midY - 30 * k), size: 120 * k * pop, fill: Self.gold)
                text(ctx, points, center: CGPoint(x: v.midX, y: v.midY + 80 * k), size: 64 * k * pop, fill: Self.white)
            } else {
                let words = DailyShareText.shotWords(points: clip.points, feet: clip.feet)
                text(ctx, words, center: CGPoint(x: v.midX, y: v.maxY - 200 * k), size: 84 * k * pop, fill: Self.white)
                text(ctx, points, center: CGPoint(x: v.midX, y: v.maxY - 118 * k), size: 56 * k * pop, fill: Self.gold)
            }
        }
        mark(ctx)
        frame(ctx, shot: clip.shot)
    }

    func end(_ ctx: CGContext, t: Double) {
        backdrop(ctx)
        if shape == .wide { ctx.drawLinearGradient(gradient, start: .zero, end: CGPoint(x: 0, y: size.height), options: []) }
        // (the tall frame's card fills the frame, letters half again as big)
        let c = CGPoint(x: size.width / 2, y: size.height / 2 - (shape == .tall ? 60 : 0))
        let k = shape == .tall ? self.k * 1.55 : self.k
        let count = Int(Double(card.total) * ease(min(1, t / 0.9)))   // the total counts up
        text(ctx, DailyShareText.points(count), center: CGPoint(x: c.x, y: c.y - 120 * k), size: 150 * k, fill: Self.white)
        text(ctx, "/ \(DailyShareText.points(DailyHoleInOne.maxTotal))", center: CGPoint(x: c.x, y: c.y - 30 * k), size: 40 * k, fill: Self.white)
        squares(ctx, center: CGPoint(x: c.x, y: c.y + 46 * k), side: 54 * k)
        text(ctx, "CAN YOU BEAT IT?", center: CGPoint(x: c.x, y: c.y + 140 * k), size: 64 * k, fill: Self.gold)
        let rank = card.top.flatMap { $0 > 0 ? "Top \($0)% in the world today" : nil }
        let name = "Daily Hole in One #\(card.number)  ·  MotionSports"
        if shape == .tall {   // (two lines: one would run off a phone-width frame)
            if let rank { text(ctx, rank, center: CGPoint(x: c.x, y: c.y + 214 * k), size: 26 * k, fill: Self.white, stroke: 0) }
            text(ctx, name, center: CGPoint(x: c.x, y: c.y + (rank == nil ? 214 : 254) * k), size: 26 * k, fill: Self.white, stroke: 0)
        } else {
            text(ctx, [rank, name].compactMap { $0 }.joined(separator: "  ·  "), center: CGPoint(x: c.x, y: c.y + 214 * k), size: 26 * k, fill: Self.white, stroke: 0)
        }
    }

    // MARK: the tall frame's header and footer (static around the picture)

    private func frame(_ ctx: CGContext, shot: Int?) {
        guard shape == .tall else { return }
        let top = video.minY, bottom = video.maxY, x = size.width / 2
        pill(ctx, "DAILY HOLE IN ONE #\(card.number)", center: CGPoint(x: x, y: top - 300), size: 34)
        text(ctx, shot == nil ? "3 SHOTS" : "SHOT \(shot! + 1) OF 3", center: CGPoint(x: x, y: top - 190), size: 88, fill: Self.white)
        text(ctx, "Same 3 shots for everyone today", center: CGPoint(x: x, y: top - 105), size: 34, fill: Self.white, stroke: 0)
        text(ctx, "CAN YOU BEAT", center: CGPoint(x: x, y: bottom + 140), size: 74, fill: Self.gold)
        text(ctx, "MY SCORE?", center: CGPoint(x: x, y: bottom + 226), size: 74, fill: Self.gold)
        mark(ctx, at: CGPoint(x: x, y: bottom + 340), size: 40, centered: true)
    }

    // MARK: pieces

    private var gradient: CGGradient { CGGradient(colorsSpace: CGColorSpace(name: CGColorSpace.sRGB), colors: [Self.navyTop, Self.navy] as CFArray, locations: [0, 1])! }
    private func backdrop(_ ctx: CGContext) {
        ctx.setFillColor(Self.navy); ctx.fill(CGRect(origin: .zero, size: size))
        if shape == .tall { ctx.drawLinearGradient(gradient, start: .zero, end: CGPoint(x: 0, y: size.height), options: []) }
    }
    private func ease(_ x: Double) -> CGFloat { CGFloat(1 - pow(1 - x, 3)) }

    /// An image into `rect`, filling it (cropped from the middle, never squashed), the right way up in the flipped context.
    private func image(_ ctx: CGContext, _ img: CGImage, in rect: CGRect) {
        let s = max(rect.width / CGFloat(img.width), rect.height / CGFloat(img.height))
        let w = CGFloat(img.width) * s, h = CGFloat(img.height) * s
        ctx.saveGState(); ctx.clip(to: rect)
        ctx.translateBy(x: rect.midX - w / 2, y: rect.midY + h / 2); ctx.scaleBy(x: 1, y: -1)
        ctx.interpolationQuality = .high
        ctx.draw(img, in: CGRect(x: 0, y: 0, width: w, height: h))
        ctx.restoreGState()
    }

    static func font(_ size: CGFloat) -> CTFont {
        let f = CTFontCreateWithName("Fredoka-Bold" as CFString, size, nil)
        if (CTFontCopyPostScriptName(f) as String).hasPrefix("Fredoka") { return f }
        if let url = Bundle.main.url(forResource: "Fredoka-Bold", withExtension: "ttf") {
            CTFontManagerRegisterFontsForURL(url as CFURL, .process, nil)
            let again = CTFontCreateWithName("Fredoka-Bold" as CFString, size, nil)
            if (CTFontCopyPostScriptName(again) as String).hasPrefix("Fredoka") { return again }
        }
        return CTFontCreateUIFontForLanguage(.emphasizedSystem, size, nil) ?? f
    }

    private func line(_ s: String, size: CGFloat, fill: CGColor, stroke: CGFloat) -> (CTLine, CTLine?) {
        let font = Self.font(size)
        let base: [NSAttributedString.Key: Any] = [NSAttributedString.Key(kCTFontAttributeName as String): font,
                                                   NSAttributedString.Key(kCTForegroundColorAttributeName as String): fill]
        let filled = CTLineCreateWithAttributedString(NSAttributedString(string: s, attributes: base))
        guard stroke > 0 else { return (filled, nil) }
        var outline = base
        outline[NSAttributedString.Key(kCTStrokeWidthAttributeName as String)] = NSNumber(value: Double(stroke))
        outline[NSAttributedString.Key(kCTStrokeColorAttributeName as String)] = Self.outline
        return (filled, CTLineCreateWithAttributedString(NSAttributedString(string: s, attributes: outline)))
    }

    /// Text centred on `center` (its middle), with the game's navy outline.
    private func text(_ ctx: CGContext, _ s: String, center: CGPoint, size: CGFloat, fill: CGColor, stroke: CGFloat = 14) {
        let (filled, outline) = line(s, size: size, fill: fill, stroke: stroke)
        let width = CTLineGetTypographicBounds(filled, nil, nil, nil)
        draw(ctx, filled, outline, at: CGPoint(x: center.x - CGFloat(width) / 2, y: center.y), size: size)
    }
    /// Text from `left` (its left edge, its middle height).
    private func text(_ ctx: CGContext, _ s: String, left: CGPoint, size: CGFloat, fill: CGColor, stroke: CGFloat = 14) {
        let (filled, outline) = line(s, size: size, fill: fill, stroke: stroke)
        draw(ctx, filled, outline, at: left, size: size)
    }
    private func draw(_ ctx: CGContext, _ filled: CTLine, _ outline: CTLine?, at p: CGPoint, size: CGFloat) {
        ctx.saveGState()
        ctx.textMatrix = CGAffineTransform(scaleX: 1, y: -1)
        let baseline = p.y + size * 0.34
        if let outline {
            // a thick outline under the letters, then a little drop below it, as the game letters them
            ctx.setLineJoin(.round)
            ctx.textPosition = CGPoint(x: p.x, y: baseline + size * 0.05); CTLineDraw(outline, ctx)
            ctx.textPosition = CGPoint(x: p.x, y: baseline); CTLineDraw(outline, ctx)
        }
        ctx.textPosition = CGPoint(x: p.x, y: baseline); CTLineDraw(filled, ctx)
        ctx.restoreGState()
    }

    /// A gold tag: "NOV 21 · #7".
    private func pill(_ ctx: CGContext, _ s: String, center: CGPoint, size: CGFloat) {
        let (filled, _) = line(s, size: size, fill: Self.outline, stroke: 0)
        let width = CGFloat(CTLineGetTypographicBounds(filled, nil, nil, nil))
        pill(ctx, s, at: CGPoint(x: center.x - width / 2 - size * 0.7, y: center.y - size * 0.8), size: size)
    }
    private func pill(_ ctx: CGContext, _ s: String, at origin: CGPoint, size: CGFloat) {
        let (filled, _) = line(s, size: size, fill: Self.outline, stroke: 0)
        let width = CGFloat(CTLineGetTypographicBounds(filled, nil, nil, nil))
        let r = CGRect(x: origin.x, y: origin.y, width: width + size * 1.4, height: size * 1.6)
        ctx.setFillColor(Self.gold); ctx.addPath(CGPath(roundedRect: r, cornerWidth: r.height / 2, cornerHeight: r.height / 2, transform: nil)); ctx.fillPath()
        draw(ctx, filled, nil, at: CGPoint(x: r.minX + size * 0.7, y: r.midY), size: size)
    }

    /// The Wordle-style squares, one per shot.
    private func squares(_ ctx: CGContext, center: CGPoint, side: CGFloat) {
        let n = card.points.count, gap = side * 0.28
        var x = center.x - (CGFloat(n) * side + CGFloat(n - 1) * gap) / 2
        for i in 0..<n {
            let p = card.points[i], f = i < card.feet.count ? card.feet[i] : -1
            let r = CGRect(x: x, y: center.y - side / 2, width: side, height: side)
            let color: CGColor = p >= DailyHoleInOne.maxShot ? Self.white : (f < 0 ? Self.red : f < 10 ? Self.green : f < 30 ? Self.yellow : Self.orange)
            ctx.setFillColor(color); ctx.addPath(CGPath(roundedRect: r, cornerWidth: side * 0.18, cornerHeight: side * 0.18, transform: nil)); ctx.fillPath()
            if p >= DailyHoleInOne.maxShot { flag(ctx, in: r) }
            x += side + gap
        }
    }
    /// A little red flag on its pin, drawn (emoji do not draw reliably into a video frame).
    private func flag(_ ctx: CGContext, in r: CGRect) {
        let pole = CGRect(x: r.minX + r.width * 0.36, y: r.minY + r.height * 0.18, width: max(2, r.width * 0.07), height: r.height * 0.64)
        ctx.setFillColor(Self.outline); ctx.fill(pole)
        ctx.setFillColor(Self.red)
        ctx.move(to: CGPoint(x: pole.maxX, y: pole.minY)); ctx.addLine(to: CGPoint(x: r.minX + r.width * 0.8, y: pole.minY + r.height * 0.16))
        ctx.addLine(to: CGPoint(x: pole.maxX, y: pole.minY + r.height * 0.32)); ctx.closePath(); ctx.fillPath()
    }

    /// "MotionSports", bottom right of the picture (or where asked).
    private func mark(_ ctx: CGContext, at p: CGPoint? = nil, size: CGFloat? = nil, centered: Bool = false) {
        let s = size ?? 30 * k
        let (motion, motionOutline) = line("Motion", size: s, fill: Self.white, stroke: 8)
        let (sports, sportsOutline) = line("Sports", size: s, fill: Self.gold, stroke: 8)
        let a = CGFloat(CTLineGetTypographicBounds(motion, nil, nil, nil)), b = CGFloat(CTLineGetTypographicBounds(sports, nil, nil, nil))
        let origin = p.map { CGPoint(x: centered ? $0.x - (a + b) / 2 : $0.x, y: $0.y) }
            ?? CGPoint(x: video.maxX - a - b - 30 * k, y: video.maxY - 34 * k)
        draw(ctx, motion, motionOutline, at: origin, size: s)
        draw(ctx, sports, sportsOutline, at: CGPoint(x: origin.x + a, y: origin.y), size: s)
    }
}
