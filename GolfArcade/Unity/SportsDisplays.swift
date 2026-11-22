import SwiftUI
import UserNotifications

@MainActor
final class SportsDisplays: NSObject {
    static let shared = SportsDisplays()
    weak var phone: UIWindow?
    var external: UIWindow?
    private var preview: UIWindow?
    private var multiplayerRenderer: UIWindow?
    private var loadingCover: UIWindow?
    private var previewOverlay: UIViewController?
    private var registration: AnyObject?
    /// The controller the iOS 27 external display accessory is registered on (the phone window's root).
    private weak var registrationOwner: UIViewController?
    private override init() {
        super.init()
        NotificationCenter.default.addObserver(self,selector:#selector(refreshNotification),name:UIApplication.didBecomeActiveNotification,object:nil)
        NotificationCenter.default.addObserver(self,selector:#selector(refreshNotification),name:UIScene.didActivateNotification,object:nil)
    }
    @objc private func refreshNotification(_ notification:Notification) { refresh() }
    func refresh() {
        let scenes=UIApplication.shared.connectedScenes.compactMap { $0 as? UIWindowScene }
        if phone == nil {
            phone=scenes.first(where: { $0.session.role == .windowApplication })?.windows.first(where: { $0.isKeyWindow })
        }
        if external == nil, let scene=scenes.first(where: { $0.session.role == .windowExternalDisplayNonInteractive && $0.activationState != .unattached }) {
            let window=UIWindow(windowScene:scene)
            window.rootViewController=Self.tvRoot(); window.isHidden=false; external=window
        }
        SportsSession.shared.displayConnected = external != nil
        if let screen = external?.windowScene?.screen {
            // AirPlay to a Mac arrives like any other screen, usually 16:10 (1440×900,
            // 1512×982…) or the size of the receiver's window; the TV canvas fits either.
            NSLog("[SportsDisplay] external %@ bounds=%.0fx%.0f scale=%.1f native=%.0fx%.0f kind=%@",
                  SportsTiming.currentTV(), screen.bounds.width, screen.bounds.height, screen.scale,
                  screen.nativeBounds.width, screen.nativeBounds.height, Self.displayKind.rawValue)
        }
        NSLog("[SportsDisplay] refresh scenes=%@ external=%d",scenes.map { $0.session.role.rawValue }.joined(separator:","),external != nil ? 1 : 0)
    }
    func register(from controller:UIViewController) {
        guard let window=controller.view.window else { return }
        phone=window
        // The scene accessory needs the iOS 27 SDK: Xcode 26 builds leave it out. UIKit's module version is 9126.x in the iOS 26 SDKs
        // and 9127.x in iOS 27's (27.2 SDK: 9127.1.13). The old gate asked for 9500, which no SDK has, so every build (0.1.6 (25),
        // Xcode 27.2 included) left it out: on iOS 27 Screen Mirroring then only mirrored the phone's controller (11-21 playtest).
        #if canImport(UIKit, _version: 9127)
        if #available(iOS 27.0, *) {
            // Owned by the phone window's root (it lives as long as the app). If that root is ever replaced, the accessory moves to
            // the new one: a registration left on a controller that went away would leave the TV mirroring the phone again.
            var top=controller
            while let parent=top.parent { top=parent }
            let owner=window.rootViewController ?? top
            if registration == nil || registrationOwner !== owner {
                if let old=registration as? UISceneAccessoryRegistration, let previous=registrationOwner { previous.unregisterSceneAccessory(old) }
                let config=UISceneConfiguration(name:"Sports External",sessionRole:.windowExternalDisplayNonInteractive)
                config.delegateClass=SportsExternalScene.self
                let added=owner.registerSceneAccessory(.externalNonInteractive(sceneConfiguration:config))
                added.isEnabled=true   // (said outright: the game's picture is what the TV should show whenever one is there)
                registration=added; registrationOwner=owner
                SportsDiagnostics.write("external display accessory registered available=\(added.isAvailable)")
            } else if let current=registration as? UISceneAccessoryRegistration, !current.isEnabled {
                current.isEnabled=true
            }
        }
        #endif
        refresh()
    }
    func gameWindow(preview usePreview:Bool) -> UIWindow? {
        refresh()
        guard let external else { return nil }
        showMenu()
        return external
    }
    /// Golf guests watch the host's screen. Keep their Unity replica underneath
    /// the opaque native controller so it can supply map and turn state.
    func multiplayerControllerWindow() -> UIWindow? {
        guard SportsSession.shared.multiplayerControllerOnly else { return nil }
        refresh()
        if let external { return external }
        guard let scene=phone?.windowScene else { return nil }
        if multiplayerRenderer == nil {
            let window=UIWindow(windowScene:scene)
            window.windowLevel = UIWindow.Level(rawValue:UIWindow.Level.normal.rawValue - 1)
            let root=UIViewController();root.view.backgroundColor = .black
            window.rootViewController=root;multiplayerRenderer=window
        }
        multiplayerRenderer?.isHidden=false
        return multiplayerRenderer
    }
    /// A golf guest's turn: its Unity replica, which draws the controller sheet, comes up over the native controller (the phone
    /// with the TV brings Unity's own window forward instead), and goes back under it afterwards.
    func showMultiplayerRenderer(_ visible: Bool) {
        guard let window = multiplayerRenderer else { return }
        window.windowLevel = UIWindow.Level(rawValue: UIWindow.Level.normal.rawValue + (visible ? 1 : -1))
        if visible { window.makeKeyAndVisible() } else { phone?.makeKeyAndVisible() }
    }
    /// Explicit automated verification may render on the paired phone without
    /// an AirPlay receiver. Normal play retains its external-display contract.
    func benchmarkWindow() -> UIWindow? {
        guard SportsSession.benchmark else { return nil }
        refresh()
        if let external { showMenu(); return external }
        guard let scene = phone?.windowScene else { return nil }
        if preview == nil {
            let window = UIWindow(windowScene: scene)
            let root = UIViewController(); root.view.backgroundColor = .black
            window.rootViewController = root; preview = window
        }
        return preview
    }
    // MARK: the menu on the phone itself (no TV)

    /// Unity's view while the menu runs on the phone with no TV: a window UNDER the app's own, which turns see-through over it
    /// (MenuTouchPad), so the app's touches and every sheet stay on top of it.
    private var plazaPhone: UIWindow?
    func phonePlazaWindow() -> UIWindow? {
        refresh()
        guard external == nil, let scene = phone?.windowScene else { return nil }
        if plazaPhone == nil {
            let window = UIWindow(windowScene: scene)
            window.windowLevel = UIWindow.Level(rawValue: UIWindow.Level.normal.rawValue - 1)
            let root = UIViewController(); root.view.backgroundColor = .black
            window.rootViewController = root; plazaPhone = window
        }
        return plazaPhone
    }
    /// Unity is attached: show it under the app's window.
    func showPhonePlaza() {
        guard let window = plazaPhone else { return }
        window.isHidden = false
        phone?.makeKeyAndVisible()
        phoneSeeThrough(true)
    }
    func endPhonePlaza() {
        if plazaPhone != nil { SportsRuntime.shared().restoreUnityWindow() }
        plazaPhone?.isHidden = true; plazaPhone = nil
        phone?.makeKeyAndVisible()
        // (still see-through if a handheld match's window is up under it)
        phoneSeeThrough(true)
    }
    var phonePlazaShown: Bool { plazaPhone?.isHidden == false }
    /// The menu on a phone with no TV fills the screen and turns with the phone (Adnan 10-29); everything else on the phone stays upright.
    var phoneMenuRotates: Bool { external == nil && HubSession.shared.onPhone && !SportsSession.shared.active }
    /// Phone casting: the screen phone shows the match sideways, like a TV, either way round (PLAN_PhoneCasting_GolfBowling.md).
    var castScreenSideways: Bool { external == nil && SportsSession.shared.active && SportsSession.shared.castScreen }
    /// The phone's windows ask again which ways they may turn; leaving the menu sideways turns the phone's screen back upright.
    func phoneOrientationChanged() {
        guard let scene = phone?.windowScene else { return }
        for window in scene.windows { window.rootViewController?.setNeedsUpdateOfSupportedInterfaceOrientations() }
        if castScreenSideways {
            if !scene.interfaceOrientation.isLandscape {
                scene.requestGeometryUpdate(.iOS(interfaceOrientations: .landscape)) { error in NSLog("[SportsDisplay] sideways request failed: %@", error.localizedDescription) }
            }
        } else if !phoneMenuRotates, scene.interfaceOrientation.isLandscape {
            scene.requestGeometryUpdate(.iOS(interfaceOrientations: .portrait)) { error in NSLog("[SportsDisplay] upright request failed: %@", error.localizedDescription) }
        }
    }
    // MARK: bowling on the phone itself (no TV)

    /// Unity's view while bowling plays on the phone with no TV (PLAN_PhonePlay): a window under the app's own, which turns
    /// see-through so the lane fills the screen and the bowling controls sit over its foot (BowlingPhoneController, phone play).
    private var playPhone: UIWindow?
    func phonePlayWindow() -> UIWindow? {
        refresh()
        guard external == nil, let scene = phone?.windowScene else { return nil }
        if playPhone == nil {
            let window = UIWindow(windowScene: scene)
            window.windowLevel = UIWindow.Level(rawValue: UIWindow.Level.normal.rawValue - 1)
            let root = UIViewController(); root.view.backgroundColor = .black
            window.rootViewController = root; playPhone = window
        }
        return playPhone
    }
    func showPhonePlay() {
        guard let window = playPhone else { return }
        window.isHidden = false
        phone?.makeKeyAndVisible()
        phoneSeeThrough(true)
    }
    func endPhonePlay() {
        guard playPhone != nil else { return }
        SportsRuntime.shared().restoreUnityWindow()
        playPhone?.isHidden = true; playPhone = nil
        phone?.makeKeyAndVisible()
        phoneSeeThrough(true)
    }
    var phonePlayShown: Bool { playPhone?.isHidden == false }
    #if DEBUG
    /// `-handheldCheck` (simulator, no Unity): a captured game frame stands in for Unity's round under the handheld deck, drawn in
    /// the top three quarters as Unity's camera is.
    func debugFakePhonePlay(image path: String?) {
        guard let window = phonePlayWindow() else {
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.25) { [weak self] in self?.debugFakePhonePlay(image: path) }; return
        }
        let root = UIViewController(); root.view.backgroundColor = .black
        let frame = UIImageView(frame: CGRect(x: 0, y: 0, width: window.bounds.width, height: window.bounds.height * (1 - SportsSession.handheldDeck)))
        frame.image = path.flatMap(UIImage.init(contentsOfFile:)); frame.contentMode = .scaleAspectFill; frame.clipsToBounds = true
        root.view.addSubview(frame)
        window.rootViewController = root
        showPhonePlay()
    }
    #endif

    /// The app's window lets the plaza or the lane (below it) show through where the controller draws nothing.
    func phoneSeeThrough(_ on: Bool) {
        guard let window = phone else { return }
        let clear = on && (phonePlazaShown || phonePlayShown)
        window.backgroundColor = clear ? .clear : .systemBackground
        window.isOpaque = !clear
        window.rootViewController?.view.backgroundColor = clear ? .clear : .systemBackground
        window.rootViewController?.view.isOpaque = !clear
    }

    private var exitCover: UIWindow?
    private var exitGeneration = 0
    private var exitModel: LoadingModel?
    private var exitTimer: Timer?
    /// The Plaza has revealed itself (HubSession.hubRevealing): the exit cover may lift now.
    private var exitHubRevealed = false
    /// Leaving a game shows the same loading screen as entering one (the venue's art, a tip card, the bar), on a model of its own,
    /// until the Plaza is built again and fades in (2026-11-19, Adnan: "should be the same loading screens you get when entering a
    /// game"; before it was a plain "Back to the clubhouse" card, then the Plaza's own boot screen).
    func beginExitCover() {
        guard let destination = external ?? preview ?? phone, let scene = destination.windowScene else { return }
        lingeringTip?.isHidden=true; lingeringTip=nil
        endExitCover()
        exitGeneration += 1; let generation = exitGeneration
        let model = LoadingModel()
        model.begin(now: LoadingModel.clockNow, key: "return")
        model.onFinish = { [weak self] in
            guard let self, generation == self.exitGeneration else { return }
            self.external?.rootViewController?.view.layoutIfNeeded(); self.phone?.rootViewController?.view.layoutIfNeeded()
            self.endExitCover()
        }
        exitModel = model; exitHubRevealed = false
        let cover = UIWindow(windowScene: scene); cover.windowLevel = .alert + 1
        let host = UIHostingController(rootView: PresentationLoadingCover(compact: scene.session.role == .windowApplication, model: model))
        cover.rootViewController = host; cover.backgroundColor = UIColor(Club.lagoonDeep)
        exitCover=cover; cover.isHidden=false; host.view.layoutIfNeeded()
        model.cardAppeared()
        ClubSound.play("whoosh", volume: 0.35)
        let timer = Timer(timeInterval: 0.1, repeats: true) { [weak self] _ in
            MainActor.assumeIsolated { self?.tickExitCover(generation) }
        }
        RunLoop.main.add(timer, forMode: .common); exitTimer = timer
    }
    /// The Plaza is up behind the cover (or will not come): the bar eases to full, and the cover lifts with the Plaza's own reveal.
    private func tickExitCover(_ generation: Int) {
        guard generation == exitGeneration, let model = exitModel else { return }
        let hub = HubSession.shared, now = LoadingModel.clockNow
        let waited = now.timeIntervalSince(model.started ?? now)
        // a Plaza that is not coming (no Unity here, no plaza wanted), or one that failed, must not hold the cover
        let notComing = !hub.wanted && waited >= LoadingModel.minimum
        let gaveUp = hub.phase == .failed || waited >= LoadingPace.longestExpected + 4
        if hub.loaded || notComing || gaveUp { model.markReady(now: now) }
        // after "ready" the cover waits for the Plaza's reveal, so the fly-in is not played under it
        model.tick(now: now, holdFinish: !(exitHubRevealed || notComing || gaveUp))
    }
    /// HubSession calls this as the Plaza reveals itself (the TV's boot screen fades / the phone's plaza shows).
    func hubRevealing() { exitHubRevealed = true }
    private func endExitCover() {
        exitTimer?.invalidate(); exitTimer = nil
        exitModel?.cancel(); exitModel = nil
        exitCover?.isHidden = true; exitCover = nil
    }
    /// How many loading covers have been shown (NO_COVER: a launch from a Plaza bay shows none).
    private(set) var coversShown = 0
    func beginLoadingCover(in destination: UIWindow, startRuntime: @escaping @MainActor () -> Void) {
        coversShown += 1
        lingeringTip?.isHidden=true; lingeringTip=nil
        exitGeneration += 1; endExitCover()
        finishLoadingCover()
        guard let scene = destination.windowScene else { startRuntime(); return }
        let cover = UIWindow(windowScene: scene)
        // On the phone's own screen (handheld play: the game's window sits just under the app's) the cover goes between the game and
        // the app, never over the app: the safety card and its button are the app's and must stay on top and tappable (2026-11-16,
        // Adnan: "it wont let u ready up after the load unless ur screen mirrored").
        let onPhone = scene.session.role == .windowApplication && destination.windowLevel < .normal
        cover.windowLevel = onPhone ? UIWindow.Level(rawValue: UIWindow.Level.normal.rawValue - 0.5) : UIWindow.Level(rawValue: destination.windowLevel.rawValue + 100)
        cover.backgroundColor = .clear
        let host = UIHostingController(rootView: PresentationLoadingCover(compact: scene.session.role == .windowApplication))
        host.view.backgroundColor = .clear; cover.rootViewController = host
        loadingCover = cover; cover.isHidden = false
        host.view.setNeedsLayout(); host.view.layoutIfNeeded()
        let launch = SportsSession.shared.sessionID
        // Give UIKit a display cycle before runEmbedded blocks the main thread on cold startup.
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.05) {
            guard self.loadingCover === cover, SportsSession.shared.active, SportsSession.shared.sessionID == launch else { return }
            SportsSession.shared.loading.cardAppeared()
            startRuntime()
        }
    }
    func revealLoadingFrame() { external?.isHidden = true; preview?.isHidden = false }
    private var lingeringTip: UIWindow?
    func finishLoadingCover() {
        if SportsSession.shared.loading.phase == .finished, let tip = SportsSession.shared.loading.tip,
           let scene = loadingCover?.windowScene, SportsSession.shared.loading.tipRemaining > 0 {
            let window=UIWindow(windowScene:scene); window.windowLevel = .alert
            let host=UIHostingController(rootView: VStack { Spacer(); Text(tip).font(IslandUI.font(18, bold: true)).foregroundStyle(.white).padding(16).background(IslandUI.navy, in: Capsule()).padding(.bottom, 48) })
            host.view.backgroundColor = .clear; window.backgroundColor = .clear; window.rootViewController=host
            window.isUserInteractionEnabled=false; window.isHidden=false; lingeringTip=window
            DispatchQueue.main.asyncAfter(deadline:.now()+SportsSession.shared.loading.tipRemaining) { [weak self] in
                window.isHidden=true; if self?.lingeringTip === window { self?.lingeringTip=nil }
            }
        }
        loadingCover?.isHidden = true; loadingCover = nil
    }

    /// The tennis setup's rings on the TV (TennisSetupTVView), in a window of their own over the game's picture: the game draws the
    /// court, this only the players' rings. It draws nothing outside setup, and nothing while the TV blinks for its delay.
    private var tennisSetupTV: UIWindow?
    func showTennisSetupOnTV() {
        let session = SportsSession.shared
        guard tennisSetupTV == nil, session.displayConnected, !session.multiplayerControllerOnly, !session.phonePlay,
              let scene = external?.windowScene else { return }
        let window = UIWindow(windowScene: scene); window.windowLevel = UIWindow.Level(rawValue: UIWindow.Level.normal.rawValue + 5)
        let host = UIHostingController(rootView: TennisSetupTVView(session: session)); host.view.backgroundColor = .clear
        window.backgroundColor = .clear; window.rootViewController = host; window.isUserInteractionEnabled = false; window.isHidden = false
        tennisSetupTV = window
    }
    func hideTennisSetupOnTV() { tennisSetupTV?.isHidden = true; tennisSetupTV = nil }
    /// The app's window is over the game on the TV (setup and post-game screens).
    var showsTVOverlay: Bool { tennisSetupTV != nil }

    private var networkOverlay: UIHostingController<MultiplayerMatchOverlay>?
    func installMultiplayerOverlay(in root: UIViewController) {
        guard SportsSession.shared.multiplayerMatchID != nil else { return }
        networkOverlay?.willMove(toParent:nil); networkOverlay?.view.removeFromSuperview(); networkOverlay?.removeFromParent()
        let host = UIHostingController(rootView:MultiplayerMatchOverlay(compact:true)); host.view.backgroundColor = .clear
        root.addChild(host); root.view.addSubview(host.view); host.didMove(toParent:root); networkOverlay = host
        host.view.translatesAutoresizingMaskIntoConstraints = false
        NSLayoutConstraint.activate([host.view.leadingAnchor.constraint(equalTo:root.view.safeAreaLayoutGuide.leadingAnchor),host.view.trailingAnchor.constraint(equalTo:root.view.safeAreaLayoutGuide.trailingAnchor),host.view.topAnchor.constraint(equalTo:root.view.safeAreaLayoutGuide.topAnchor),host.view.heightAnchor.constraint(equalToConstant:150)])
    }
    func restorePhoneControls() {
        if external != nil && preview != nil { endPreview() }
        phone?.makeKeyAndVisible()
        if let preview {
            if !SportsSession.shared.loading.finished {
                preview.isHidden = true; phone?.makeKeyAndVisible(); return
            }
            previewOverlay?.willMove(toParent: nil); previewOverlay?.view.removeFromSuperview(); previewOverlay?.removeFromParent()
            phone?.isHidden=true
            preview.makeKeyAndVisible()
            let overlay=UIHostingController(rootView:SportsPreviewControls())
            previewOverlay=overlay
            guard let root=preview.rootViewController else { return }
            root.addChild(overlay); root.view.addSubview(overlay.view); overlay.didMove(toParent:root)
            installMultiplayerOverlay(in:root)
            overlay.view.translatesAutoresizingMaskIntoConstraints=false
            NSLayoutConstraint.activate([
                overlay.view.leadingAnchor.constraint(equalTo:root.view.safeAreaLayoutGuide.leadingAnchor),
                overlay.view.trailingAnchor.constraint(equalTo:root.view.safeAreaLayoutGuide.trailingAnchor),
                overlay.view.bottomAnchor.constraint(equalTo:root.view.safeAreaLayoutGuide.bottomAnchor),
                overlay.view.heightAnchor.constraint(equalToConstant:150)])
        } else if let root = external?.rootViewController { installMultiplayerOverlay(in:root) }
    }
    /// Finished matches use the full native phone screen, including on-phone gameplay.
    func showMatchControls() {
        preview?.isHidden = true
        phone?.makeKeyAndVisible()
    }

    /// Opt-in automated device run: capture the actual controller window after completion.
    func captureBenchmarkFinish() {
        guard SportsSession.benchmark, let window = phone else { return }
        let renderer = UIGraphicsImageRenderer(bounds: window.bounds)
        let image = renderer.image { _ in window.drawHierarchy(in: window.bounds, afterScreenUpdates: true) }
        let directory = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("visual-overhaul/postgame", isDirectory: true)
            .appendingPathComponent(UUID().uuidString, isDirectory: true)
        try? FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        let url = directory.appendingPathComponent("PostGameDevice.png")
        try? image.pngData()?.write(to: url)
        let result = SportsSession.shared.finishedMatch
        let report: [String: Any] = ["startedUtc": ISO8601DateFormatter().string(from: Date()),
            "sport": "tennis", "matchComplete": result != nil, "won": result?.won ?? false,
            "score": result?.score ?? "", "phoneVisible": !window.isHidden,
            "launchArguments": ProcessInfo.processInfo.arguments,
            "screenshot": "PostGameDevice.png"]
        if let data = try? JSONSerialization.data(withJSONObject: report, options: [.prettyPrinted, .sortedKeys]) {
            try? data.write(to: directory.appendingPathComponent("report.json"), options: .atomic)
        }
        SportsDiagnostics.write("postgame device screenshot saved; phoneVisible=\(!window.isHidden) finished=\(SportsSession.shared.finishedMatch != nil)")
    }

    func endPreview() {
        finishLoadingCover()
        networkOverlay?.willMove(toParent:nil); networkOverlay?.view.removeFromSuperview(); networkOverlay?.removeFromParent(); networkOverlay = nil
        if let child=previewOverlay { child.willMove(toParent:nil); child.view.removeFromSuperview(); child.removeFromParent() }
        previewOverlay=nil
        preview?.isHidden=true; preview=nil; multiplayerRenderer?.isHidden=true; multiplayerRenderer=nil; phone?.makeKeyAndVisible()
    }
    func isPreview(_ window:UIWindow?) -> Bool { window != nil && window === preview }

    enum DisplayKind: String { case none, tv, mac }
    /// What the phone is mirroring to: a Mac (AirPlay Receiver) or a TV. The receiver's name
    /// usually says ("Adnan's MacBook Pro"); otherwise a 16:10 screen is almost always a Mac.
    static var displayKind: DisplayKind {
        guard let screen = shared.external?.windowScene?.screen else { return .none }
        let name = SportsTiming.currentTV().lowercased()
        if name.contains("mac") || name.contains("imac") { return .mac }
        let aspect = screen.bounds.width / max(1, screen.bounds.height)
        return abs(aspect - 1.6) < 0.06 ? .mac : .tv
    }
    /// The TV's own screen: the menu, loading and results (TennisTVRoot). It sits above
    /// Unity's display and is hidden while a game is on.
    static func tvRoot() -> UIViewController {
        let host=UIHostingController(rootView:TennisTVRoot())
        host.view.backgroundColor = .black
        return host
    }
    func showMenu() {
        guard let window=external else { return }
        if !(window.rootViewController is UIHostingController<TennisTVRoot>) { window.rootViewController=Self.tvRoot() }
        window.windowLevel = .normal + 1
        window.isHidden=false
    }
}

final class SportsAppDelegate: NSObject, UIApplicationDelegate {
    func application(_ application: UIApplication, didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]? = nil) -> Bool {
        // invites as notifications: the delegate and the Join / Not now actions (permission is asked later, after the first invite)
        UNUserNotificationCenter.current().delegate = ClubNotificationDelegate.shared
        ClubPush.registerCategories()
        return true
    }
    // (Unity hears it from SportsRuntime, which forwards it to UnityAppController)
    func applicationDidReceiveMemoryWarning(_ application: UIApplication) {
        SportsDiagnostics.write("memory warning \(SportsDiagnostics.memory)")
        MatchHeroData.releaseCache()
    }
    func application(_ application: UIApplication, didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data) {
        ClubHub.shared.setPushToken(deviceToken.map { String(format: "%02x", $0) }.joined(), env: ClubPush.environment)
    }
    func application(_ application: UIApplication, didFailToRegisterForRemoteNotificationsWithError error: Error) {
        // (no Push Notifications capability in this build, or no network: invites still arrive in the game)
        SportsDiagnostics.write("push registration failed: \(error.localizedDescription)")
    }
    func application(_ application:UIApplication, supportedInterfaceOrientationsFor window:UIWindow?) -> UIInterfaceOrientationMask {
        if SportsDisplays.shared.isPreview(window) || window?.windowScene?.session.role == .windowExternalDisplayNonInteractive { return .landscape }
        // a window left without a scene (its TV went away): any way up, so its controller always has an orientation in common
        if let window, window.windowScene == nil { return .all }
        // (the walkable Plaza on a phone with no TV stays upright too: it draws above the controls; the menu alone turns either way)
        if SportsDisplays.shared.castScreenSideways { return .landscape }
        return SportsDisplays.shared.phoneMenuRotates ? .allButUpsideDown : .portrait
    }
    func application(_ application:UIApplication, configurationForConnecting session:UISceneSession, options:UIScene.ConnectionOptions) -> UISceneConfiguration {
        let config=UISceneConfiguration(name:session.role == .windowExternalDisplayNonInteractive ? "Sports External" : nil,sessionRole:session.role)
        if session.role == .windowExternalDisplayNonInteractive {
            config.delegateClass=SportsExternalScene.self
        }
        return config
    }
}

final class SportsExternalScene: NSObject, UIWindowSceneDelegate {
    var window:UIWindow?
    func scene(_ scene:UIScene, willConnectTo session:UISceneSession, options:UIScene.ConnectionOptions) {
        NSLog("[SportsDisplay] external scene connected")
        guard let scene=scene as? UIWindowScene else { return }
        let window=UIWindow(windowScene:scene)
        window.rootViewController=SportsDisplays.tvRoot(); window.isHidden=false
        self.window=window; SportsDisplays.shared.external=window; SportsSession.shared.displayConnected=true
        SportsDisplays.shared.showMenu()
        SportsSession.shared.routeGameToExternalDisplay()
    }
    func sceneDidDisconnect(_ scene:UIScene) {
        SportsSession.shared.pause(reason:"Display disconnected — reconnect and tap Ready"); SportsSession.shared.displayConnected=false
        SportsSession.shared.status="Display disconnected. Reconnect your TV or Mac to continue; this phone remains your controller."
        SportsDisplays.shared.external=nil; window=nil
        // the app's TV window went with the TV: golf and bowling put Unity's own end cards back on (the phone game)
        SportsDisplays.shared.hideTennisSetupOnTV()
        if SportsSession.shared.sport != "tennis" { SportsSession.shared.command("postGameTV", value: 0) }
        RecordingService.shared.displayLost()   // what was recorded so far is finished and saved
        HubSession.shared.displayLost()
    }
}

struct SportsPreviewControls:View {
    @State private var session=SportsSession.shared
    var body:some View {
        VStack {
            if session.finishedMatch != nil {
                MatchFinishControls(session: session, compact: true)
            } else {
            HStack {
                if session.sport == "tennis" { PointClipControls(session: session) }
                if session.sport != "tennis" { Text(session.feedback).font(.caption).lineLimit(1) }
                Button(session.paused || (session.sport == "golf" && !session.golfShotReady) ? "Ready" : "Pause") { if session.paused || (session.sport == "golf" && !session.golfShotReady) { session.readyToPlay() } else { session.pause() } }
                Button("Exit Game") { session.exitGame() }.accessibilityIdentifier("game-exit")
            }
            if session.sport == "golf", session.golfPhase == "Result" {
                GolfShotResultControls(session: session)
            }
            if session.sport == "golf", session.golfPhase == "RoundDone" {
                Button(session.golfHasNextHole ? "Next Hole" : "Play Again") { session.command("golfContinue") }
                    .accessibilityIdentifier("golf-continue")
            }
            if session.sport == "tennis" && session.ready {
                if session.tennisPhase == "rally" { Text("Early ← · On time ↑ · Late →").font(.caption) }
                if session.tennisPhase == "serve" || session.tennisPhase == "toss" { ServeAimPad(session:session).frame(width:180,height:90); if session.tennisPhase == "serve" { Button("Toss") { session.toss() } } }
            }
            }
        }.padding().background(.regularMaterial)
    }
}

struct DisplayRegistration: UIViewControllerRepresentable {
    final class Controller:UIViewController {
        override func viewDidAppear(_ animated:Bool) { super.viewDidAppear(animated); SportsDisplays.shared.register(from:self) }
    }
    func makeUIViewController(context:Context) -> Controller { Controller() }
    func updateUIViewController(_ controller:Controller,context:Context) {
        DispatchQueue.main.async { SportsDisplays.shared.register(from:controller) }
    }
}

/// An independent native window covers Unity startup and fades only after the rendered-frame gate.
private struct PresentationLoadingCover: View {
    let compact: Bool
    /// The return from a game runs the same screen on a model of its own (it never touches the Plaza's frame reveal).
    var model: LoadingModel? = nil
    private var loading: LoadingModel { model ?? SportsSession.shared.loading }
    var body: some View {
        GeometryReader { geometry in
            ZStack {
            Club.lagoonDeep
            // (online tennis sets up the racket after this: the court scan needs the court on the TV)
            LoadingScreen(menu: .shared, compact: compact, model: model, returning: model != nil)
                .frame(width: compact ? geometry.size.width : 1280, height: compact ? geometry.size.height : 720)
                .scaleEffect(compact ? 1 : min(geometry.size.width / 1280, geometry.size.height / 720))
                .frame(width: geometry.size.width, height: geometry.size.height)
            }.opacity(1 - loading.transitionFraction)
        }.ignoresSafeArea()
        .onChange(of: loading.phase) { _, phase in
            if phase == .transitioning { ClubSound.play("pop", volume: 0.35); if model == nil { SportsDisplays.shared.revealLoadingFrame() } }
        }
    }
}
