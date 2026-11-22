import SwiftUI
import AVFoundation
import GameKit

/// Permissions asked in context (Adnan, 2026-11-21, after the first-time-player run): nothing at launch. Game Center's sign-in
/// comes when the player first picks an online game, Local Network when they first pick a local (nearby) match, and the camera
/// right before tennis loads. Camera and Local Network get our card first (what it is for, then Apple's prompt); a refused one
/// gets a card that says how to turn it back on, and play goes on by itself once it is on.
@MainActor @Observable
final class PermissionGate {
    static let shared = PermissionGate()

    enum Kind: String { case gameCenter, localNetwork, camera }
    /// ask: our card before Apple's prompt. waiting: Apple's sheet or prompt is up. denied: refused, here is how to turn it on.
    enum Stage: Equatable { case ask, waiting, denied }
    struct Request: Identifiable {
        let id = UUID()
        let kind: Kind
        var stage: Stage
        let onGranted: @MainActor () -> Void
        var onCancel: (@MainActor () -> Void)? = nil
    }
    private(set) var request: Request?
    let defaults: UserDefaults
    init(defaults: UserDefaults = .standard) { self.defaults = defaults }

    // MARK: seams (tests replace them)

    /// The unit-test host app: the gates stand open unless a test sets these seams (no camera or Game Center in a test run).
    static let unitTestHost = ProcessInfo.processInfo.environment["XCTestConfigurationFilePath"] != nil
    var cameraStatus: @MainActor () -> AVAuthorizationStatus = { unitTestHost ? .authorized : AVCaptureDevice.authorizationStatus(for: .video) }
    var askCamera: @MainActor (@escaping @MainActor (Bool) -> Void) -> Void = { done in
        AVCaptureDevice.requestAccess(for: .video) { granted in Task { @MainActor in done(granted) } }
    }
    var gameCenterSignedIn: @MainActor () -> Bool = { unitTestHost || GKLocalPlayer.local.isAuthenticated }
    /// Apple's sign-in: its held sheet if Game Center offered one, else a new sign-in. The result comes to `gameCenterChanged`.
    var signInToGameCenter: @MainActor () -> Void = { ClubSignIn.signInForPlay() }
    var localNetworkDenied: @MainActor () -> Bool = { MultiplayerService.shared.localNetworkDenied }
    var clearLocalNetworkDenied: @MainActor () -> Void = { MultiplayerService.shared.recheckLocalNetwork() }
    var openSettings: @MainActor () -> Void = {
        if let url = URL(string: UIApplication.openSettingsURLString) { UIApplication.shared.open(url) }
    }

    // MARK: what the player has asked for (kept across launches)

    private static let localPlayKey = "permissions.localPlay.asked.v1", onlineKey = "permissions.online.wanted.v1"
    /// The player has picked a local match once (and so been asked for Local Network): from then on the phone looks for nearby
    /// games in the background, so "Join X's game?" can pop up.
    var localPlayAsked: Bool { defaults.bool(forKey: Self.localPlayKey) || (Self.unitTestHost && !enforceInTests) }
    /// Tests of the gates themselves turn them on.
    var enforceInTests = false
    /// The player has picked something online once: Game Center's sign-in and friends prompt may come up by themselves after that.
    var onlineWanted: Bool { defaults.bool(forKey: Self.onlineKey) }
    func noteOnlineWanted() { defaults.set(true, forKey: Self.onlineKey) }

    // MARK: Game Center: when the player first picks an online game

    func requireGameCenter(then: @escaping @MainActor () -> Void, onCancel: (@MainActor () -> Void)? = nil) {
        noteOnlineWanted()
        if gameCenterSignedIn() { then(); return }
        show(Request(kind: .gameCenter, stage: .waiting, onGranted: then, onCancel: onCancel))
        signInToGameCenter()
    }
    /// Game Center answered (signed in, or the sheet was closed / sign-in failed).
    func gameCenterChanged() {
        guard let r = request, r.kind == .gameCenter else { return }
        if gameCenterSignedIn() { grant() } else if r.stage == .waiting { request?.stage = .denied; track("denied") }
    }

    // MARK: Local Network: when the player first picks a local match

    /// `then` runs at once when the player was asked before; the first time, after our card (iOS asks on the first look for phones).
    func requireLocalNetwork(then: @escaping @MainActor () -> Void, onCancel: (@MainActor () -> Void)? = nil) {
        if localPlayAsked { then(); return }
        show(Request(kind: .localNetwork, stage: .ask, onGranted: then, onCancel: onCancel))
    }
    /// A local match found Local Network refused: say how to turn it on; `retry` runs when the player is back with it on.
    func localNetworkRefused(retry: @escaping @MainActor () -> Void, onCancel: (@MainActor () -> Void)? = nil) {
        if let r = request, r.kind == .localNetwork, r.stage == .denied { return }
        show(Request(kind: .localNetwork, stage: .denied, onGranted: retry, onCancel: onCancel))
    }

    // MARK: Camera: right before tennis loads

    /// Tennis finds the TV and times its picture with the rear camera.
    var cameraNeedsCard: Bool { cameraStatus() != .authorized }
    func requireCamera(then: @escaping @MainActor () -> Void, onCancel: (@MainActor () -> Void)? = nil) {
        switch cameraStatus() {
        case .authorized: then()
        case .notDetermined: show(Request(kind: .camera, stage: .ask, onGranted: then, onCancel: onCancel))
        default: show(Request(kind: .camera, stage: .denied, onGranted: then, onCancel: onCancel))
        }
    }

    // MARK: the card's buttons

    func primary() {
        guard let r = request else { return }
        track("tap", ["stage": "\(r.stage)"])
        switch (r.kind, r.stage) {
        case (.camera, .ask):
            request?.stage = .waiting
            askCamera { [weak self] granted in
                guard let self, self.request?.kind == .camera else { return }
                if granted { self.grant() } else { self.request?.stage = .denied; self.track("denied") }
            }
        case (.localNetwork, .ask):
            defaults.set(true, forKey: Self.localPlayKey)
            grant()   // the local match looks for phones now: that is when iOS asks
        case (.gameCenter, .denied):
            request?.stage = .waiting; signInToGameCenter()
        case (_, .denied):
            openSettings()
        default: break
        }
    }
    func cancel() {
        guard let r = request else { return }
        track("cancel", ["stage": "\(r.stage)"]); request = nil
        r.onCancel?()
        HubSession.shared.evaluate()
    }
    /// Back in the app (from Settings, or after Apple's prompt): anything now allowed goes on by itself.
    func appBecameActive() {
        guard let r = request, r.stage != .ask else { return }
        switch r.kind {
        case .camera: if cameraStatus() == .authorized { grant() }
        case .gameCenter: if gameCenterSignedIn() { grant() }
        case .localNetwork:
            guard r.stage == .denied else { return }
            clearLocalNetworkDenied(); grant()   // try again: still refused shows this card again
        }
    }

    private func show(_ r: Request) {
        request = r; track("show", ["stage": "\(r.stage)"])
        HubSession.shared.evaluate()
    }
    private func grant() {
        guard let r = request else { return }
        track("granted"); request = nil
        r.onGranted()
        HubSession.shared.evaluate()
    }
    private func track(_ what: String, _ props: [String: String] = [:]) {
        guard let r = request else { return }
        Analytics.track("permission_\(what)", props.merging(["kind": r.kind.rawValue]) { a, _ in a })
    }
    /// Tests.
    func reset() { request = nil; defaults.removeObject(forKey: Self.localPlayKey); defaults.removeObject(forKey: Self.onlineKey) }
    func debugSetLocalPlayAsked(_ on: Bool) { defaults.set(on, forKey: Self.localPlayKey) }

    // MARK: words

    struct Words { let icon: String, title: String, body: String, steps: [String], primary: String?, cancel: String }
    static func words(_ kind: Kind, _ stage: Stage) -> Words {
        switch (kind, stage) {
        case (.camera, .ask), (.camera, .waiting):
            Words(icon: "camera.fill", title: "Tennis uses your camera",
                  body: "Point your phone at the TV: the camera finds the screen and times its picture, so your swings land on time. Nothing is recorded or uploaded.",
                  steps: ["Tap Allow camera.", "Then tap Allow when your iPhone asks."], primary: stage == .ask ? "Allow camera" : nil, cancel: "Not now")
        case (.camera, .denied):
            Words(icon: "camera.fill", title: "Turn on the camera",
                  body: "Tennis can't find your TV with the camera off.",
                  steps: ["Tap Open Settings.", "Turn on Camera.", "Come back here to play."], primary: "Open Settings", cancel: "Not now")
        case (.localNetwork, .ask), (.localNetwork, .waiting):
            Words(icon: "iphone.radiowaves.left.and.right", title: "Play with a phone nearby",
                  body: "Your phone looks for your friend's phone in the room. No shared Wi-Fi needed, just keep Wi-Fi on.",
                  steps: ["Tap Continue.", "Then tap Allow when your iPhone asks to find devices on your network."], primary: "Continue", cancel: "Not now")
        case (.localNetwork, .denied):
            Words(icon: "iphone.radiowaves.left.and.right", title: "Turn on Local Network",
                  body: "Phones in the same room can't find each other while it's off.",
                  steps: ["Tap Open Settings.", "Turn on Local Network.", "Come back here to play."], primary: "Open Settings", cancel: "Not now")
        case (.gameCenter, .ask), (.gameCenter, .waiting):
            Words(icon: "person.2.fill", title: "Signing in to Game Center…",
                  body: "Online games use Game Center to find players and your friends.", steps: [], primary: nil, cancel: "Cancel")
        case (.gameCenter, .denied):
            Words(icon: "person.2.fill", title: "Sign in to Game Center",
                  body: "Online games use Game Center to find players and your friends.",
                  steps: ["Open the Settings app.", "Tap Game Center and sign in.", "Come back here to play."], primary: "Try again", cancel: "Not now")
        }
    }
}

/// The card, over everything on the phone (SportsHome), in the play-safe card's style.
struct PermissionSheet: View {
    let request: PermissionGate.Request
    var body: some View {
        let w = PermissionGate.words(request.kind, request.stage)
        ScrollView {
            VStack(alignment: .leading, spacing: 18) {
                Image(systemName: w.icon).font(.system(size: 40, weight: .bold)).foregroundStyle(MotionBrand.gold)
                    .frame(width: 84, height: 84)
                    .background(MotionBrand.navyInk.opacity(0.55), in: Circle())
                    .overlay(Circle().strokeBorder(MotionBrand.gold, lineWidth: 2.5))
                    .padding(.top, 20)
                Text(w.title).font(MotionBrand.font(.extraBoldItalic, 34)).lineLimit(2).minimumScaleFactor(0.6)
                    .accessibilityIdentifier("permission-title")
                Text(w.body).font(MotionBrand.font(.medium, 17)).fixedSize(horizontal: false, vertical: true)
                if !w.steps.isEmpty {
                    VStack(alignment: .leading, spacing: 10) {
                        ForEach(Array(w.steps.enumerated()), id: \.offset) { i, line in
                            HStack(alignment: .top, spacing: 12) {
                                Text("\(i + 1)").font(MotionBrand.font(.extraBold, 15)).foregroundStyle(MotionBrand.navyInk)
                                    .frame(width: 28, height: 28).background(MotionBrand.gold, in: Circle())
                                Text(line).font(MotionBrand.font(.medium, 17)).fixedSize(horizontal: false, vertical: true)
                            }
                        }
                    }
                    .padding(16).frame(maxWidth: .infinity, alignment: .leading)
                    .background(MotionBrand.navyInk.opacity(0.55), in: RoundedRectangle(cornerRadius: 20, style: .continuous))
                    .overlay(RoundedRectangle(cornerRadius: 20, style: .continuous).strokeBorder(.white.opacity(0.25), lineWidth: 1.5))
                }
                if request.stage == .waiting { ProgressView().tint(MotionBrand.gold).scaleEffect(1.4).frame(maxWidth: .infinity) }
                Spacer(minLength: 8)
                if let primary = w.primary {
                    Button { PermissionGate.shared.primary() } label: { Text(primary) }
                        .buttonStyle(MotionButtonStyle(kind: .primary)).accessibilityIdentifier("permission-primary")
                }
                Button { PermissionGate.shared.cancel() } label: { Text(w.cancel) }
                    .buttonStyle(MotionButtonStyle(kind: .ghost)).frame(maxWidth: .infinity)
                    .accessibilityIdentifier("permission-cancel")
            }
            .foregroundStyle(.white)
            .padding(.horizontal, 22).padding(.bottom, 30)
        }
        .scrollIndicators(.hidden)
        .background(MotionBrand.background.ignoresSafeArea())
        .preferredColorScheme(.dark)
        .accessibilityIdentifier("permission-\(request.kind.rawValue)-\(request.stage)")
    }
}
