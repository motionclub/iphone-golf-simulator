import SwiftUI
import UIKit

/// A reading from the game, in the same club order and map projection as the TV HUD.
struct GolfControllerReading: Codable {
    struct PartyPlayer: Codable, Identifiable {
        var seat: Int; var name: String; var controlled: Bool; var canEmote: Bool; var emotes: [String]
        var id: Int { seat }
    }
    struct Party: Codable {
        var turn: Int; var shotID: Int64; var player: String; var outcome: String; var phase: String
        var myTurn: Bool; var shared: Bool; var putt: Bool
        var resultSeconds: Double; var carry: Double; var roll: Double; var apex: Double; var total: Double
        var players: [PartyPlayer]
    }
    var party: Party?
    struct Point: Codable { var x: Double; var y: Double }
    var hole: Int
    var name: String
    var par: Int
    var yards: Double
    var wind: Double
    var windDegrees: Double
    var clubIndex: Int
    var clubName: String
    var clubYards: Double
    var aimDegrees: Double
    var ball: Point?
    var pin: Point?
    var landing: Point?
    var path: [Point]?
    var reach: [Point]?
    /// A putt's meter marks (25/50/75/100 %) where each rolls the ball, and their feet.
    var targets: [Point]?
    var targetLabels: [String]?
    var mapImage: String?
    var direction: Point?

    static let waiting = Self(hole: 0, name: "CONNECTING", par: 0, yards: 0, wind: 0, windDegrees: 0,
                              clubIndex: 0, clubName: "Driver", clubYards: 240, aimDegrees: 0)
    #if DEBUG
    static let reference = Self(hole: 21, name: "Obsidian Slab", par: 3, yards: 166, wind: 7, windDegrees: 90,
                                clubIndex: 7, clubName: "Lob Wedge", clubYards: 50, aimDegrees: -3)
    #endif
    var aimLabel: String {
        abs(aimDegrees) < 0.5 ? "STRAIGHT" : "\(Int(abs(aimDegrees).rounded()))° \(aimDegrees < 0 ? "LEFT" : "RIGHT")"
    }
}

private enum GolfControllerStyle {
    static let blue = Color(hex: "008AF5"), ink = Color(hex: "005AB5")
    static let yellow = Color(hex: "FFD300")
    static let amber = Color(hex: "F2A81D"), green = Color(hex: "00C92C")
    static func font(_ size: CGFloat) -> Font { ClubFonts.font(.ui, size: size, weight: 900, width: nil) }
}

/// Reuses the supplied illustration as an art atlas. All controls and labels are live SwiftUI.
private enum GolfControllerArtwork {
    static let atlas: UIImage? = {
        guard let url = Bundle.main.url(forResource: "golf-controller-artwork", withExtension: "png") else { return nil }
        return UIImage(contentsOfFile: url.path)
    }()
    static func sprite(_ rect: CGRect) -> UIImage? {
        guard let cg = atlas?.cgImage?.cropping(to: rect) else { return nil }
        return UIImage(cgImage: cg)
    }
    static let club = sprite(CGRect(x: 127, y: 603, width: 99, height: 108))
    #if DEBUG
    static let referenceMap = sprite(CGRect(x: 23, y: 232, width: 417, height: 296))
    #endif
}

/// Bold white type with the blue outline from the supplied controller reference.
private struct GolfControllerText: View {
    let text: String
    var size: CGFloat
    var stroke: CGFloat = 3
    var lines: Int? = nil
    private var label: some View { Text(text).lineLimit(lines).minimumScaleFactor(0.6) }
    var body: some View {
        ZStack {
            ForEach(0..<8, id: \.self) { i in
                label.offset(x: cos(Double(i) * .pi / 4) * stroke,
                                  y: sin(Double(i) * .pi / 4) * stroke + 1)
                    .foregroundStyle(GolfControllerStyle.ink)
            }
            label.foregroundStyle(.white)
        }
        .font(GolfControllerStyle.font(size)).multilineTextAlignment(.center).lineSpacing(-3)
        .fixedSize(horizontal: false, vertical: true)
        .accessibilityElement(children: .ignore).accessibilityLabel(text.replacingOccurrences(of: "\n", with: " "))
    }
}

/// The flick at the end of a look slide (GolfPhoneController.slideLook): quick and mostly vertical, it takes the aerial view all the
/// way up or back down. `distance` is the travel it needs in the pad's own points. Returns true for up, false for down, nil for no flick.
enum GolfLookFlick {
    static func direction(translation t: CGSize, velocity v: CGSize, distance: CGFloat) -> Bool? {
        guard abs(t.height) >= distance, abs(t.height) > abs(t.width) * 1.6, abs(v.height) >= 300,
              (v.height < 0) == (t.height < 0) else { return nil }
        return t.height < 0
    }
}

/// Sliding up or down on the aim pad moves the aerial view with the finger (11-23, Adnan: "it still doesnt let you slide up"; only a
/// quick flick used to count). Each drag is sorted once, when it has travelled `decideAfter` points: mostly vertical is a look slide,
/// anything else is aim, for the rest of that drag.
enum GolfLookSlide {
    enum Axis { case aim, look }
    static let decideAfter: CGFloat = 14
    static func axis(translation t: CGSize) -> Axis? {
        guard hypot(t.width, t.height) >= decideAfter else { return nil }
        return abs(t.height) > abs(t.width) * 1.6 ? .look : .aim
    }
    /// The look (0 at the golfer, 1 the full aerial view) after sliding `dy` points (up is negative) from `start`; `range` points is a
    /// whole climb.
    static func value(start: Double, dy: CGFloat, range: CGFloat) -> Double {
        max(0, min(1, start - Double(dy / range)))
    }
}

struct GolfPhoneController: View {
    @Bindable var session: SportsSession
    @State private var partyChat = false
    /// Leave game or Leave party, waiting on its check (online: it says what happens to the others).
    private enum Leaving { case game, party }
    @State private var leaving: Leaving?
    @State private var stickOffset = CGSize.zero
    /// Drag to aim works like a pointer (11-16, Adnan: "the trackpad is a bit too sensitive"): the finger moves the aim gently, in
    /// any direction (GolfPhoneController.trackpad).
    @State private var lastDrag: CGPoint?
    @State private var pointer: CGVector?
    /// How far one point of finger travel moves the aim's unit direction: about 0.2° per point near the current aim.
    static let aimPointerGain: CGFloat = 0.0035
    @State private var draggingAim = false
    @State private var lastAimSent = -Double.infinity
    /// The aim when the drag began: a flick puts it back, so swiping for the aerial view doesn't also turn the aim.
    @State private var dragStartAim: CGVector?
    /// Slid up on the aim pad (11-20, Adnan: "swiping up on the controller doesnt let you go aerial mode"; 11-23 a slide, not only a
    /// flick): the aiming camera climbs and looks up the hole to the pin (GolfGame's look, as the TV stick pushed up), 0 at the
    /// golfer to 1 the full aerial view. It stays where the slide leaves it until a slide down or the shot.
    @State private var look: Double = 0
    /// How the drag in progress is read (GolfLookSlide.axis); nil until it has moved far enough to tell.
    @State private var dragAxis: GolfLookSlide.Axis?
    @State private var lookAtDragStart: Double = 0
    @State private var lastLookSent = -Double.infinity
    /// Handheld play: the hole map opened full screen from its corner of the game view.
    @State private var mapExpanded = Self.debugMapOpen
    private static var debugMapOpen: Bool {
        #if DEBUG
        ProcessInfo.processInfo.arguments.contains("-handheldMapOpen")
        #else
        false
        #endif
    }
    private var reading: GolfControllerReading { session.golfController }
    private var canAim: Bool { session.ready && session.golfPhase == "Aim" && !session.paused && (reading.party?.myTurn ?? true) }
    /// A result screen with buttons is up on the TV (a shot's result, a hole out, the round's end): the pad steers its buttons
    /// instead of the aim, and its centre taps the one that is lit.
    private var canMenu: Bool { session.ready && !session.paused && session.golfMenuOpen }
    /// The course being played: the controller wears its material (UI OVERHAUL 11-15, boards 04-06).
    private var skin: MapSkin { MapSkin.of(sport: "golf", venue: session.shownGolfCourse) }
    private var playerName: String { reading.party?.player ?? MapSkin.playerName(session) }
    private var isDesignPreview: Bool {
        #if DEBUG
        ProcessInfo.processInfo.arguments.contains("-golfControllerDesign")
        #else
        false
        #endif
    }

    var body: some View {
        Group {
            // no TV of this phone's own: the round above, the controls on a deck below (handheld play)
            if session.phonePlay { handheldLayout }
            else {
                GeometryReader { geometry in
                    let scale = min(geometry.size.width / 464, geometry.size.height / 1000)
                    ZStack {
                        MapControllerBackground(skin: skin)
                        controllerCanvas
                            .frame(width: 464, height: 1000)
                            .scaleEffect(scale)
                            .frame(width: geometry.size.width, height: geometry.size.height)
                        // (this layout ignores the safe area: the map keeps clear of the Dynamic Island and the home bar)
                        if mapExpanded {
                            ZStack { LinearGradient(colors: [skin.top, skin.bottom], startPoint: .top, endPoint: .bottom); handheldMap.padding(.top, 54).padding(.bottom, 20) }
                                .transition(.opacity)
                        }
                    }
                    .animation(.easeOut(duration: 0.18), value: mapExpanded)
                    .onChange(of: session.golfPhase) { _, phase in if phase != "Aim" { mapExpanded = false } }
                }
                .ignoresSafeArea()
            }
        }
        .statusBarHidden().persistentSystemOverlays(.hidden).preferredColorScheme(.dark)
        .sheet(isPresented: $session.menuPauseVisible) {
            GamePauseMenu(session: session)
        }
        // (the game drops the aerial look for each new shot; the controller follows)
        .onChange(of: session.golfPhase) { _, phase in if phase != "Aim" { look = 0 } }
        .onChange(of: session.paused) { _, paused in
            if paused { draggingAim = false; stickOffset = .zero; lastDrag = nil; pointer = nil; dragStartAim = nil; dragAxis = nil }
        }
    }

    /// The 464 × 1000 canvas (boards 04-06): name plate and pause, HOLE · PAR over the yards to the pin, the club selector, the
    /// drag-to-aim panel (the hole map under it, the shot's state cards over it) and TAP TO SWING.
    private var controllerCanvas: some View {
        ZStack(alignment: .topLeading) {
            Color.clear
            // (top left is the record / mic dock, CaptureDock; feedback is in the pause menu)
            MapPlate(skin: skin, text: playerName.uppercased(), height: 104).mapEntrance(delay: 0.1).position(x: 232, y: 70)
                .accessibilityIdentifier("controller-name-plate")
            Button { session.pause() } label: { MapPauseFace(skin: skin, size: 50) }
                .buttonStyle(.plain).position(x: 414, y: 70).accessibilityLabel("Pause golf").accessibilityIdentifier("golf-pause")
            holeCard.frame(width: 260).position(x: 232, y: 184)
            tvStatus.frame(width: 78, height: 30).position(x: 52, y: 190)
            windChip.position(x: 404, y: 190)
            clubSelector.frame(width: 424, height: 88).position(x: 232, y: 298)
            aimPanel.frame(width: 424, height: 420).position(x: 232, y: 572)
            swingSlot.frame(width: 424, height: 104).position(x: 232, y: 856)
            Text(reading.party?.phase == "result" ? (reading.party?.shared == true ? "Next player starts automatically" : "Pick an emote · next player starts automatically") : reading.party?.myTurn == false ? "Watch the shot · react with your player" : "Drag to aim · tap to swing · tap again to cancel")
                .font(MapFont.semi(14)).foregroundStyle(.white.opacity(0.8))
                .frame(width: 440).position(x: 232, y: 948)
        }.overlay {
            // (on one shared phone the turn just passes: no reaction panel)
            if let party=reading.party, !party.shared, party.phase == "result" || party.phase == "flight" || !party.myTurn {
                GolfPartyEmoteControls(session:session,party:party).padding(20).frame(width:424,height:410)
                    .mapPanel(skin, radius: 26).position(x:232,y:600)
            }
        }.buttonStyle(GolfControllerPressStyle())
    }

    /// HOLE 1 · PAR 4 on a tab over the yards to the pin (board: "416 yd").
    private var holeCard: some View {
        VStack(spacing: -12) {
            Text("HOLE \(reading.hole) · PAR \(reading.par)").font(MapFont.bold(17)).foregroundStyle(skin.ink)
                .padding(.horizontal, 16).padding(.vertical, 5)
                .background(skin.cream, in: Capsule()).overlay(Capsule().strokeBorder(skin.frame, lineWidth: 2.5)).zIndex(1)
                .accessibilityIdentifier("golf-hole-reading")
            HStack(alignment: .firstTextBaseline, spacing: 4) {
                Text("\(Int(reading.yards.rounded()))").font(MapFont.bold(54)).monospacedDigit()
                Text("yd").font(MapFont.bold(30))
            }
            .foregroundStyle(skin.cream).frame(maxWidth: .infinity).padding(.top, 14).padding(.bottom, 4)
            .mapPanel(skin, radius: 24)
        }
        .accessibilityElement(children: .combine).accessibilityLabel("Hole \(reading.hole), par \(reading.par), \(Int(reading.yards.rounded())) yards")
    }

    /// The handheld map's hole badge.
    private var holeBadge: some View {
        Text("HOLE \(reading.hole) · PAR \(reading.par)").font(MapFont.bold(22)).foregroundStyle(skin.ink)
            .padding(.horizontal, 18).frame(maxHeight: .infinity)
            .background(skin.cream, in: Capsule()).overlay(Capsule().strokeBorder(skin.frame, lineWidth: 3))
            .accessibilityIdentifier("golf-hole-reading")
    }

    /// Calm, or the wind's speed with an arrow the way it blows.
    private var windChip: some View {
        HStack(spacing: 4) {
            if reading.wind >= 0.5 {
                Image(systemName: "location.north.fill").font(.system(size: 13, weight: .black)).rotationEffect(.degrees(reading.windDegrees))
            }
            Text(reading.wind < 0.5 ? "Calm" : "\(Int(reading.wind.rounded())) mph").font(MapFont.bold(15))
        }
        .foregroundStyle(skin.ink).padding(.horizontal, 10).frame(height: 32)
        .background(skin.cream, in: Capsule()).overlay(Capsule().strokeBorder(skin.frame, lineWidth: 2))
        .accessibilityLabel(reading.wind < 0.5 ? "Calm" : "Wind \(Int(reading.wind.rounded())) miles an hour")
    }

    private var tvStatus: some View {
        Text(session.multiplayerControllerOnly ? "PARTY" : session.displayConnected ? "TV ON" : "TV OFF").font(MapFont.bold(13))
            .foregroundStyle(.white).frame(width: 72, height: 28)
            .background((session.displayConnected || session.multiplayerControllerOnly) ? Color(hex: "1FA94A") : skin.frameDeep, in: Capsule())
            .overlay(Capsule().stroke(.white.opacity(0.8), lineWidth: 2))
            .accessibilityLabel(session.multiplayerControllerOnly ? "Using the host’s display" : session.displayConnected ? "TV connected" : "TV disconnected")
    }

    /// The handheld map's stat chips: PAR 4 · 416 YD · 7 MPH.
    private func statBadge(_ text: String, icon: String?) -> some View {
        HStack(spacing: 6) {
            if let icon {
                if icon == "wind" {
                    Image(systemName: "location.north.fill").font(.system(size: 15, weight: .black)).rotationEffect(.degrees(reading.windDegrees))
                } else { Circle().fill(skin.ink).frame(width: 12, height: 12) }
            }
            Text(text).font(MapFont.bold(19)).lineLimit(1).minimumScaleFactor(0.7)
        }.foregroundStyle(skin.ink).frame(maxWidth: .infinity, maxHeight: .infinity)
            .background(skin.cream, in: RoundedRectangle(cornerRadius: 14))
            .overlay(RoundedRectangle(cornerRadius: 14).stroke(skin.frame, lineWidth: 2.5))
    }

    /// Drag to aim (boards 04-06): the hole map under a tint of the course's colour, corner brackets, the aim reticle that follows the
    /// thumb, chevrons that nudge the aim, and the aim's reading. Over it, the shot's state cards (result, round over, a friend's turn, Ready).
    private var aimPanel: some View {
        GeometryReader { g in
            let size = g.size
            ZStack {
                GolfControllerMap(reading: reading, image: session.golfControllerMap, reference: isDesignPreview)
                    .opacity(0.6).accessibilityIdentifier("golf-course-preview")
                LinearGradient(colors: [skin.surface.opacity(0.5), skin.bottom.opacity(0.7)], startPoint: .top, endPoint: .bottom)
                AimBrackets().stroke(skin.line, style: StrokeStyle(lineWidth: 3.5, lineCap: .round)).padding(24)
                // the curve the aim sends the ball along (board: a dashed arc to an arrowhead), turned with the aim
                AimArc().stroke(skin.line.opacity(0.8), style: StrokeStyle(lineWidth: 3, lineCap: .round, dash: [8, 8]))
                    .frame(width: size.width * 0.5, height: size.height * 0.36).offset(y: -size.height * 0.16)
                    .rotationEffect(.degrees(reading.aimDegrees), anchor: .bottom)
                aimArrow("chevron.up", x: 0, y: -size.height / 2 + 30, label: "Aim up course") { session.aimGolf(across: 0, forward: 1) }
                aimArrow("chevron.down", x: 0, y: size.height / 2 - 30, label: "Aim down course") { session.aimGolf(across: 0, forward: -1) }
                aimArrow("chevron.left", x: -size.width / 2 + 30, y: 0, label: "Aim left") { nudge(-1) }
                aimArrow("chevron.right", x: size.width / 2 - 30, y: 0, label: "Aim right") { nudge(1) }
                // the hole map full screen (2026-11-16, Adnan: a map "ppl can click to expand … make sure thats a thing for airplay mode")
                if session.golfControllerMap != nil || isDesignPreview {
                    Button { mapExpanded = true } label: {
                        Image(systemName: "arrow.up.left.and.arrow.down.right").font(.system(size: 17, weight: .black)).foregroundStyle(skin.ink)
                            .frame(width: 46, height: 46).background(skin.cream, in: Circle()).overlay(Circle().strokeBorder(skin.frame, lineWidth: 2.5))
                    }.buttonStyle(.plain).offset(x: size.width / 2 - 38, y: -size.height / 2 + 38)
                        .accessibilityLabel("Open the hole map").accessibilityIdentifier("golf-map-open")
                }
                Button {
                    if canMenu { session.selectGolfMenu() }
                    else if session.paused || !session.golfShotReady { session.readyToPlay() }
                } label: {
                    ZStack {
                        Circle().strokeBorder(skin.cream, lineWidth: 4).frame(width: 64, height: 64)
                        Circle().fill(skin.cream).frame(width: 18, height: 18)
                        ForEach(0..<4, id: \.self) { i in
                            Capsule().fill(skin.cream).frame(width: 4, height: 14).offset(y: -40).rotationEffect(.degrees(Double(i) * 90))
                        }
                    }.frame(width: 92, height: 92).contentShape(Circle()).shadow(color: .black.opacity(0.35), radius: 3, y: 2)
                }.buttonStyle(.plain).offset(thumbOffset(scale: 2.2))
                    .disabled(!canAim && !canMenu)
                    .accessibilityLabel(canMenu ? "Select" : "Ready for shot")
                    .accessibilityIdentifier("golf-aim-center")
                Text(look > 0.05 && canAim ? "Aerial view · slide down" : reading.aimLabel == "STRAIGHT" ? "Drag to aim · slide up: aerial" : reading.aimLabel.capitalized).font(MapFont.bold(21)).foregroundStyle(skin.cream)
                    .lineLimit(1).minimumScaleFactor(0.7).frame(maxWidth: size.width - 40)
                    .shadow(color: .black.opacity(0.45), radius: 2, y: 1)
                    .offset(y: size.height / 2 - 74)
                    .accessibilityIdentifier("golf-aim-reading")
                stateCards.padding(18)
            }
            .contentShape(Rectangle())
            .simultaneousGesture(DragGesture(minimumDistance: 8, coordinateSpace: .local)
                .onChanged { drag in padDrag(drag, centre: CGPoint(x: size.width / 2, y: size.height / 2), reach: 110, lookRange: 170, final: false) }
                .onEnded { drag in
                    padDrag(drag, centre: CGPoint(x: size.width / 2, y: size.height / 2), reach: 110, lookRange: 170, final: true)
                    // (the TV's menu ring re-arms when the stick comes back to the middle)
                    if canMenu { session.aimGolf(across: 0, forward: 0) }
                    draggingAim = false; stickOffset = .zero; lastDrag = nil; pointer = nil; dragStartAim = nil; dragAxis = nil
                })
        }
        .clipShape(RoundedRectangle(cornerRadius: 28, style: .continuous))
        .background { RoundedRectangle(cornerRadius: 28, style: .continuous).fill(skin.frameDeep).offset(y: 5) }
        .overlay(RoundedRectangle(cornerRadius: 28, style: .continuous).strokeBorder(skin.line.opacity(0.9), lineWidth: 3))
        .accessibilityElement(children: .contain)
        .accessibilityIdentifier("golf-aim-joystick")
    }

    /// What the shot is waiting on, over the aim panel: connecting, a shot's result, the round's end, a friend's turn, Ready.
    @ViewBuilder private var stateCards: some View {
        if !session.ready || !session.loading.finished {
            ProgressView("Connecting to the course").font(MapFont.semi(16)).tint(skin.ink).foregroundStyle(skin.ink)
                .padding(22).background(skin.cream, in: RoundedRectangle(cornerRadius: 20))
        } else if session.golfPhase == "Result" {
            GolfShotResultControls(session: session).padding(20).mapPanel(skin, radius: 22)
        } else if session.golfPhase == "RoundDone" {
            VStack(spacing: 14) {
                // the Daily Hole in One: share the three shots first (mockups: ArtDir/ui/daily-challenge-ui-mockups)
                if session.holeInOneDay != 0 { DailyShareButton(skin: skin, height: 84).frame(width: 320) }
                Button { session.continueGolfRound() } label: {
                    MapActionFace(skin: skin, title: session.golfHasNextHole ? "Next Hole" : TennisMenu.shared.postMatch?.golf != nil ? "Finish Round" : "Rematch", height: session.holeInOneDay != 0 ? 60 : 76)
                }.buttonStyle(.plain).frame(width: 300).accessibilityIdentifier("golf-continue")
            }
        } else if let party=reading.party, !party.myTurn && !session.paused {
            Text("\(party.player)’s turn").font(MapFont.bold(24)).foregroundStyle(skin.ink)
                .padding(.horizontal, 24).padding(.vertical, 14).background(skin.cream, in: Capsule())
                .overlay(Capsule().strokeBorder(skin.frame, lineWidth: 3))
        // (in a round with others the game readies each shot by itself)
        } else if session.paused || (session.golfPhase == "Aim" && !session.golfShotReady && reading.party == nil) {
            VStack(spacing: 10) {
                Text("Ready to swing?").font(MapFont.bold(26))
                Text("Tap Ready, then tap to swing and swing.").font(MapFont.semi(16)).multilineTextAlignment(.center)
            }.foregroundStyle(skin.ink).padding(22)
                .background(skin.cream, in: RoundedRectangle(cornerRadius: 22))
                .overlay(RoundedRectangle(cornerRadius: 22).strokeBorder(skin.frame, lineWidth: 3))
        }
    }

    /// The club selector (board: ◀ [club] Driver 240 yd ▶): the club's picture and name on a pill of the course's material.
    private var clubSelector: some View {
        HStack(spacing: 10) {
            arrowButton(right: false) { changeClub(-1) }
            GolfControllerClubIcon(index: reading.clubIndex).frame(width: 58, height: 62).accessibilityHidden(true)
            VStack(alignment: .leading, spacing: -2) {
                Text(reading.clubName).font(MapFont.bold(26)).lineLimit(1).minimumScaleFactor(0.6)
                Text("\(Int(reading.clubYards.rounded())) yd").font(MapFont.bold(22)).monospacedDigit()
            }.foregroundStyle(skin.ink).frame(maxWidth: .infinity, alignment: .leading)
                .accessibilityElement(children: .ignore)
                .accessibilityLabel("\(reading.clubName), \(Int(reading.clubYards)) yards")
                .accessibilityIdentifier("golf-selected-club")
            arrowButton(right: true) { changeClub(1) }
        }
        .padding(.horizontal, 12)
        .frame(maxHeight: .infinity)
        .background {
            Capsule().fill(skin.frameDeep).offset(y: 5)
            Capsule().fill(LinearGradient(colors: [skin.cream, skin.cream.mix(skin.frame, 0.1)], startPoint: .top, endPoint: .bottom))
            Capsule().strokeBorder(skin.frame, lineWidth: 4)
        }
    }

    /// The handheld deck's club card (the selector's content, square).
    private var clubCard: some View {
        VStack(spacing: 4) {
            GolfControllerClubIcon(index: reading.clubIndex).frame(width: 70, height: 76).accessibilityHidden(true)
            Text(reading.clubName).font(MapFont.bold(24)).lineLimit(1).minimumScaleFactor(0.6)
            Text("\(Int(reading.clubYards.rounded())) yd").font(MapFont.bold(22)).monospacedDigit()
        }
        .foregroundStyle(skin.ink).frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(skin.cream, in: RoundedRectangle(cornerRadius: 22))
        .overlay(RoundedRectangle(cornerRadius: 22).strokeBorder(skin.frame, lineWidth: 4))
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("\(reading.clubName), \(Int(reading.clubYards)) yards")
        .accessibilityIdentifier("golf-selected-club")
    }

    private func arrowButton(right: Bool, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            Image(systemName: right ? "chevron.right" : "chevron.left").font(.system(size: 24, weight: .black)).foregroundStyle(skin.cream)
                .frame(width: 58, height: 58)
                .background { Circle().fill(skin.ink.opacity(0.5)).offset(y: 3); Circle().fill(skin.ink); Circle().strokeBorder(skin.cream, lineWidth: 2.5) }
        }.disabled(!canAim).accessibilityLabel(right ? "Next club" : "Previous club")
            .accessibilityIdentifier(right ? "golf-club-next" : "golf-club-previous")
    }

    /// TAP TO SWING (board: the wide accent button); Ready first when the round waits for it; dimmed while nothing can be done.
    @ViewBuilder private var swingSlot: some View {
        let waiting = session.ready && session.loading.finished && !session.menuPauseVisible
            && (session.paused || (session.golfPhase == "Aim" && !session.golfShotReady && reading.party == nil))
        if canAim && session.golfShotReady { wideSwingButton }
        else if waiting {
            Button { session.readyToPlay() } label: { MapActionFace(skin: skin, title: "READY", height: 96) }
                .buttonStyle(.plain).accessibilityIdentifier("golf-ready")
        } else {
            MapActionFace(skin: skin, title: (reading.targets ?? []).isEmpty ? "TAP TO SWING" : "TAP TO PUTT", height: 96).opacity(0.45).accessibilityHidden(true)
        }
    }

    /// One tap starts the swing at once; tap again to cancel (the live face: SWING! with a glow).
    private var wideSwingButton: some View {
        let face = session.golfTap.face
        let putting = !(reading.targets ?? []).isEmpty
        let live = face == .swinging
        return Button { session.tapGolfSwing() } label: {
            MapActionFace(skin: skin, title: live ? (putting ? "PUTT!" : "SWING!") : (putting ? "TAP TO PUTT" : "TAP TO SWING"),
                          subtitle: live ? "Tap to cancel" : nil, height: 96, pressed: live, live: live)
                .animation(.easeOut(duration: 0.1), value: face)
        }.buttonStyle(.plain)
            .accessibilityLabel(live ? (putting ? "Putting: swing now, tap to cancel" : "Swinging: swing now, tap to cancel") : (putting ? "Tap to putt" : "Tap to swing"))
            .accessibilityHint("Starts the swing at once. Tap again to cancel it.")
            .accessibilityIdentifier("golf-start-swing")
    }

    /// The handheld deck's round aim pad (a joystick on the course's surface).
    private var aimPad: some View {
        ZStack {
            Circle().fill(skin.surface).overlay(Circle().stroke(skin.line, lineWidth: 5))
            Image(systemName: "chevron.up").font(.system(size: 14, weight: .black)).foregroundStyle(skin.cream).offset(y: -58)
            Image(systemName: "chevron.down").font(.system(size: 14, weight: .black)).foregroundStyle(skin.cream).offset(y: 58)
            Image(systemName: "chevron.left").font(.system(size: 14, weight: .black)).foregroundStyle(skin.cream).offset(x: -58)
            Image(systemName: "chevron.right").font(.system(size: 14, weight: .black)).foregroundStyle(skin.cream).offset(x: 58)
            Button {
                if canMenu { session.selectGolfMenu() }
                else if session.paused || !session.golfShotReady { session.readyToPlay() }
            } label: {
                Circle().fill(skin.cream).frame(width: 61, height: 61).overlay(Circle().strokeBorder(skin.frame, lineWidth: 3))
                    .overlay(Circle().fill(skin.ink).frame(width: 14, height: 14))
            }.offset(thumbOffset(scale: 1))
                .disabled(!canAim && !canMenu)
                .accessibilityLabel(canMenu ? "Select" : "Ready for shot")
                .accessibilityIdentifier("golf-aim-center")
        }.contentShape(Circle())
            .simultaneousGesture(DragGesture(minimumDistance: 8, coordinateSpace: .local)
                .onChanged { drag in padDrag(drag, centre: CGPoint(x: 78, y: 78), reach: 48, lookRange: 110, final: false) }
                .onEnded { drag in
                    padDrag(drag, centre: CGPoint(x: 78, y: 78), reach: 48, lookRange: 110, final: true)
                    if canMenu { session.aimGolf(across: 0, forward: 0) }
                    draggingAim = false; stickOffset = .zero; lastDrag = nil; pointer = nil; dragStartAim = nil; dragAxis = nil
                })
            .accessibilityIdentifier("golf-aim-joystick")
    }

    /// Tap to swing: motion counts only after this is tapped, so aiming or changing club can't be read as
    /// a swing. One tap starts the swing at once, whatever the phone is doing; tap it again to cancel.
    /// A swing left alone for a while, a new aim or a club change cancels it too. It sits beside the pad,
    /// under the thumb that just aimed.
    private var startSwingButton: some View {
        let face = session.golfTap.face
        let putting = !(reading.targets ?? []).isEmpty
        let label = face == .swinging ? (putting ? "PUTT!\nTAP: CANCEL" : "SWING!\nTAP: CANCEL") : (putting ? "TAP TO\nPUTT" : "TAP TO\nSWING")
        let live = face == .swinging
        return Button { session.tapGolfSwing() } label: {
            Text(label).font(MapFont.bold(live ? 18 : 20)).multilineTextAlignment(.center).lineLimit(2).minimumScaleFactor(0.6)
                .foregroundStyle(skin.accentInk).frame(width: 108, height: 108)
                .background { Circle().fill(skin.accentDeep).offset(y: live ? 1 : 5); Circle().fill(skin.accent) }
                .overlay(Circle().stroke(live ? skin.glow : .white.opacity(0.7), lineWidth: live ? 6 : 3))
                .scaleEffect(live ? 1.08 : 1).offset(y: live ? 3 : 0)
                .animation(.easeOut(duration: 0.1), value: face)
        }.buttonStyle(.plain)
            .accessibilityLabel(live ? (putting ? "Putting: swing now, tap to cancel" : "Swinging: swing now, tap to cancel") : (putting ? "Tap to putt" : "Tap to swing"))
            .accessibilityHint("Starts the swing at once. Tap again to cancel it.")
            .accessibilityIdentifier("golf-start-swing")
    }
    private func thumbOffset(scale: CGFloat) -> CGSize {
        if draggingAim { return CGSize(width: stickOffset.width * scale, height: stickOffset.height * scale) }
        guard let direction = reading.direction else { return .zero }
        return CGSize(width: direction.x * 16 * scale, height: -direction.y * 16 * scale)
    }
    /// `reach`: how far the thumb travels from `centre`. The shown stick is kept in the 48-point units the round pad was drawn in.
    private func updateJoystick(_ location: CGPoint, centre: CGPoint, reach: CGFloat, final: Bool) {
        guard canAim || canMenu else { return }
        if canAim && !canMenu { trackpad(location, centre: centre, reach: reach, final: final); return }
        let dx = location.x - centre.x, dy = location.y - centre.y
        let distance = hypot(dx, dy)
        guard distance > 10 else { return }
        draggingAim = true
        let length = min(reach, distance) / reach * 48
        stickOffset = CGSize(width: dx / distance * length, height: dy / distance * length)
        let now = ProcessInfo.processInfo.systemUptime
        // (every 1/60 s: at 1/30 the aim line, marker and golfer on the TV turned in steps while the stick moved)
        guard final || now - lastAimSent >= 1.0 / 60 else { return }
        lastAimSent = now
        session.aimGolf(across: dx / distance, forward: -dy / distance)
    }
    /// The drag moves the aim like a pointer (2026-11-16, Adnan: "too sensitive", then "i cant go up on the trackpad"): the aim's own
    /// direction on the map (up = up the course) is nudged by the finger's movement, aimPointerGain per point, in any direction, and
    /// sent as that direction; where the drag started does not matter.
    private func trackpad(_ location: CGPoint, centre: CGPoint, reach: CGFloat, final: Bool) {
        draggingAim = true
        let dx = max(-reach, min(reach, location.x - centre.x)), dy = max(-reach, min(reach, location.y - centre.y))
        stickOffset = CGSize(width: dx / reach * 48, height: dy / reach * 48)
        if pointer == nil {
            let d = reading.direction.map { CGVector(dx: CGFloat($0.x), dy: CGFloat($0.y)) } ?? CGVector(dx: 0, dy: 1)
            let n = max(0.001, hypot(d.dx, d.dy)); pointer = CGVector(dx: d.dx / n, dy: d.dy / n)
            if dragStartAim == nil { dragStartAim = pointer }
        }
        if let last = lastDrag, var p = pointer {
            p.dx += (location.x - last.x) * Self.aimPointerGain; p.dy -= (location.y - last.y) * Self.aimPointerGain
            let n = max(0.001, hypot(p.dx, p.dy)); p = CGVector(dx: p.dx / n, dy: p.dy / n); pointer = p
        }
        lastDrag = final ? nil : location
        let now = ProcessInfo.processInfo.systemUptime
        if let p = pointer, final || now - lastAimSent >= 1.0 / 60 {
            lastAimSent = now
            session.aimGolf(across: Double(p.dx), forward: Double(p.dy))
        }
        if final { pointer = nil }
    }
    /// One drag on an aim pad. While aiming, a mostly vertical drag is a look slide (GolfLookSlide): the aerial view follows the
    /// finger, `lookRange` points for the whole climb, and a quick flick at the end goes all the way up or back down. Any other drag
    /// (and every drag in the TV's menu ring) is the aim stick.
    private func padDrag(_ drag: DragGesture.Value, centre: CGPoint, reach: CGFloat, lookRange: CGFloat, final: Bool) {
        if dragAxis == nil, canAim && !canMenu, let axis = GolfLookSlide.axis(translation: drag.translation) {
            dragAxis = axis
            if axis == .look {
                lookAtDragStart = look
                // (the first few points went to the aim: put it back, so sliding for the view doesn't also turn the shot)
                if let start = dragStartAim { session.aimGolf(across: Double(start.dx), forward: Double(start.dy)) }
                draggingAim = false; stickOffset = .zero; lastDrag = nil; pointer = nil
            }
        }
        if dragAxis == .look { slideLook(drag, range: lookRange, final: final); return }
        updateJoystick(drag.location, centre: centre, reach: reach, final: final)
    }
    private func slideLook(_ drag: DragGesture.Value, range: CGFloat, final: Bool) {
        guard canAim && !canMenu else { return }
        var value = GolfLookSlide.value(start: lookAtDragStart, dy: drag.translation.height, range: range)
        if final, let up = GolfLookFlick.direction(translation: drag.translation, velocity: drag.velocity, distance: GolfLookSlide.decideAfter) {
            value = up ? 1 : 0
        }
        let now = ProcessInfo.processInfo.systemUptime
        guard value != look || final, final || now - lastLookSent >= 1.0 / 30 else { return }
        let before = look
        look = value; lastLookSent = now
        session.lookGolf(value)
        // a tick at the top and at the bottom of the climb
        if session.haptics, value != before, value == 1 || value == 0 { UIImpactFeedbackGenerator(style: .medium).impactOccurred() }
    }
    private func aimArrow(_ symbol: String, x: CGFloat, y: CGFloat, label: String, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            Image(systemName: symbol).font(.system(size: 20, weight: .black)).foregroundStyle(skin.cream)
                .shadow(color: .black.opacity(0.35), radius: 1, y: 1).frame(width: 52, height: 52)
        }.offset(x: x, y: y).disabled(!canAim && !canMenu).accessibilityLabel(label)
            .accessibilityIdentifier("golf-\(label.lowercased().replacingOccurrences(of: " ", with: "-"))")
    }
    private func nudge(_ direction: Double) {
        session.setAim(direction)
        if session.haptics { UISelectionFeedbackGenerator().selectionChanged() }
    }
    private func changeClub(_ direction: Int) {
        session.command("club", value: Double(direction))
        if session.haptics { UISelectionFeedbackGenerator().selectionChanged() }
    }

}

// MARK: handheld play (no TV of this phone's own, PLAN_PhonePlay_Handheld.md)

/// The phone held upright like a Game Boy: the round (Unity's camera and its HUD) in the top three quarters, the controller's
/// club card, aim pad and swing button shrunk onto a deck in the bottom quarter, and the hole map in the game view's corner,
/// a tap opening it full screen.
extension GolfPhoneController {
    private var handheldLayout: some View {
        ZStack {
            HandheldFrame {
                handheldGame
            } deck: {
                handheldDeck
            } deckBackground: {
                ZStack(alignment: .top) {
                    LinearGradient(colors: [skin.top, skin.bottom], startPoint: .top, endPoint: .bottom)
                    Rectangle().fill(skin.frame).frame(height: 4)
                }
            }
            if mapExpanded { handheldMap.transition(.opacity) }
        }
        .animation(.easeOut(duration: 0.18), value: mapExpanded)
        // the map closes for the shot itself, so the flight is seen
        .onChange(of: session.golfPhase) { _, phase in if phase != "Aim" { mapExpanded = false } }
    }

    private var mapRatio: CGFloat {
        guard let image = session.golfControllerMap, image.size.width > 0 else { return 1.4 }
        return min(2.2, max(0.6, image.size.height / image.size.width))
    }

    private var handheldGame: some View {
        ZStack(alignment: .bottomTrailing) {
            Color.clear
            VStack(spacing: 10) { Spacer(minLength: 0); handheldStateCards }
                .frame(maxWidth: .infinity).padding(.horizontal, 12).padding(.bottom, 12)
            if session.ready && session.loading.finished && session.golfPhase == "Aim" && (session.golfControllerMap != nil || isDesignPreview) {
                miniMap.padding(12)
            }
        }
    }

    private var miniMap: some View {
        Button { mapExpanded = true } label: {
            GolfControllerMap(reading: reading, image: session.golfControllerMap, reference: isDesignPreview)
                .frame(width: 92, height: 92 * mapRatio)
                .clipShape(RoundedRectangle(cornerRadius: 12))
                .overlay(RoundedRectangle(cornerRadius: 12).stroke(.white, lineWidth: 3))
                .overlay(alignment: .topTrailing) {
                    Image(systemName: "arrow.up.left.and.arrow.down.right").font(.system(size: 10, weight: .black)).foregroundStyle(.white)
                        .frame(width: 22, height: 22).background(skin.surface, in: RoundedRectangle(cornerRadius: 7))
                        .overlay(RoundedRectangle(cornerRadius: 7).stroke(.white, lineWidth: 1.5)).padding(5)
                }
                .shadow(color: skin.ink.opacity(0.35), radius: 0, y: 3)
        }.buttonStyle(GolfControllerPressStyle())
            .accessibilityLabel("Open the hole map").accessibilityIdentifier("golf-handheld-map")
    }

    /// What the controller's map card shows over the map between shots (a result, the round's end, a friend's turn), here as
    /// cards at the foot of the game view.
    @ViewBuilder private var handheldStateCards: some View {
        if let party = reading.party, !party.shared, party.phase == "result" || party.phase == "flight" || !party.myTurn {
            GolfPartyEmoteControls(session: session, party: party).padding(16)
                .background(skin.surface.opacity(0.95), in: RoundedRectangle(cornerRadius: 20))
        } else if session.golfPhase == "Result" {
            GolfShotResultControls(session: session).padding(16)
                .background(skin.ink.opacity(0.94), in: RoundedRectangle(cornerRadius: 20))
        } else if session.golfPhase == "RoundDone" {
            HStack(spacing: 12) {
                if session.holeInOneDay != 0 { DailyShareButton(skin: skin, height: 58).frame(width: 260) }
                Button(session.golfHasNextHole ? "NEXT HOLE" : TennisMenu.shared.postMatch?.golf != nil ? "FINISH ROUND" : "REMATCH") { session.continueGolfRound() }
                    .font(GolfControllerStyle.font(26)).padding(.horizontal, 26).padding(.vertical, 14).foregroundStyle(skin.ink)
                    .background(skin.accent, in: Capsule()).overlay(Capsule().stroke(.white, lineWidth: 3))
                    .accessibilityIdentifier("golf-continue")
            }
        } else if let party = reading.party, !party.myTurn, !session.paused {
            Text("\(party.player)’s turn").font(Club.ui(20, 900)).foregroundStyle(.white)
                .padding(.horizontal, 18).padding(.vertical, 12).background(skin.ink.opacity(0.94), in: Capsule())
        }
    }

    /// The deck, on a 464 × 220 design canvas (HandheldFrame scales it): club bottom left, aim pad in the middle, swing bottom right.
    private var handheldDeck: some View {
        ZStack(alignment: .topLeading) {
            Color.clear
            GolfControllerText(text: "CLUB", size: 19, stroke: 3).position(x: 84, y: 16)
            GolfControllerText(text: "AIM", size: 19, stroke: 3).position(x: 232, y: 16)
            clubCard.frame(width: 240, height: 148).scaleEffect(0.6).frame(width: 144, height: 89).position(x: 84, y: 98)
            arrowButton(right: false) { changeClub(-1) }.scaleEffect(0.6).position(x: 10, y: 98)
            arrowButton(right: true) { changeClub(1) }.scaleEffect(0.6).position(x: 160, y: 98)
            aimPad.frame(width: 156, height: 156).scaleEffect(0.7).frame(width: 109, height: 109).position(x: 232, y: 100)
            GolfControllerText(text: reading.aimLabel, size: 14, stroke: 1)
                .frame(width: 112, height: 26).background(skin.ink, in: RoundedRectangle(cornerRadius: 12))
                .overlay(RoundedRectangle(cornerRadius: 12).stroke(.white, lineWidth: 2.5))
                .position(x: 232, y: 178)
                .accessibilityIdentifier("golf-aim-reading")
            handheldSwingSlot.position(x: 394, y: 100)
            Button { session.pause() } label: {
                Image(systemName: "pause.fill").font(.system(size: 17, weight: .black)).foregroundStyle(.white)
                    .frame(width: 40, height: 40).background(skin.surface, in: Circle())
                    .overlay(Circle().stroke(.white, lineWidth: 2.5))
            }.position(x: 440, y: 18).accessibilityLabel("Pause golf").accessibilityIdentifier("golf-pause")
            Text(reading.party?.myTurn == false ? "WATCH THE SHOT" : "DRAG TO AIM · TAP TO SWING · TAP AGAIN TO CANCEL")
                .font(GolfControllerStyle.font(10)).foregroundStyle(skin.ink)
                .frame(width: 464).position(x: 232, y: 208)
        }
    }

    /// Tap to swing when the shot is ready; Ready first when the round waits for it (after a pause, or before a solo shot).
    @ViewBuilder private var handheldSwingSlot: some View {
        let waiting = session.ready && session.loading.finished && !session.menuPauseVisible
            && (session.paused || (session.golfPhase == "Aim" && !session.golfShotReady && reading.party == nil))
        if canAim && session.golfShotReady { startSwingButton }
        else if waiting {
            Button { session.readyToPlay() } label: {
                GolfControllerText(text: "READY", size: 24, stroke: 3).frame(width: 108, height: 108)
                    .background(skin.accent, in: Circle()).overlay(Circle().stroke(.white, lineWidth: 4))
                    .shadow(color: skin.ink.opacity(0.25), radius: 0, y: 4)
            }.buttonStyle(.plain).accessibilityIdentifier("golf-ready")
        } else {
            GolfControllerText(text: "TAP TO\nSWING", size: 21, stroke: 3, lines: 2).frame(width: 108, height: 108)
                .background(skin.accent, in: Circle()).overlay(Circle().stroke(.white, lineWidth: 4))
                .opacity(0.45).accessibilityHidden(true)
        }
    }

    /// The hole map opened from the game view: the whole screen, with the hole, par, yards and wind under it.
    private var handheldMap: some View {
        ZStack {
            LinearGradient(colors: [skin.top, skin.bottom], startPoint: .top, endPoint: .bottom).ignoresSafeArea()
            VStack(spacing: 14) {
                HStack {
                    holeBadge.frame(height: 60).fixedSize()
                    Spacer()
                    Button { mapExpanded = false } label: {
                        Image(systemName: "xmark").font(.system(size: 17, weight: .black)).foregroundStyle(.white)
                            .frame(width: 44, height: 44).background(skin.surface, in: Circle()).overlay(Circle().stroke(.white, lineWidth: 3))
                    }.accessibilityLabel("Close the map")
                }
                GolfControllerMap(reading: reading, image: session.golfControllerMap, reference: isDesignPreview)
                    .aspectRatio(1 / mapRatio, contentMode: .fit)
                    .accessibilityIdentifier("golf-handheld-map-open")
                    .clipShape(RoundedRectangle(cornerRadius: 16))
                    .overlay(RoundedRectangle(cornerRadius: 16).stroke(.white, lineWidth: 5))
                    .shadow(color: skin.ink.opacity(0.16), radius: 0, y: 4)
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                HStack(spacing: 8) {
                    statBadge("PAR \(reading.par)", icon: nil)
                    statBadge("\(Int(reading.yards.rounded())) YD", icon: "circle.fill")
                    statBadge("\(Int(reading.wind.rounded())) MPH", icon: "wind")
                }.frame(height: 46)
                Button { mapExpanded = false } label: {
                    GolfControllerText(text: "BACK TO SHOT", size: 22, stroke: 3).padding(.horizontal, 30).padding(.vertical, 12)
                        .background(skin.accent, in: Capsule()).overlay(Capsule().stroke(.white, lineWidth: 3))
                }.buttonStyle(GolfControllerPressStyle()).accessibilityIdentifier("golf-handheld-map-close")
            }
            .padding(.horizontal, 16).padding(.top, 8).padding(.bottom, 12)
        }
    }
}

private struct GolfControllerPressStyle: ButtonStyle {
    @Environment(\.accessibilityReduceMotion) private var reducedMotion
    func makeBody(configuration: Configuration) -> some View {
        configuration.label.scaleEffect(configuration.isPressed ? 0.94 : 1)
            .animation(reducedMotion ? nil : .easeOut(duration: 0.12), value: configuration.isPressed)
    }
}

private struct GolfHoleFlag: View {
    var number: Int
    var body: some View {
        ZStack(alignment: .top) {
            Ellipse().fill(Color(hex: "00CF26")).frame(width: 37, height: 18).offset(y: 31)
            Rectangle().fill(.white).frame(width: 2, height: 35).offset(x: -3, y: 3)
            Text("\(number)").font(.system(size: 11, weight: .black)).foregroundStyle(.white)
                .frame(width: 24, height: 15).background(.red).rotationEffect(.degrees(6)).offset(x: 9, y: 3)
        }.accessibilityHidden(true)
    }
}

private struct GolfControllerSky: View {
    var body: some View {
        GeometryReader { g in
            LinearGradient(colors: [Color(hex: "00A5ED"), Color(hex: "00ACF0"), Color(hex: "6ED0F5")],
                           startPoint: .top, endPoint: .bottom).frame(width: g.size.width, height: g.size.height)
            ForEach(0..<5, id: \.self) { i in
                let locations: [(Double, Double, CGFloat)] = [(0.02, 0.061, 128), (-0.02, 0.611, 124), (1.06, 0.267, 112), (1.025, 0.768, 145), (0.055, 0.939, 120)]
                let p = locations[i]
                GolfCloud().frame(width: p.2 * g.size.width / 464, height: p.2 * g.size.width / 464 * 0.68)
                    .position(x: g.size.width * p.0, y: g.size.height * p.1)
            }
        }.accessibilityHidden(true)
    }
}
private struct GolfCloud: View {
    var body: some View {
        GeometryReader { g in
            ZStack {
                Ellipse().fill(.white.opacity(0.95)).frame(width: g.size.width, height: g.size.height * 0.59).offset(y: g.size.height * 0.18)
                Circle().fill(Color(hex: "F0F8FF")).frame(width: g.size.height * 0.85).offset(x: -g.size.width * 0.15, y: -g.size.height * 0.13)
                Circle().fill(.white).frame(width: g.size.height * 0.62).offset(x: g.size.width * 0.12, y: g.size.height * 0.08)
            }.frame(width: g.size.width, height: g.size.height)
        }
    }
}

private struct GolfControllerMap: View {
    var reading: GolfControllerReading
    var image: UIImage?
    var reference: Bool
    private var referenceImage: UIImage? {
        #if DEBUG
        reference ? GolfControllerArtwork.referenceMap : nil
        #else
        nil
        #endif
    }
    var body: some View {
        GeometryReader { geometry in
            ZStack {
                Color(hex: "E94C0E")
                if let image { Image(uiImage: image).resizable().scaledToFit() }
                else if let illustration = referenceImage {
                    Image(uiImage: illustration).resizable().scaledToFill()
                } else {
                    LinearGradient(colors: [Color(hex: "48BDE5"), Color(hex: "A7E8F7")], startPoint: .topLeading, endPoint: .bottomTrailing)
                    ProgressView().tint(.white)
                }
                if image != nil {
                    // Fit the marks into exactly the same aspect-fit image rectangle.
                    Canvas { context, size in
                        guard let image else { return }
                        let ratio = min(size.width / image.size.width, size.height / image.size.height)
                        let w = image.size.width * ratio, h = image.size.height * ratio
                        func point(_ p: GolfControllerReading.Point) -> CGPoint {
                            CGPoint(x: (size.width-w)/2 + p.x*w, y: (size.height-h)/2 + (1-p.y)*h)
                        }
                        for p in (reading.path ?? []) + (reading.reach ?? []) {
                            let at = point(p); context.fill(Path(ellipseIn: CGRect(x: at.x-1.7, y: at.y-1.7, width: 3.4, height: 3.4)), with: .color(.white))
                        }
                        // a putt's meter marks, coloured like the TV map's power stops, with their feet
                        let stops = [Color(red: 0.52, green: 0.85, blue: 1), Color(red: 0.5, green: 0.95, blue: 0.78), Color(red: 1, green: 0.88, blue: 0.42), Color(red: 1, green: 0.61, blue: 0.36)]
                        for (i, p) in (reading.targets ?? []).enumerated() {
                            let at = point(p), dot = Path(ellipseIn: CGRect(x: at.x-4, y: at.y-4, width: 8, height: 8))
                            context.fill(dot, with: .color(stops[i % stops.count])); context.stroke(dot, with: .color(GolfControllerStyle.ink), lineWidth: 1.2)
                            guard let labels = reading.targetLabels, i < labels.count else { continue }
                            context.draw(Text(labels[i]).font(.system(size: 10, weight: .heavy)).foregroundColor(.white),
                                         at: CGPoint(x: at.x + 8, y: at.y), anchor: .leading)
                        }
                        for (p, color, radius) in [(reading.pin, Color.red, 4.0), (reading.landing, GolfControllerStyle.yellow, 5.0), (reading.ball, Color.white, 6.0)] {
                            guard let p else { continue }; let at = point(p)
                            let shape = Path(ellipseIn: CGRect(x: at.x-radius, y: at.y-radius, width: radius*2, height: radius*2))
                            context.fill(shape, with: .color(color)); context.stroke(shape, with: .color(GolfControllerStyle.ink), lineWidth: 1.5)
                        }
                    }
                }
            }.frame(width: geometry.size.width, height: geometry.size.height).clipped()
        }.accessibilityLabel("Course preview with current ball, pin, and projected shot")
    }
}

private struct GolfControllerClubIcon: View {
    var index: Int
    var body: some View {
        ZStack {
            if index >= 2 && index <= 8, let art = GolfControllerArtwork.club {
                Image(uiImage: art).resizable().scaledToFit()
            } else {
                Canvas { context, size in
                    let sx = size.width / 99, sy = size.height / 108
                    func point(_ x: CGFloat, _ y: CGFloat) -> CGPoint { CGPoint(x: x*sx, y: y*sy) }
                    var shaft = Path(); shaft.move(to: point(86, 6)); shaft.addLine(to: point(61, 82))
                    context.stroke(shaft, with: .color(Color(white: 0.25)), style: StrokeStyle(lineWidth: 9*sx, lineCap: .round))
                    context.stroke(shaft, with: .linearGradient(Gradient(colors: [.white, .gray, .white]), startPoint: point(77, 30), endPoint: point(88, 35)), style: StrokeStyle(lineWidth: 6*sx, lineCap: .round))
                    let bounds = index == 9 ? CGRect(x: 5*sx, y: 78*sy, width: 60*sx, height: 18*sy) : CGRect(x: 4*sx, y: 65*sy, width: 64*sx, height: 36*sy)
                    let shape = Path(roundedRect: bounds, cornerRadius: (index == 9 ? 5 : 17)*sx)
                    context.fill(shape, with: .linearGradient(Gradient(colors: [Color(white: index == 9 ? 0.92 : 0.37), Color(white: index == 9 ? 0.57 : 0.09)]), startPoint: point(30, 65), endPoint: point(40, 102)))
                    context.stroke(shape, with: .color(Color(white: 0.23)), lineWidth: 1.5*sx)
                    var glint=Path(); glint.move(to: point(15, index == 9 ? 82 : 74)); glint.addLine(to: point(51, index == 9 ? 82 : 70))
                    context.stroke(glint, with: .color(.white.opacity(0.7)), style: StrokeStyle(lineWidth: 2*sx, lineCap: .round))
                }
            }
        }
    }
}

/// Drag to aim's corner brackets (board: four L marks inside the panel).
private struct AimBrackets: Shape {
    func path(in r: CGRect) -> Path {
        var p = Path(); let l: CGFloat = 26
        for (x, y, dx, dy) in [(r.minX, r.minY, 1.0, 1.0), (r.maxX, r.minY, -1.0, 1.0), (r.minX, r.maxY, 1.0, -1.0), (r.maxX, r.maxY, -1.0, -1.0)] {
            p.move(to: CGPoint(x: x + dx * l, y: y)); p.addLine(to: CGPoint(x: x, y: y)); p.addLine(to: CGPoint(x: x, y: y + dy * l))
        }
        return p
    }
}

/// The aim's curve from the reticle up and over to an arrowhead.
private struct AimArc: Shape {
    func path(in r: CGRect) -> Path {
        var p = Path()
        let start = CGPoint(x: r.midX, y: r.maxY), end = CGPoint(x: r.maxX * 0.9, y: r.minY + 6)
        p.move(to: start); p.addQuadCurve(to: end, control: CGPoint(x: r.midX + r.width * 0.05, y: r.minY))
        p.move(to: CGPoint(x: end.x - 14, y: end.y - 6)); p.addLine(to: end); p.addLine(to: CGPoint(x: end.x - 8, y: end.y + 13))
        return p
    }
}
