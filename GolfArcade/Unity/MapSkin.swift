import CoreText
import SwiftUI
import UIKit

// UI OVERHAUL (Adnan 2026-11-15, "UI overhaul.zip" → 01 Current UI): every map dresses its own controller, HUD and loading screen
// in the material of its sculpted title (Tropical Resort's wood and waves, Sky Tower's lavender tower and clouds, Magma Crater's
// basalt and lava …). Map names stand alone, players are their usernames only (no YOU, no sport labels). The sculpted pieces
// (titles, name plates, event banners, cards, balls) are cut from the boards themselves (MapSkins/skin-*.png, Apple Vision subject
// lift, sample text painted out so the game writes live names on them); the rest is drawn here in each map's palette.
// Unity has the same skins (Assets/Scripts/UI/MapSkin.cs, Resources/MapSkins) for the TV.

/// One map's look.
struct MapSkin: Equatable, Identifiable {
    enum Sport: String { case tennis, golf, bowling }
    /// "tennis-resort", "golf-cliffside", "bowling-neon" (the asset names' key).
    let id: String
    let sport: Sport
    /// The map's name as it stands on its own ("Sky Tower").
    let title: String
    /// The controller's screen, top to bottom.
    let top: Color, bottom: Color
    /// The rim around the screen and the panels (wood, lavender tower, basalt, limestone …) and its shade.
    let frame: Color, frameDeep: Color
    /// Inner panels (the aim pad, the serve court) and their outline.
    let surface: Color, line: Color
    /// Cream pills and their type.
    let cream: Color, ink: Color
    /// The one big action (TOSS, TAP TO SWING, Hold to start): its face, its lip and its type.
    let accent: Color, accentDeep: Color, accentInk: Color
    /// The map's light: lava, neon, the tower's lamps (meter fills, rings, progress).
    let glow: Color
    /// Type on the sculpted plate: fill and outline.
    let plateText: Color, plateStroke: Color
    /// Type on the card (LAST THROW, the result card).
    let cardText: Color, cardStroke: Color
    /// Small flourishes in the controller's corners.
    let symbols: [String]
    let symbolColor: Color
    /// Where the name goes on the plate / event / card art (fractions of the image), from the boards (MapSkins/manifest.json).
    let plateBox: CGRect
    let eventBox: CGRect?
    let cardBox: CGRect?

    static func == (a: MapSkin, b: MapSkin) -> Bool { a.id == b.id }

    @MainActor var titleImage: UIImage? { MapSkin.image("skin-title-\(id)") }
    @MainActor var plateImage: UIImage? { MapSkin.image("skin-plate-\(id)") }
    @MainActor var eventImage: UIImage? { MapSkin.image("skin-event-\(id)") }
    @MainActor var cardImage: UIImage? { MapSkin.image("skin-card-\(id)") }
    @MainActor var ballImage: UIImage? { sport == .bowling ? MapSkin.image("skin-ball-\(id)") : nil }
    /// Loading art for this map (02 Loading art): one is picked per load.
    var loadingArt: [String] {
        switch id {
        case "tennis-resort": ["load-tennis-resort-forehand", "load-tennis-resort-volley"]
        case "tennis-skyscraper": ["load-tennis-rooftop-serve", "load-tennis-rooftop-stretch"]
        case "tennis-volcano": ["load-tennis-volcano-backhand"]
        case "golf-cliffside": ["load-golf-cliffside-male", "load-golf-cliffside-female"]
        case "golf-wildisles": ["load-golf-wildisles-male"]
        case "golf-magma": ["load-golf-magma-male", "load-golf-magma-female"]
        case "bowling-club": ["load-bowling-club-set"]
        case "bowling-neon": ["load-bowling-neon-release", "load-bowling-neon-strike"]
        case "bowling-tiki": ["load-bowling-tiki-approach"]
        default: ["load-bowling-magma-spare"]
        }
    }

    // MARK: lookup

    /// The skin for a sport's venue key (Unity's: tennis resort/skyscraper/volcano, golf cliffside/wildisles/magma, bowling
    /// club/neon/tiki/magma). Unknown keys fall back to the sport's first map.
    static func of(sport: String, venue: String) -> MapSkin {
        let s = sport == "golf" ? "golf" : sport == "bowling" ? "bowling" : "tennis"
        let key = s == "golf" ? MultiplayerLobby.currentGolfVenue(MultiplayerLobby.golfRoundParts(venue).course) : venue
        return all.first { $0.id == "\(s)-\(key)" } ?? all.first { $0.sport.rawValue == s }!
    }
    /// The map being played (or loading) now.
    @MainActor static var current: MapSkin {
        let s = SportsSession.shared
        return of(sport: s.sport, venue: s.sport == "golf" ? s.shownGolfCourse : s.sport == "bowling" ? s.bowlingVenue : s.tennisVenue)
    }

    // MARK: assets

    @MainActor private static var cache: [String: UIImage] = [:]
    @MainActor static func image(_ name: String) -> UIImage? {
        if let hit = cache[name] { return hit }
        guard let url = Bundle.main.url(forResource: name, withExtension: name.hasPrefix("load-") ? "jpg" : "png"),
              let image = UIImage(contentsOfFile: url.path) else { return nil }
        cache[name] = image
        return image
    }
}

// MARK: - The ten maps

extension MapSkin {
    private static func box(_ x0: CGFloat, _ y0: CGFloat, _ x1: CGFloat, _ y1: CGFloat) -> CGRect { CGRect(x: x0, y: y0, width: x1 - x0, height: y1 - y0) }

    static let all: [MapSkin] = [
        MapSkin(id: "tennis-resort", sport: .tennis, title: "Tropical Resort",
                top: Color(hex: "1E3C73"), bottom: Color(hex: "142A55"), frame: Color(hex: "D49553"), frameDeep: Color(hex: "8A5426"),
                surface: Color(hex: "1F4FA8"), line: Color(hex: "F4E3C3"), cream: Color(hex: "FFF1D8"), ink: Color(hex: "16264A"),
                accent: Color(hex: "35DCCB"), accentDeep: Color(hex: "1A9C93"), accentInk: Color(hex: "112A4C"), glow: Color(hex: "35DCCB"),
                plateText: Color(hex: "FFF1D8"), plateStroke: Color(hex: "0F2147"), cardText: Color(hex: "16264A"), cardStroke: Color(hex: "FFF6E6"),
                symbols: ["leaf.fill", "sun.max.fill", "water.waves"], symbolColor: Color(hex: "57B947"),
                plateBox: box(0.286, 0.473, 0.703, 0.665), eventBox: box(0.221, 0.448, 0.782, 0.714), cardBox: nil),
        MapSkin(id: "tennis-skyscraper", sport: .tennis, title: "Sky Tower",
                top: Color(hex: "2A2F72"), bottom: Color(hex: "1C2056"), frame: Color(hex: "A592E0"), frameDeep: Color(hex: "6A55B8"),
                surface: Color(hex: "2B66D8"), line: Color(hex: "E9E2FF"), cream: Color(hex: "FFF3DF"), ink: Color(hex: "1D2157"),
                accent: Color(hex: "4FE3EE"), accentDeep: Color(hex: "21A9BD"), accentInk: Color(hex: "16194B"), glow: Color(hex: "B9A6FF"),
                plateText: Color(hex: "FFF3DF"), plateStroke: Color(hex: "151946"), cardText: Color(hex: "1D2157"), cardStroke: Color(hex: "FFF6E6"),
                symbols: ["cloud.fill", "building.2.fill", "sparkle"], symbolColor: Color(hex: "E8E3FF"),
                plateBox: box(0.275, 0.514, 0.749, 0.751), eventBox: box(0.182, 0.485, 0.812, 0.875), cardBox: nil),
        MapSkin(id: "tennis-volcano", sport: .tennis, title: "Magma Crater",
                top: Color(hex: "2E2629"), bottom: Color(hex: "1D1719"), frame: Color(hex: "463A3D"), frameDeep: Color(hex: "1E1719"),
                surface: Color(hex: "3A3236"), line: Color(hex: "FF8B2B"), cream: Color(hex: "FFEBD2"), ink: Color(hex: "2A1B16"),
                accent: Color(hex: "FFA032"), accentDeep: Color(hex: "D2621A"), accentInk: Color(hex: "2A140A"), glow: Color(hex: "FF8B2B"),
                plateText: Color(hex: "FFEBD2"), plateStroke: Color(hex: "1E1416"), cardText: Color(hex: "FFEBD2"), cardStroke: Color(hex: "1E1416"),
                symbols: ["flame.fill", "mountain.2.fill", "sparkles"], symbolColor: Color(hex: "FF8B2B"),
                plateBox: box(0.283, 0.293, 0.816, 0.591), eventBox: box(0.242, 0.429, 0.805, 0.742), cardBox: nil),
        MapSkin(id: "golf-cliffside", sport: .golf, title: "Cliffside",
                top: Color(hex: "1A4F7A"), bottom: Color(hex: "103757"), frame: Color(hex: "EFE3C8"), frameDeep: Color(hex: "B8A57F"),
                surface: Color(hex: "1A5A88"), line: Color(hex: "D5ECF7"), cream: Color(hex: "FFF4DF"), ink: Color(hex: "123A5C"),
                accent: Color(hex: "33E0E4"), accentDeep: Color(hex: "1CA3B4"), accentInk: Color(hex: "0F3352"), glow: Color(hex: "33E0E4"),
                plateText: Color(hex: "143A5C"), plateStroke: Color(hex: "FFF6E4"), cardText: Color(hex: "143A5C"), cardStroke: Color(hex: "FFF6E4"),
                symbols: ["camera.macro", "leaf.fill", "water.waves"], symbolColor: Color(hex: "F59BBF"),
                plateBox: box(0.258, 0.408, 0.812, 0.741), eventBox: nil, cardBox: box(0.303, 0.129, 0.795, 0.524)),
        MapSkin(id: "golf-wildisles", sport: .golf, title: "Wild Isles",
                top: Color(hex: "2D7032"), bottom: Color(hex: "1C4B22"), frame: Color(hex: "E9D9B5"), frameDeep: Color(hex: "A88A5A"),
                surface: Color(hex: "2F7A35"), line: Color(hex: "D9F2B8"), cream: Color(hex: "FFF3DB"), ink: Color(hex: "1F4A1F"),
                accent: Color(hex: "86D52C"), accentDeep: Color(hex: "4E9A17"), accentInk: Color(hex: "173A12"), glow: Color(hex: "B7F05A"),
                plateText: Color(hex: "FFF3DB"), plateStroke: Color(hex: "1C4519"), cardText: Color(hex: "FFF3DB"), cardStroke: Color(hex: "1C4519"),
                symbols: ["leaf.fill", "tree.fill", "flag.fill"], symbolColor: Color(hex: "8FD45A"),
                plateBox: box(0.247, 0.366, 0.794, 0.671), eventBox: nil, cardBox: box(0.328, 0.236, 0.734, 0.546)),
        MapSkin(id: "golf-magma", sport: .golf, title: "Magma Open",
                top: Color(hex: "3D7A2A"), bottom: Color(hex: "275219"), frame: Color(hex: "3B3230"), frameDeep: Color(hex: "1C1514"),
                surface: Color(hex: "4C8A30"), line: Color(hex: "D7F0A5"), cream: Color(hex: "FFF0D6"), ink: Color(hex: "2A1E14"),
                accent: Color(hex: "FFA42A"), accentDeep: Color(hex: "D9641A"), accentInk: Color(hex: "2B1406"), glow: Color(hex: "FF8B22"),
                plateText: Color(hex: "FFF0D6"), plateStroke: Color(hex: "1F3A12"), cardText: Color(hex: "FFF0D6"), cardStroke: Color(hex: "1F3A12"),
                symbols: ["flame.fill", "flag.fill", "sparkles"], symbolColor: Color(hex: "FF9A2A"),
                plateBox: box(0.248, 0.381, 0.774, 0.642), eventBox: nil, cardBox: box(0.247, 0.24, 0.758, 0.589)),
        MapSkin(id: "bowling-club", sport: .bowling, title: "Club Lanes",
                top: Color(hex: "1E2756"), bottom: Color(hex: "131A3E"), frame: Color(hex: "8A5A30"), frameDeep: Color(hex: "4E2F16"),
                surface: Color(hex: "26306A"), line: Color(hex: "D9B25A"), cream: Color(hex: "FFF1D8"), ink: Color(hex: "1B2148"),
                accent: Color(hex: "FFF1D8"), accentDeep: Color(hex: "C9A464"), accentInk: Color(hex: "1B2148"), glow: Color(hex: "E9B949"),
                plateText: Color(hex: "FFF1D8"), plateStroke: Color(hex: "121838"), cardText: Color(hex: "1B2148"), cardStroke: Color(hex: "FFF6E6"),
                symbols: ["crown.fill", "star.fill", "sparkle"], symbolColor: Color(hex: "E9B949"),
                plateBox: box(0.232, 0.472, 0.803, 0.75), eventBox: nil, cardBox: box(0.175, 0.373, 0.834, 0.794)),
        MapSkin(id: "bowling-neon", sport: .bowling, title: "Neon Nights",
                top: Color(hex: "3A1266"), bottom: Color(hex: "1E0A3C"), frame: Color(hex: "8A4DFF"), frameDeep: Color(hex: "4A1E9A"),
                surface: Color(hex: "2C0E52"), line: Color(hex: "FF3EA5"), cream: Color(hex: "FFF1F8"), ink: Color(hex: "2A0B4D"),
                accent: Color(hex: "FF3EA5"), accentDeep: Color(hex: "B81A73"), accentInk: Color(hex: "FFFFFF"), glow: Color(hex: "2DE2F0"),
                plateText: Color(hex: "FFF1F8"), plateStroke: Color(hex: "D61F86"), cardText: Color(hex: "FFFFFF"), cardStroke: Color(hex: "2A0B4D"),
                symbols: ["bolt.fill", "star.fill", "sparkles"], symbolColor: Color(hex: "2DE2F0"),
                plateBox: box(0.208, 0.107, 0.87, 0.644), eventBox: nil, cardBox: box(0.146, 0.189, 0.873, 0.784)),
        MapSkin(id: "bowling-tiki", sport: .bowling, title: "Tiki Shores",
                top: Color(hex: "11535A"), bottom: Color(hex: "0A3A40"), frame: Color(hex: "E2AE4C"), frameDeep: Color(hex: "9A6A22"),
                surface: Color(hex: "136169"), line: Color(hex: "F3D489"), cream: Color(hex: "FFF1D6"), ink: Color(hex: "123B40"),
                accent: Color(hex: "FFF1D6"), accentDeep: Color(hex: "D7B57A"), accentInk: Color(hex: "123B40"), glow: Color(hex: "3FD8C8"),
                plateText: Color(hex: "FFF1D6"), plateStroke: Color(hex: "0C3A40"), cardText: Color(hex: "123B40"), cardStroke: Color(hex: "FFF6E6"),
                symbols: ["leaf.fill", "sun.max.fill", "camera.macro"], symbolColor: Color(hex: "F04848"),
                plateBox: box(0.255, 0.238, 0.769, 0.69), eventBox: nil, cardBox: box(0.195, 0.259, 0.848, 0.741)),
        MapSkin(id: "bowling-magma", sport: .bowling, title: "Magma Lanes",
                top: Color(hex: "40231D"), bottom: Color(hex: "241210"), frame: Color(hex: "5A3A2E"), frameDeep: Color(hex: "2A1712"),
                surface: Color(hex: "4A2B23"), line: Color(hex: "FF8B2B"), cream: Color(hex: "FFEBD2"), ink: Color(hex: "3A1F18"),
                accent: Color(hex: "FFEBD2"), accentDeep: Color(hex: "D9A877"), accentInk: Color(hex: "3A1F18"), glow: Color(hex: "FF8B2B"),
                plateText: Color(hex: "FFEBD2"), plateStroke: Color(hex: "241210"), cardText: Color(hex: "FFEBD2"), cardStroke: Color(hex: "241210"),
                symbols: ["flame.fill", "sparkles", "flame"], symbolColor: Color(hex: "FF8B2B"),
                plateBox: box(0.282, 0.402, 0.87, 0.687), eventBox: nil, cardBox: box(0.112, 0.179, 0.779, 0.632)),
    ]
}

// MARK: - Type

/// The sculpted lettering's live twin: Fredoka (OFL, Fonts/Fredoka-*.ttf), chunky and rounded; the system's rounded heavy if missing.
enum MapFont {
    nonisolated(unsafe) private static var registered = false
    static func register() {
        guard !registered else { return }
        registered = true
        for name in ["Fredoka-Bold", "Fredoka-SemiBold"] {
            if let url = Bundle.main.url(forResource: name, withExtension: "ttf") { CTFontManagerRegisterFontsForURL(url as CFURL, .process, nil) }
        }
    }
    static func bold(_ size: CGFloat) -> Font {
        register()
        return UIFont(name: "Fredoka-Bold", size: size) != nil ? .custom("Fredoka-Bold", fixedSize: size) : .system(size: size, weight: .heavy, design: .rounded)
    }
    static func semi(_ size: CGFloat) -> Font {
        register()
        return UIFont(name: "Fredoka-SemiBold", size: size) != nil ? .custom("Fredoka-SemiBold", fixedSize: size) : .system(size: size, weight: .bold, design: .rounded)
    }
    static func uiBold(_ size: CGFloat) -> UIFont {
        register()
        return UIFont(name: "Fredoka-Bold", size: size) ?? .systemFont(ofSize: size, weight: .heavy)
    }
}

/// Raised lettering: a fill, an outline all round and a soft drop, like the boards' sculpted type.
struct MapLetters: View {
    let text: String
    var size: CGFloat
    var fill: Color
    var stroke: Color
    var strokeWidth: CGFloat = 2.5
    var lines = 1
    var body: some View {
        let label = Text(text).font(MapFont.bold(size)).lineLimit(lines).minimumScaleFactor(0.4).multilineTextAlignment(.center)
        ZStack {
            ForEach(0..<8, id: \.self) { i in
                label.foregroundStyle(stroke)
                    .offset(x: cos(Double(i) * .pi / 4) * strokeWidth, y: sin(Double(i) * .pi / 4) * strokeWidth)
            }
            label.foregroundStyle(fill)
        }
        .shadow(color: .black.opacity(0.28), radius: 0, y: size * 0.06)
        .accessibilityElement(children: .ignore).accessibilityLabel(text)
    }
}

// MARK: - Sculpted pieces

/// A sculpted piece with live type in its window: the plate (a username), the event banner (POINT + name) or the card.
struct MapPlate: View {
    enum Kind { case plate, event, card }
    let skin: MapSkin
    var kind: Kind = .plate
    let text: String
    var height: CGFloat = 70
    var body: some View {
        let image = kind == .plate ? skin.plateImage : kind == .event ? skin.eventImage : skin.cardImage
        let box = (kind == .plate ? skin.plateBox : kind == .event ? skin.eventBox : skin.cardBox) ?? skin.plateBox
        let fill = kind == .card ? skin.cardText : skin.plateText, stroke = kind == .card ? skin.cardStroke : skin.plateStroke
        if let image {
            let width = height * image.size.width / max(1, image.size.height)
            Image(uiImage: image).resizable().interpolation(.high).frame(width: width, height: height)
                .overlay(alignment: .topLeading) {
                    MapLetters(text: text, size: box.height * height * 0.9, fill: fill, stroke: stroke, strokeWidth: max(1.2, height * 0.022))
                        .frame(width: box.width * width, height: box.height * height)
                        .offset(x: box.minX * width, y: box.minY * height)
                }
                .accessibilityElement(children: .ignore).accessibilityLabel(text)
        } else {
            MapLetters(text: text, size: height * 0.42, fill: skin.cream, stroke: skin.ink)
                .padding(.horizontal, 22).frame(height: height * 0.7)
                .background(skin.frame, in: Capsule())
        }
    }
}

/// The map's sculpted title (arrival, loading, results).
struct MapTitleArt: View {
    let skin: MapSkin
    var height: CGFloat = 120
    var body: some View {
        if let image = skin.titleImage {
            Image(uiImage: image).resizable().interpolation(.high).scaledToFit().frame(height: height)
                .shadow(color: .black.opacity(0.35), radius: 10, y: 6)
                .accessibilityLabel(skin.title).accessibilityIdentifier("map-title-\(skin.id)")
        } else {
            MapLetters(text: skin.title.uppercased(), size: height * 0.36, fill: skin.cream, stroke: skin.ink, lines: 2)
        }
    }
}

// MARK: - Controller chrome

/// The controller's screen: the map's colours, a rim of its material and its flourishes in the corners.
struct MapControllerBackground: View {
    let skin: MapSkin
    var body: some View {
        GeometryReader { g in
            ZStack {
                LinearGradient(colors: [skin.top, skin.bottom], startPoint: .top, endPoint: .bottom)
                RadialGradient(colors: [skin.glow.opacity(0.16), .clear], center: UnitPoint(x: 0.5, y: 0.42), startRadius: 0, endRadius: g.size.height * 0.55)
                // the rim: a band of the map's material just inside the screen's rounded edge
                RoundedRectangle(cornerRadius: 46, style: .continuous)
                    .strokeBorder(LinearGradient(colors: [skin.frame, skin.frameDeep], startPoint: .top, endPoint: .bottom), lineWidth: 9)
                    .overlay(RoundedRectangle(cornerRadius: 40, style: .continuous).strokeBorder(.black.opacity(0.22), lineWidth: 2).padding(9))
                    .padding(4)
                MapFlourishes(skin: skin, size: g.size)
            }
        }
        .ignoresSafeArea()
        .accessibilityHidden(true)
    }
}

/// The corner flourishes (leaves, clouds, flames, stars …) at the four corners, small and quiet.
private struct MapFlourishes: View {
    let skin: MapSkin
    let size: CGSize
    var body: some View {
        let s = skin.symbols
        ZStack {
            flourish(s[0], 34, x: 34, y: 92, angle: -28)
            flourish(s[1 % s.count], 22, x: 66, y: 64, angle: 12)
            flourish(s[0], 34, x: size.width - 34, y: 92, angle: 28, flip: true)
            flourish(s[2 % s.count], 22, x: size.width - 68, y: 64, angle: -10)
            flourish(s[0], 40, x: 32, y: size.height - 40, angle: 210)
            flourish(s[2 % s.count], 24, x: 72, y: size.height - 22, angle: 0)
            flourish(s[0], 40, x: size.width - 32, y: size.height - 40, angle: 150, flip: true)
            flourish(s[1 % s.count], 24, x: size.width - 74, y: size.height - 22, angle: 0)
        }
    }
    private func flourish(_ symbol: String, _ points: CGFloat, x: CGFloat, y: CGFloat, angle: Double, flip: Bool = false) -> some View {
        Image(systemName: symbol).font(.system(size: points, weight: .bold)).foregroundStyle(skin.symbolColor.opacity(0.85))
            .shadow(color: .black.opacity(0.3), radius: 0, y: 2)
            .scaleEffect(x: flip ? -1 : 1, y: 1).rotationEffect(.degrees(angle)).position(x: x, y: y)
    }
}

/// A cream pill (T, WIDE, ◀ ▶, Board 20, Frame 4 · Ball 1): the map's ink, a rim of its frame and a raised lip.
struct MapPill<Label: View>: View {
    let skin: MapSkin
    var height: CGFloat = 52
    var lit = false
    @ViewBuilder let label: () -> Label
    var body: some View {
        label()
            .font(MapFont.bold(height * 0.42)).foregroundStyle(lit ? skin.accentInk : skin.ink)
            .padding(.horizontal, height * 0.4).frame(minHeight: height)
            .background {
                Capsule().fill(skin.frameDeep).offset(y: 4)
                Capsule().fill(lit ? skin.accent : skin.cream)
                Capsule().strokeBorder(skin.frame, lineWidth: 2.5)
            }
    }
}

/// The one big action of a screen (TOSS, TAP TO SWING, Hold to start): the map's accent with a deep lip.
struct MapActionFace: View {
    let skin: MapSkin
    let title: String
    var subtitle: String? = nil
    var height: CGFloat = 96
    var pressed = false
    var live = false
    var body: some View {
        VStack(spacing: 2) {
            Text(title).font(MapFont.bold(subtitle == nil ? height * 0.42 : height * 0.32)).lineLimit(1).minimumScaleFactor(0.5)
            if let subtitle { Text(subtitle).font(MapFont.semi(height * 0.2)).lineLimit(1).minimumScaleFactor(0.6) }
        }
        .foregroundStyle(skin.accentInk)
        .frame(maxWidth: .infinity, minHeight: height)
        .background {
            Capsule().fill(skin.accentDeep).offset(y: pressed ? 2 : 7)
            Capsule().fill(LinearGradient(colors: [skin.accent.mix(.white, 0.25), skin.accent], startPoint: .top, endPoint: .bottom))
            Capsule().strokeBorder(.white.opacity(0.55), lineWidth: 2.5).padding(3)
            if live { Capsule().strokeBorder(skin.glow, lineWidth: 5).shadow(color: skin.glow, radius: 10) }
        }
        .offset(y: pressed ? 5 : 0)
    }
}

/// A rounded panel of the map's surface (the serve court, the aim pad, the rally card).
struct MapPanel: ViewModifier {
    let skin: MapSkin
    var radius: CGFloat = 22
    func body(content: Content) -> some View {
        content.background {
            RoundedRectangle(cornerRadius: radius, style: .continuous).fill(skin.frameDeep).offset(y: 4)
            RoundedRectangle(cornerRadius: radius, style: .continuous).fill(skin.surface)
            RoundedRectangle(cornerRadius: radius, style: .continuous).strokeBorder(skin.line.opacity(0.85), lineWidth: 2.5)
        }
    }
}
extension View {
    func mapPanel(_ skin: MapSkin, radius: CGFloat = 22) -> some View { modifier(MapPanel(skin: skin, radius: radius)) }
}

/// The round cream pause button the boards put top right.
struct MapPauseFace: View {
    let skin: MapSkin
    var size: CGFloat = 50
    var symbol = "pause.fill"
    var body: some View {
        Image(systemName: symbol).font(.system(size: size * 0.38, weight: .black)).foregroundStyle(skin.ink)
            .frame(width: size, height: size)
            .background {
                Circle().fill(skin.frameDeep).offset(y: 3)
                Circle().fill(skin.cream)
                Circle().strokeBorder(skin.frame, lineWidth: 2.5)
            }
    }
}

/// The controller's header: the player's name on the map's plate (usernames only), with the pause button.
struct MapControllerHeader<Trailing: View>: View {
    let skin: MapSkin
    let name: String
    var plateHeight: CGFloat = 74
    @ViewBuilder let trailing: () -> Trailing
    var body: some View {
        ZStack {
            MapPlate(skin: skin, text: name.uppercased(), height: plateHeight).mapEntrance(delay: 0.1).accessibilityIdentifier("controller-name-plate")
            HStack { Spacer(); trailing() }
        }
    }
}

// MARK: - Setup cards (board 13: Set your direction · Timing check · Ready to play · Paused)

extension MapSkin {
    /// The player's username (never YOU).
    @MainActor static func playerName(_ session: SportsSession) -> String {
        let p = session.players.indices.contains(session.playerIndex) ? session.players[session.playerIndex].name : ""
        return p.isEmpty ? "Player" : p
    }
}

/// A setup step on the phone: the map's sculpted title on top, the player's name on a tab, and a cream card with the step's
/// headline, picture, words and buttons in the map's ink.
struct MapSetupCard<Content: View>: View {
    let skin: MapSkin
    let name: String
    let title: String
    @ViewBuilder let content: () -> Content
    var body: some View {
        VStack(spacing: 0) {
            MapTitleArt(skin: skin, height: 118).mapEntrance(delay: 0.1).mapBob(amount: 3).padding(.bottom, -10).zIndex(1)
            Text(name.uppercased()).font(MapFont.bold(17)).foregroundStyle(skin.cream).lineLimit(1).minimumScaleFactor(0.6)
                .padding(.horizontal, 22).padding(.vertical, 7)
                .background(skin.ink, in: Capsule()).overlay(Capsule().strokeBorder(skin.frame, lineWidth: 2.5))
                .padding(.bottom, -16).zIndex(2)
            VStack(spacing: 14) {
                Text(title).font(MapFont.bold(30)).multilineTextAlignment(.center).lineLimit(2).minimumScaleFactor(0.6)
                    .padding(.top, 26)
                content()
            }
            .foregroundStyle(skin.ink)
            .padding(.horizontal, 20).padding(.bottom, 20)
            .frame(maxWidth: .infinity)
            .background {
                RoundedRectangle(cornerRadius: 30, style: .continuous).fill(skin.frameDeep).offset(y: 5)
                RoundedRectangle(cornerRadius: 30, style: .continuous).fill(skin.cream)
                RoundedRectangle(cornerRadius: 30, style: .continuous).strokeBorder(skin.frame, lineWidth: 4)
            }
        }
        .frame(maxWidth: .infinity)
    }
}

/// A quiet text button under a setup card's action (Skip for now, Try again).
struct MapQuietButton: View {
    let skin: MapSkin
    let title: String
    let action: () -> Void
    var body: some View {
        Button(action: action) {
            MapPill(skin: skin, height: 46) { Text(title).font(MapFont.bold(18)) }
        }.buttonStyle(.plain)
    }
}

// MARK: - Motion (loading in: the sculpted pieces pop in on a spring and then bob, like the TV's intro plates)

/// Pops a piece in when it appears: from `from`, small and tilted, onto a springy settle (Reduce Motion: a plain fade).
/// The animations are scale / offset / opacity, which Core Animation runs in the render server, so a Unity load holding the
/// main thread does not freeze them halfway.
struct MapEntrance: ViewModifier {
    var delay: Double = 0
    var from = CGSize(width: 0, height: 30)
    var scale: CGFloat = 0.55
    var tilt: Double = -6
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @State private var on = false
    func body(content: Content) -> some View {
        content
            .scaleEffect(on || reduceMotion ? 1 : scale)
            .rotationEffect(.degrees(on || reduceMotion ? 0 : tilt))
            .offset(on || reduceMotion ? .zero : from)
            .opacity(on ? 1 : 0)
            .onAppear {
                withAnimation(reduceMotion ? .easeOut(duration: 0.25).delay(delay) : .spring(response: 0.55, dampingFraction: 0.58).delay(delay)) { on = true }
            }
    }
}

/// A slow bob while a piece waits on screen (the TV plates do the same).
struct MapBob: ViewModifier {
    var amount: CGFloat = 5
    var period: Double = 1.4
    var delay: Double = 0.7
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @State private var up = false
    func body(content: Content) -> some View {
        content.offset(y: up ? -amount : amount * 0.4)
            .onAppear {
                guard !reduceMotion else { return }
                withAnimation(.easeInOut(duration: period).repeatForever(autoreverses: true).delay(delay)) { up = true }
            }
    }
}

/// The loading art's slow push-in while the load runs.
struct MapPushIn: ViewModifier {
    var seconds = 7.0
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @State private var settled = false
    func body(content: Content) -> some View {
        content.scaleEffect(settled || reduceMotion ? 1 : 1.08)
            .onAppear { withAnimation(.easeOut(duration: seconds)) { settled = true } }
    }
}

extension View {
    func mapEntrance(delay: Double = 0, from: CGSize = CGSize(width: 0, height: 30), scale: CGFloat = 0.55, tilt: Double = -6) -> some View {
        modifier(MapEntrance(delay: delay, from: from, scale: scale, tilt: tilt))
    }
    func mapBob(amount: CGFloat = 5, delay: Double = 0.7) -> some View { modifier(MapBob(amount: amount, delay: delay)) }
    func mapPushIn(seconds: Double = 7) -> some View { modifier(MapPushIn(seconds: seconds)) }
}
