from pathlib import Path
p=Path('GolfArcade/Multiplayer/MultiplayerModels.swift');s=p.read_text();needle='''    var participants: [MultiplayerParticipant]
    func valid() -> Bool {''';s=s.replace(needle,'''    var participants: [MultiplayerParticipant]
    var usesHostGolfDisplay: Bool { sport == "golf" && localID != hostID }
    func valid() -> Bool {''');p.write_text(s)
p=Path('GolfArcade/Unity/SportsSession.swift');s=p.read_text().replace('    private(set) var multiplayerMatchID: String?','    private(set) var multiplayerMatchID: String?\n    private(set) var multiplayerControllerOnly = false')
s=s.replace('multiplayerMatchID=configuration.matchID','multiplayerMatchID=configuration.matchID\n        multiplayerControllerOnly=configuration.usesHostGolfDisplay')
s=s.replace('if !active { multiplayerMatchID=nil }','if !active { multiplayerMatchID=nil; multiplayerControllerOnly=false }')
s=s.replace('guard let window = Self.benchmark ? SportsDisplays.shared.benchmarkWindow() : SportsDisplays.shared.gameWindow(preview:preview) else {','guard let window = Self.benchmark ? SportsDisplays.shared.benchmarkWindow() : multiplayerControllerOnly ? SportsDisplays.shared.multiplayerControllerWindow() : SportsDisplays.shared.gameWindow(preview:preview) else {')
s=s.replace('guard displayConnected else { pause(reason: "Reconnect your TV or Mac to continue."); return }','guard displayConnected || multiplayerControllerOnly else { pause(reason: "Reconnect your TV or Mac to continue."); return }')
s=s.replace('guard displayConnected, active, ready, loading.finished else { return }','guard displayConnected || multiplayerControllerOnly, active, ready, loading.finished else { return }')
s=s.replace('multiplayerMatchID=nil; multiplayerSeat = -1','multiplayerMatchID=nil; multiplayerSeat = -1; multiplayerControllerOnly=false')
p.write_text(s)
p=Path('GolfArcade/Unity/SportsDisplays.swift');s=p.read_text().replace('    private var preview: UIWindow?','    private var preview: UIWindow?\n    private var multiplayerRenderer: UIWindow?')
needle='    /// Explicit automated verification may render on the paired phone without'
s=s.replace(needle,'''    /// Golf guests watch the host's screen. Keep their Unity replica underneath
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
''' + needle)
s=s.replace('preview?.isHidden=true; preview=nil; phone?.makeKeyAndVisible()','preview?.isHidden=true; preview=nil; multiplayerRenderer?.isHidden=true; multiplayerRenderer=nil; phone?.makeKeyAndVisible()')
p.write_text(s)
p=Path('GolfArcade/Unity/GolfController.swift');s=p.read_text().replace('session.displayConnected ? "TV ON" : "TV OFF"','session.multiplayerControllerOnly ? "PARTY" : session.displayConnected ? "TV ON" : "TV OFF"').replace('session.displayConnected ? Color(hex: "00C92C")','(session.displayConnected || session.multiplayerControllerOnly) ? Color(hex: "00C92C")').replace('session.displayConnected ? "TV connected" : "TV disconnected"','session.multiplayerControllerOnly ? "Using the host’s display" : session.displayConnected ? "TV connected" : "TV disconnected"').replace('.disabled(!session.displayConnected).accessibilityIdentifier("golf-resume")','.disabled(!session.displayConnected && !session.multiplayerControllerOnly).accessibilityIdentifier("golf-resume")').replace('if !session.displayConnected { Text("Reconnect your TV to continue.") }','if !session.displayConnected && !session.multiplayerControllerOnly { Text("Reconnect your TV to continue.") }');p.write_text(s)
p=Path('GolfArcadeTests/MultiplayerTests.swift');s=p.read_text().replace('remote.runtimeLoaded();XCTAssertEqual(host.lobby?.phase,.playing)','remote.runtimeLoaded();XCTAssertEqual(host.lobby?.phase,.playing)\n        XCTAssertTrue(remoteRuntime.configurations.last!.usesHostGolfDisplay)\n        XCTAssertFalse(runtime.configurations.last!.usesHostGolfDisplay)');p.write_text(s)
