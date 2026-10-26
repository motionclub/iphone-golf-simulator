import SwiftUI
import SceneKit

// The sports-arcade front end around the tennis screens: title, main menu, game select, each
// sport's hub, character, settings, how-to, the golf lesson, connecting a screen, and loading.
// Laid out for the 1280×720 TV canvas, or stacked for the phone held upright (`compact`).


// MARK: - Main menu

// A self-contained lobby design system, independent of the legacy arcade screens.


// MARK: - Game select


// MARK: - A sport's hub


// MARK: - Exhibition


// MARK: - Character


// MARK: - Settings

struct SettingsScreen: View {
    let menu: TennisMenu
    let compact: Bool
    var body: some View {
        let s = SportsSession.shared
        let p = s.players.indices.contains(s.playerIndex) ? s.players[s.playerIndex] : nil
        VStack(alignment: .leading, spacing: compact ? 10 : 12) {
            ArcadeText(text: "SETTINGS", size: compact ? 34 : 46, top: .white, bottom: Arcade.sky)
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 10) {
                    ForEach(SettingsTab.allCases, id: \.self) { tab in
                        let id = "tab-\(tab.rawValue)"
                        let current = menu.settingsTab == tab
                        Text(tab.title.uppercased()).font(Arcade.font(compact ? 14 : 17)).tracking(1)
                            .foregroundStyle(current ? Arcade.navyDeep : .white)
                            .padding(.horizontal, 16).padding(.vertical, 8)
                            .background(Capsule().fill(current ? AnyShapeStyle(LinearGradient(colors: [Arcade.gold, Arcade.goldDeep], startPoint: .top, endPoint: .bottom)) : AnyShapeStyle(Arcade.navyDeep.opacity(0.7))))
                            .focusGlow(menu.isFocused(id), corner: 30)
                            .onTapGesture { menu.tap(id) }
                    }
                }.padding(.vertical, 8).padding(.horizontal, 4)
            }
            VStack(spacing: 10) {
                ForEach(TennisMenu.settingsRows(menu.settingsTab), id: \.self) { id in
                    let (label, value) = Self.describe(id, s, p)
                    ChoiceRow(label: label, value: value, focused: menu.isFocused(id), compact: compact) { menu.tap(id) }
                }
            }
            if !menu.notice.isEmpty {
                Text(menu.notice).font(Arcade.font(compact ? 14 : 17, .bold)).foregroundStyle(Arcade.gold)
            }
            Spacer(minLength: 0)
            HStack {
                ArcadeButton(title: "Back", icon: "chevron.left", focused: menu.isFocused("back"),
                             top: Arcade.skyDeep, bottom: Arcade.navy, size: compact ? 20 : 22) { menu.tap("back") }
                Spacer()
                if !compact { HintBar() }
            }
        }
        .padding(compact ? 18 : 36)
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
    }

    static func describe(_ id: String, _ s: SportsSession, _ p: Player?) -> (String, String) {
        switch id {
        case "level": ("Training & exhibition coach", TennisMenu.trainingLevels.first { abs($0.difficulty - s.tennisDifficulty) < 0.01 }?.name ?? "Standard")
        case "coaching": ("Coaching tips in matches", s.coachingTips ? "On" : "Off")
        case "resetTips": ("Show every coaching tip again", "Reset")
        case "resetProgress": ("Reset tutorials & campaign", TennisMenu.shared.confirmingReset ? "Press again" : "Reset…")
        case "range": ("Step to cross court", "\(Int(s.travel * 100)) cm")
        case "hand": ("Plays", p?.handedness == .left ? "Left-handed" : "Right-handed")
        case "relock": ("Court direction", "Set again")
        case "timing": ("Swing timing check", "Run next match")
        case "swingPrediction": ("Swing prediction", s.swingPrediction ? "On" : "Off")
        case "fastInput": ("120 Hz swing input", s.fastInput ? "On" : "Off")
        case "howto":
            ("How to connect a TV or Mac", SportsDisplays.displayKind == .mac ? "Mac connected" : SportsDisplays.displayKind == .tv ? "TV connected" : "Open")
        case "tennisCamera": ("Tennis camera", s.tennisCamera == "elevated" ? "Elevated" : "Chase")
        case "fps": ("120 fps on the phone", s.highFrameRate ? "On" : "Off")
        case "overscan": ("Screen edge margin", s.overscan == 0 ? "None" : "\(Int(s.overscan * 100))%")
        case "sound": ("Sound", s.sound ? "On" : "Off")
        case "haptics": ("Haptics", s.haptics ? "On" : "Off")
        case "hapticStrength": ("Hit strength", RacketFeel.strengths[RacketFeel.strengthIndex(s.hapticStrength)].name)
        case "racketSound": ("Racket sound on the phone", s.racketSound ? "On" : "Off")
        case "feelTest": ("Feel test", TennisMenu.shared.feelTestLabel.isEmpty ? "Play" : TennisMenu.shared.feelTestLabel)
        case "bigText": ("Larger text on the phone remote", s.bigText ? "On" : "Off")
        case "reduceMotion": ("Reduce motion (still b-roll)", s.reduceMotion ? "On" : "Off")
        case "bench": ("Frame-time benchmark", "Info")
        default: (id, "")
        }
    }
}

// MARK: - How to play, and the golf lesson


// MARK: - Connect a screen (phone only)


// MARK: - Loading

/// Ten short tips per sport, including controls, identity and game-night etiquette.
enum PartyLoadingTips {
    static func tips(for sport: Sport) -> [String] {
        let shared = [
            "Leave enough room for a full swing.",
            "Pause before passing the phone.",
            "Your outfit is saved in the Locker.",
            "Play on a TV for a wider view.",
            "Adjust sound and haptics in Settings.",
            "You can change your look between matches."
        ]
        return shared + (sport == .golf ? [
            "A smooth swing beats a frantic one.",
            "Check your aim before you take the shot.",
            "Give the golfer a little quiet before the swing.",
            "Use a shorter swing for a short putt."
        ] : [
            "Tap Toss, then time your serve swing.",
            "Meet the ball in front of you for a clean return.",
            "Aim for open court instead of swinging harder.",
            "Tap Dive to reach a wide ball."
        ])
    }
}

@MainActor enum PresentationPortraits {
    private static let cache = NSCache<NSString, UIImage>()
    static func key(_ player: Player, sport: Sport) -> String {
        let encoder = JSONEncoder(); encoder.outputFormatting = [.sortedKeys]
        guard let data = try? encoder.encode(player), var appearance = (try? JSONSerialization.jsonObject(with: data)) as? [String: Any] else { return "unavailable" }
        appearance.removeValue(forKey: "id"); appearance.removeValue(forKey: "name")
        return "v1|\(sport.rawValue)|" + ((try? JSONSerialization.data(withJSONObject: appearance, options: .sortedKeys))?.base64EncodedString() ?? "unavailable")
    }
    static func image(_ player: Player, sport: Sport) -> UIImage? {
        let key = key(player, sport: sport) as NSString
        if let image = cache.object(forKey: key) { return image }
        let coordinator = CharacterModelPreview.Coordinator(cameraDistance: 3.8)
        coordinator.update(player, sport: sport)
        guard let root = coordinator.hero, let asset = MatchHero.asset(female: player.standardFemale, golf: sport == .golf),
              let rig = HeroRig(root: root, asset: asset),
              let clip = rig.data.clips.first(where: { $0.key == "wave" || $0.key == "bringIt" })?.value else { return nil }
        rig.attach(); rig.apply(clip.pose(at: clip.length * 0.35, loop: false))
        rig.data.applyMorphWeights(clip.morphWeights(at: clip.length * 0.35, loop: false), to: root)
        coordinator.camera?.position = SCNVector3(0, 0.95, 3.8)
        coordinator.camera?.look(at: SCNVector3(0, 0.9, 0))
        let renderer = SCNRenderer(device: nil, options: nil)
        renderer.scene = coordinator.scene; renderer.pointOfView = coordinator.camera
        let image = renderer.snapshot(atTime: 0, with: CGSize(width: 320, height: 320), antialiasingMode: .multisampling4X)
        cache.countLimit = 24; cache.setObject(image, forKey: key)
        return image
    }
}

private struct PresentationRosterCard: View {
    let name: String
    let player: Player?
    let sport: Sport
    let loaded: Bool?
    let compact: Bool
    @State private var portrait: UIImage?
    private var cacheKey: String { player.map { PresentationPortraits.key($0, sport: sport) } ?? name }
    var body: some View {
        VStack(spacing: 4) {
            ZStack {
                RoundedRectangle(cornerRadius: 22).fill(Club.lagoonDeep.opacity(0.72))
                if let portrait { Image(uiImage: portrait).resizable().scaledToFit() }
                else { Image(systemName: "person.fill").resizable().scaledToFit().foregroundStyle(IslandUI.lime.opacity(0.8)).padding(26) }
            }.frame(height: compact ? 140 : 245)
            HStack(spacing: 6) {
                Text(name).font(IslandUI.font(compact ? 19 : 26, bold: true)).lineLimit(1).minimumScaleFactor(0.75)
                if loaded == true { Image(systemName: "checkmark.circle.fill").foregroundStyle(IslandUI.lime) }
            }
        }.accessibilityElement(children: .ignore).accessibilityLabel("\(name)\(loaded == true ? ", loaded" : "")")
        .task(id: cacheKey) {
            portrait = nil
            // Let the cover paint before allocating an offscreen hero render.
            try? await Task.sleep(for: .milliseconds(120))
            guard !Task.isCancelled, let player else { return }
            portrait = PresentationPortraits.image(player, sport: sport)
        }
    }
}

// MARK: - MotionSports loading pieces (MotionSports_Brand_Guide.pdf §4–8)

/// The loading screens' type: Kanit (§5) once its TTFs are in the bundle; until then SF's heavy italic, which keeps the brand's
/// loud, slanted look (the club fonts are upright).
enum MSLoadingFont {
    static func display(_ size: CGFloat) -> Font { kanit("Kanit-ExtraBoldItalic", size) ?? .system(size: size, weight: .black).italic() }
    static func subline(_ size: CGFloat) -> Font { kanit("Kanit-MediumItalic", size) ?? .system(size: size, weight: .semibold).italic() }
    static func body(_ size: CGFloat) -> Font { kanit("Kanit-Medium", size) ?? .system(size: size, weight: .medium) }
    private static func kanit(_ name: String, _ size: CGFloat) -> Font? { UIFont(name: name, size: size) != nil ? .custom(name, fixedSize: size) : nil }
}

/// "MotionSports": white Motion, Wordmark Gold Sports, no space, with its required text shadow (§6).
struct MSWordmark: View {
    let size: CGFloat
    var body: some View {
        (Text("Motion").foregroundColor(MSBrand.white) + Text("Sports").foregroundColor(MSBrand.goldWordmark))
            .font(MSLoadingFont.display(size)).fixedSize()
            .shadow(color: MSBrand.textShadow.opacity(0.55), radius: size / 14, y: size / 40)
            .accessibilityLabel("MotionSports")
    }
}

/// The swing arc's head: a 4-point white sparkle with a soft glow (§7).
struct MSSparkle: View {
    var color: Color = .white
    var body: some View {
        Canvas { ctx, size in
            let c = CGPoint(x: size.width / 2, y: size.height / 2), r = min(size.width, size.height) / 2, w = r * 0.16
            var star = Path()
            star.move(to: CGPoint(x: c.x, y: c.y - r))
            star.addQuadCurve(to: CGPoint(x: c.x + r, y: c.y), control: CGPoint(x: c.x + w, y: c.y - w))
            star.addQuadCurve(to: CGPoint(x: c.x, y: c.y + r), control: CGPoint(x: c.x + w, y: c.y + w))
            star.addQuadCurve(to: CGPoint(x: c.x - r, y: c.y), control: CGPoint(x: c.x - w, y: c.y + w))
            star.addQuadCurve(to: CGPoint(x: c.x, y: c.y - r), control: CGPoint(x: c.x - w, y: c.y - w))
            ctx.drawLayer { glow in glow.addFilter(.blur(radius: r * 0.35)); glow.fill(star, with: .color(MSBrand.gold.opacity(0.9))) }
            ctx.fill(star, with: .color(color))
            ctx.fill(Path(ellipseIn: CGRect(x: c.x - w * 1.6, y: c.y - w * 1.6, width: w * 3.2, height: w * 3.2)), with: .color(.white))
        }
        .accessibilityHidden(true)
    }
}

/// The loading bar: a white-rimmed pill on Navy Ink, filled in the sport's colour with a sparkle riding its head.
struct MSLoadingBar: View {
    let progress: Double
    var fill: Color = MSBrand.gold
    var height: CGFloat = 20
    var body: some View {
        GeometryReader { g in
            let inset = height * 0.22, track = g.size.width - inset * 2
            let p = min(1, max(0, progress.isFinite ? progress : 0)), w = max(height - inset * 2, track * p)
            ZStack(alignment: .leading) {
                Capsule().fill(MSBrand.navyInk)
                Capsule().fill(LinearGradient(colors: [fill.mix(.white, 0.35), fill, fill.mix(MSBrand.goldDeep, 0.25)], startPoint: .top, endPoint: .bottom))
                    .frame(width: w, height: height - inset * 2).padding(.leading, inset)
                MSSparkle().frame(width: height * 2.4, height: height * 2.4).position(x: inset + w, y: height / 2)
            }
            .overlay(Capsule().strokeBorder(.white, lineWidth: max(2, height * 0.14)))
            .shadow(color: MSBrand.shadowInk.opacity(0.43), radius: height * 0.5, y: height * 0.3)
        }
        .frame(height: height)
        .animation(.easeOut(duration: 0.35), value: progress)
        .accessibilityElement(children: .ignore).accessibilityLabel("Loading \(Int((progress * 100).rounded())) percent")
    }
}

/// Loading without a spinner (§7): a short swing arc chasing round a faint ring.
struct MSArcRing: View {
    var color: Color = .white
    var body: some View {
        TimelineView(.animation(minimumInterval: 1.0 / 30)) { context in
            let turn = context.date.timeIntervalSinceReferenceDate.truncatingRemainder(dividingBy: 1.1) / 1.1
            ZStack {
                Circle().stroke(.white.opacity(0.18), lineWidth: 4)
                Circle().trim(from: 0, to: 0.36)
                    .stroke(AngularGradient(colors: [color.opacity(0), color, .white], center: .center, startAngle: .degrees(0), endAngle: .degrees(130)),
                            style: StrokeStyle(lineWidth: 5, lineCap: .round))
                    .shadow(color: MSBrand.arcWarm.opacity(0.7), radius: 4)
                    .rotationEffect(.degrees(turn * 360))
            }
        }
        .accessibilityHidden(true)
    }
}

/// The signature swing arc across a screen (§7): part of a tilted ellipse, tapering from 15 % at the tail to full width at the
/// head, alpha 0 → 1, a white core with an Arc Warm fringe and glow. Points are fractions of the view.
struct MSSwingArc: View {
    var center = CGPoint(x: 0.64, y: 1.06)
    var radii = CGSize(width: 0.6, height: 0.79)
    var from: Double = 168, to: Double = 28   // degrees, tail → head
    var width: CGFloat = 16
    var body: some View {
        Canvas { ctx, size in
            let steps = 160
            func point(_ t: Double) -> CGPoint {
                let a = (from + (to - from) * t) * .pi / 180
                return CGPoint(x: size.width * (center.x + radii.width * cos(a)), y: size.height * (center.y - radii.height * sin(a)))
            }
            // One filled ribbon per layer (no seams between pieces), widening from 15 % at the tail to full at the head.
            func ribbon(_ scale: CGFloat) -> Path {
                var left: [CGPoint] = [], right: [CGPoint] = []
                for i in 0...steps {
                    let t = Double(i) / Double(steps), p = point(t), q = point(min(1, t + 0.002)), r = point(max(0, t - 0.002))
                    let dx = q.x - r.x, dy = q.y - r.y, len = max(0.0001, hypot(dx, dy))
                    let half = width * scale * (0.15 + 0.85 * t) / 2
                    left.append(CGPoint(x: p.x - dy / len * half, y: p.y + dx / len * half))
                    right.append(CGPoint(x: p.x + dy / len * half, y: p.y - dx / len * half))
                }
                var path = Path(); path.addLines(left + right.reversed()); path.closeSubpath()
                return path
            }
            // alpha 0 → 1 tail to head (the arc runs left to right)
            let tail = point(0), head = point(1)
            func shade(_ color: Color, _ alpha: Double) -> GraphicsContext.Shading {
                .linearGradient(Gradient(stops: [.init(color: color.opacity(0), location: 0), .init(color: color.opacity(alpha * 0.35), location: 0.45),
                                                 .init(color: color.opacity(alpha), location: 1)]), startPoint: tail, endPoint: head)
            }
            ctx.drawLayer { glow in glow.addFilter(.blur(radius: width * 1.8)); glow.fill(ribbon(3.4), with: shade(MSBrand.arcWarm, 0.75)) }
            ctx.drawLayer { soft in soft.addFilter(.blur(radius: width * 0.3)); soft.fill(ribbon(1.2), with: shade(MSBrand.arcWarm, 1)) }
            ctx.fill(ribbon(0.5), with: shade(.white, 1))
        }
        .allowsHitTesting(false).accessibilityHidden(true)
    }
}

extension MSBrand {
    static let arcWarm = Color(hex: "EDB15D")
    /// Royal at the spotlight, Deep Navy, Navy Ink at the edges (§4 background + spotlight).
    static func backdrop(spotlight: UnitPoint = UnitPoint(x: 0.3, y: 0.46), radius: CGFloat = 900) -> some View {
        ZStack {
            LinearGradient(colors: [navyInk, navyDeep, Color(hex: "0B2C86")], startPoint: .top, endPoint: .bottom)
            RadialGradient(colors: [Color(hex: "1D4FB8"), Color(hex: "123A9A").opacity(0.6), .clear], center: spotlight, startRadius: 0, endRadius: radius)
        }
    }
}

extension Color {
    /// This colour moved `amount` of the way to `other` (sRGB).
    func mix(_ other: Color, _ amount: Double) -> Color {
        let a = UIColor(self), b = UIColor(other)
        var (r1, g1, b1, a1, r2, g2, b2, a2): (CGFloat, CGFloat, CGFloat, CGFloat, CGFloat, CGFloat, CGFloat, CGFloat) = (0, 0, 0, 0, 0, 0, 0, 0)
        a.getRed(&r1, green: &g1, blue: &b1, alpha: &a1); b.getRed(&r2, green: &g2, blue: &b2, alpha: &a2)
        let t = CGFloat(amount)
        return Color(red: Double(r1 + (r2 - r1) * t), green: Double(g1 + (g2 - g1) * t), blue: Double(b1 + (b2 - b1) * t), opacity: Double(a1 + (a2 - a1) * t))
    }
}

/// Loading into a match (venue tips, picked 2026-10-25): the venue's key art full screen, a tip card (TENNIS TIP 1/2) with a
/// headline and one line of how to play, and the bar with what is loading and how far. The TV draws it on its 1280×720 canvas;
/// the phone stacks the same pieces upright, with Leave match. The bar is LoadingModel.displayProgress (measured milestones).
struct LoadingScreen: View {
    let menu: TennisMenu
    let compact: Bool
    private var session: SportsSession { .shared }
    private var loading: LoadingModel { session.loading }
    private var service: MultiplayerService { menu.online.service }
    private var lobbyLoading: Bool { service.lobby?.phase == .loading }
    private var sport: Sport {
        if lobbyLoading { return service.lobby?.sport == .golf ? .golf : .tennis }
        if session.sport == "bowling" { return .bowling }
        return menu.launch?.sport ?? Sport(rawValue: session.sport) ?? .tennis
    }
    private var venueID: String { lobbyLoading ? service.lobby?.venue ?? (sport == .golf ? session.golfCourse : session.tennisVenue) : (sport == .golf ? session.golfCourse : session.tennisVenue) }
    private var golfCourse: String { MultiplayerLobby.currentGolfVenue(MultiplayerLobby.golfRoundParts(venueID).course) }
    /// "Tropical Resort", "Cliffside", "the lanes".
    private var venueName: String {
        switch sport {
        case .golf: GolfCourseChoice(rawValue: golfCourse)?.title ?? "Cliffside"
        case .bowling: "the lanes"
        default: TennisVenueChoice(rawValue: venueID)?.title ?? "Tropical Resort"
        }
    }
    private var modeLine: String {
        if sport == .golf { return "Golf · Stroke Play · \(GolfCourseChoice.venueTitle(lobbyLoading || menu.launch?.daily != nil ? venueID : MultiplayerLobby.golfRound(venueID, holes: session.golfHoles, link: session.golfLinkCourses)))" }
        if sport == .bowling { return "Bowling · 10 frames" }
        if menu.launch?.mode == .training { return "Tennis · Practice · \(venueName)" }
        return "Tennis · Singles · \(venueName)"
    }
    /// The venue's loading art (Assets: loading-<sport>-<venue>), else its map still.
    private var art: UIImage? {
        switch sport {
        case .golf: UIImage(named: "loading-golf-\(golfCourse)") ?? UIImage(named: "map-golf-\(golfCourse).jpg")
        case .bowling: UIImage(named: "loading-bowling-lanes")
        default: UIImage(named: "loading-tennis-\(venueID)") ?? UIImage(named: "map-\(venueID).jpg")
        }
    }
    /// The sport's colour on the bar and the percentage: tennis gold, golf green, bowling glow blue.
    private var accent: Color { sport == .golf ? MSBrand.success : sport == .bowling ? MSBrand.glow : MSBrand.gold }
    /// What the bar says: the venue, or why it is waiting.
    private var line: String {
        let status = loading.statusText
        return loading.phase == .loading && !loading.isStalled && loading.waitingPlayers.isEmpty ? "Loading \(venueName)…" : status
    }
    private var percent: Int { Int((loading.displayProgress * 100).rounded()) }
    /// The tip card sits left for tip 1 and right for tip 2, the wordmark in the other top corner.
    private var cardLeading: Bool { (loading.tipNumber ?? 1) == 1 }

    var body: some View {
        Group { if compact { phone } else { tv } }
            .accessibilityIdentifier("presentation-loading-card")
    }

    private var backdrop: some View {
        ZStack {
            MSBrand.backdrop()
            if let art { Image(uiImage: art).resizable().scaledToFill() }
        }
    }

    // MARK: TV (1280×720)

    private var tv: some View {
        ZStack(alignment: .topLeading) {
            backdrop.frame(width: 1280, height: 720).clipped()
            LinearGradient(stops: [.init(color: MSBrand.navyInk.opacity(0.45), location: 0), .init(color: .clear, location: 0.22),
                                   .init(color: .clear, location: 0.58), .init(color: MSBrand.navyInk.opacity(0.78), location: 1)],
                           startPoint: .top, endPoint: .bottom)
            MSWordmark(size: 34).position(x: cardLeading ? 1150 - 105 : 130 + 105, y: 66)
            if loading.tip != nil {
                tipCard(width: 600).frame(width: 600)
                    .position(x: cardLeading ? 130 + 300 : 1150 - 300, y: 452)
                    .id(loading.tipNumber).transition(.opacity)
            }
            if needsControls { controls.position(x: 640, y: 300) }
            bar(labelSize: 24, height: 20).frame(width: 1020).position(x: 130 + 510, y: 618)
            MSArcRing(color: accent).frame(width: 44, height: 44).position(x: 1190, y: 636)
        }
        .frame(width: 1280, height: 720).clipped()
        .ignoresSafeArea()
        .foregroundStyle(.white)
        .animation(.easeInOut(duration: 0.35), value: loading.tipNumber)
    }

    // MARK: Phone (upright)

    private var phone: some View {
        GeometryReader { g in
            ZStack(alignment: .top) {
                MSBrand.backdrop(spotlight: UnitPoint(x: 0.5, y: 0.6), radius: 520).ignoresSafeArea()
                VStack(spacing: 0) {
                    ZStack(alignment: .bottomLeading) {
                        backdrop.frame(width: g.size.width, height: g.size.height * 0.44).clipped()
                        LinearGradient(colors: [MSBrand.navyInk.opacity(0.55), .clear, .clear, MSBrand.navyDeep], startPoint: .top, endPoint: .bottom)
                        VStack(alignment: .leading, spacing: 2) {
                            Text(venueName == "the lanes" ? "Bowling" : venueName).font(MSLoadingFont.display(34)).lineLimit(1).minimumScaleFactor(0.6)
                            Text(modeLine).font(MSLoadingFont.subline(15)).foregroundStyle(MSBrand.n300).lineLimit(1).minimumScaleFactor(0.7)
                        }
                        .shadow(color: MSBrand.textShadow.opacity(0.6), radius: 6, y: 2)
                        .padding(.horizontal, 22).padding(.bottom, 14)
                    }
                    .frame(height: g.size.height * 0.44)
                    .overlay(alignment: .top) { MSWordmark(size: 24).padding(.top, g.safeAreaInsets.top + 12) }
                    VStack(spacing: 22) {
                        if loading.tip != nil { tipCard(width: nil).id(loading.tipNumber).transition(.opacity) }
                        Spacer(minLength: 0)
                        HStack(alignment: .bottom, spacing: 12) {
                            bar(labelSize: 17, height: 16)
                            MSArcRing(color: accent).frame(width: 30, height: 30)
                        }
                        controls
                    }
                    .padding(.horizontal, 22).padding(.top, 26).padding(.bottom, max(18, g.safeAreaInsets.bottom))
                }
            }
            .ignoresSafeArea()
            .foregroundStyle(.white)
            .animation(.easeInOut(duration: 0.35), value: loading.tipNumber)
        }
    }

    // MARK: Pieces

    /// TENNIS TIP 1/2 · phone icon · headline in gold · one line of how to play.
    private func tipCard(width: CGFloat?) -> some View {
        let tv = width != nil
        return HStack(alignment: .center, spacing: tv ? 18 : 14) {
            RoundedRectangle(cornerRadius: tv ? 12 : 10, style: .continuous)
                .fill(LinearGradient(colors: [MSBrand.lift, MSBrand.royal], startPoint: .top, endPoint: .bottom))
                .overlay(Image(systemName: "iphone").font(.system(size: tv ? 30 : 24, weight: .bold)).foregroundStyle(.white))
                .overlay(RoundedRectangle(cornerRadius: tv ? 12 : 10, style: .continuous).strokeBorder(.white.opacity(0.35), lineWidth: 1.5))
                .frame(width: tv ? 60 : 48, height: tv ? 60 : 48)
            VStack(alignment: .leading, spacing: tv ? 6 : 4) {
                Text(loading.tipTitle ?? "").font(MSLoadingFont.display(tv ? 30 : 22)).foregroundStyle(MSBrand.gold).lineLimit(1).minimumScaleFactor(0.7)
                Text(loading.tip ?? "").font(MSLoadingFont.body(tv ? 19 : 15)).foregroundStyle(.white).fixedSize(horizontal: false, vertical: true)
            }
            Spacer(minLength: 0)
        }
        .padding(.horizontal, tv ? 22 : 16).padding(.top, tv ? 26 : 22).padding(.bottom, tv ? 20 : 16)
        .background(LinearGradient(colors: [Color(hex: "1A3FA0"), MSBrand.navyDeep], startPoint: .top, endPoint: .bottom),
                    in: RoundedRectangle(cornerRadius: tv ? 16 : 14, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: tv ? 16 : 14, style: .continuous).strokeBorder(.white, lineWidth: tv ? 4 : 3))
        .shadow(color: MSBrand.shadowInk.opacity(0.43), radius: 14, y: 11)
        .overlay(alignment: .topLeading) {
            Text("\(sport.title) TIP \(loading.tipNumber ?? 1)/\(LoadingModel.tipsPerLoad)")
                .font(MSLoadingFont.display(tv ? 14 : 12)).tracking(0.5).foregroundStyle(MSBrand.navyInk)
                .padding(.horizontal, 12).padding(.vertical, 4)
                .background(MSBrand.gold, in: Capsule()).overlay(Capsule().strokeBorder(.white, lineWidth: 2))
                .offset(x: tv ? 18 : 14, y: tv ? -14 : -12)
        }
        .accessibilityElement(children: .combine).accessibilityIdentifier("loading-tip")
    }

    /// "Loading Tropical Resort…" and the percentage over the bar.
    private func bar(labelSize: CGFloat, height: CGFloat) -> some View {
        VStack(spacing: height * 0.6) {
            HStack(alignment: .firstTextBaseline) {
                Text(line).font(MSLoadingFont.display(labelSize)).lineLimit(1).minimumScaleFactor(0.6)
                    .shadow(color: MSBrand.textShadow.opacity(0.6), radius: 4, y: 1)
                Spacer(minLength: 10)
                Text("\(percent)%").font(MSLoadingFont.display(labelSize)).foregroundStyle(accent).monospacedDigit()
                    .shadow(color: MSBrand.textShadow.opacity(0.6), radius: 4, y: 1)
            }
            MSLoadingBar(progress: loading.displayProgress, fill: accent, height: height)
        }
        .accessibilityElement(children: .combine).accessibilityIdentifier("presentation-loading-status")
    }

    /// Leave / Retry / Keep waiting. The phone always offers Leave match; the TV shows them only when there is a decision.
    private var needsControls: Bool {
        loading.isStalled || loading.phase == .failed || (session.multiplayerMatchID != nil || lobbyLoading) && service.loadingNeedsDecision
    }
    private var controls: some View {
        HStack(spacing: 16) {
            if session.multiplayerMatchID != nil || lobbyLoading {
                if service.loadingNeedsDecision {
                    IslandAction(title: "Keep waiting", focused: menu.isFocused("net-wait"), primary: true, compact: true) { menu.tap("net-wait") }
                }
                IslandAction(title: "Leave match", focused: menu.isFocused("net-leave"), compact: true) { menu.tap("net-leave") }
            } else {
                IslandAction(title: "Leave match", focused: menu.isFocused("loadingBack"), compact: true) { menu.tap("loadingBack") }
                if loading.isStalled || loading.phase == .failed {
                    IslandAction(title: "Retry", focused: menu.isFocused("loadingRetry"), primary: true, compact: true) { menu.tap("loadingRetry") }
                }
            }
        }
    }
    static func label(_ launch: MenuLaunch, _ opponent: TennisOpponent?) -> String {
        launch.sport == .golf ? (GolfCourseChoice(rawValue: SportsSession.shared.golfCourse)?.title ?? "Cliffside") : (TennisVenueChoice(rawValue: SportsSession.shared.tennisVenue)?.title ?? "Tropical Resort")
    }
}


extension TennisMenu {
    /// A readable name for a menu item, for the phone remote.
    static func label(for id: String) -> String {
        if id.hasPrefix("home-emote-") { return TennisMenu.homeEmoteName(String(id.dropFirst(11))) }
        if id.hasPrefix("sport-"), let s = Sport(rawValue: String(id.dropFirst(6))) { return s.playable ? s.title.capitalized : "\(s.title.capitalized) · coming soon" }
        if id.hasPrefix("tab-"), let t = SettingsTab(rawValue: String(id.dropFirst(4))) { return "Settings · \(t.title)" }
        if id.hasPrefix("lk-") { return lockerLabel(id) }
        if id.hasPrefix("map-"), let v = TennisVenueChoice(rawValue: String(id.dropFirst(4))) { return v.title }
        if id.hasPrefix("rival"), let r = Int(id.dropFirst(5)) {
            let o = TennisCampaign.draw[r]
            return TennisCampaign.shared.unlocked(r) ? "Exhibition · \(o.name)" : "Exhibition · Locked"
        }
        switch id {
        case "homeCampaign": return "Campaign"
        case "store": return "Store · Coming soon"
        case "campaignPlay": return "Play Round"
        case "quickOpponent": return "Opponent"
        case "quickDifficulty": return "Difficulty"
        case "quickLength": return "Match length"
        case "quickStart": return "Start Match"
        case "homePlay": return "Play with Friends"
        case "partySolo": return "Single Player"
        case "partyMultiplayer": return "Multiplayer"
        case "partyOnline": return "Online"
        case "partyLocal": return "Local"
        case "partyNearby": return "Join a Friend"
        case "partyLocalGolf": return "Golf · Pass the Phone"
        case "partyLocalTennis": return "Tennis · Two Phones"
        case "partyNearbyTennis": return "Tennis with a friend nearby"
        case "localPlayers2", "localPlayers3", "localPlayers4": return "\(id.dropFirst("localPlayers".count)) Players"
        case "onlineQuick": return "Quick Match"
        case "homeInvite": return "Play with Friends"
        case "homeEmotes": return "Emotes"
        case "betaFeedback": return "Feedback"
        case "loadingBack": return "Back to Home"; case "loadingRetry": return "Retry loading"
        case "play": return "Play"; case "character": return "Locker"; case "settings": return "Settings"
        case "howto": return "How to play"; case let g where g.hasPrefix("guide-"): return GuideDeck(rowID: g)?.title ?? "Guide"; case "tutorial": return "Tutorial"; case "replayTutorial": return "Replay tutorial"
        case "campaign": return "Island Circuit"; case "training": return "Training court"; case "exhibition": return "Exhibition"
        case "round": return "Play Cliffside"; case "golfCampaign": return "Golf campaign · coming soon"; case "golfTraining": return "Driving range · coming soon"
        case "nextPage", "nextCard": return "Next"; case "prev": return "Previous"; case "randomize": return "Randomize"; case "reset": return "Kit colours"
        default:
            let s = SportsSession.shared
            let p = s.players.indices.contains(s.playerIndex) ? s.players[s.playerIndex] : nil
            let (label, value) = SettingsScreen.describe(id, s, p)
            if label != id { return "\(label): \(value)" }
            switch id {
            case "body": return "Body: \(p?.standardFemale == true ? "Female" : "Male")"
            case "skin": return "Skin: \(TennisMenu.skinTones[p?.standardSkin ?? 2])"
            case "shirt": return "Shirt: \((p?.outfitName("shirt") ?? "Kit colour"))"
            case "shorts": return "\(TennisMenu.shared.lockerBottomName): \((p?.outfitName("shorts") ?? "Kit colour"))"
            case "accent": return "Bands: \((p?.outfitName("accent") ?? "Kit colour"))"
            case "racket": return "Racket: \((p?.outfitName("racket") ?? "Kit colour"))"
            default: return id.prefix(1).uppercased() + id.dropFirst()
            }
        }
    }
}
