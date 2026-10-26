import SwiftUI
import UIKit

/// MotionSports brand tokens for SwiftUI (MotionSports_Brand_Guide.pdf §3, §5; the same values as
/// Unity's MotionSports.Brand.BrandColors). Kanit is used when its TTFs are in the app bundle and
/// registered; until then the club fonts stand in (the brand kit's fonts are not in the project yet).
enum MSBrand {
    static let navyInk = Color(hex: "061A4B"), navyDeep = Color(hex: "0B2878"), royal = Color(hex: "003EB8")
    static let bright = Color(hex: "1F62D6"), lift = Color(hex: "286EE6"), glow = Color(hex: "78BEFF")
    static let gold = Color(hex: "F5C542"), goldWordmark = Color(hex: "F1B120"), goldDeep = Color(hex: "C48812")
    static let white = Color.white, shadowInk = Color(hex: "000A32"), textShadow = Color(hex: "00082D")
    static let n300 = Color(hex: "B7C2DC"), n500 = Color(hex: "6B7A9E")
    static let success = Color(hex: "34C77B"), error = Color(hex: "FF5A5F")

    enum Style { case display, title, heading, button, hudNumber, hudLabel, subline, body, caption }

    /// The brand type style at a phone size (the guide's TV sizes × 0.6 are the defaults callers pass).
    static func font(_ style: Style, _ size: CGFloat) -> Font {
        let kanit: String
        switch style {
        case .display, .title, .button: kanit = "Kanit-ExtraBoldItalic"
        case .heading: kanit = "Kanit-BoldItalic"
        case .subline: kanit = "Kanit-MediumItalic"
        case .hudNumber: kanit = "Kanit-ExtraBold"
        case .hudLabel: kanit = "Kanit-SemiBold"
        case .body, .caption: kanit = "Kanit-Medium"
        }
        if UIFont(name: kanit, size: size) != nil { return .custom(kanit, fixedSize: size) }
        switch style {
        case .display, .title: return Club.display(size)
        case .heading, .subline: return Club.title(size)
        case .button, .hudLabel: return Club.caps(size)
        case .hudNumber: return Club.display(size, condensed: false)
        case .body, .caption: return Club.ui(size, 500)
        }
    }
}
