import SwiftUI

/// The onboarding brand kit (from the 10-25 TV onboarding, retired 2026-11-15 for PLAN_Onboarding_v3; its screens are in
/// work/onboarding/retired-v2). The lesson HUD (LessonCenter) still draws with these.
/// Brand look of the onboarding canvas (navy panels with white borders, one gold button per screen, white + gold headlines).
enum Onb {
    static let navy = Color(hex: "0B2878"), ink = Color(hex: "061A4B"), deep = Color(hex: "000A32"), blue = Color(hex: "003EB8")
    static let gold = Color(hex: "F1B120"), goldHi = Color(hex: "F5C542"), goldDark = Color(hex: "C48812")
    static let mute = Color(hex: "B9C9F2"), soft = Color(hex: "DCE6FF"), green = Color(hex: "4CE08A"), coral = Color(hex: "FF8B7E")
    static func font(_ size: CGFloat, _ weight: CGFloat = 800) -> Font { ClubFonts.font(.ui, size: size, weight: weight, width: nil) }
}

struct OnbBackdrop: View {
    var image: String? = "onboarding-plaza.jpg"
    var blur: CGFloat = 12
    var shade: Double = 0.66
    var body: some View {
        ZStack {
            LinearGradient(colors: [Onb.navy, Onb.blue], startPoint: .top, endPoint: .bottom)
            if let image, let ui = UIImage(named: image) {
                Image(uiImage: ui).resizable().scaledToFill().frame(width: 1320, height: 760).blur(radius: blur).clipped()
                Onb.ink.opacity(shade)
            } else {
                RadialGradient(colors: [Color(hex: "4082F0").opacity(0.55), .clear], center: UnitPoint(x: 0.68, y: 0.6), startRadius: 0, endRadius: 520)
                OnbArcs().stroke(Color.white.opacity(0.08), lineWidth: 8)
            }
        }
        .frame(width: 1280, height: 720).clipped()
    }
}
private struct OnbArcs: Shape {
    func path(in r: CGRect) -> Path {
        var p = Path()
        for (i, k) in [0.0, 0.08, 0.16].enumerated() {
            let w = r.width * (0.78 + k), h = r.height * (0.95 + k)
            p.addEllipse(in: CGRect(x: r.width * 0.36 - CGFloat(i) * 30, y: r.height * 0.88 - h / 2 + r.height * 0.2, width: w, height: h))
        }
        return p
    }
}
struct OnbWordmark: View {
    var size: CGFloat = 32
    var body: some View {
        (Text("Motion").foregroundStyle(.white) + Text("Sports").foregroundStyle(Onb.gold))
            .font(Onb.font(size, 900)).italic().shadow(color: Onb.ink.opacity(0.55), radius: 4, y: 2)
    }
}
struct OnbHeadline: View {
    let first: String, second: String
    var size: CGFloat = 56
    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            Text(first).foregroundStyle(.white)
            Text(second).foregroundStyle(Onb.goldHi)
        }
        .font(Onb.font(size, 900)).italic().lineLimit(1).minimumScaleFactor(0.6)
        .shadow(color: Onb.ink.opacity(0.55), radius: 5, y: 2)
    }
}
/// The three parts of onboarding, across the top.
struct OnbActBar: View {
    let act: Int
    var body: some View {
        HStack(spacing: 4) {
            ForEach(Array(["HELLO", "YOUR PLAYER", "FIRST LESSON"].enumerated()), id: \.offset) { i, label in
                HStack(spacing: 7) {
                    Text("\(i + 1)").font(Onb.font(11, 900)).frame(width: 19, height: 19).overlay(Circle().strokeBorder(lineWidth: 1.5))
                    Text(label).font(Onb.font(14, 800)).italic().tracking(0.8)
                }
                .foregroundStyle(i == act ? Onb.ink : i < act ? .white : Onb.mute)
                .padding(.horizontal, 15).frame(height: 30)
                .background(i == act ? Onb.goldHi : .clear, in: Capsule())
            }
        }
        .padding(.horizontal, 6).frame(height: 42)
        .background(Onb.navy.opacity(0.92), in: Capsule()).overlay(Capsule().strokeBorder(.white, lineWidth: 3))
        .shadow(color: Onb.deep.opacity(0.43), radius: 9, y: 9)
    }
}
/// The frame every non-lesson step shares: wordmark, the act bar and the remote hint.
struct OnbFrame<Content: View>: View {
    let act: Int
    var image: String? = "onboarding-plaza.jpg"
    var blur: CGFloat = 12
    var shade: Double = 0.66
    var wordmark = true
    @ViewBuilder let content: () -> Content
    var body: some View {
        ZStack(alignment: .topLeading) {
            OnbBackdrop(image: image, blur: blur, shade: shade)
            content()
            if wordmark { OnbWordmark().padding(.leading, 48).padding(.top, 30) }
            OnbActBar(act: act).frame(maxWidth: .infinity).padding(.top, 28)
            HStack(spacing: 8) {
                Image(systemName: "iphone.gen3").font(.system(size: 14, weight: .bold))
                Text("ARROWS MOVE  ·  A SELECTS  ·  B GOES BACK").font(Onb.font(12, 800)).tracking(1.2)
            }
            .foregroundStyle(Onb.soft.opacity(0.8)).frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .bottomTrailing)
            .padding(.trailing, 40).padding(.bottom, 20)
        }
        .frame(width: 1280, height: 720)
    }
}
/// The gold button: the one way on, glowing when the remote's focus is on it.
struct OnbGoldButton: View {
    let title: String
    var icon: String? = nil
    var focused: Bool
    var width: CGFloat = 300
    var height: CGFloat = 66
    var action: () -> Void
    var body: some View {
        Button(action: action) {
            HStack(spacing: 10) {
                if let icon { Image(systemName: icon).font(.system(size: height * 0.32, weight: .black)) }
                Text(title).font(Onb.font(height * 0.42, 900)).italic().tracking(1.2)
            }
            .foregroundStyle(Onb.ink).frame(width: width, height: height)
            .background(LinearGradient(colors: [Onb.goldHi, Onb.gold], startPoint: .top, endPoint: .bottom), in: Capsule())
            .overlay(alignment: .bottom) { Capsule().fill(Onb.goldDark).frame(height: 4).padding(.horizontal, height * 0.3).opacity(0.9) }
            .overlay(Capsule().strokeBorder(.white, lineWidth: focused ? 5 : 0).padding(-7))
            .shadow(color: focused ? Onb.goldHi.opacity(0.6) : Onb.deep.opacity(0.43), radius: focused ? 16 : 9, y: focused ? 0 : 9)
            .scaleEffect(focused ? 1.04 : 1)
        }.buttonStyle(.plain)
    }
}
struct OnbOutlineButton: View {
    let title: String
    var icon: String? = nil
    var focused: Bool
    var width: CGFloat = 200
    var height: CGFloat = 60
    var action: () -> Void
    var body: some View {
        Button(action: action) {
            HStack(spacing: 8) {
                if let icon { Image(systemName: icon).font(.system(size: height * 0.3, weight: .black)) }
                Text(title).font(Onb.font(height * 0.36, 900)).italic()
            }
            .foregroundStyle(focused ? Onb.ink : .white).frame(width: width, height: height)
            .background(focused ? Color.white : Onb.navy, in: Capsule())
            .overlay(Capsule().strokeBorder(.white, lineWidth: 3.5))
            .shadow(color: Onb.deep.opacity(0.4), radius: 8, y: 8)
            .scaleEffect(focused ? 1.04 : 1)
        }.buttonStyle(.plain)
    }
}
extension View {
    /// Navy panel with the brand's white border.
    func onbPanel(radius: CGFloat = 28, border: Color = .white, line: CGFloat = 3.5) -> some View {
        background(Onb.navy.opacity(0.95), in: RoundedRectangle(cornerRadius: radius, style: .continuous))
            .overlay(RoundedRectangle(cornerRadius: radius, style: .continuous).strokeBorder(border, lineWidth: line))
            .shadow(color: Onb.deep.opacity(0.43), radius: 10, y: 10)
    }
}
/// The player in the SceneKit locker render, on a studio pedestal.
struct OnbHeroStage: View {
    let player: Player
    var body: some View {
        ZStack(alignment: .bottom) {
            RadialGradient(colors: [Color(hex: "3F7BEA"), Color(hex: "1D4DB8"), Onb.navy], center: UnitPoint(x: 0.5, y: 0.42), startRadius: 10, endRadius: 360)
            Ellipse().fill(Onb.ink.opacity(0.55)).frame(width: 330, height: 60).padding(.bottom, 44)
            Ellipse().strokeBorder(.white.opacity(0.35), lineWidth: 3).frame(width: 300, height: 50).padding(.bottom, 50)
            CharacterModelPreview(player: player, cameraDistance: 3.6, idleSport: .tennis)
                .padding(.top, 20).padding(.bottom, 30)
        }
    }
}

/// Paper confetti on the right of the reward screen (fixed, so snapshots match).
struct OnbConfetti: View {
    var body: some View {
        Canvas { context, size in
            let colors: [Color] = [Onb.goldHi, .white, Color(hex: "4C8DFF"), Color(hex: "FF6B5B"), Onb.green]
            for k in 0..<46 {
                let r = abs((sin(Double(k) * 12.9898) * 43758.5453).truncatingRemainder(dividingBy: 1))
                let r2 = abs((sin(Double(k) * 78.233) * 12345.678).truncatingRemainder(dividingBy: 1))
                var piece = context
                piece.translateBy(x: 660 + r * 600, y: 14 + r2 * 680)
                piece.rotate(by: .degrees(r * 180))
                piece.fill(Path(roundedRect: CGRect(x: 0, y: 0, width: 9 + Double(k % 3) * 4, height: 17 + Double(k % 4) * 4), cornerRadius: 2),
                           with: .color(colors[k % colors.count]))
            }
        }
        .frame(width: 1280, height: 720)
    }
}

extension SportProgress {
    /// Lessons finished (golf, tennis, bowling).
    var tutorialCount: Int { [Sport.golf, .tennis, .bowling].filter(finishedTutorial).count }
}
