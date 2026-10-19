import Foundation
import AVFoundation
import ImageIO
import UniformTypeIdentifiers

@main struct ReviewVideo {
    static func main() async throws {
        let source = URL(fileURLWithPath: CommandLine.arguments[1])
        let out = URL(fileURLWithPath: CommandLine.arguments[2], isDirectory: true)
        try FileManager.default.createDirectory(at: out, withIntermediateDirectories: true)
        let asset = AVURLAsset(url: source)
        let duration = try await asset.load(.duration).seconds
        print("duration=\(duration)")
        let generator = AVAssetImageGenerator(asset: asset)
        generator.appliesPreferredTrackTransform = true
        generator.maximumSize = CGSize(width: 402, height: 874)
        for second in stride(from: 0.0, to: duration, by: 2.0) {
            let result = try await generator.image(at: CMTime(seconds: second, preferredTimescale: 600))
            let name = String(format: "frame-%03d.png", Int(second))
            let file = out.appendingPathComponent(name)
            let destination = CGImageDestinationCreateWithURL(file as CFURL, UTType.png.identifier as CFString, 1, nil)!
            CGImageDestinationAddImage(destination, result.image, nil)
            CGImageDestinationFinalize(destination)
        }
    }
}
