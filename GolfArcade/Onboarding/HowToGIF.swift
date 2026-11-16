import SwiftUI
import ImageIO

/// How to play, as a looping GIF of a player seen from behind in front of their TV (Adnan 2026-11-15: 2D GIFs made with GPT image
/// generation, shown only inside each sport's Tutorial lesson, in game). The files are GolfArcade/Onboarding/HowTo/howto-<sport>.gif
/// (brief: work/onboarding-v3/CODEX_PROMPT_HowToPlay_GIFs.md). A sport without its file shows nothing.
struct HowToGIF: UIViewRepresentable {
    let sport: Sport
    static func url(_ sport: Sport) -> URL? { stand[sport] ?? Bundle.main.url(forResource: "howto-\(sport.rawValue)", withExtension: "gif") }
    /// Snapshot tests: a stand-in GIF per sport (never set in the app).
    nonisolated(unsafe) static var stand: [Sport: URL] = [:]
    static func available(_ sport: Sport) -> Bool { url(sport) != nil }

    func makeUIView(context: Context) -> UIImageView {
        let view = UIImageView()
        view.contentMode = .scaleAspectFill
        view.clipsToBounds = true
        view.setContentCompressionResistancePriority(.defaultLow, for: .horizontal)
        view.setContentCompressionResistancePriority(.defaultLow, for: .vertical)
        view.image = Self.image(sport)
        return view
    }
    func updateUIView(_ view: UIImageView, context: Context) {}

    nonisolated(unsafe) private static var cache: [Sport: UIImage] = [:]
    /// The GIF's frames as one animated image (each frame held for its own delay).
    static func image(_ sport: Sport) -> UIImage? {
        if let hit = cache[sport] { return hit }
        guard let url = url(sport), let source = CGImageSourceCreateWithURL(url as CFURL, nil) else { return nil }
        var frames: [UIImage] = [], total = 0.0
        for i in 0..<CGImageSourceGetCount(source) {
            guard let cg = CGImageSourceCreateImageAtIndex(source, i, nil) else { continue }
            let props = CGImageSourceCopyPropertiesAtIndex(source, i, nil) as? [CFString: Any]
            let gif = props?[kCGImagePropertyGIFDictionary] as? [CFString: Any]
            let delay = (gif?[kCGImagePropertyGIFUnclampedDelayTime] as? Double) ?? (gif?[kCGImagePropertyGIFDelayTime] as? Double) ?? 0.1
            let held = max(0.02, delay)
            // UIImage.animatedImage plays frames evenly: repeat a frame for its longer holds (in 20 ms steps)
            for _ in 0..<max(1, Int((held / 0.02).rounded())) { frames.append(UIImage(cgImage: cg)) }
            total += held
        }
        guard !frames.isEmpty else { return nil }
        let image = UIImage.animatedImage(with: frames, duration: total)
        cache[sport] = image
        return image
    }
}

/// The GIF in a card with the brand's border (the lesson's first step on the TV or the phone).
struct HowToGIFCard: View {
    let sport: Sport
    var corner: CGFloat = 18
    var body: some View {
        if HowToGIF.available(sport) {
            Color.clear.aspectRatio(16 / 10, contentMode: .fit)
                .overlay { HowToGIF(sport: sport) }
                .clipShape(RoundedRectangle(cornerRadius: corner, style: .continuous))
                .overlay(RoundedRectangle(cornerRadius: corner, style: .continuous).strokeBorder(.white, lineWidth: 3))
                .accessibilityLabel("How to play \(sport.rawValue): a player seen from behind, swinging the phone 2 metres back from the TV")
        }
    }
}
