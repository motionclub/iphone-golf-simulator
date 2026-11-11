// Scan bench: phone-camera frames of a TV in a room (from Blender renders) through each TV-scan method.
// Usage: bench <render_dir> <assets_dir> <out_dir> [previewCount]
import Foundation
import CoreImage
import CoreImage.CIFilterBuiltins
import CoreGraphics
import ImageIO
import UniformTypeIdentifiers
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


struct Pose: Decodable { let name: String; let room: Int; let negative: Bool; let centre: [Double]; let corners: [[Double]]; let distance: Double
    let view_angle: Double; let roll: Double; let portrait: Bool; let tv_width: Double; let wall_mount: Bool; let hfov: Double }
func rayAngle(_ a: SIMD2<Double>, _ b: SIMD2<Double>, aspect: Double, hfov: Double) -> Double {
    let tw = tan(hfov / 2 * .pi / 180), th = tw / aspect
    func ray(_ p: SIMD2<Double>) -> SIMD3<Double> { simd_normalize(SIMD3((p.x - 0.5) * 2 * tw, (0.5 - p.y) * 2 * th, -1)) }
    return acos(min(1, max(-1, simd_dot(ray(a), ray(b))))) * 180 / .pi
}
let args = CommandLine.arguments
let renders = URL(fileURLWithPath: args[1]), assets = URL(fileURLWithPath: args[2])
let poses = try! JSONDecoder().decode([Pose].self, from: Data(contentsOf: renders.appendingPathComponent("poses.json")))
let courts = ["loading-tennis-resort.jpg", "loading-tennis-volcano.jpg"].map { cgImage(assets.appendingPathComponent($0)) }
let courtTex = courts.map { Tex(linear($0)) }
let blackTex = Tex(linear(flat(0))), whiteTex = Tex(linear(flat(1)))
let lights: [(String, Float)] = [("bright", 0.10), ("dim", 0.012), ("dark", 0.0012)]
let lock = NSLock(); var rows = ["case,pose,light,found,error_deg,delay_ms,true_ms"]
DispatchQueue.concurrentPerform(iterations: poses.count) { pi in
    let pose = poses[pi]
    let room = loadLinear(renders.appendingPathComponent(pose.name + "_room.exr"))
    let uv = pose.negative ? nil : loadLinear(renders.appendingPathComponent(pose.name + "_uv.exr"))
    var lum = [Float]()
    for y in stride(from: 0, to: room.h, by: 4) { for x in stride(from: 0, to: room.w, by: 4) { lum.append(luminance(room, y * room.w + x)) } }
    lum.sort(); let roomMedian = max(1e-6, lum[lum.count / 2])
    var out = [String]()
    for (li, light) in lights.enumerated() {
        let kRoom = light.1 / roomMedian
        var rand = Rand(s: UInt64(pi * 7919 + 13 + li * 101) &* 2654435761)
        let dark = composite(room: room, uv: uv, tex: pose.negative ? nil : blackTex, kRoom: kRoom)
        let bright = composite(room: room, uv: uv, tex: pose.negative ? nil : whiteTex, kRoom: kRoom)
        let court = composite(room: room, uv: uv, tex: pose.negative ? nil : courtTex[pi % 2], kRoom: kRoom)
        let gDark = meter(dark, bias: 0), gBright = meter(bright, bias: 0), gCourt = meter(court, bias: 0)
        let rendered = 100.0, delay = 0.06 + Double(rand.uniform()) * 0.2
        let sway = SIMD2<Float>(rand.uniform() * 80 - 40, rand.uniform() * 80 - 40)   // px/s at 640 wide: a hand not holding still
        for blink in [true, false] {
            if pose.negative && !blink { continue }
            var frames = [SportsScreenFinder.Frame](); var rowsCount = 0
            var t = rendered - 0.3
            while t <= rendered + 0.8 {
                let lit = blink && t >= rendered + delay && t < rendered + delay + 0.45
                let scene = blink ? (lit ? bright : dark) : court
                let ease = Float(min(1, max(0, (t - rendered - delay) / 0.3)))
                let gain = blink ? (lit ? gDark + (gBright - gDark) * ease : gDark) : gCourt
                let shift = sway * Float(t - rendered) + SIMD2<Float>(rand.uniform() * 4 - 2, rand.uniform() * 4 - 2)
                let rgb = camera(scene, Shot(gain: gain, blur: rand.uniform() * 3, blurAngle: rand.uniform() * .pi, shift: shift, seed: rand.next(), outW: 640, outH: 480))
                let g = SportsScreenFinder.grid(pixelBuffer(rgb, 640, 480))!
                rowsCount = g.rows; frames.append(.init(time: t, cells: g.cells, attitude: nil))
                t += 1.0 / 30
            }
            let seen = SportsScreenFinder.sighting(frames, rows: rowsCount, rendered: rendered)
            var err = "", dms = ""
            if let seen {
                dms = String(format: "%.0f", seen.delay * 1000)
                if !pose.negative {
                    // the truth where the picture was in the frame it was found in (the hand swayed)
                    let s = sway * Float(frames[seen.frame].time - rendered)
                    let truth = SIMD2(pose.centre[0] - Double(s.x) / 640, pose.centre[1] - Double(s.y) / 480)
                    err = String(format: "%.2f", rayAngle(seen.at, truth, aspect: 4.0 / 3, hfov: pose.hfov))
                }
            }
            out.append("\(pose.negative ? "no_tv" : blink ? "blink" : "no_blink"),\(pose.name),\(light.0),\(seen == nil ? 0 : 1),\(err),\(dms),\(String(format: "%.0f", delay * 1000))")
        }
    }
    lock.lock(); rows.append(contentsOf: out); lock.unlock()
}
try! rows.joined(separator: "\n").write(toFile: args[3], atomically: true, encoding: .utf8)
print("rows", rows.count - 1)
