import CoreText
import SwiftUI

/// MotionSports brand tokens for the phone (Brand Guide v1.0; Unity's BrandColors has the same values). The phone controller uses
/// the TV's styles at 0.6x. Kanit (OFL, Fonts/Kanit-*.ttf) is registered once.
enum MotionBrand {
    static let navyInk = Color(hex: "061A4B"), navyDeep = Color(hex: "0B2878"), royal = Color(hex: "003EB8"), bright = Color(hex: "1F62D6")
    static let lift = Color(hex: "286EE6"), glow = Color(hex: "78BEFF"), gold = Color(hex: "F5C542"), goldWordmark = Color(hex: "F1B120")
    static let goldDeep = Color(hex: "C48812"), arcWarm = Color(hex: "EDB15D"), shadowInk = Color(hex: "000A32"), textShadow = Color(hex: "00082D")
    static let success = Color(hex: "34C77B"), error = Color(hex: "FF5A5F"), n700 = Color(hex: "2A3558"), n500 = Color(hex: "6B7A9E"), n300 = Color(hex: "B7C2DC")
    /// The menu background: Deep Navy at the top to Royal by 24 % of the height, then flat Royal.
    static let background = LinearGradient(stops: [.init(color: navyDeep, location: 0), .init(color: royal, location: 0.24), .init(color: royal, location: 1)], startPoint: .top, endPoint: .bottom)

    enum Weight: String { case extraBoldItalic = "ExtraBoldItalic", boldItalic = "BoldItalic", mediumItalic = "MediumItalic", extraBold = "ExtraBold", semiBold = "SemiBold", medium = "Medium" }
    nonisolated(unsafe) private static var registered = false
    nonisolated(unsafe) private static var names: [Weight: String] = [:]
    static func register() {
        guard !registered else { return }
        registered = true
        for w in [Weight.extraBoldItalic, .boldItalic, .mediumItalic, .extraBold, .semiBold, .medium] {
            guard let url = Bundle.main.url(forResource: "Kanit-" + w.rawValue, withExtension: "ttf") else { continue }
            CTFontManagerRegisterFontsForURL(url as CFURL, .process, nil)
            if let list = CTFontManagerCreateFontDescriptorsFromURL(url as CFURL) as? [CTFontDescriptor], let d = list.first,
               let name = CTFontDescriptorCopyAttribute(d, kCTFontNameAttribute) as? String { names[w] = name }
        }
    }
    /// Kanit at `size` points (the system's heavy rounded face if the files are missing).
    static func font(_ weight: Weight, _ size: CGFloat) -> Font {
        register()
        if let name = names[weight] { return .custom(name, fixedSize: size) }
        let fallback: Font.Weight = weight == .medium || weight == .mediumItalic ? .medium : weight == .semiBold ? .semibold : .heavy
        let f = Font.system(size: size, weight: fallback, design: .rounded)
        return [.extraBoldItalic, .boldItalic, .mediumItalic].contains(weight) ? f.italic() : f
    }
}

/// The wordmark: "Motion" white + "Sports" Wordmark Gold, Kanit ExtraBold Italic, with its shadow.
struct MotionWordmark: View {
    var size: CGFloat = 30
    var body: some View {
        (Text("Motion").foregroundColor(.white) + Text("Sports").foregroundColor(MotionBrand.goldWordmark))
            .font(MotionBrand.font(.extraBoldItalic, size))
            .shadow(color: MotionBrand.textShadow.opacity(0.55), radius: size / 60, y: size / 40)
            .accessibilityLabel("MotionSports")
    }
}

/// The gold primary pill (gold -> wordmark gold, a Gold Deep lip that collapses when pressed) and the navy secondary.
struct MotionButtonStyle: ButtonStyle {
    enum Kind { case primary, secondary, ghost }
    var kind: Kind = .secondary
    var height: CGFloat = 58
    func makeBody(configuration: Configuration) -> some View {
        let pressed = configuration.isPressed
        return configuration.label
            .font(MotionBrand.font(.extraBoldItalic, kind == .primary ? 24 : 21)).textCase(.uppercase)
            .foregroundStyle(kind == .primary ? MotionBrand.navyInk : .white)
            .frame(maxWidth: kind == .ghost ? nil : .infinity, minHeight: height)
            .padding(.bottom, kind == .primary && !pressed ? 4 : 0)
            .background {
                switch kind {
                case .primary:
                    ZStack(alignment: .bottom) {
                        Capsule().fill(MotionBrand.goldDeep)
                        Capsule().fill(LinearGradient(colors: [MotionBrand.gold, MotionBrand.goldWordmark], startPoint: .top, endPoint: .bottom)).padding(.bottom, pressed ? 0 : 4)
                    }
                case .secondary: Capsule().fill(MotionBrand.navyDeep).overlay(Capsule().strokeBorder(.white, lineWidth: 3))
                case .ghost: Color.clear
                }
            }
            .overlay(alignment: .bottom) { if kind == .ghost { Rectangle().fill(MotionBrand.gold).frame(height: 3).offset(y: -10) } }
            .shadow(color: kind == .ghost ? .clear : MotionBrand.shadowInk.opacity(0.43), radius: 10, y: 8)
            .scaleEffect(pressed ? 0.94 : 1).animation(.easeOut(duration: 0.12), value: pressed)
    }
}
