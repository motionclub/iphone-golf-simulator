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

struct GolfPhoneController: View {
    @Bindable var session: SportsSession
    @State private var partyChat = false
    @State private var stickOffset = CGSize.zero
    @State private var draggingAim = false
    @State private var lastAimSent = -Double.infinity
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
                        GolfControllerSky().ignoresSafeArea()
                        controllerCanvas
                            .frame(width: 464, height: 1000)
                            .scaleEffect(scale)
                            .frame(width: geometry.size.width, height: geometry.size.height)
                    }
                }
                .ignoresSafeArea()
            }
        }
        .statusBarHidden().persistentSystemOverlays(.hidden).preferredColorScheme(.light)
        .sheet(isPresented: $session.menuPauseVisible) {
            pauseMenu
        }
        .onChange(of: session.paused) { _, paused in
            if paused { draggingAim = false; stickOffset = .zero }
        }
    }

    private var controllerCanvas: some View {
        ZStack(alignment: .topLeading) {
            Color.clear
            Button { BetaFeedback.open() } label: {
                Text("Feedback").font(GolfControllerStyle.font(11)).foregroundStyle(GolfControllerStyle.ink)
                    .frame(width: 132, height: 48)
            }.buttonStyle(.plain).position(x: 78, y: 48)
                .accessibilityLabel("Send feedback by text").accessibilityIdentifier("beta-feedback")
            holeBadge.frame(width: 240, height: 64).position(x: 224, y: 119)
            Text((reading.party?.player ?? reading.name).uppercased()).font(GolfControllerStyle.font(13)).foregroundStyle(GolfControllerStyle.ink)
                .lineLimit(1).minimumScaleFactor(0.7).padding(.horizontal, 12).frame(minWidth: 118, minHeight: 20)
                .background(GolfControllerStyle.yellow, in: Capsule()).overlay(Capsule().stroke(.white, lineWidth: 2))
                .position(x: 224, y: 152)
            tvStatus.frame(width: 78, height: 52).position(x: 412, y: 101)
            Button { session.pause() } label: {
                Image(systemName: "pause.fill").font(.system(size: 24, weight: .black)).foregroundStyle(.white)
                    .frame(width: 56, height: 56).background(GolfControllerStyle.blue, in: Circle())
                    .overlay(Circle().stroke(.white, lineWidth: 3))
            }.position(x: 52, y: 112).accessibilityLabel("Pause golf").accessibilityIdentifier("golf-pause")
            statBadge("PAR \(reading.par)", icon: nil).frame(width: 136, height: 46).position(x: 86, y: 188)
            statBadge("\(Int(reading.yards.rounded())) YD", icon: "circle.fill").frame(width: 136, height: 46).position(x: 232, y: 188)
            statBadge("\(Int(reading.wind.rounded())) MPH", icon: "wind").frame(width: 136, height: 46).position(x: 378, y: 188)
            mapCard.frame(width: 424, height: 306).position(x: 232, y: 381)
            sectionTitle("CLUB", lines: true).frame(width: 320, height: 26).position(x: 232, y: 568)
            clubCard.frame(width: 240, height: 148).position(x: 232, y: 666)
            arrowButton(right: false) { changeClub(-1) }.position(x: 68, y: 666)
            arrowButton(right: true) { changeClub(1) }.position(x: 396, y: 666)
            sectionTitle("AIM", lines: false).position(x: 232, y: 766)
            aimPad.frame(width: 156, height: 156).position(x: 232, y: 866)
            if canAim && session.golfShotReady { startSwingButton.position(x: 384, y: 866) }
            GolfControllerText(text: reading.aimLabel, size: 15, stroke: 1)
                .frame(width: 126, height: 34).background(GolfControllerStyle.ink, in: RoundedRectangle(cornerRadius: 14))
                .overlay(RoundedRectangle(cornerRadius: 14).stroke(.white, lineWidth: 3))
                .shadow(color: .black.opacity(0.15), radius: 0, y: 3).position(x: 232, y: 946)
                .accessibilityIdentifier("golf-aim-reading")
            Text(reading.party?.phase == "result" ? (reading.party?.shared == true ? "NEXT PLAYER STARTS AUTOMATICALLY" : "PICK AN EMOTE · NEXT PLAYER STARTS AUTOMATICALLY") : reading.party?.myTurn == false ? "WATCH THE SHOT · REACT WITH YOUR PLAYER" : "DRAG TO AIM · TAP TO SWING · TAP AGAIN TO CANCEL")
                .font(GolfControllerStyle.font(11)).foregroundStyle(GolfControllerStyle.ink)
                .position(x: 232, y: 985)
        }.overlay {
            // (on one shared phone the turn just passes: no reaction panel)
            if let party=reading.party, !party.shared, party.phase == "result" || party.phase == "flight" || !party.myTurn {
                GolfPartyEmoteControls(session:session,party:party).padding(20).frame(width:424,height:410)
                    .background(GolfControllerStyle.blue,in:RoundedRectangle(cornerRadius:24)).position(x:232,y:760)
            }
        }.buttonStyle(GolfControllerPressStyle())
    }

    private var holeBadge: some View {
        HStack(spacing: 10) {
            GolfHoleFlag(number: reading.hole).frame(width: 34, height: 48)
            GolfControllerText(text: "HOLE \(reading.hole)", size: 38, stroke: 5).minimumScaleFactor(0.65).lineLimit(1)
        }.padding(.horizontal, 13).background(GolfControllerStyle.blue, in: RoundedRectangle(cornerRadius: 16))
            .overlay(RoundedRectangle(cornerRadius: 16).stroke(.white, lineWidth: 4))
            .shadow(color: GolfControllerStyle.ink.opacity(0.3), radius: 0, y: 4)
            .accessibilityIdentifier("golf-hole-reading")
    }

    private var tvStatus: some View {
        GolfControllerText(text: session.multiplayerControllerOnly ? "PARTY" : session.displayConnected ? "TV ON" : "TV OFF", size: 13, stroke: 1)
            .frame(width: 72, height: 30)
            .background((session.displayConnected || session.multiplayerControllerOnly) ? Color(hex: "00C92C") : GolfControllerStyle.ink, in: Capsule())
            .overlay(Capsule().stroke(.white, lineWidth: 2.5)).shadow(color: .black.opacity(0.16), radius: 0, y: 3)
            .accessibilityLabel(session.multiplayerControllerOnly ? "Using the host’s display" : session.displayConnected ? "TV connected" : "TV disconnected")
    }

    private var pauseMenu: some View {
        NavigationStack {
            Form {
                Section {
                    Button("Resume game") { session.readyToPlay() }
                        .disabled(!session.displayConnected && !session.multiplayerControllerOnly && !session.phonePlay).accessibilityIdentifier("golf-resume")
                    if !session.displayConnected && !session.multiplayerControllerOnly && !session.phonePlay { Text("Reconnect your TV to continue.") }
                }
                Section("Settings") {
                    Toggle("Sound", isOn: $session.sound)
                        .onChange(of: session.sound) { _, enabled in session.command("sound", value: enabled ? 1 : 0) }
                    Toggle("Haptics", isOn: $session.haptics)
                        .onChange(of: session.haptics) { _, enabled in session.command("haptics", value: enabled ? 1 : 0) }
                }
                // the golf screen has no room for the chat and settings buttons, so they live here (record and mic stay on the screen)
                PartySettingsSections()
                if PartyChat.enabled { Section("Party") {
                    Button { PartyChat.shared.stripOpen = true } label: { Label("Party chat", systemImage: "bubble.left.and.bubble.right.fill") }.accessibilityIdentifier("golf-party-chat")
                } }
                Section {
                    Button("Send feedback") { BetaFeedback.open() }
                    Button("Leave game", role: .destructive) { session.exitGame() }
                        .accessibilityIdentifier("controller-exit")
                }
            }.scrollContentBackground(.hidden).navigationTitle("Golf paused").navigationBarTitleDisplayMode(.inline)
                .sheet(isPresented: $partyChat) { PartyChatView(dismiss: { partyChat = false }).presentationDetents([.large]) }
        }.interactiveDismissDisabled().presentationDetents([.large])
            .presentationBackground(Color(hex: "FFF9ED"))
    }

    private func statBadge(_ text: String, icon: String?) -> some View {
        HStack(spacing: 8) {
            if let icon {
                if icon == "wind" {
                    Image(systemName: "location.north.fill").font(.system(size: 21, weight: .black))
                        .foregroundStyle(Color(hex: "00E3FF")).rotationEffect(.degrees(reading.windDegrees))
                        .shadow(color: GolfControllerStyle.ink, radius: 0, x: 2, y: 3)
                } else { Circle().fill(.white).frame(width: 21, height: 21) }
            }
            GolfControllerText(text: text, size: 22, stroke: 3).lineLimit(1).minimumScaleFactor(0.7)
        }.frame(maxWidth: .infinity, maxHeight: .infinity)
            .background(GolfControllerStyle.blue, in: RoundedRectangle(cornerRadius: 14))
            .overlay(RoundedRectangle(cornerRadius: 14).stroke(.white, lineWidth: 3))
            .shadow(color: GolfControllerStyle.ink.opacity(0.16), radius: 0, y: 3)
    }

    private var mapCard: some View {
        ZStack {
            GolfControllerMap(reading: reading, image: session.golfControllerMap, reference: isDesignPreview)
            if !session.ready || !session.loading.finished {
                ProgressView("Connecting to the course").padding(22).background(.regularMaterial, in: RoundedRectangle(cornerRadius: 18))
            } else if session.golfPhase == "Result" {
                GolfShotResultControls(session: session).padding(20).background(GolfControllerStyle.ink.opacity(0.94))
            } else if session.golfPhase == "RoundDone" {
                Button(session.golfHasNextHole ? "NEXT HOLE" : TennisMenu.shared.postMatch?.golf != nil ? "FINISH ROUND" : "REMATCH") { session.continueGolfRound() }
                    .font(GolfControllerStyle.font(28)).padding(18).foregroundStyle(GolfControllerStyle.ink)
                    .background(GolfControllerStyle.yellow, in: Capsule()).accessibilityIdentifier("golf-continue")
            } else if let party=reading.party, !party.myTurn && !session.paused {
                Text("\(party.player)’s turn").font(Club.ui(22,900)).foregroundStyle(.white)
                    .padding(18).background(GolfControllerStyle.ink.opacity(0.94),in:Capsule())
            // (in a round with others the game readies each shot by itself)
            } else if session.paused || (session.golfPhase == "Aim" && !session.golfShotReady && reading.party == nil) {
                VStack(spacing: 10) {
                    GolfControllerText(text: "READY TO SWING?", size: 25)
                    Text("Tap Ready, then tap the swing button and swing.").font(Club.ui(16, 700)).foregroundStyle(.white)
                    Button { session.readyToPlay() } label: {
                        GolfControllerText(text: "READY", size: 26).padding(.horizontal, 34).padding(.vertical, 12)
                            .background(GolfControllerStyle.yellow, in: Capsule())
                    }.accessibilityIdentifier("golf-ready")
                }.padding(20).background(GolfControllerStyle.ink.opacity(0.95), in: RoundedRectangle(cornerRadius: 20))
            }
        }.clipShape(RoundedRectangle(cornerRadius: 16))
            .overlay(RoundedRectangle(cornerRadius: 16).stroke(.white, lineWidth: 5))
            .shadow(color: GolfControllerStyle.ink.opacity(0.16), radius: 0, y: 4)
            .accessibilityIdentifier("golf-course-preview")
    }

    private func sectionTitle(_ text: String, lines: Bool) -> some View {
        HStack(spacing: 20) {
            if lines { Capsule().fill(.white.opacity(0.9)).frame(width: 102, height: 3) }
            GolfControllerText(text: text, size: 26, stroke: 4)
            if lines { Capsule().fill(.white.opacity(0.9)).frame(width: 102, height: 3) }
        }
    }

    private var clubCard: some View {
        ZStack {
            RoundedRectangle(cornerRadius: 18).fill(Color(hex: "DDDDB7")).padding(-5)
            RoundedRectangle(cornerRadius: 16).fill(GolfControllerStyle.yellow)
            HStack(spacing: 7) {
                GolfControllerClubIcon(index: reading.clubIndex).frame(width: 99, height: 108)
                    .accessibilityHidden(true)
                VStack(spacing: 13) {
                    GolfControllerText(text: reading.clubName.uppercased().replacingOccurrences(of: " ", with: "\n"), size: 25, stroke: 4, lines: reading.clubName.contains(" ") ? 2 : 1)
                        .minimumScaleFactor(0.6).frame(width: 108, height: 53)
                    GolfControllerText(text: "\(Int(reading.clubYards.rounded())) YD", size: 27, stroke: 4)
                }
            }.offset(y: -6)
            HStack(spacing: 4) {
                ForEach(0..<10, id: \.self) { index in
                    Circle().fill(index == reading.clubIndex ? GolfControllerStyle.blue : .white)
                        .frame(width: 7, height: 7)
                }
            }.offset(y: 56)
        }.overlay(RoundedRectangle(cornerRadius: 16).stroke(.white, lineWidth: 4))
            .padding(5)
            .accessibilityElement(children: .ignore)
            .accessibilityLabel("\(reading.clubName), \(Int(reading.clubYards)) yards")
            .accessibilityIdentifier("golf-selected-club")
    }

    private func arrowButton(right: Bool, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            ZStack {
                Circle().fill(GolfControllerStyle.blue).overlay(Circle().stroke(.white, lineWidth: 3))
                Image(systemName: "play.fill").font(.system(size: 29, weight: .black))
                    .foregroundStyle(.white).rotationEffect(.degrees(right ? 0 : 180))
                    .shadow(color: GolfControllerStyle.ink, radius: 0, x: 2, y: 3)
            }.frame(width: 62, height: 62).shadow(color: GolfControllerStyle.ink.opacity(0.15), radius: 0, y: 4)
        }.disabled(!canAim).accessibilityLabel(right ? "Next club" : "Previous club")
            .accessibilityIdentifier(right ? "golf-club-next" : "golf-club-previous")
    }

    private var aimPad: some View {
        ZStack {
            Circle().fill(GolfControllerStyle.blue)
                .overlay(Circle().stroke(Color(hex: "B4E5FF"), lineWidth: 6))
                .overlay(Circle().stroke(.white, lineWidth: 2).padding(3))
                .shadow(color: GolfControllerStyle.ink.opacity(0.14), radius: 0, y: 4)
            Ellipse().fill(Color(hex: "65A8ED")).frame(width: 122, height: 62).offset(y: -33)
            aimArrow("triangle.fill", rotation: 0, x: 0, y: -53, label: "Aim up course") { session.aimGolf(across: 0, forward: 1) }
            aimArrow("triangle.fill", rotation: 180, x: 0, y: 53, label: "Aim down course") { session.aimGolf(across: 0, forward: -1) }
            aimArrow("triangle.fill", rotation: -90, x: -54, y: 0, label: "Aim left") { nudge(-1) }
            aimArrow("triangle.fill", rotation: 90, x: 54, y: 0, label: "Aim right") { nudge(1) }
            Button {
                if canMenu { session.selectGolfMenu() }
                else if session.paused || !session.golfShotReady { session.readyToPlay() }
            } label: {
                ZStack {
                    Circle().fill(Color(hex: "D0E9FA"))
                    Circle().fill(.white).frame(width: 43, height: 40).offset(x: -1, y: -10)
                }.frame(width: 61, height: 61).overlay(Circle().stroke(.white, lineWidth: 3))
                    .shadow(color: GolfControllerStyle.ink.opacity(0.5), radius: 0, y: 4)
            }.offset(thumbOffset)
                .disabled(!canAim && !canMenu)
                .accessibilityLabel(canMenu ? "Select" : "Ready for shot")
                .accessibilityIdentifier("golf-aim-center")
        }.contentShape(Circle())
            .simultaneousGesture(DragGesture(minimumDistance: 8, coordinateSpace: .local)
                .onChanged { drag in updateJoystick(drag.location, final: false) }
                .onEnded { drag in
                    updateJoystick(drag.location, final: true)
                    // (the TV's menu ring re-arms when the stick comes back to the middle)
                    if canMenu { session.aimGolf(across: 0, forward: 0) }
                    draggingAim = false; stickOffset = .zero
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
        let fill = face == .swinging ? GolfControllerStyle.green : GolfControllerStyle.yellow
        let live = face == .swinging
        return Button { session.tapGolfSwing() } label: {
            GolfControllerText(text: label, size: live ? 19 : 21, stroke: 3, lines: 2).frame(width: 108, height: 108)
                .background(fill, in: Circle()).overlay(Circle().stroke(.white, lineWidth: live ? 6 : 4))
                .shadow(color: GolfControllerStyle.ink.opacity(0.25), radius: 0, y: live ? 1 : 4)
                .scaleEffect(live ? 1.08 : 1).offset(y: live ? 3 : 0)
                .animation(.easeOut(duration: 0.1), value: face)
        }.buttonStyle(.plain)
            .accessibilityLabel(live ? (putting ? "Putting: swing now, tap to cancel" : "Swinging: swing now, tap to cancel") : (putting ? "Tap to putt" : "Tap to swing"))
            .accessibilityHint("Starts the swing at once. Tap again to cancel it.")
            .accessibilityIdentifier("golf-start-swing")
    }
    private var thumbOffset: CGSize {
        if draggingAim { return stickOffset }
        guard let direction = reading.direction else { return .zero }
        return CGSize(width: direction.x * 16, height: -direction.y * 16)
    }
    private func updateJoystick(_ location: CGPoint, final: Bool) {
        guard canAim || canMenu else { return }
        let dx = location.x - 78, dy = location.y - 78
        let distance = hypot(dx, dy)
        guard distance > 10 else { return }
        draggingAim = true
        let length = min(48, distance)
        stickOffset = CGSize(width: dx / distance * length, height: dy / distance * length)
        let now = ProcessInfo.processInfo.systemUptime
        // (every 1/60 s: at 1/30 the aim line, marker and golfer on the TV turned in steps while the stick moved)
        guard final || now - lastAimSent >= 1.0 / 60 else { return }
        lastAimSent = now
        session.aimGolf(across: dx / distance, forward: -dy / distance)
    }
    private func aimArrow(_ symbol: String, rotation: Double, x: CGFloat, y: CGFloat, label: String,
                          action: @escaping () -> Void) -> some View {
        Button(action: action) {
            Image(systemName: symbol).font(.system(size: 13, weight: .bold)).foregroundStyle(.white)
                .rotationEffect(.degrees(rotation)).frame(width: 52, height: 52)
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
                    GolfControllerSky()
                    Rectangle().fill(.white).frame(height: 3)
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
                        .frame(width: 22, height: 22).background(GolfControllerStyle.blue, in: RoundedRectangle(cornerRadius: 7))
                        .overlay(RoundedRectangle(cornerRadius: 7).stroke(.white, lineWidth: 1.5)).padding(5)
                }
                .shadow(color: GolfControllerStyle.ink.opacity(0.35), radius: 0, y: 3)
        }.buttonStyle(GolfControllerPressStyle())
            .accessibilityLabel("Open the hole map").accessibilityIdentifier("golf-handheld-map")
    }

    /// What the controller's map card shows over the map between shots (a result, the round's end, a friend's turn), here as
    /// cards at the foot of the game view.
    @ViewBuilder private var handheldStateCards: some View {
        if let party = reading.party, !party.shared, party.phase == "result" || party.phase == "flight" || !party.myTurn {
            GolfPartyEmoteControls(session: session, party: party).padding(16)
                .background(GolfControllerStyle.blue.opacity(0.95), in: RoundedRectangle(cornerRadius: 20))
        } else if session.golfPhase == "Result" {
            GolfShotResultControls(session: session).padding(16)
                .background(GolfControllerStyle.ink.opacity(0.94), in: RoundedRectangle(cornerRadius: 20))
        } else if session.golfPhase == "RoundDone" {
            Button(session.golfHasNextHole ? "NEXT HOLE" : TennisMenu.shared.postMatch?.golf != nil ? "FINISH ROUND" : "REMATCH") { session.continueGolfRound() }
                .font(GolfControllerStyle.font(26)).padding(.horizontal, 26).padding(.vertical, 14).foregroundStyle(GolfControllerStyle.ink)
                .background(GolfControllerStyle.yellow, in: Capsule()).overlay(Capsule().stroke(.white, lineWidth: 3))
                .accessibilityIdentifier("golf-continue")
        } else if let party = reading.party, !party.myTurn, !session.paused {
            Text("\(party.player)’s turn").font(Club.ui(20, 900)).foregroundStyle(.white)
                .padding(.horizontal, 18).padding(.vertical, 12).background(GolfControllerStyle.ink.opacity(0.94), in: Capsule())
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
                .frame(width: 112, height: 26).background(GolfControllerStyle.ink, in: RoundedRectangle(cornerRadius: 12))
                .overlay(RoundedRectangle(cornerRadius: 12).stroke(.white, lineWidth: 2.5))
                .position(x: 232, y: 178)
                .accessibilityIdentifier("golf-aim-reading")
            handheldSwingSlot.position(x: 394, y: 100)
            Button { session.pause() } label: {
                Image(systemName: "pause.fill").font(.system(size: 17, weight: .black)).foregroundStyle(.white)
                    .frame(width: 40, height: 40).background(GolfControllerStyle.blue, in: Circle())
                    .overlay(Circle().stroke(.white, lineWidth: 2.5))
            }.position(x: 440, y: 18).accessibilityLabel("Pause golf").accessibilityIdentifier("golf-pause")
            Text(reading.party?.myTurn == false ? "WATCH THE SHOT" : "DRAG TO AIM · TAP TO SWING · TAP AGAIN TO CANCEL")
                .font(GolfControllerStyle.font(10)).foregroundStyle(GolfControllerStyle.ink)
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
                    .background(GolfControllerStyle.yellow, in: Circle()).overlay(Circle().stroke(.white, lineWidth: 4))
                    .shadow(color: GolfControllerStyle.ink.opacity(0.25), radius: 0, y: 4)
            }.buttonStyle(.plain).accessibilityIdentifier("golf-ready")
        } else {
            GolfControllerText(text: "TAP TO\nSWING", size: 21, stroke: 3, lines: 2).frame(width: 108, height: 108)
                .background(GolfControllerStyle.yellow, in: Circle()).overlay(Circle().stroke(.white, lineWidth: 4))
                .opacity(0.45).accessibilityHidden(true)
        }
    }

    /// The hole map opened from the game view: the whole screen, with the hole, par, yards and wind under it.
    private var handheldMap: some View {
        ZStack {
            GolfControllerSky().ignoresSafeArea()
            VStack(spacing: 14) {
                HStack {
                    holeBadge.frame(height: 60).fixedSize()
                    Spacer()
                    Button { mapExpanded = false } label: {
                        Image(systemName: "xmark").font(.system(size: 17, weight: .black)).foregroundStyle(.white)
                            .frame(width: 44, height: 44).background(GolfControllerStyle.blue, in: Circle()).overlay(Circle().stroke(.white, lineWidth: 3))
                    }.accessibilityLabel("Close the map")
                }
                GolfControllerMap(reading: reading, image: session.golfControllerMap, reference: isDesignPreview)
                    .aspectRatio(1 / mapRatio, contentMode: .fit)
                    .accessibilityIdentifier("golf-handheld-map-open")
                    .clipShape(RoundedRectangle(cornerRadius: 16))
                    .overlay(RoundedRectangle(cornerRadius: 16).stroke(.white, lineWidth: 5))
                    .shadow(color: GolfControllerStyle.ink.opacity(0.16), radius: 0, y: 4)
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                HStack(spacing: 8) {
                    statBadge("PAR \(reading.par)", icon: nil)
                    statBadge("\(Int(reading.yards.rounded())) YD", icon: "circle.fill")
                    statBadge("\(Int(reading.wind.rounded())) MPH", icon: "wind")
                }.frame(height: 46)
                Button { mapExpanded = false } label: {
                    GolfControllerText(text: "BACK TO SHOT", size: 22, stroke: 3).padding(.horizontal, 30).padding(.vertical, 12)
                        .background(GolfControllerStyle.yellow, in: Capsule()).overlay(Capsule().stroke(.white, lineWidth: 3))
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
