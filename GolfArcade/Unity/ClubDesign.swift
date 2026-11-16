import AVFoundation
import CoreText
import SwiftUI

// "Motion Club": the palette, the type (Rubik UI; the display face falls back to the system's rounded heavy) and the UI sounds
// that the menus still share. (Its screen scaffold, backdrops, crest, cards and buttons served only the "Coming soon" sport
// screen and left with it, 2026-11-15, with MenuArt/club-*.png / scene-*.jpg and the Bricolage font.)

enum Club {
    // Palette.
    static let lagoonDeep = Color(hex: "0A192D"), violet = Color(hex: "5B2BD9")
    static let coral = Color(hex: "FF7556"), green = Color(hex: "35B87E"), sun = Color(hex: "D7F044")
    static let cream = Color(hex: "FFF9EE"), ink = Color(hex: "10243D")
    static let sky = Color(hex: "35B8C7")

    // Type: Rubik (wght 300–900) for UI; `display` / `title` ask for a display face that is not bundled, so they get the system's rounded type.
    static func display(_ size: CGFloat, condensed: Bool = true) -> Font {
        ClubFonts.font(.display, size: size, weight: 800, width: condensed ? 78 : 100)
    }
    static func title(_ size: CGFloat) -> Font { ClubFonts.font(.display, size: size, weight: 760, width: 92) }
    static func ui(_ size: CGFloat, _ weight: CGFloat = 500) -> Font { ClubFonts.font(.ui, size: size, weight: weight, width: nil) }
    static func caps(_ size: CGFloat) -> Font { ClubFonts.font(.ui, size: size, weight: 700, width: nil) }
}

/// The bundled variable fonts, registered once and instanced at the exact axes asked for.
enum ClubFonts {
    enum Face { case display, ui }
    nonisolated(unsafe) private static var descriptors: [Face: CTFontDescriptor] = [:]
    nonisolated(unsafe) private static var registered = false

    static func register() {
        guard !registered else { return }
        registered = true
        for (face, file) in [(Face.ui, "Rubik")] {
            guard let url = Bundle.main.url(forResource: file, withExtension: "ttf") else { continue }
            CTFontManagerRegisterFontsForURL(url as CFURL, .process, nil)
            if let list = CTFontManagerCreateFontDescriptorsFromURL(url as CFURL) as? [CTFontDescriptor], let d = list.first {
                descriptors[face] = d
            }
        }
    }

    static func font(_ face: Face, size: CGFloat, weight: CGFloat, width: CGFloat?) -> Font {
        register()
        guard let base = descriptors[face] else {
            return .system(size: size, weight: weight > 650 ? .heavy : weight > 450 ? .semibold : .regular, design: .rounded)
        }
        var axes: [NSNumber: NSNumber] = [NSNumber(value: 0x77676874): NSNumber(value: Double(weight))]   // 'wght'
        if let width { axes[NSNumber(value: 0x77647468)] = NSNumber(value: Double(width)) }             // 'wdth'
        if face == .display { axes[NSNumber(value: 0x6F70737A)] = NSNumber(value: Double(min(96, max(12, size)))) } // 'opsz'
        let d = CTFontDescriptorCreateCopyWithAttributes(base, [kCTFontVariationAttribute: axes] as CFDictionary)
        return Font(CTFontCreateWithFontDescriptor(d, size, nil))
    }
}

/// UI sounds: tick on move, pop on select, whoosh between screens. Silent when Sound is off.
@MainActor
enum ClubSound {
    private static var players: [String: AVAudioPlayer] = [:]
    /// Makes and primes every player at launch, so the first tap is not late.
    static func preload() { for name in ["tick", "pop", "whoosh"] { _ = player(name) } }
    private static func player(_ name: String) -> AVAudioPlayer? {
        if players[name] == nil, let url = Bundle.main.url(forResource: name, withExtension: "wav") {
            players[name] = try? AVAudioPlayer(contentsOf: url)
            players[name]?.prepareToPlay()
        }
        return players[name]
    }
    static func play(_ name: String, volume: Float = 0.5) {
        guard SportsSession.shared.sound, let p = player(name) else { return }
        p.volume = volume; p.currentTime = 0; p.play()
    }
}


// MARK: - Island menus, drawn in the MotionSports brand (MotionBrand: Royal / Deep Navy, Kanit, white type, gold accents)
// The token names are the old Island ones so every screen follows: `navy` is the dark ink that sits on gold, `ink` is the
// white type on navy panels, `lime` is the gold accent, `paper` / `card` are the Deep Navy panels.
// Deliberately separate from Arcade: the in-match serve meter keeps its original tokens.
enum IslandUI {
    static let navy = MotionBrand.navyInk
    static let ink = Color.white
    static let lime = MotionBrand.gold
    static let paper = MotionBrand.navyDeep
    static let muted = MotionBrand.n300
    /// A chosen chip or the focused row: Lift on the navy, so it reads apart from the gold primary.
    static let selected = MotionBrand.lift
    static let shadow = MotionBrand.shadowInk
    static let danger = MotionBrand.error
    /// Kanit: Medium for body, SemiBold for labels, ExtraBold Italic for headline sizes (as the brand's headlines).
    static func font(_ size: CGFloat, bold: Bool = false) -> Font {
        MotionBrand.font(!bold ? .medium : size >= 24 ? .extraBoldItalic : .semiBold, size)
    }
}

struct IslandBackdrop: View {
    var intro = false
    var room: ClubRoom = .terrace
    var body: some View {
        Group {
            if !intro && room == .locker {
                ClubEnvironmentView(room: .locker)
            } else {
                ClubLivingImageView(room: intro ? .entrance : room)
            }
        }
        .ignoresSafeArea().accessibilityHidden(true).allowsHitTesting(false)
    }
}

struct IslandWordmark: View {
    var size: CGFloat = 36
    /// Now the MotionSports wordmark (the brand replaced the palm "Motion Club" mark).
    var body: some View { MotionWordmark(size: size) }
}

struct IslandAction: View {
    let title: String
    var focused = false
    var primary = false
    var tint: Color? = nil
    var compact = false
    var identifier = ""
    let action: () -> Void
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @ScaledMetric(relativeTo: .title3) private var typeScale = 1.0
    var body: some View {
        Button(action: action) {
            HStack(spacing: 16) {
                Text(title).font(IslandUI.font(compact ? 20 * min(typeScale, 1.5) : 27, bold: true)).lineLimit(1).minimumScaleFactor(0.8)
                Spacer(minLength: 10)
                if primary { Image(systemName: "play.fill").font(.system(size: 15, weight: .bold)) }
            }
            .foregroundStyle(primary ? IslandUI.navy : IslandUI.ink)
            .padding(.horizontal, 22).frame(minHeight: compact ? 48 : 58)
            .background(primary ? (tint ?? IslandUI.lime) : focused ? IslandUI.selected : IslandUI.paper, in: Capsule())
            .overlay(Capsule().strokeBorder(focused ? IslandUI.lime : primary ? .clear : IslandUI.ink, lineWidth: focused ? 3.5 : 2.5))
            .shadow(color: IslandUI.shadow.opacity(0.4), radius: 8, y: 6)
        }.buttonStyle(.plain).accessibilityLabel(title).accessibilityIdentifier(identifier)
            .accessibilityAddTraits(focused ? .isSelected : [])
            .animation(reduceMotion ? nil : .easeOut(duration: 0.15), value: focused)
    }
}

struct IslandShell<Content: View>: View {
    var title: String
    var compact: Bool
    @ViewBuilder var content: () -> Content
    var body: some View {
        ZStack {
            IslandBrandBackground()
            VStack(alignment: .leading, spacing: compact ? 18 : 24) {
                HStack(alignment: .center) {
                    if !compact { MotionWordmark(size: 30).padding(.trailing, 20); Rectangle().fill(.white.opacity(0.35)).frame(width: 2, height: 46).padding(.trailing, 20) }
                    Text(title).font(MotionBrand.font(.extraBoldItalic, compact ? 34 : 46)).foregroundStyle(IslandUI.ink)
                        .lineLimit(1).minimumScaleFactor(0.6)
                        .shadow(color: MotionBrand.textShadow.opacity(0.5), radius: 0, y: compact ? 2 : 3)
                    Spacer()
                }
                content().frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
            }.padding(.horizontal, compact ? 22 : 52).padding(.vertical, compact ? 22 : 36)
        }
        .foregroundStyle(IslandUI.ink)
        .preferredColorScheme(.dark)
    }
}

/// The brand's menu field (Deep Navy into Royal) with the soft Lift glow the pointer controller uses.
struct IslandBrandBackground: View {
    var body: some View {
        ZStack {
            MotionBrand.background
            RadialGradient(colors: [MotionBrand.lift.opacity(0.5), .clear], center: .init(x: 0.5, y: 0.35), startRadius: 0, endRadius: 420)
        }
        .ignoresSafeArea().allowsHitTesting(false).accessibilityHidden(true)
    }
}

struct IslandPlayer: View {
    let player: Player
    var sport: Sport? = nil
    var body: some View {
        GeometryReader { g in
            ZStack {
                CharacterModelPreview(player: player, cameraDistance: 2.95, outfitSport: sport ?? .tennis, idleSport: sport)
                    .accessibilityLabel("\(player.name), equipped character")
            }
        }
    }
}

struct IslandSelector: View {
    let label: String
    let value: String
    var swatch: Color? = nil
    var focused = false
    var compact = false
    let step: (Int) -> Void
    var body: some View {
        HStack(spacing: 12) {
            Text(label).font(IslandUI.font(compact ? 15 : 20, bold: true)).lineLimit(1).minimumScaleFactor(0.8)
            Spacer(minLength: 8)
            if let swatch { Circle().fill(swatch).frame(width: 23, height: 23).overlay(Circle().strokeBorder(IslandUI.ink.opacity(0.6))) }
            Button { step(-1) } label: { Image(systemName: "chevron.left").frame(width: 36, height: 44) }
                .accessibilityLabel("Previous \(label)")
            Text(value).font(IslandUI.font(compact ? 15 : 20, bold: true)).lineLimit(1).minimumScaleFactor(0.7)
                .frame(width: compact ? 96 : 152)
            Button { step(1) } label: { Image(systemName: "chevron.right").frame(width: 36, height: 44) }
                .accessibilityLabel("Next \(label)")
        }.buttonStyle(.plain).foregroundStyle(IslandUI.ink)
            .padding(.horizontal, compact ? 12 : 18)
            .islandFocus(focused, radius: 13)
            .accessibilityElement(children: .contain)
    }
}
