import SwiftUI

/// The first-launch screens on the TV (option B): a SwiftUI window over the paused club, on TennisTVRoot's 1280×720 canvas.
/// Brand look of the onboarding canvas (navy panels with white borders, one gold button per screen, white + gold headlines).
enum Onb {
    static let navy = Color(hex: "0B2878"), ink = Color(hex: "061A4B"), deep = Color(hex: "000A32"), blue = Color(hex: "003EB8")
    static let gold = Color(hex: "F1B120"), goldHi = Color(hex: "F5C542"), goldDark = Color(hex: "C48812")
    static let mute = Color(hex: "B9C9F2"), soft = Color(hex: "DCE6FF"), green = Color(hex: "4CE08A"), coral = Color(hex: "FF8B7E")
    static func font(_ size: CGFloat, _ weight: CGFloat = 800) -> Font { ClubFonts.font(.ui, size: size, weight: weight, width: nil) }
}

struct OnboardingTV: View {
    @Bindable var flow: OnboardingFlow
    var body: some View {
        ZStack {
            switch flow.step {
            case .hello: OnbHello(flow: flow)
            case .account: OnbAccount(flow: flow)
            case .controller: OnbController(flow: flow)
            case .room: OnbRoom(flow: flow)
            case .player: OnbPlayer(flow: flow)
            case .card: OnbCard(flow: flow)
            case .choose: OnbChoose(flow: flow)
            case .lesson(let sport): OnbLessonPaused(flow: flow, sport: sport)
            case .reward(let sport): OnbReward(flow: flow, sport: sport)
            case .done: Onb.deep
            }
        }
        .frame(width: 1280, height: 720)
        .clipped()
        .animation(.spring(response: 0.42, dampingFraction: 0.86), value: flow.step.key)
        .accessibilityIdentifier("onboarding-tv-\(flow.step.key)")
    }
}

// MARK: - Pieces

/// The club behind every screen: the plaza still, blurred and dimmed, or the brand field.
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

// MARK: - 1 · Hello

private struct OnbHello: View {
    @Bindable var flow: OnboardingFlow
    var body: some View {
        OnbFrame(act: 0, blur: 0, shade: 0, wordmark: false) {
            LinearGradient(stops: [.init(color: Onb.ink.opacity(0.9), location: 0), .init(color: Onb.ink.opacity(0.55), location: 0.45), .init(color: .clear, location: 0.72)],
                           startPoint: .leading, endPoint: .trailing)
            VStack(alignment: .leading, spacing: 0) {
                Text("WELCOME TO THE CLUB").font(Onb.font(20, 800)).tracking(4.4).foregroundStyle(Onb.goldHi)
                VStack(alignment: .leading, spacing: -16) {
                    Text("Motion").foregroundStyle(.white)
                    Text("Sports").foregroundStyle(Onb.gold)
                }.font(Onb.font(112, 900)).italic().padding(.top, 4)
                Text("Golf and tennis on your TV. Your phone is the club, the racket and the remote.")
                    .font(Onb.font(24, 600)).foregroundStyle(.white).frame(width: 520, alignment: .leading).padding(.top, 18)
                OnbGoldButton(title: "LET'S GO", icon: "play.fill", focused: flow.isFocused("go"), width: 340, height: 70) { flow.tap("go") }
                    .padding(.top, 34).accessibilityIdentifier("onboarding-go")
                HStack(spacing: 8) {
                    Circle().fill(Onb.green).frame(width: 10, height: 10)
                    Text("Phone connected · press A on your phone").font(Onb.font(16, 700)).foregroundStyle(Onb.soft)
                }.padding(.top, 16)
            }
            .shadow(color: Onb.ink.opacity(0.6), radius: 6, y: 2)
            .padding(.leading, 74).padding(.top, 130)
        }
    }
}

// MARK: - 2 · The controller

private struct OnbController: View {
    @Bindable var flow: OnboardingFlow
    var body: some View {
        OnbFrame(act: 0) {
            HStack(alignment: .top, spacing: 56) {
                VStack(alignment: .leading, spacing: 30) {
                    OnbHeadline(first: "Your phone is", second: "the controller")
                    VStack(spacing: 14) {
                        row("arrowtriangle.up.fill", "ARROWS", "Move around every screen, one step per click.")
                        row("a.circle.fill", "A · SELECT", "The big button picks what is lit up.")
                        row("chevron.backward.circle.fill", "B · BACK", "Goes back a step. Home returns to the club.")
                    }
                }.frame(width: 560)
                VStack(spacing: 22) {
                    Text("TRY IT").font(Onb.font(18, 800)).tracking(3).foregroundStyle(Onb.goldHi)
                    Text(flow.isFocused("next") ? "That's all the menus need." : "Press A on your phone")
                        .font(Onb.font(30, 900)).italic().multilineTextAlignment(.center).foregroundStyle(.white)
                    if flow.isFocused("next") {
                        OnbGoldButton(title: "NEXT", icon: "checkmark", focused: true, width: 280, height: 70) { flow.tap("next") }
                    } else {
                        OnbGoldButton(title: "PRESS A", focused: true, width: 280, height: 70) { flow.tap("try") }
                    }
                    Text("When a game starts, the same phone becomes your club or racket.")
                        .font(Onb.font(17, 600)).foregroundStyle(Onb.soft).multilineTextAlignment(.center).frame(width: 360)
                }
                .frame(width: 470, height: 420).onbPanel(radius: 30)
            }
            .padding(.leading, 74).padding(.top, 126)
        }
    }
    private func row(_ icon: String, _ title: String, _ text: String) -> some View {
        HStack(spacing: 18) {
            Image(systemName: icon).font(.system(size: 26, weight: .black)).foregroundStyle(Onb.ink)
                .frame(width: 56, height: 56).background(Onb.goldHi, in: Circle())
            VStack(alignment: .leading, spacing: 2) {
                Text(title).font(Onb.font(22, 900)).italic()
                Text(text).font(Onb.font(17, 600)).foregroundStyle(Onb.soft)
            }
            Spacer(minLength: 0)
        }
        .foregroundStyle(.white).padding(.horizontal, 18).frame(height: 84).onbPanel(radius: 22)
    }
}

// MARK: - 1b · Your Apple Account (Game Center)

private struct OnbAccount: View {
    @Bindable var flow: OnboardingFlow
    var body: some View {
        OnbFrame(act: 0) {
            // (re-read once a second: Apple's sheet on the phone signs in without telling this view)
            TimelineView(.periodic(from: .now, by: 1)) { _ in
                VStack(alignment: .leading, spacing: 30) {
                    OnbHeadline(first: "Sign in to play", second: "with your friends")
                    HStack(spacing: 24) {
                        tile("person.2.fill", "Your friends", "Everyone you know on Game Center, ready to invite.")
                        tile("envelope.open.fill", "Invites", "A friend invites you: one tap and you're in their party.")
                        tile("globe", "Online play", "Tennis, golf and bowling with players anywhere.")
                    }
                    if flow.signedIn {
                        HStack(spacing: 18) {
                            OnbGoldButton(title: "NEXT", icon: "checkmark", focused: flow.isFocused("next"), width: 280, height: 66) { flow.tap("next") }
                                .accessibilityIdentifier("onboarding-account-next")
                            Text("Signed in\(flow.accountName.isEmpty ? "" : " as \(flow.accountName)")").font(Onb.font(22, 800)).foregroundStyle(Onb.goldHi)
                        }
                    } else {
                        HStack(spacing: 18) {
                            OnbGoldButton(title: "SIGN IN", icon: "person.crop.circle.badge.checkmark", focused: flow.isFocused("signin"), width: 300, height: 66) { flow.tap("signin") }
                                .accessibilityIdentifier("onboarding-account-signin")
                            OnbOutlineButton(title: "NOT NOW", focused: flow.isFocused("later"), width: 220, height: 60) { flow.tap("later") }
                                .accessibilityIdentifier("onboarding-account-later")
                        }
                        Text("Your Apple Account's Game Center sign-in. It opens on your phone.").font(Onb.font(18, 600)).foregroundStyle(Onb.soft)
                    }
                }
                .padding(.leading, 74).padding(.top, 126)
            }
        }
    }
    private func tile(_ icon: String, _ title: String, _ text: String) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Image(systemName: icon).font(.system(size: 42, weight: .bold)).foregroundStyle(Onb.goldHi)
            Text(title).font(Onb.font(27, 900)).italic().foregroundStyle(.white)
            Text(text).font(Onb.font(17, 600)).foregroundStyle(Onb.soft).fixedSize(horizontal: false, vertical: true)
            Spacer(minLength: 0)
        }
        .padding(24).frame(width: 360, height: 200, alignment: .topLeading).onbPanel()
    }
}

// MARK: - 3 · Room to swing

private struct OnbRoom: View {
    @Bindable var flow: OnboardingFlow
    var body: some View {
        OnbFrame(act: 0) {
            VStack(alignment: .leading, spacing: 36) {
                OnbHeadline(first: "Give yourself", second: "some room")
                HStack(spacing: 24) {
                    tile("tv", "About 2 m back", "Stand facing the TV, far enough to swing without hitting it.")
                    tile("iphone.gen3", "Grip it firmly", "A case with grip helps. A phone flies further than a ball.")
                    tile("circle.dashed", "Clear a circle", "Arm plus a club's length around you. Pets and friends outside it.")
                }
                OnbGoldButton(title: "I'M READY", focused: flow.isFocused("ready"), width: 300, height: 66) { flow.tap("ready") }
                    .accessibilityIdentifier("onboarding-ready")
            }
            .padding(.leading, 74).padding(.top, 126)
        }
    }
    private func tile(_ icon: String, _ title: String, _ text: String) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Image(systemName: icon).font(.system(size: 46, weight: .bold)).foregroundStyle(Onb.goldHi)
            Text(title).font(Onb.font(27, 900)).italic().foregroundStyle(.white)
            Text(text).font(Onb.font(17, 600)).foregroundStyle(Onb.soft).fixedSize(horizontal: false, vertical: true)
            Spacer(minLength: 0)
        }
        .padding(24).frame(width: 360, height: 220, alignment: .topLeading).onbPanel()
    }
}

// MARK: - 4 · Your player

private struct OnbPlayer: View {
    @Bindable var flow: OnboardingFlow
    var body: some View {
        OnbFrame(act: 1, blur: 14, shade: 0.72) {
            if let player = flow.player {
                HStack(spacing: 40) {
                    ZStack(alignment: .bottom) {
                        OnbHeroStage(player: player)
                        nameTag(player.name).padding(.bottom, 20)
                    }
                    .frame(width: 520, height: 580).clipShape(RoundedRectangle(cornerRadius: 30, style: .continuous))
                    .overlay(RoundedRectangle(cornerRadius: 30, style: .continuous).strokeBorder(.white, lineWidth: 3.5))
                    .shadow(color: Onb.deep.opacity(0.43), radius: 10, y: 10)
                    .accessibilityIdentifier("onboarding-hero")
                    editor(player)
                }
                .padding(.leading, 60).padding(.top, 104)
            }
        }
    }
    private func nameTag(_ name: String) -> some View {
        HStack(spacing: 8) {
            Text("P1").font(Onb.font(13, 900)).foregroundStyle(Onb.ink).frame(width: 30, height: 30).background(Onb.goldHi, in: Circle())
            Text(name).font(Onb.font(20, 800)).italic().foregroundStyle(.white)
        }
        .padding(.leading, 5).padding(.trailing, 16).frame(height: 42)
        .background(Onb.navy.opacity(0.94), in: Capsule()).overlay(Capsule().strokeBorder(.white, lineWidth: 3))
    }
    private func editor(_ player: Player) -> some View {
        VStack(alignment: .leading, spacing: 18) {
            OnbHeadline(first: "Make your", second: "player", size: 44)
            group("BODY", focused: flow.focused == "male" || flow.focused == "female") {
                HStack(spacing: 10) {
                    segment("MALE", on: !player.standardFemale, focused: flow.isFocused("male")) { flow.tap("male") }
                    segment("FEMALE", on: player.standardFemale, focused: flow.isFocused("female")) { flow.tap("female") }
                }
            }
            group("SKIN", focused: flow.isFocused("skin"), hint: "◀ ▶") {
                HStack(spacing: 11) {
                    ForEach(Array(LockerColor.skinPresets.enumerated()), id: \.offset) { i, t in
                        swatch(Color(hex: LockerColor.ramp(LockerColor.skinStops, t)), on: flow.skinIndex == i, round: true)
                    }
                }
            }
            group("SHIRT COLOUR", focused: flow.isFocused("shirt"), hint: "◀ ▶") {
                HStack(spacing: 11) {
                    ForEach(Array(OnboardingFlow.shirts.enumerated()), id: \.offset) { i, hex in
                        swatch(Color(hex: hex), on: flow.shirtIndex == i, round: false)
                    }
                }
            }
            group("NAME", focused: flow.isFocused("name"), hint: "TYPE IT ON YOUR PHONE") {
                Text(player.name).font(Onb.font(22, 800)).foregroundStyle(.white)
                    .frame(maxWidth: .infinity, alignment: .leading).padding(.horizontal, 14).frame(height: 46)
                    .background(Onb.ink, in: RoundedRectangle(cornerRadius: 14, style: .continuous))
                    .overlay(RoundedRectangle(cornerRadius: 14, style: .continuous).strokeBorder(.white, lineWidth: 2.5))
            }
            HStack(spacing: 14) {
                OnbOutlineButton(title: "SHUFFLE", icon: "dice.fill", focused: flow.isFocused("shuffle"), width: 170, height: 60) { flow.tap("shuffle") }
                OnbGoldButton(title: "THAT'S ME!", focused: flow.isFocused("save"), width: 290, height: 62) { flow.tap("save") }
                    .accessibilityIdentifier("onboarding-character-save")
            }.padding(.top, 2)
        }
        .padding(28).frame(width: 560, height: 580, alignment: .topLeading).onbPanel(radius: 30)
    }
    private func group<C: View>(_ title: String, focused: Bool, hint: String? = nil, @ViewBuilder content: () -> C) -> some View {
        VStack(alignment: .leading, spacing: 7) {
            HStack {
                Text(title).font(Onb.font(13, 800)).tracking(2).foregroundStyle(focused ? Onb.goldHi : Onb.mute)
                Spacer()
                if focused, let hint { Text(hint).font(Onb.font(12, 800)).tracking(1).foregroundStyle(Onb.goldHi) }
            }
            content()
        }
        .padding(.horizontal, 10).padding(.vertical, 7)
        .background(focused ? Color.white.opacity(0.07) : .clear, in: RoundedRectangle(cornerRadius: 14, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 14, style: .continuous).strokeBorder(focused ? Onb.goldHi : .clear, lineWidth: 2.5))
        .padding(.horizontal, -10)
    }
    private func segment(_ title: String, on: Bool, focused: Bool, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            Text(title).font(Onb.font(20, 900)).italic().foregroundStyle(on ? Onb.ink : .white)
                .frame(maxWidth: .infinity).frame(height: 46)
                .background(on ? Onb.goldHi : .clear, in: Capsule())
                .overlay(Capsule().strokeBorder(focused ? .white : (on ? Onb.goldHi : .white.opacity(0.7)), lineWidth: focused ? 4 : 2.5))
        }.buttonStyle(.plain)
    }
    private func swatch(_ color: Color, on: Bool, round: Bool) -> some View {
        let shape = RoundedRectangle(cornerRadius: round ? 22 : 12, style: .continuous)
        return color.frame(width: 44, height: 44).clipShape(shape)
            .overlay(shape.strokeBorder(on ? .white : Onb.ink, lineWidth: on ? 3.5 : 2))
            .overlay(shape.strokeBorder(Onb.goldHi, lineWidth: 3).padding(-6).opacity(on ? 1 : 0))
    }
}

// MARK: - 5 · Club card

private struct OnbCard: View {
    @Bindable var flow: OnboardingFlow
    var body: some View {
        OnbFrame(act: 1, blur: 6, shade: 0.55) {
            if let player = flow.player {
                ZStack(alignment: .topLeading) {
                    VStack(alignment: .leading, spacing: 18) {
                        OnbHeadline(first: "Looking sharp,", second: "\(player.name)!", size: 58)
                        Text("Here's your club card. Friends see it when you invite them to play.")
                            .font(Onb.font(21, 600)).foregroundStyle(Color(hex: "EAF0FF")).frame(width: 480, alignment: .leading)
                        OnbGoldButton(title: "LET'S PLAY", focused: flow.isFocused("play"), width: 300, height: 66) { flow.tap("play") }
                            .padding(.top, 14).accessibilityIdentifier("onboarding-card-play")
                        Text("B on your phone changes anything").font(Onb.font(15, 700)).foregroundStyle(Onb.soft)
                    }
                    .padding(.leading, 74).padding(.top, 170)
                    card(player).rotationEffect(.degrees(2.5)).offset(x: 720, y: 92)
                }
            }
        }
    }
    private func card(_ player: Player) -> some View {
        VStack(spacing: 0) {
            HStack {
                Text("MOTIONSPORTS CLUB").font(Onb.font(22, 900)).italic()
                Spacer()
                Text("MEMBER").font(Onb.font(15, 900)).tracking(1.2)
            }.foregroundStyle(Onb.ink).padding(.horizontal, 22).frame(height: 62).background(Onb.gold)
            OnbHeroStage(player: player).frame(height: 360)
            VStack(alignment: .leading, spacing: 10) {
                Text(player.name).font(Onb.font(36, 900)).italic().foregroundStyle(.white)
                HStack(spacing: 8) {
                    chip("LEVEL \(Progression.shared.entry(for: player.id).level)")
                    chip("ROOKIE")
                    chip("\(flow.progress.tutorialCount) / 2 LESSONS", gold: true)
                }
            }.padding(20).frame(maxWidth: .infinity, alignment: .leading)
        }
        .frame(width: 440).background(Onb.navy)
        .clipShape(RoundedRectangle(cornerRadius: 30, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 30, style: .continuous).strokeBorder(.white, lineWidth: 4))
        .shadow(color: Onb.deep.opacity(0.5), radius: 14, y: 14)
    }
    private func chip(_ text: String, gold: Bool = false) -> some View {
        Text(text).font(Onb.font(14, 800)).tracking(0.8).foregroundStyle(gold ? Onb.goldHi : .white)
            .padding(.horizontal, 12).frame(height: 32).background(Onb.ink, in: Capsule())
    }
}

// MARK: - 6 · Choose the first lesson

private struct OnbChoose: View {
    @Bindable var flow: OnboardingFlow
    var body: some View {
        OnbFrame(act: 2) {
            VStack(alignment: .leading, spacing: 28) {
                OnbHeadline(first: "Pick your", second: "first lesson")
                HStack(spacing: 32) {
                    card(.golf, image: "course-golf-cliffside.jpg", kicker: "LESSON · ABOUT 6 MIN", title: "GOLF",
                         line: "Distance, clean contact, aim and putting, then a real hole")
                    card(.tennis, image: "map-resort.jpg", kicker: "LESSON · ABOUT 5 MIN", title: "TENNIS",
                         line: "Court setup, timing, aim, serve and dive, then a real point")
                }
                Button { flow.tap("skip") } label: {
                    (Text("Played before? ").foregroundStyle(Onb.soft) + Text("Skip lessons and go to the club").foregroundStyle(flow.isFocused("skip") ? .white : Onb.goldHi))
                        .font(Onb.font(18, 700)).underline(flow.isFocused("skip"))
                        .padding(.horizontal, 14).padding(.vertical, 8)
                        .background(flow.isFocused("skip") ? Onb.navy : .clear, in: Capsule())
                        .overlay(Capsule().strokeBorder(flow.isFocused("skip") ? .white : .clear, lineWidth: 2.5))
                }.buttonStyle(.plain).padding(.leading, -14).accessibilityIdentifier("onboarding-skip-lessons")
            }
            .padding(.leading, 74).padding(.top, 116)
        }
    }
    private func card(_ sport: Sport, image: String, kicker: String, title: String, line: String) -> some View {
        let focused = flow.isFocused(sport.rawValue)
        let done = SportProgress.shared.finishedTutorial(sport)
        return Button { flow.tap(sport.rawValue) } label: {
            ZStack(alignment: .bottomLeading) {
                if let ui = UIImage(named: image) { Image(uiImage: ui).resizable().scaledToFill().frame(width: 540, height: 370).clipped() }
                LinearGradient(stops: [.init(color: .clear, location: 0.3), .init(color: Onb.ink.opacity(0.92), location: 0.8)], startPoint: .top, endPoint: .bottom)
                VStack(alignment: .leading, spacing: 6) {
                    Text(done ? "DONE · PLAY IT AGAIN" : kicker).font(Onb.font(16, 800)).tracking(2.6).foregroundStyle(Onb.goldHi)
                    Text(title).font(Onb.font(62, 900)).italic().foregroundStyle(.white)
                    Text(line).font(Onb.font(18, 600)).foregroundStyle(Color(hex: "EAF0FF"))
                }.padding(26)
                Text("START").font(Onb.font(20, 900)).italic().foregroundStyle(Onb.ink)
                    .padding(.horizontal, 20).frame(height: 42)
                    .background(LinearGradient(colors: [Onb.goldHi, Onb.gold], startPoint: .top, endPoint: .bottom), in: Capsule())
                    .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topTrailing).padding(22)
            }
            .frame(width: 540, height: 370)
            .clipShape(RoundedRectangle(cornerRadius: 30, style: .continuous))
            .overlay(RoundedRectangle(cornerRadius: 30, style: .continuous).strokeBorder(.white, lineWidth: 4))
            .overlay(RoundedRectangle(cornerRadius: 34, style: .continuous).strokeBorder(Onb.goldHi, lineWidth: 6).padding(-8).opacity(focused ? 1 : 0))
            .shadow(color: Onb.deep.opacity(0.5), radius: 14, y: 14)
            .scaleEffect(focused ? 1.03 : 1)
        }
        .buttonStyle(.plain).accessibilityIdentifier("onboarding-game-\(sport.rawValue)")
    }
}

// MARK: - A lesson left before its end

private struct OnbLessonPaused: View {
    @Bindable var flow: OnboardingFlow
    let sport: Sport
    var body: some View {
        OnbFrame(act: 2) {
            VStack(alignment: .leading, spacing: 22) {
                OnbHeadline(first: "\(sport.title.capitalized) lesson", second: "paused")
                Text("Pick up where you left off: station \(flow.store.lessonStation(sport) + 1) of 8.")
                    .font(Onb.font(22, 600)).foregroundStyle(Color(hex: "EAF0FF"))
                OnbGoldButton(title: "RESUME", icon: "play.fill", focused: flow.isFocused("resume"), width: 300) { flow.tap("resume") }
                OnbOutlineButton(title: "PICK A LESSON", focused: flow.isFocused("choose"), width: 300) { flow.tap("choose") }
                OnbOutlineButton(title: "SKIP LESSONS", focused: flow.isFocused("skip"), width: 300) { flow.tap("skip") }
            }
            .padding(.leading, 74).padding(.top, 150)
        }
    }
}

// MARK: - The reward

private struct OnbReward: View {
    @Bindable var flow: OnboardingFlow
    let sport: Sport
    var body: some View {
        let other: Sport = sport == .golf ? .tennis : .golf
        let otherDone = SportProgress.shared.finishedTutorial(other)
        OnbFrame(act: 2, image: sport == .golf ? "course-golf-cliffside.jpg" : "map-resort.jpg", blur: 12, shade: 0.66) {
            ZStack(alignment: .topLeading) {
                OnbConfetti().allowsHitTesting(false)
                if let player = flow.player {
                    OnbHeroStage(player: player).frame(width: 440, height: 560)
                        .clipShape(RoundedRectangle(cornerRadius: 30, style: .continuous))
                        .overlay(RoundedRectangle(cornerRadius: 30, style: .continuous).strokeBorder(.white, lineWidth: 4))
                        .shadow(color: Onb.deep.opacity(0.5), radius: 14, y: 14)
                        .rotationEffect(.degrees(-2)).offset(x: 760, y: 100)
                }
                VStack(alignment: .leading, spacing: 0) {
                    Text("NICE WORK, \((flow.player?.name ?? "Player 1").uppercased())").font(Onb.font(20, 800)).tracking(4).foregroundStyle(Onb.goldHi)
                    OnbHeadline(first: "\(sport.title.capitalized) lesson", second: "complete!", size: 64).padding(.top, 4)
                    HStack(spacing: 14) {
                        tile("star.fill", "Lesson badge", "on your club card")
                        if flow.store.rewardXP(sport) > 0 { tile("bolt.fill", "+\(flow.store.rewardXP(sport)) XP", "towards your next level") }
                        else { tile("checkmark.seal.fill", "\(flow.progress.tutorialCount) of 2 lessons", "on your club card") }
                        if let item = flow.store.rewardItem(sport) { tile("crown.fill", item == "white-headband" ? "Headband" : item.capitalized, "unlocked in the Locker") }
                        else { tile(sport == .golf ? "flag.fill" : "sportscourt.fill", sport == .golf ? "Courses open" : "Island Circuit", sport == .golf ? "play any round" : "round 1 open") }
                    }.padding(.top, 26)
                    HStack(spacing: 14) {
                        OnbGoldButton(title: sport == .golf ? "PLAY A ROUND" : "PLAY A MATCH", focused: flow.isFocused("play"), width: 300) { flow.tap("play") }
                        if !otherDone {
                            OnbOutlineButton(title: other == .tennis ? "TENNIS LESSON" : "GOLF LESSON", focused: flow.isFocused("other"), width: 250) { flow.tap("other") }
                        }
                    }.padding(.top, 30)
                    OnbOutlineButton(title: "TO THE CLUB", icon: "house.fill", focused: flow.isFocused("menu"), width: 250, height: 54) { flow.tap("menu") }
                        .padding(.top, 14)
                }
                .padding(.leading, 74).padding(.top, 118)
            }
        }
    }
    private func tile(_ icon: String, _ title: String, _ note: String) -> some View {
        VStack(alignment: .leading, spacing: 0) {
            Image(systemName: icon).font(.system(size: 32, weight: .black)).foregroundStyle(Onb.goldHi)
            Spacer(minLength: 0)
            Text(title).font(Onb.font(21, 900)).italic().foregroundStyle(.white).lineLimit(1).minimumScaleFactor(0.7)
            Text(note).font(Onb.font(13, 700)).foregroundStyle(Onb.mute)
        }
        .padding(16).frame(width: 190, height: 136, alignment: .topLeading).onbPanel(radius: 22)
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
    /// Lessons finished (the club card's "n / 2 LESSONS").
    var tutorialCount: Int { [Sport.golf, .tennis].filter(finishedTutorial).count }
}
