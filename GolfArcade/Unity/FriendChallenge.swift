import SwiftUI
import UIKit

// THE FRIEND CHALLENGE (Adnan's pick, 2026-11-21): ArtDir/ui/daily-challenge-ui-mockups/concepts/03-friend-challenge.html
// (proof/03-friend-challenge.png). After the Daily Hole in One the player opens "Challenge a friend": an invite card (MotionSports,
// the date, "Beat my score.", the score out of 3,000, a golf ball, and a gold "Play the Nov 15 challenge ↗" footer), the message
// that goes with it, Share challenge and Copy challenge link. A friend gets the message and the card in their messages.
// Colours and type are the mockup's (concepts.css): Royal / Deep Navy, gold, Kanit ExtraBold Italic and Inter.

enum FriendChallengeStyle {
    static let ink = Color(hex: "061A4B"), royal = Color(hex: "003EB8"), lift = Color(hex: "286EE6")
    static let gold = Color(hex: "F5C542"), pale = Color(hex: "E0EDFF"), paler = Color(hex: "EFF6FF"), footerInk = Color(hex: "24335B")
    static let sheet = Color(hex: "FBFCFF"), well = Color(hex: "E8EEF8"), messageFill = Color(hex: "F1F5FB"), messageLine = Color(hex: "DAE2F0")
    static let border = Color(hex: "D4DEEE"), muted = Color(hex: "566484")

    nonisolated(unsafe) private static var registered = false
    /// Inter (Regular / SemiBold / Bold), bundled with the app for this card (Kanit comes from MotionBrand).
    static func registerInter() {
        guard !registered else { return }
        registered = true
        for name in ["Inter-Regular", "Inter-SemiBold", "Inter-Bold"] {
            if let url = Bundle.main.url(forResource: name, withExtension: "ttf") { CTFontManagerRegisterFontsForURL(url as CFURL, .process, nil) }
        }
    }
    static func inter(_ size: CGFloat, _ weight: Font.Weight = .regular) -> Font {
        registerInter()
        let name = weight == .bold ? "Inter-Bold" : weight == .semibold ? "Inter-SemiBold" : "Inter-Regular"
        return UIFont(name: name, size: size) != nil ? .custom(name, fixedSize: size) : .system(size: size, weight: weight)
    }
    static func kanit(_ size: CGFloat) -> Font { MotionBrand.font(.extraBoldItalic, size) }
}

/// What the card says.
struct FriendChallengeInfo: Equatable, Sendable {
    var day: Int
    var total: Int
    /// "Nov 15, 2026" (top right) and "Nov 15" (the footer).
    var longDate: String { DailyShareText.formatted(day: day, "MMM d, yyyy") }
    var shortDate: String { DailyShareText.formatted(day: day, "MMM d") }
    var score: String { DailyShareText.points(total) }
}

/// The invite card, laid out on the mockup's 526-point width (scale it for smaller places).
struct FriendChallengeCard: View {
    let info: FriendChallengeInfo
    /// The shared picture has square corners (Messages rounds its own); the preview keeps the mockup's bubble corners.
    var bubble = true
    private typealias S = FriendChallengeStyle
    static let width: CGFloat = 526

    var body: some View {
        VStack(spacing: 0) {
            hero.frame(width: Self.width, height: Self.width / 1.91)
            footer
        }
        .frame(width: Self.width)
        .background(S.royal)
        .clipShape(UnevenRoundedRectangle(topLeadingRadius: bubble ? 14 : 0, bottomLeadingRadius: bubble ? 4 : 0,
                                          bottomTrailingRadius: bubble ? 14 : 0, topTrailingRadius: bubble ? 14 : 0, style: .continuous))
        .accessibilityElement(children: .combine)
        .accessibilityLabel("MotionSports, \(info.longDate). Daily Hole in One. Beat my score: \(info.score) out of 3,000 points. Play the \(info.shortDate) challenge.")
    }

    private var hero: some View {
        ZStack(alignment: .topLeading) {
            S.royal
            RadialGradient(colors: [S.lift, S.lift.opacity(0)], center: UnitPoint(x: 0.95, y: 0.9), startRadius: 0, endRadius: Self.width * 0.66)
            FriendChallengeBall().frame(width: 120, height: 120).opacity(0.89)
                .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .bottomTrailing)
                .padding(.trailing, 20).offset(y: 22)
            VStack(alignment: .leading, spacing: 0) {
                HStack {
                    (Text("Motion").foregroundStyle(.white) + Text("Sports").foregroundStyle(S.gold)).font(S.kanit(23))
                    Spacer()
                    Text(info.longDate).font(S.inter(12, .semibold)).foregroundStyle(S.pale)
                }
                Text("Daily Hole in One").font(S.inter(14, .bold)).foregroundStyle(S.paler).padding(.top, 31)
                (Text("Beat my ") + Text("score.").foregroundStyle(S.gold)).font(S.kanit(47)).foregroundStyle(.white).padding(.top, 10)
                HStack(alignment: .lastTextBaseline, spacing: 10) {
                    Text(info.score).font(S.kanit(83)).foregroundStyle(.white).minimumScaleFactor(0.6).lineLimit(1)
                    Text("out of \(DailyShareText.points(DailyHoleInOne.maxTotal))\npoints").font(S.inter(13, .semibold)).foregroundStyle(S.pale)
                }.padding(.top, 14)
            }
            .padding(.horizontal, 24).padding(.top, 20)
        }
        .clipped()
    }

    private var footer: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text("Play the \(info.shortDate) challenge ↗").font(S.inter(20, .bold)).foregroundStyle(S.ink)
            Text("MotionSports · \(DailyShareText.closes)").font(S.inter(13)).foregroundStyle(S.footerInk)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(.horizontal, 25).padding(.top, 19).padding(.bottom, 21)
        .background(S.gold)
    }
}

/// The card's golf ball: warm cream, shaded, with a field of dimples fading to the rim (concepts.css .ball).
struct FriendChallengeBall: View {
    var body: some View {
        Canvas { ctx, size in
            let r = CGRect(origin: .zero, size: size), circle = Path(ellipseIn: r)
            ctx.fill(circle, with: .radialGradient(Gradient(stops: [
                .init(color: Color(hex: "FFFDF1"), location: 0), .init(color: Color(hex: "FFF7DD"), location: 0.31),
                .init(color: Color(hex: "F4D88A"), location: 0.72), .init(color: Color(hex: "C7912A"), location: 1)]),
                center: CGPoint(x: size.width * 0.32, y: size.height * 0.25), startRadius: 0, endRadius: size.width * 0.78))
            ctx.clip(to: circle)
            let step = size.width / 8, c = CGPoint(x: size.width * 0.52, y: size.height * 0.51)
            for row in -1...9 {
                for col in -1...9 {
                    let x = CGFloat(col) * step + (row % 2 == 0 ? 0 : step / 2), y = CGFloat(row) * step * 0.9
                    let d = hypot(x - c.x, y - c.y) / (size.width / 2)
                    guard d < 0.95 else { continue }
                    let fade = max(0, 1 - max(0, d - 0.55) / 0.4) * 0.77
                    ctx.fill(Path(ellipseIn: CGRect(x: x - 2.2, y: y - 2.2, width: 4.4, height: 4.4)), with: .color(Color(hex: "8C5319").opacity(0.24 * fade)))
                    ctx.fill(Path(ellipseIn: CGRect(x: x - 1.6, y: y + 1, width: 3.2, height: 1.6)), with: .color(Color(hex: "FFF9C9").opacity(0.4 * fade)))
                }
            }
            // the shade on the lower right
            ctx.fill(circle, with: .radialGradient(Gradient(colors: [.clear, Color(hex: "713800").opacity(0.21)]),
                                                   center: CGPoint(x: size.width * 0.35, y: size.height * 0.3), startRadius: size.width * 0.35, endRadius: size.width * 0.62))
        }
        .accessibilityHidden(true)
    }
}

/// "Challenge a friend": the card, the message, Share challenge and Copy challenge link (the mockup's phone).
struct FriendChallengeSheet: View {
    var share: DailyShare = .shared
    @Environment(\.dismiss) private var dismiss
    @State private var linkCopied = false
    private typealias S = FriendChallengeStyle

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("Challenge a friend").font(S.inter(20, .bold)).kerning(-1.1).foregroundStyle(S.ink)
                Spacer()
                Button("Done") { dismiss() }.font(S.inter(13, .bold)).foregroundStyle(S.royal)
                    .frame(minWidth: 44, minHeight: 44).accessibilityIdentifier("friend-challenge-done")
            }
            if let info = share.info {
                FriendChallengeCard(info: info).scaleEffect(0.515, anchor: .topLeading)
                    .frame(width: FriendChallengeCard.width * 0.515, height: FriendChallengeCard.cardHeight * 0.515, alignment: .topLeading)
                    .padding(8).frame(maxWidth: .infinity).background(S.well, in: RoundedRectangle(cornerRadius: 11))
                    .accessibilityIdentifier("friend-challenge-card")
            }
            VStack(alignment: .leading, spacing: 5) {
                Text("Message preview").font(S.inter(13, .bold)).foregroundStyle(S.ink)
                Text(share.messagePreview ?? "").font(S.inter(13)).lineSpacing(3).foregroundStyle(S.ink)
                    .fixedSize(horizontal: false, vertical: true).accessibilityIdentifier("friend-challenge-message")
            }
            .frame(maxWidth: .infinity, alignment: .leading).padding(.horizontal, 12).padding(.vertical, 11)
            .background(S.messageFill, in: RoundedRectangle(cornerRadius: 10))
            .overlay(RoundedRectangle(cornerRadius: 10).strokeBorder(S.messageLine))
            Button { share.share() } label: {
                Label(share.shareTitle, systemImage: "square.and.arrow.up").font(S.inter(15, .bold)).foregroundStyle(S.ink)
                    .frame(maxWidth: .infinity, minHeight: 45).background(S.gold, in: RoundedRectangle(cornerRadius: 10))
            }.buttonStyle(.plain).accessibilityIdentifier("friend-challenge-share")
            Button {
                share.copyLink(); linkCopied = true
                Task { try? await Task.sleep(for: .seconds(2)); linkCopied = false }
            } label: {
                Text(linkCopied ? "Link copied" : "Copy challenge link").font(S.inter(15, .bold)).foregroundStyle(S.ink)
                    .frame(maxWidth: .infinity, minHeight: 45).background(.white, in: RoundedRectangle(cornerRadius: 10))
                    .overlay(RoundedRectangle(cornerRadius: 10).strokeBorder(S.border))
            }.buttonStyle(.plain).accessibilityIdentifier("friend-challenge-copy")
            Spacer(minLength: 0)
        }
        .padding(.horizontal, 17).padding(.top, 18).padding(.bottom, 26)
        .frame(maxWidth: 440)
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
        .background(S.sheet)
    }
}

extension FriendChallengeCard {
    /// The card's height on its 526-point width: the 1.91:1 picture plus the gold footer.
    static var cardHeight: CGFloat { width / 1.91 + 85 }

    /// The card as the picture that is shared (2× its points: 1052 px wide, square corners).
    @MainActor static func image(_ info: FriendChallengeInfo) -> UIImage? {
        let renderer = ImageRenderer(content: FriendChallengeCard(info: info, bubble: false))
        renderer.scale = 2
        return renderer.uiImage
    }
}

/// CHALLENGE A FRIEND, on the phone once the day's three shots are scored (the golf controller's round-done card).
struct DailyShareButton: View {
    var share: DailyShare = .shared
    let skin: MapSkin
    var height: CGFloat = 80
    @State private var open = false
    var body: some View {
        if share.result != nil {
            Button { open = true } label: {
                MapActionFace(skin: skin, title: "Challenge a friend", subtitle: "Send your \(share.info?.score ?? "") to beat", height: height, live: true)
            }
            .buttonStyle(.plain)
            .accessibilityIdentifier("daily-share")
            .sheet(isPresented: $open) {
                FriendChallengeSheet(share: share).presentationDetents([.large]).presentationDragIndicator(.visible)
            }
        }
    }
}
