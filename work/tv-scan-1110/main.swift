// Scan bench: phone-camera frames of a TV in a room (from Blender renders) through each TV-scan method.
// Usage: bench <render_dir> <assets_dir> <out_dir> [previewCount]
import Foundation
import CoreImage
import CoreImage.CIFilterBuiltins
import CoreGraphics
import ImageIO
import UniformTypeIdentifiers
import Vision
import CoreVideo
import simd

// MARK: - Linear float images

struct RGBF { var w: Int; var h: Int; var p: [Float] }   // linear RGB, 3 floats a pixel, row 0 at the top

func loadLinear(_ url: URL) -> RGBF {
    let src = CGImageSourceCreateWithURL(url as CFURL, nil)!
    let cg = CGImageSourceCreateImageAtIndex(src, 0, [kCGImageSourceShouldAllowFloat: true] as CFDictionary)!
    return linear(cg)
}
func linear(_ cg: CGImage) -> RGBF {
    let w = cg.width, h = cg.height
    var rgba = [Float](repeating: 0, count: w * h * 4)
    let space = CGColorSpace(name: CGColorSpace.extendedLinearSRGB)!
    rgba.withUnsafeMutableBytes { raw in
        let ctx = CGContext(data: raw.baseAddress, width: w, height: h, bitsPerComponent: 32, bytesPerRow: w * 16, space: space,
                            bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue | CGBitmapInfo.floatComponents.rawValue | CGBitmapInfo.byteOrder32Little.rawValue)!
        ctx.draw(cg, in: CGRect(x: 0, y: 0, width: w, height: h))
    }
    var p = [Float](repeating: 0, count: w * h * 3)
    for i in 0..<(w * h) { p[i * 3] = rgba[i * 4]; p[i * 3 + 1] = rgba[i * 4 + 1]; p[i * 3 + 2] = rgba[i * 4 + 2] }
    return RGBF(w: w, h: h, p: p)
}

// MARK: - Screen content with mip levels

struct Tex {
    var levels: [RGBF]
    init(_ base: RGBF) {
        levels = [base]
        while let last = levels.last, last.w > 4, last.h > 4 {
            let w = last.w / 2, h = last.h / 2
            var p = [Float](repeating: 0, count: w * h * 3)
            for y in 0..<h { for x in 0..<w { for c in 0..<3 {
                let a = last.p[((2 * y) * last.w + 2 * x) * 3 + c], b = last.p[((2 * y) * last.w + 2 * x + 1) * 3 + c]
                let d = last.p[((2 * y + 1) * last.w + 2 * x) * 3 + c], e = last.p[((2 * y + 1) * last.w + 2 * x + 1) * 3 + c]
                p[(y * w + x) * 3 + c] = (a + b + d + e) / 4 } } }
            levels.append(RGBF(w: w, h: h, p: p))
        }
    }
    func bilinear(_ l: RGBF, _ u: Float, _ v: Float) -> SIMD3<Float> {
        let x = min(Float(l.w - 1), max(0, u * Float(l.w) - 0.5)), y = min(Float(l.h - 1), max(0, (1 - v) * Float(l.h) - 0.5))
        let x0 = Int(x), y0 = Int(y), x1 = min(l.w - 1, x0 + 1), y1 = min(l.h - 1, y0 + 1)
        let fx = x - Float(x0), fy = y - Float(y0)
        func at(_ x: Int, _ y: Int) -> SIMD3<Float> { let i = (y * l.w + x) * 3; return SIMD3(l.p[i], l.p[i + 1], l.p[i + 2]) }
        return (at(x0, y0) * (1 - fx) + at(x1, y0) * fx) * (1 - fy) + (at(x0, y1) * (1 - fx) + at(x1, y1) * fx) * fy
    }
    /// `footprint`: texels of the base level per output pixel.
    func sample(_ u: Float, _ v: Float, footprint: Float) -> SIMD3<Float> {
        let lod = max(0, log2(max(1, footprint)))
        let l0 = min(levels.count - 1, Int(lod)), l1 = min(levels.count - 1, l0 + 1), f = lod - Float(Int(lod))
        return bilinear(levels[l0], u, v) * (1 - f) + bilinear(levels[l1], u, v) * f
    }
}

/// The room with the screen showing `tex` (nil: screen off), room light scaled by `kRoom`.
func composite(room: RGBF, uv: RGBF?, tex: Tex?, kRoom: Float, kTV: Float = 1) -> RGBF {
    var out = room
    for i in 0..<out.p.count { out.p[i] *= kRoom }
    guard let uv, let tex else { return out }
    let w = uv.w, h = uv.h, tw = Float(tex.levels[0].w), th = Float(tex.levels[0].h)
    func uvAt(_ x: Int, _ y: Int) -> SIMD2<Float>? {
        guard x >= 0, y >= 0, x < w, y < h else { return nil }
        let i = (y * w + x) * 3, cov = uv.p[i + 2]
        return cov > 0.5 ? SIMD2(uv.p[i] / cov, uv.p[i + 1] / cov) : nil
    }
    for y in 0..<h { for x in 0..<w {
        let i = (y * w + x) * 3, cov = uv.p[i + 2]
        guard cov > 0.002 else { continue }
        let u = uv.p[i] / cov, v = uv.p[i + 1] / cov
        var fp: Float = 1
        let here = SIMD2<Float>(u, v)
        for (dx, dy) in [(1, 0), (-1, 0), (0, 1), (0, -1)] {
            if let n = uvAt(x + dx, y + dy) { fp = max(fp, abs(n.x - here.x) * tw, abs(n.y - here.y) * th) }
        }
        let c = tex.sample(u, v, footprint: fp) * kTV * min(1, cov)
        out.p[i] += c.x; out.p[i + 1] += c.y; out.p[i + 2] += c.z
    } }
    return out
}

func luminance(_ img: RGBF, _ i: Int) -> Float { 0.2126 * img.p[i * 3] + 0.7152 * img.p[i * 3 + 1] + 0.0722 * img.p[i * 3 + 2] }

/// Centre-weighted average metering to mid grey, `bias` EV.
func meter(_ img: RGBF, bias: Float) -> Float {
    var sum: Float = 0, wsum: Float = 0
    for y in stride(from: 0, to: img.h, by: 4) { for x in stride(from: 0, to: img.w, by: 4) {
        let dx = (Float(x) / Float(img.w) - 0.5) / 0.35, dy = (Float(y) / Float(img.h) - 0.5) / 0.35
        let wgt = exp(-(dx * dx + dy * dy) / 2)
        sum += wgt * luminance(img, y * img.w + x); wsum += wgt
    } }
    return min(400, max(0.05, 0.18 / max(1e-6, sum / wsum) * pow(2, bias)))
}

struct Shot { var gain: Float; var blur: Float; var blurAngle: Float; var shift: SIMD2<Float>; var seed: UInt64; var outW: Int; var outH: Int }

struct Rand { var s: UInt64
    mutating func next() -> UInt64 { s ^= s << 13; s ^= s >> 7; s ^= s << 17; return s }
    mutating func uniform() -> Float { Float(next() % 1_000_000) / 1_000_000 }
    mutating func gauss() -> Float { let u = max(1e-6, uniform()), v = uniform(); return sqrt(-2 * log(u)) * cos(2 * .pi * v) }
}

/// Phone camera: hand blur and shake (optics), exposure, clipping, the ISP's downscale, tone curve and noise; 8-bit sRGB out.
func camera(_ img: RGBF, _ s: Shot) -> [UInt8] {
    let w = img.w, h = img.h
    // motion blur along a line, `blur` px at the output scale, and a shift of the whole picture (hand shake between frames)
    let scale = Float(w) / Float(s.outW)
    let taps = max(1, Int(s.blur * scale))
    let dir = SIMD2<Float>(cos(s.blurAngle), sin(s.blurAngle))
    var blurred = [Float](repeating: 0, count: w * h * 3)
    for y in 0..<h { for x in 0..<w {
        var acc = SIMD3<Float>(0, 0, 0)
        for t in 0..<taps {
            let o = (Float(t) - Float(taps - 1) / 2) * dir + s.shift * scale
            let sx = min(w - 1, max(0, x + Int(o.x.rounded()))), sy = min(h - 1, max(0, y + Int(o.y.rounded())))
            let i = (sy * w + sx) * 3
            acc += SIMD3(img.p[i], img.p[i + 1], img.p[i + 2])
        }
        acc /= Float(taps)
        let i = (y * w + x) * 3
        blurred[i] = min(1, acc.x * s.gain); blurred[i + 1] = min(1, acc.y * s.gain); blurred[i + 2] = min(1, acc.z * s.gain)
    } }
    // downscale to the output size (box), tone curve, noise
    let fx = w / s.outW, fy = h / s.outH
    var out = [UInt8](repeating: 0, count: s.outW * s.outH * 3)
    var r = Rand(s: s.seed | 1)
    let sigma: Float = 1.2 + 0.5 * sqrt(max(1, s.gain))
    for y in 0..<s.outH { for x in 0..<s.outW { for c in 0..<3 {
        var acc: Float = 0
        for yy in 0..<fy { for xx in 0..<fx { acc += blurred[((y * fy + yy) * w + x * fx + xx) * 3 + c] } }
        acc /= Float(fx * fy)
        let srgb = acc <= 0.0031308 ? 12.92 * acc : 1.055 * pow(acc, 1 / 2.4) - 0.055
        out[(y * s.outW + x) * 3 + c] = UInt8(max(0, min(255, (srgb * 255 + r.gauss() * sigma).rounded())))
    } } }
    return out
}

/// The camera's 420f buffer (BT.601 full range), as AVFoundation hands it to the app.
func pixelBuffer(_ rgb: [UInt8], _ w: Int, _ h: Int) -> CVPixelBuffer {
    var pb: CVPixelBuffer?
    CVPixelBufferCreate(nil, w, h, kCVPixelFormatType_420YpCbCr8BiPlanarFullRange, [kCVPixelBufferIOSurfacePropertiesKey: [:]] as CFDictionary, &pb)
    let b = pb!
    CVPixelBufferLockBaseAddress(b, []); defer { CVPixelBufferUnlockBaseAddress(b, []) }
    let yp = CVPixelBufferGetBaseAddressOfPlane(b, 0)!.assumingMemoryBound(to: UInt8.self), yr = CVPixelBufferGetBytesPerRowOfPlane(b, 0)
    let cp = CVPixelBufferGetBaseAddressOfPlane(b, 1)!.assumingMemoryBound(to: UInt8.self), cr = CVPixelBufferGetBytesPerRowOfPlane(b, 1)
    for y in 0..<h { for x in 0..<w {
        let i = (y * w + x) * 3
        let R = Float(rgb[i]), G = Float(rgb[i + 1]), B = Float(rgb[i + 2])
        yp[y * yr + x] = UInt8(max(0, min(255, 0.299 * R + 0.587 * G + 0.114 * B)))
    } }
    for y in 0..<(h / 2) { for x in 0..<(w / 2) {
        var cb: Float = 0, crv: Float = 0
        for (dx, dy) in [(0, 0), (1, 0), (0, 1), (1, 1)] {
            let i = ((2 * y + dy) * w + 2 * x + dx) * 3
            let R = Float(rgb[i]), G = Float(rgb[i + 1]), B = Float(rgb[i + 2])
            cb += 128 - 0.168736 * R - 0.331264 * G + 0.5 * B; crv += 128 + 0.5 * R - 0.418688 * G - 0.081312 * B
        }
        cp[y * cr + 2 * x] = UInt8(max(0, min(255, cb / 4))); cp[y * cr + 2 * x + 1] = UInt8(max(0, min(255, crv / 4)))
    } }
    return b
}
func lumaPlane(_ rgb: [UInt8], _ w: Int, _ h: Int) -> [UInt8] {
    var y = [UInt8](repeating: 0, count: w * h)
    for i in 0..<(w * h) { y[i] = UInt8(max(0, min(255, 0.299 * Float(rgb[i * 3]) + 0.587 * Float(rgb[i * 3 + 1]) + 0.114 * Float(rgb[i * 3 + 2])))) }
    return y
}
func savePNG(_ rgb: [UInt8], _ w: Int, _ h: Int, _ url: URL) {
    var rgba = [UInt8](repeating: 255, count: w * h * 4)
    for i in 0..<(w * h) { rgba[i * 4] = rgb[i * 3]; rgba[i * 4 + 1] = rgb[i * 3 + 1]; rgba[i * 4 + 2] = rgb[i * 3 + 2] }
    let ctx = CGContext(data: &rgba, width: w, height: h, bitsPerComponent: 8, bytesPerRow: w * 4, space: CGColorSpace(name: CGColorSpace.sRGB)!,
                        bitmapInfo: CGImageAlphaInfo.noneSkipLast.rawValue)!
    let dest = CGImageDestinationCreateWithURL(url as CFURL, UTType.png.identifier as CFString, 1, nil)!
    CGImageDestinationAddImage(dest, ctx.makeImage()!, nil); CGImageDestinationFinalize(dest)
}

// MARK: - Screen pictures: the court, the scan card with a code, black and white

func cgImage(_ url: URL) -> CGImage { CGImageSourceCreateImageAtIndex(CGImageSourceCreateWithURL(url as CFURL, nil)!, 0, nil)! }

enum Code { case qr, aztec }
let payload = "MS1"
func codeImage(_ code: Code) -> CGImage {
    let ci: CIImage
    switch code {
    case .qr: let f = CIFilter.qrCodeGenerator(); f.message = payload.data(using: .ascii)!; f.correctionLevel = "M"; ci = f.outputImage!
    case .aztec: let f = CIFilter.aztecCodeGenerator(); f.message = payload.data(using: .ascii)!; f.compactStyle = 1; f.layers = 1; f.correctionLevel = 23; ci = f.outputImage!
    }
    return CIContext().createCGImage(ci, from: ci.extent)!
}
/// The TV during the scan: the court dimmed, a white card in the middle holding the code (`share` of the TV's height).
func scanCard(court: CGImage, code: CGImage, share: Double) -> CGImage {
    let w = 1920, h = 1080
    let ctx = CGContext(data: nil, width: w, height: h, bitsPerComponent: 8, bytesPerRow: w * 4, space: CGColorSpace(name: CGColorSpace.sRGB)!,
                        bitmapInfo: CGImageAlphaInfo.noneSkipLast.rawValue)!
    ctx.draw(court, in: CGRect(x: 0, y: 0, width: w, height: h))
    ctx.setFillColor(CGColor(gray: 0, alpha: 0.55)); ctx.fill(CGRect(x: 0, y: 0, width: w, height: h))
    let side = Double(h) * share
    let card = CGRect(x: (Double(w) - side) / 2, y: (Double(h) - side) / 2, width: side, height: side)
    ctx.setFillColor(CGColor(gray: 1, alpha: 1))
    ctx.addPath(CGPath(roundedRect: card, cornerWidth: side * 0.06, cornerHeight: side * 0.06, transform: nil)); ctx.fillPath()
    ctx.interpolationQuality = .none
    let inner = card.insetBy(dx: side * 0.08, dy: side * 0.08)
    ctx.draw(code, in: inner)
    return ctx.makeImage()!
}
func flat(_ v: CGFloat) -> CGImage {
    let ctx = CGContext(data: nil, width: 64, height: 36, bitsPerComponent: 8, bytesPerRow: 256, space: CGColorSpace(name: CGColorSpace.sRGB)!,
                        bitmapInfo: CGImageAlphaInfo.noneSkipLast.rawValue)!
    ctx.setFillColor(CGColor(gray: v, alpha: 1)); ctx.fill(CGRect(x: 0, y: 0, width: 64, height: 36)); return ctx.makeImage()!
}

// MARK: - Scan methods

enum Found { case at(SIMD2<Double>), none }

func detectCurrent(_ b: CVPixelBuffer) -> Found {
    if case .screen(let p) = SportsScreenFinder.find(b) { return .at(p) }; return .none
}
func detectOld(_ b: CVPixelBuffer) -> Found {
    if case .screen = OldScreenFinder.find(b) { return .at(SIMD2(0.5, 0.5)) }; return .none   // the old scan took the heading through the lens
}
func detectCode(_ b: CVPixelBuffer, _ symbology: VNBarcodeSymbology) -> Found {
    let request = VNDetectBarcodesRequest(); request.symbologies = [symbology]
    try? VNImageRequestHandler(cvPixelBuffer: b, orientation: .up).perform([request])
    for r in request.results ?? [] where r.payloadStringValue == payload {
        let bb = r.boundingBox
        // the code's middle: the mean of its four corners (Vision: origin bottom-left)
        let xs = [r.topLeft.x, r.topRight.x, r.bottomLeft.x, r.bottomRight.x], ys = [r.topLeft.y, r.topRight.y, r.bottomLeft.y, r.bottomRight.y]
        let cx = xs.reduce(0, +) / 4, cy = ys.reduce(0, +) / 4
        _ = bb
        return .at(SIMD2(Double(cx), 1 - Double(cy)))
    }
    return .none
}

/// Flash locate: the part of the picture that turned bright between a frame with the TV black and one with it white.
/// 8x8 blocks, the largest connected patch of blocks that brightened, which must be big and solid enough to be a screen.
struct FlashLocate {
    static let block = 8, minimumRise = 40.0, minimumShare = 0.004, minimumFill = 0.4
    static func find(dark: [UInt8], bright: [UInt8], w: Int, h: Int) -> Found {
        let bw = w / block, bh = h / block
        var rise = [Double](repeating: 0, count: bw * bh)
        for by in 0..<bh { for bx in 0..<bw {
            var s = 0
            for y in (by * block)..<(by * block + block) { for x in (bx * block)..<(bx * block + block) { s += Int(bright[y * w + x]) - Int(dark[y * w + x]) } }
            rise[by * bw + bx] = Double(s) / Double(block * block)
        } }
        let peak = rise.max() ?? 0
        let threshold = max(minimumRise, peak * 0.5)
        var label = [Int](repeating: -1, count: bw * bh)
        var best: (count: Int, sx: Double, sy: Double, sw: Double, minX: Int, maxX: Int, minY: Int, maxY: Int)?
        for start in 0..<(bw * bh) where rise[start] >= threshold && label[start] < 0 {
            var stack = [start]; label[start] = start
            var count = 0, sx = 0.0, sy = 0.0, sw = 0.0, minX = bw, maxX = 0, minY = bh, maxY = 0
            while let i = stack.popLast() {
                let x = i % bw, y = i / bw
                count += 1; sx += Double(x) * rise[i]; sy += Double(y) * rise[i]; sw += rise[i]
                minX = min(minX, x); maxX = max(maxX, x); minY = min(minY, y); maxY = max(maxY, y)
                for (dx, dy) in [(1, 0), (-1, 0), (0, 1), (0, -1)] {
                    let nx = x + dx, ny = y + dy
                    guard nx >= 0, ny >= 0, nx < bw, ny < bh else { continue }
                    let j = ny * bw + nx
                    if label[j] < 0 && rise[j] >= threshold { label[j] = start; stack.append(j) }
                }
            }
            if best == nil || count > best!.count { best = (count, sx, sy, sw, minX, maxX, minY, maxY) }
        }
        guard let b = best else { return .none }
        let share = Double(b.count) / Double(bw * bh)
        let fill = Double(b.count) / Double((b.maxX - b.minX + 1) * (b.maxY - b.minY + 1))
        guard share >= minimumShare, fill >= minimumFill else { return .none }
        return .at(SIMD2((b.sx / b.sw + 0.5) / Double(bw), (b.sy / b.sw + 0.5) / Double(bh)))
    }
}

// MARK: - Bench

struct Pose: Decodable { let name: String; let room: Int; let negative: Bool; let centre: [Double]; let corners: [[Double]]; let distance: Double
    let view_angle: Double; let roll: Double; let portrait: Bool; let tv_width: Double; let wall_mount: Bool; let hfov: Double }

func rayAngle(_ a: SIMD2<Double>, _ b: SIMD2<Double>, aspect: Double, hfov: Double) -> Double {
    let tw = tan(hfov / 2 * .pi / 180), th = tw / aspect
    func ray(_ p: SIMD2<Double>) -> SIMD3<Double> { simd_normalize(SIMD3((p.x - 0.5) * 2 * tw, (0.5 - p.y) * 2 * th, -1)) }
    return acos(min(1, max(-1, simd_dot(ray(a), ray(b))))) * 180 / .pi
}

let args = CommandLine.arguments
let renders = URL(fileURLWithPath: args[1]), assets = URL(fileURLWithPath: args[2]), outDir = URL(fileURLWithPath: args[3])
let previews = args.count > 4 ? Int(args[4])! : 6
try? FileManager.default.createDirectory(at: outDir, withIntermediateDirectories: true)
let poses = try! JSONDecoder().decode([Pose].self, from: Data(contentsOf: renders.appendingPathComponent("poses.json")))
let courts = ["loading-tennis-resort.jpg", "loading-tennis-volcano.jpg"].map { cgImage(assets.appendingPathComponent($0)) }
let courtTex = courts.map { Tex(linear($0)) }
let qrTex = courts.map { Tex(linear(scanCard(court: $0, code: codeImage(.qr), share: 0.72))) }
let aztecTex = courts.map { Tex(linear(scanCard(court: $0, code: codeImage(.aztec), share: 0.72))) }
let blackTex = Tex(linear(flat(0))), whiteTex = Tex(linear(flat(1)))
savePNG({ let c = scanCard(court: courts[0], code: codeImage(.qr), share: 0.72); let l = linear(c); return l.p.map { UInt8(max(0, min(255, ($0 <= 0.0031308 ? 12.92 * $0 : 1.055 * pow($0, 1 / 2.4) - 0.055) * 255))) } }(), 1920, 1080, outDir.appendingPathComponent("tv_scan_card_qr.png"))

struct Light { let name: String; let median: Float }
let lights = [Light(name: "bright", median: 0.10), Light(name: "dim", median: 0.012), Light(name: "dark", median: 0.0012)]
struct Exposure { let name: String; let bias: Float }
let exposures = [Exposure(name: "auto", bias: 0), Exposure(name: "minus2", bias: -2)]

// result rows: method, pose, light, exposure, found, error (deg), ms
var rows = [String]()
rows.append("method,pose,negative,light,exposure,res,found,error_deg,ms,distance,view_angle,tv_width,cx,cy,portrait")
let previewLock = NSLock(); var previewCount = 0
let rowLock = NSLock()

func timed<T>(_ f: () -> T) -> (T, Double) { let t0 = DispatchTime.now().uptimeNanoseconds; let r = f(); return (r, Double(DispatchTime.now().uptimeNanoseconds - t0) / 1e6) }

func evaluate(_ pi: Int) -> [String] {
    let pose = poses[pi]
    var rows = [String]()
    let room = loadLinear(renders.appendingPathComponent(pose.name + "_room.exr"))
    let uv = pose.negative ? nil : loadLinear(renders.appendingPathComponent(pose.name + "_uv.exr"))
    // the room's light level: scale so the median surface reads `median` of the TV's white
    var lum = [Float](); lum.reserveCapacity(room.w * room.h / 16)
    for y in stride(from: 0, to: room.h, by: 4) { for x in stride(from: 0, to: room.w, by: 4) { lum.append(luminance(room, y * room.w + x)) } }
    lum.sort(); let roomMedian = max(1e-6, lum[lum.count / 2])
    let truth = SIMD2(pose.centre[0], pose.centre[1])
    for light in lights { for exposure in exposures {
        let kRoom = light.median / roomMedian
        var rand = Rand(s: UInt64(pi * 7919 + 13) &* 2654435761 &+ UInt64(light.median * 1e5) &+ UInt64(exposure.bias + 9))
        let court = pi % 2
        func shot(_ img: RGBF, gain: Float, shift: SIMD2<Float> = .zero, w: Int = 640, h: Int = 480) -> [UInt8] {
            camera(img, Shot(gain: gain, blur: rand.uniform() * 3, blurAngle: rand.uniform() * .pi, shift: shift, seed: rand.next(), outW: w, outH: h))
        }
        func record(_ method: String, _ res: String, _ found: Found, _ ms: Double) {
            var f = 0, err = "", cx = "", cy = ""
            if case .at(let p) = found { f = 1; cx = String(format: "%.3f", p.x); cy = String(format: "%.3f", p.y)
                if !pose.negative { err = String(format: "%.2f", rayAngle(p, truth, aspect: 4.0 / 3, hfov: pose.hfov)) } }
            rows.append("\(method),\(pose.name),\(pose.negative ? 1 : 0),\(light.name),\(exposure.name),\(res),\(f),\(err),\(String(format: "%.1f", ms)),\(String(format: "%.2f", pose.distance)),\(String(format: "%.0f", pose.view_angle)),\(pose.tv_width),\(cx),\(cy),\(pose.portrait ? 1 : 0)")
        }
        // the court on the TV (or, for a negative, the TV out of view; plus the TV switched off)
        let courtScene = composite(room: room, uv: uv, tex: pose.negative ? nil : courtTex[court], kRoom: kRoom)
        let gain = meter(courtScene, bias: exposure.bias)
        let courtFrame = shot(courtScene, gain: gain)
        let courtBuffer = pixelBuffer(courtFrame, 640, 480)
        let (c1, t1) = timed { detectCurrent(courtBuffer) }; record("rectangle_any(current)", "640", c1, t1)
        let (c2, t2) = timed { detectOld(courtBuffer) }; record("rectangle_centred(old)", "640", c2, t2)
        if !pose.negative && exposure.bias == 0 {
            let offScene = composite(room: room, uv: uv, tex: blackTex, kRoom: kRoom)
            let offBuffer = pixelBuffer(shot(offScene, gain: meter(offScene, bias: 0)), 640, 480)
            let (o1, s1) = timed { detectCurrent(offBuffer) }; record("rectangle_any(current)|tv_off", "640", o1, s1)
            let (o2, s2) = timed { detectOld(offBuffer) }; record("rectangle_centred(old)|tv_off", "640", o2, s2)
        }
        // the scan card with a code
        for (name, texs, sym) in [("qr", qrTex, VNBarcodeSymbology.qr), ("aztec", aztecTex, VNBarcodeSymbology.aztec)] {
            let scene = composite(room: room, uv: uv, tex: pose.negative ? nil : texs[court], kRoom: kRoom)
            let g = meter(scene, bias: exposure.bias)
            for (w, h) in [(640, 480), (1280, 960)] {
                let buffer = pixelBuffer(shot(scene, gain: g, w: w, h: h), w, h)
                let (r, t) = timed { detectCode(buffer, sym) }; record("code_\(name)", "\(w)", r, t)
            }
        }
        // flash: exposure held from the court, the TV black then white, the hand moving a few pixels in between
        let dark = composite(room: room, uv: uv, tex: pose.negative ? nil : blackTex, kRoom: kRoom)
        let bright = composite(room: room, uv: uv, tex: pose.negative ? nil : whiteTex, kRoom: kRoom)
        let shake = SIMD2<Float>(rand.uniform() * 8 - 4, rand.uniform() * 8 - 4)
        let darkY = lumaPlane(shot(dark, gain: gain), 640, 480), brightY = lumaPlane(shot(bright, gain: gain, shift: shake), 640, 480)
        let (fl, tf) = timed { FlashLocate.find(dark: darkY, bright: brightY, w: 640, h: 480) }; record("flash_locate", "640", fl, tf)
        if !pose.negative {
            let dimmed = composite(room: room, uv: uv, tex: courtTex[court], kRoom: kRoom, kTV: 0.25)
            let dimY = lumaPlane(shot(dimmed, gain: gain), 640, 480), fullY = lumaPlane(shot(courtScene, gain: gain, shift: shake), 640, 480)
            let (sp, ts) = timed { FlashLocate.find(dark: dimY, bright: fullY, w: 640, h: 480) }; record("pulse_locate(court dim->full)", "640", sp, ts)
            // no flash, same shake: the court twice (must find nothing)
            let still = lumaPlane(shot(courtScene, gain: gain, shift: shake), 640, 480)
            let (nf, tn) = timed { FlashLocate.find(dark: lumaPlane(courtFrame, 640, 480), bright: still, w: 640, h: 480) }
            record("flash_locate|no_flash", "640", nf, tn)
        }
        previewLock.lock(); let wantPreview = previewCount < previews && exposure.bias == 0; if wantPreview { previewCount += 1 }; previewLock.unlock()
        if wantPreview {
            savePNG(courtFrame, 640, 480, outDir.appendingPathComponent("preview_\(pose.name)_\(light.name)_court.png"))
            let card = composite(room: room, uv: uv, tex: pose.negative ? nil : qrTex[court], kRoom: kRoom)
            savePNG(shot(card, gain: meter(card, bias: 0)), 640, 480, outDir.appendingPathComponent("preview_\(pose.name)_\(light.name)_qr.png"))
        }
    } }
    if pi % 10 == 0 { FileHandle.standardError.write("pose \(pi + 1)/\(poses.count)\n".data(using: .utf8)!) }
    return rows
}
DispatchQueue.concurrentPerform(iterations: poses.count) { pi in
    let r = evaluate(pi)
    rowLock.lock(); rows.append(contentsOf: r); rowLock.unlock()
}
try! rows.joined(separator: "\n").write(to: outDir.appendingPathComponent("results.csv"), atomically: true, encoding: .utf8)
print("rows \(rows.count - 1)")
