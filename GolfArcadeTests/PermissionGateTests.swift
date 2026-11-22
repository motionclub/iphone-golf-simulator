import XCTest
import SwiftUI
import AVFoundation
@testable import GolfArcade

/// Permissions asked in context (Adnan 2026-11-21, after the first-time-player run "Maya"): nothing at launch; Game Center when
/// the player first picks an online game, Local Network when they first pick a local match, the camera right before tennis loads.
/// Each refusal gets a card that says how to turn it on, and play goes on by itself once it is on.
@MainActor final class PermissionGateTests: XCTestCase {
    private var suite: UserDefaults!
    private var gate: PermissionGate!
    private var settingsOpened = 0
    override func setUp() async throws {
        suite = UserDefaults(suiteName: "permissions-\(UUID())")
        gate = PermissionGate(defaults: suite)
        gate.enforceInTests = true
        gate.openSettings = { [unowned self] in settingsOpened += 1 }
    }

    // MARK: camera

    func testCameraIsAskedWithOurCardFirstThenTheLaunchGoesOn() {
        var status = AVAuthorizationStatus.notDetermined, asked = 0, ran = 0
        gate.cameraStatus = { status }
        gate.askCamera = { done in asked += 1; status = .authorized; done(true) }
        gate.requireCamera(then: { ran += 1 })
        XCTAssertEqual(gate.request?.kind, .camera); XCTAssertEqual(gate.request?.stage, .ask, "our card, before Apple's prompt")
        XCTAssertEqual(asked, 0, "Apple's prompt waits for the player's tap")
        gate.primary()
        XCTAssertEqual(asked, 1); XCTAssertEqual(ran, 1, "allowed: tennis loads"); XCTAssertNil(gate.request)
        gate.requireCamera(then: { ran += 1 })
        XCTAssertEqual(ran, 2); XCTAssertNil(gate.request, "allowed once: no card again")
    }

    func testARefusedCameraSaysHowToTurnItOnAndGoesOnByItself() {
        var status = AVAuthorizationStatus.notDetermined, ran = 0, cancelled = 0
        gate.cameraStatus = { status }
        gate.askCamera = { done in status = .denied; done(false) }
        gate.requireCamera(then: { ran += 1 }, onCancel: { cancelled += 1 })
        gate.primary()   // Allow camera → Apple's prompt → Don't Allow
        XCTAssertEqual(gate.request?.stage, .denied, "a refusal is explained, not a dead end")
        XCTAssertEqual(PermissionGate.words(.camera, .denied).primary, "Open Settings")
        gate.primary()
        XCTAssertEqual(settingsOpened, 1)
        gate.appBecameActive()
        XCTAssertEqual(gate.request?.stage, .denied, "still off: the card stays")
        status = .authorized
        gate.appBecameActive()
        XCTAssertEqual(ran, 1, "turned on in Settings: tennis goes on by itself"); XCTAssertNil(gate.request); XCTAssertEqual(cancelled, 0)

        status = .denied
        gate.requireCamera(then: { ran += 1 }, onCancel: { cancelled += 1 })
        XCTAssertEqual(gate.request?.stage, .denied, "refused before: straight to how to turn it on")
        gate.cancel()
        XCTAssertEqual(cancelled, 1); XCTAssertEqual(ran, 1); XCTAssertNil(gate.request)
    }

    // MARK: Game Center

    func testGameCenterSignsInWhenAnOnlineGameIsPickedAndExplainsAClosedSheet() {
        var signedIn = false, sheets = 0, ran = 0
        gate.gameCenterSignedIn = { signedIn }
        gate.signInToGameCenter = { sheets += 1 }
        XCTAssertFalse(gate.onlineWanted)
        gate.requireGameCenter(then: { ran += 1 })
        XCTAssertTrue(gate.onlineWanted, "from now on the friends prompt may come after sign-in")
        XCTAssertEqual(sheets, 1, "Apple's sign-in shows now, not at launch")
        XCTAssertEqual(gate.request?.stage, .waiting)
        gate.gameCenterChanged()   // the sheet was closed without signing in
        XCTAssertEqual(gate.request?.stage, .denied)
        XCTAssertEqual(PermissionGate.words(.gameCenter, .denied).steps.count, 3, "how to sign in from Settings")
        gate.primary()   // Try again
        XCTAssertEqual(sheets, 2); XCTAssertEqual(gate.request?.stage, .waiting)
        signedIn = true
        gate.gameCenterChanged()
        XCTAssertEqual(ran, 1, "signed in: the online game goes on"); XCTAssertNil(gate.request)
        gate.requireGameCenter(then: { ran += 1 })
        XCTAssertEqual(ran, 2); XCTAssertEqual(sheets, 2, "signed in: no screen at all")
    }

    func testSigningInLaterInSettingsGoesOnWhenTheAppComesBack() {
        var signedIn = false, ran = 0
        gate.gameCenterSignedIn = { signedIn }; gate.signInToGameCenter = {}
        gate.requireGameCenter(then: { ran += 1 }); gate.gameCenterChanged()
        XCTAssertEqual(gate.request?.stage, .denied)
        signedIn = true; gate.appBecameActive()
        XCTAssertEqual(ran, 1); XCTAssertNil(gate.request)
    }

    /// At launch Game Center's sheet (a signed-out player) is held, not shown: it waits for an online game.
    func testALaunchSheetIsHeldUntilThePlayerWantsOnlinePlay() {
        let saved = ClubSignIn.wanted; ClubSignIn.wanted = false
        defer { ClubSignIn.wanted = saved; ClubSignIn.authenticationFinished() }
        let sheet = UIViewController()
        ClubSignIn.offer(sheet)
        XCTAssertNil(sheet.presentingViewController, "nothing shows on a first launch")
        XCTAssertNotNil(ClubSignIn.pendingController, "kept for the first online game")
    }

    // MARK: Local Network

    func testLocalNetworkIsAskedOnTheFirstLocalMatchOnly() {
        var ran = 0, cleared = 0
        XCTAssertFalse(gate.localPlayAsked)
        gate.requireLocalNetwork(then: { ran += 1 })
        XCTAssertEqual(gate.request?.kind, .localNetwork); XCTAssertEqual(gate.request?.stage, .ask)
        gate.primary()
        XCTAssertTrue(gate.localPlayAsked); XCTAssertEqual(ran, 1)
        gate.requireLocalNetwork(then: { ran += 1 })
        XCTAssertEqual(ran, 2); XCTAssertNil(gate.request, "asked once")

        gate.clearLocalNetworkDenied = { cleared += 1 }
        gate.localNetworkRefused(retry: { ran += 1 })
        XCTAssertEqual(gate.request?.stage, .denied)
        gate.primary(); XCTAssertEqual(settingsOpened, 1)
        gate.appBecameActive()
        XCTAssertEqual(cleared, 1); XCTAssertEqual(ran, 3, "back from Settings: the local match looks again")
    }

    // MARK: the menu

    private func hub(_ service: MultiplayerService) -> HubSession {
        let hub = HubSession(); hub.partyService = service; hub.permissions = gate
        hub.debugLive(session: "perm")
        return hub
    }

    /// No background look for nearby games before the player picks a local match; the first one shows our card, then looks for a
    /// friend's game for a moment: one there is joined, none and this phone hosts.
    func testTheFirstLocalMatchAsksThenJoinsAFriendsGameOrHostsOne() {
        let saved = SportsSession.shared.displayConnected; SportsSession.shared.displayConnected = true
        let savedContext = ClubHub.shared.context; ClubHub.shared.context = { ClubHubContext() }
        let savedLook = HubSession.nearbyLookSeconds
        TennisMenu.shared.debugShow(.main); OnboardingFlow.shared.exitToMenu()
        let service = MultiplayerService(), hub = hub(service)
        defer { service.leave(); ClubHub.shared.context = savedContext; HubSession.nearbyLookSeconds = savedLook; HubTestState.restore(display: saved) }
        var browsing: [Bool] = [], hosted = 0, joined: [String] = []
        hub.nearbyBrowse = { _, on in browsing.append(on) }
        hub.nearbyHost = { _ in hosted += 1 }
        hub.nearbyJoin = { _, lobby in joined.append(lobby.name) }

        hub.nearbyTick()
        XCTAssertFalse(hub.wantsNearbyBrowse); XCTAssertEqual(browsing, [], "a first launch's menu never looks for phones (no iOS prompt)")
        hub.useStation(HubSession.nearbyBay)
        XCTAssertEqual(gate.request?.kind, .localNetwork, "our card before iOS asks"); XCTAssertEqual(browsing, []); XCTAssertEqual(hosted, 0)
        gate.primary()
        XCTAssertEqual(browsing, [true], "now it looks (this is when iOS asks)"); XCTAssertEqual(hosted, 0, "not hosting yet")
        XCTAssertNotNil(hub.nearbyLookingSince)
        service.debugSetDiscovered([.init(id: LocalMultiplayerTransport.advertisedName("Maya", token: UUID().uuidString), name: "Maya",
                                          endpoint: .hostPort(host: "127.0.0.1", port: 9), sport: "tennis", players: 1)])
        hub.nearbyTick()
        XCTAssertEqual(joined, ["Maya"], "a friend who picked Local play too joins that game, not a second one"); XCTAssertEqual(hosted, 0)

        // a second phone, no friend's game around: it hosts after the look
        gate.reset(); gate.enforceInTests = true
        let other = MultiplayerService(), host = self.hub(other)
        defer { other.leave() }
        host.nearbyBrowse = { _, _ in }; host.nearbyHost = { _ in hosted += 1 }
        HubSession.nearbyLookSeconds = 0
        host.useStation(HubSession.nearbyBay); gate.primary()
        host.nearbyTick(); host.nearbyTick()
        XCTAssertEqual(hosted, 1, "nobody's game nearby: this phone hosts one"); XCTAssertTrue(host.nearbyHosting)
        host.leaveStation()
    }

    /// Local Network refused on the first local match: the card says how to turn it on; back with it on, the match looks again.
    func testARefusedLocalNetworkIsExplainedAndRetried() {
        let saved = SportsSession.shared.displayConnected; SportsSession.shared.displayConnected = true
        let savedContext = ClubHub.shared.context; ClubHub.shared.context = { ClubHubContext() }
        TennisMenu.shared.debugShow(.main); OnboardingFlow.shared.exitToMenu()
        let service = MultiplayerService(), hub = hub(service)
        defer { service.leave(); ClubHub.shared.context = savedContext; HubTestState.restore(display: saved) }
        var hosted = 0
        hub.nearbyBrowse = { _, _ in }; hub.nearbyHost = { _ in hosted += 1 }
        gate.clearLocalNetworkDenied = { service.debugSetLocalNetworkDenied(false) }
        hub.useStation(HubSession.nearbyBay); gate.primary()
        service.debugSetLocalNetworkDenied(true)   // "Don't Allow"
        hub.nearbyTick()
        XCTAssertEqual(gate.request?.kind, .localNetwork); XCTAssertEqual(gate.request?.stage, .denied)
        XCTAssertEqual(hub.station, HubSession.nearbyBay, "the local match stays open behind the card")
        gate.appBecameActive()   // back from Settings with it on
        XCTAssertNil(gate.request); XCTAssertEqual(hosted, 1, "it tries again by itself")
        hub.leaveStation()
    }

    /// An online bench with no Game Center: Apple's sign-in now (the bench opens once signed in). A tennis bench: the camera first.
    func testOnlineBenchesAskForGameCenterAndTennisBenchesForTheCamera() {
        let saved = SportsSession.shared.displayConnected; SportsSession.shared.displayConnected = true
        TennisMenu.shared.debugShow(.main); OnboardingFlow.shared.exitToMenu()
        let service = MultiplayerService(), hub = hub(service)
        defer { hub.leaveStation(); HubSession.shared.leaveStation(); service.leave(); HubTestState.restore(display: saved) }
        var signedIn = false, camera = AVAuthorizationStatus.notDetermined
        gate.gameCenterSignedIn = { signedIn }; gate.signInToGameCenter = {}
        gate.cameraStatus = { camera }; gate.askCamera = { done in camera = .authorized; done(true) }
        hub.useStation("bay-golf-online")
        XCTAssertEqual(gate.request?.kind, .gameCenter); XCTAssertNil(hub.station, "nothing opens before sign-in")
        signedIn = true; gate.gameCenterChanged()
        XCTAssertEqual(hub.station, "bay-golf-online", "signed in: the bench opens by itself")   // (its search runs on the shared hub)
        hub.leaveStation()
        hub.useStation("bay-tennis-online")
        XCTAssertEqual(gate.request?.kind, .camera, "tennis: the camera before a match can be found"); XCTAssertNil(hub.station)
        gate.primary()
        XCTAssertEqual(hub.station, "bay-tennis-online")
    }

    /// Every tennis launch passes SportsSession.start: with the camera not allowed, it holds for the card instead of loading.
    func testATennisLaunchHoldsForTheCameraCard() {
        let session = SportsSession.shared, shared = PermissionGate.shared
        let saved = (session.displayConnected, session.sport, shared.cameraStatus)
        defer { shared.cancel(); session.displayConnected = saved.0; session.sport = saved.1; shared.cameraStatus = saved.2 }
        shared.cameraStatus = { .denied }
        session.displayConnected = true; session.sport = "tennis"
        session.start()
        XCTAssertFalse(session.active, "nothing loads")
        XCTAssertEqual(shared.request?.kind, .camera); XCTAssertEqual(shared.request?.stage, .denied)
        XCTAssertTrue(session.status.contains("camera"), session.status)
    }

    // MARK: the cards

    func testCardsSnapshot() async throws {
        let dir = (ProcessInfo.processInfo.environment["ONB_SNAP_DIR"].map { URL(fileURLWithPath: $0) }
                   ?? FileManager.default.temporaryDirectory.appendingPathComponent("onboarding")).appendingPathComponent("permissions")
        try FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        let scene = try XCTUnwrap(UIApplication.shared.connectedScenes.compactMap { $0 as? UIWindowScene }.first)
        let size = CGSize(width: 402, height: 874)
        for (kind, stage) in [(PermissionGate.Kind.camera, PermissionGate.Stage.ask), (.camera, .denied), (.localNetwork, .ask),
                              (.localNetwork, .denied), (.gameCenter, .waiting), (.gameCenter, .denied)] {
            let host = UIHostingController(rootView: PermissionSheet(request: .init(kind: kind, stage: stage, onGranted: {})))
            host.safeAreaRegions = []
            let window = UIWindow(windowScene: scene)
            window.frame = CGRect(origin: .zero, size: size); window.rootViewController = host; window.isHidden = false
            host.view.frame = window.bounds; host.view.layoutIfNeeded()
            try await Task.sleep(for: .seconds(0.8))
            let image = UIGraphicsImageRenderer(size: size).image { _ in host.view.drawHierarchy(in: window.bounds, afterScreenUpdates: true) }
            try XCTUnwrap(image.pngData()).write(to: dir.appendingPathComponent("\(kind.rawValue)-\(stage).png"))
            window.isHidden = true
        }
    }
}
