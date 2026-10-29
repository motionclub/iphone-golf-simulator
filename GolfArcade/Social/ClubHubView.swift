import MessageUI
import SwiftUI

/// The online hub (one button on the phone): invites, your party, who is online, who is not, adding friends, inviting someone
/// without the app. Dark and quiet like the plaza controller. PLAN_OnlineHub_FriendsInvites.md §4.
struct ClubHubView: View {
    @Bindable var hub = ClubHub.shared
    var dismiss: () -> Void = {}
    @State private var code = ""
    @State private var sharing = false
    @State private var texting = false
    @State private var shareText = ""
    @State private var confirmJoin: HubInvite?
    @State private var confirmRemove: MultiplayerParticipant?
    private var calls: CallWatcher { .shared }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 18) {
                    statusCard
                    if !hub.notice.isEmpty { noticeBar }
                    if let invite = hub.resolvedInvite { codeCard(invite) }
                    if !hub.invites.isEmpty { invitesSection }
                    partySection
                    friendsSections
                    if !hub.recentNotFriends.isEmpty, hub.canInvite { recentSection }
                    // (the empty list already has its own big Add a friend button)
                    inviteNewSection
                    if hub.presenceOn { settingsSection }
                }
                .padding(.horizontal, 20).padding(.vertical, 14)
            }
            .background(IslandBrandBackground().ignoresSafeArea())
            .navigationTitle("Friends").navigationBarTitleDisplayMode(.inline)
            .toolbar { ToolbarItem(placement: .confirmationAction) { Button("Done") { hub.clearNotice(); dismiss() }.accessibilityIdentifier("club-hub-done") } }
            .toolbarBackground(IslandUI.dark, for: .navigationBar).toolbarBackground(.visible, for: .navigationBar)
        }
        .preferredColorScheme(.dark)
        .foregroundStyle(.white)
        .task { hub.start(); hub.friendsOpened(); await hub.refresh() }
        .sheet(isPresented: $sharing) { ShareSheet(items: [shareText]).presentationDetents([.medium, .large]) }
        .sheet(isPresented: $texting) { MessageComposer(body: shareText).ignoresSafeArea() }
        .confirmationDialog("Remove \(confirmRemove?.name ?? "them") from the party?", isPresented: Binding(get: { confirmRemove != nil }, set: { if !$0 { confirmRemove = nil } }), titleVisibility: .visible) {
            Button("Remove", role: .destructive) { if let p = confirmRemove { leaderAction { try MultiplayerService.shared.removeFromParty(p.id) } }; confirmRemove = nil }
            Button("Keep", role: .cancel) { confirmRemove = nil }
        }
        .confirmationDialog("Leave your party to join \(confirmJoin?.from.name ?? "them")?", isPresented: Binding(get: { confirmJoin != nil }, set: { if !$0 { confirmJoin = nil } }), titleVisibility: .visible) {
            Button("Leave and join") { if let i = confirmJoin { hub.accept(i) }; confirmJoin = nil }
            Button("Stay", role: .cancel) { confirmJoin = nil }
        }
        .accessibilityIdentifier("club-hub")
    }

    // MARK: sections

    private var statusCard: some View {
        HStack(spacing: 12) {
            Circle().fill(statusColor).frame(width: 12, height: 12).shadow(color: statusColor, radius: 5)
            VStack(alignment: .leading, spacing: 2) {
                Text(statusTitle).font(IslandUI.font(17, bold: true)).accessibilityIdentifier("club-hub-status")
                Text(statusDetail).font(IslandUI.font(13)).foregroundStyle(.white.opacity(0.65))
            }
            Spacer()
            if hub.link == .signedOut {
                Button("Sign in") { ClubSignIn.signIn() }
                    .buttonStyle(.borderedProminent).tint(IslandUI.lime).foregroundStyle(IslandUI.navy)
            }
        }
        .padding(14).background(.white.opacity(0.08), in: RoundedRectangle(cornerRadius: 18, style: .continuous))
    }
    private var statusColor: Color {
        switch hub.link { case .online: IslandUI.lime; case .connecting: .orange; case .notConfigured: hub.canInvite ? IslandUI.lime : .gray; case .signedOut: .orange; case .offline: .red.opacity(0.8) }
    }
    private var statusTitle: String {
        switch hub.link {
        case .online: hub.invisible ? "You appear offline" : "You are online"
        case .connecting: "Connecting…"
        case .notConfigured: "Play with friends"
        case .signedOut: "Sign in to play with friends"
        case .offline: "Not connected"
        }
    }
    private var statusDetail: String {
        switch hub.link {
        case .online: "\(hub.onlineFriends.count) friend\(hub.onlineFriends.count == 1 ? "" : "s") online"
        case .connecting: "Reaching the Club Hub"
        case .notConfigured: "Tap Invite next to a friend. They get it even if their game is closed."
        case .signedOut: "Game Center keeps your friends list."
        case .offline(let why): why.isEmpty ? "Trying again…" : why
        }
    }
    private var noticeBar: some View {
        Text(hub.notice).font(IslandUI.font(14, bold: true)).foregroundStyle(IslandUI.navy)
            .frame(maxWidth: .infinity, alignment: .leading).padding(12).background(IslandUI.lime, in: RoundedRectangle(cornerRadius: 14, style: .continuous))
            .onTapGesture { hub.clearNotice() }.accessibilityIdentifier("club-hub-notice")
    }

    private func codeCard(_ invite: HubInvite) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("INVITE FOUND").font(IslandUI.font(12, bold: true)).tracking(1.6).foregroundStyle(IslandUI.lime)
            Text("\(invite.from.name) is hosting \(invite.sportTitle)").font(IslandUI.font(20, bold: true))
            Button { hub.accept(invite) } label: { bigButton("Join \(invite.from.name)") }.accessibilityIdentifier("club-code-join")
        }
        .padding(14).background(.white.opacity(0.1), in: RoundedRectangle(cornerRadius: 18, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 18, style: .continuous).strokeBorder(IslandUI.lime.opacity(0.6), lineWidth: 2))
    }

    private var invitesSection: some View {
        section("Invites", badge: hub.invites.count) {
            ForEach(hub.invites) { invite in
                VStack(alignment: .leading, spacing: 10) {
                    HStack(spacing: 12) {
                        avatar(invite.from.name, dot: nil)
                        VStack(alignment: .leading, spacing: 2) {
                            Text(invite.from.name).font(IslandUI.font(17, bold: true))
                            Text(invite.line).font(IslandUI.font(13)).foregroundStyle(.white.opacity(0.65))
                        }
                        Spacer()
                    }
                    HStack(spacing: 10) {
                        Button { join(invite) } label: { smallButton("Join", filled: true) }.accessibilityIdentifier("club-invite-join-\(invite.from.id)")
                        Button { hub.decline(invite) } label: { smallButton("Not now", filled: false) }.accessibilityIdentifier("club-invite-decline-\(invite.from.id)")
                    }
                }
                .padding(12).background(.white.opacity(0.07), in: RoundedRectangle(cornerRadius: 14, style: .continuous))
            }
        }
    }

    private var partySection: some View {
        let lobby = MultiplayerService.shared.lobby
        return Group {
            if let lobby, lobby.phase == .lobby, MultiplayerService.shared.isParty {
                section("Your party") {
                    ForEach(lobby.participants.filter { !$0.isGuest }, id: \.id) { p in
                        HStack(spacing: 12) {
                            avatar(p.name, dot: p.connected ? IslandUI.lime : .gray)
                            Text(p.name + (p.id == MultiplayerService.shared.localID ? " (you)" : "")).font(IslandUI.font(16, bold: true))
                            if p.id == lobby.ownerID { Image(systemName: "crown.fill").font(.system(size: 13)).foregroundStyle(IslandUI.lime) }
                            if !p.connected { Text("Coming back…").font(IslandUI.font(12)).foregroundStyle(.white.opacity(0.55)) }
                            Spacer()
                            // the leader's tools: hand over the crown, or take someone out (with a check first)
                            if MultiplayerService.shared.isOwner, p.id != MultiplayerService.shared.localID {
                                Menu {
                                    if p.connected {
                                        Button { leaderAction { try MultiplayerService.shared.makeLeader(p.id) } } label: { Label("Make \(p.name) the leader", systemImage: "crown") }
                                    }
                                    Button(role: .destructive) { confirmRemove = p } label: { Label("Remove from party", systemImage: "person.fill.xmark") }
                                } label: {
                                    Image(systemName: "ellipsis.circle.fill").font(.system(size: 28)).foregroundStyle(.white.opacity(0.75)).frame(width: 44, height: 44)
                                }
                                .accessibilityLabel("Options for \(p.name)").accessibilityIdentifier("club-party-member-\(p.id)")
                            }
                        }
                    }
                    Button(role: .destructive) { hub.leaveParty() } label: { smallButton("Leave party", filled: false) }
                        .accessibilityIdentifier("club-party-leave")
                }
            }
        }
    }

    private var friendsSections: some View {
        Group {
            if hub.access == .authorized || !hub.friends.isEmpty {
                if hub.presenceOn {
                    section("Online", badge: hub.onlineFriends.count) {
                        if hub.onlineFriends.isEmpty { empty("None of your friends are online.") }
                        ForEach(hub.onlineFriends) { friendRow($0) }
                    }
                }
                section(hub.presenceOn ? "Offline" : "Your friends", badge: hub.presenceOn ? hub.offlineFriends.count : nil) {
                    if hub.offlineFriends.isEmpty { if showsNoFriendsYet { noFriendsYet } else { empty("Nobody offline.") } }
                    ForEach(hub.offlineFriends) { friendRow($0) }
                }
            } else {
                section("Friends") {
                    switch hub.access {
                    case .notDetermined:
                        Text("Let MotionSports see your Game Center friends, so you can invite them.").font(IslandUI.font(14)).foregroundStyle(.white.opacity(0.75))
                        Button { Task { await hub.allowFriends() } } label: { bigButton("Show my friends") }.accessibilityIdentifier("club-allow-friends")
                    case .denied, .restricted:
                        Text("Friends are turned off for this game. Turn them on in Settings › Game Center › MotionSports.").font(IslandUI.font(14)).foregroundStyle(.white.opacity(0.75))
                        Button { if let url = URL(string: UIApplication.openSettingsURLString) { UIApplication.shared.open(url) } } label: { bigButton("Open Settings") }
                            .accessibilityIdentifier("club-open-settings")
                    default:
                        empty("Sign in to Game Center to see your friends.")
                    }
                }
            }
            if !hub.blockedFriends.isEmpty {
                section("Blocked") { ForEach(hub.blockedFriends) { f in
                    HStack { Text(f.name).font(IslandUI.font(15)); Spacer(); Button("Unblock") { hub.unblock(f) }.font(IslandUI.font(14, bold: true)) }
                } }
            }
        }
    }

    private func friendRow(_ f: ClubHub.Friend, recent: Bool = false) -> some View {
        let state = recent ? "Play again together" : f.online ? stateText(f.state) : hub.presenceOn ? "Offline · they get your invite" : "Tap Invite to play together"
        let sent = hub.sent[f.id]
        return HStack(spacing: 12) {
            avatar(f.name, dot: hub.presenceOn ? (f.online ? IslandUI.lime : .gray.opacity(0.6)) : nil)
            VStack(alignment: .leading, spacing: 2) {
                Text(f.name).font(IslandUI.font(17, bold: true))
                Text(sent?.text ?? state).font(IslandUI.font(13)).foregroundStyle(sent == nil ? .white.opacity(0.6) : IslandUI.lime)
            }
            Spacer()
            if inParty(f.id) {
                Text("In your party").font(IslandUI.font(13, bold: true)).foregroundStyle(IslandUI.lime)
            } else if let sent, sent.pending {
                Button { hub.cancelInvite(to: f) } label: { smallButton("Cancel", filled: false) }
            } else if sent == .accepted {
                ProgressView().tint(IslandUI.lime)
            } else if hub.canJoin(f) {
                VStack(spacing: 8) {
                    Button { hub.join(f) } label: { smallButton("Join", filled: true) }
                        .accessibilityIdentifier("club-join-\(f.id)")
                    Button { hub.invite(f) } label: { smallButton("Invite", filled: false) }
                        .accessibilityIdentifier("club-invite-\(f.id)")
                }
            } else {
                // one tap, online or offline (offline friends get it the moment they open the game)
                Button { hub.invite(f) } label: { smallButton("Invite", filled: true) }
                    .disabled(!hub.canInvite).opacity(hub.canInvite ? 1 : 0.4)
                    .accessibilityIdentifier("club-invite-\(f.id)")
            }
        }
        .padding(10).background(.white.opacity(0.06), in: RoundedRectangle(cornerRadius: 14, style: .continuous))
        .contextMenu { Button(role: .destructive) { hub.block(f) } label: { Label("Block \(f.name)", systemImage: "hand.raised.fill") } }
        .accessibilityElement(children: .combine).accessibilityIdentifier("club-friend-\(f.id)")
    }

    /// People played with recently who are not friends (a quick match, a friend's friend in a party): Invite them again.
    private var recentSection: some View {
        section("Played with recently") {
            ForEach(hub.recentNotFriends.prefix(6)) { p in friendRow(ClubHub.Friend(id: p.id, name: p.name), recent: true) }
        }
    }

    private var showsNoFriendsYet: Bool { (hub.access == .authorized || !hub.friends.isEmpty) && hub.offlineFriends.isEmpty && hub.onlineFriends.isEmpty }
    private var noFriendsYet: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("No friends here yet").font(IslandUI.font(18, bold: true))
            Text("A friend shows up here when they have MotionSports and you are friends in Game Center.").font(IslandUI.font(14)).foregroundStyle(.white.opacity(0.75))
            Button { hub.addFriend() } label: { bigButton("Add a friend") }.accessibilityIdentifier("club-add-friend-empty")
        }
        .padding(14).background(.white.opacity(0.07), in: RoundedRectangle(cornerRadius: 14, style: .continuous))
    }

    private func inParty(_ id: String) -> Bool {
        hub.friendInParty(id)
    }
    private func stateText(_ s: HubPresenceState?) -> String {
        switch s { case .plaza?: "In the Plaza"; case .lobby?: "In a lobby"; case .match?: "In a match"; case .away?: "Away"; case .dnd?: "Do not disturb"; case nil: "Online" }
    }

    /// Everyone who is not in the list above: people on your FaceTime call, and (when the empty list has no big button of its own) a
    /// Game Center friend request.
    private var inviteNewSection: some View {
        section("Invite someone new") {
            Button { textInvite() } label: {
                rowButton("message.fill", "Text an invite", "Any phone number. They don't need the game yet")
            }.accessibilityIdentifier("club-text-invite")
            if hub.cloud.on || hub.link == .online {
                HStack(spacing: 10) {
                    TextField("Got a code? Type it here", text: $code).textInputAutocapitalization(.characters).autocorrectionDisabled()
                        .font(IslandUI.font(16, bold: true)).padding(12).background(.white.opacity(0.1), in: RoundedRectangle(cornerRadius: 12))
                        .submitLabel(.join).onSubmit { hub.resolve(code) }
                        .accessibilityIdentifier("club-code-field")
                    Button { hub.resolve(code) } label: { smallButton("Join", filled: true) }.disabled(code.isEmpty).accessibilityIdentifier("club-code-find")
                }
            }
            Button { startSharePlay() } label: {
                rowButton("shareplay", calls.active ? "Invite everyone on your call" : "Invite your FaceTime call",
                          calls.active ? "They tap Join on their phone" : "Start a FaceTime call first, then tap here")
            }.accessibilityIdentifier("club-shareplay")
            if !showsNoFriendsYet {
                Button { hub.addFriend() } label: { rowButton("person.badge.plus", "Add a friend", "Send a Game Center friend request") }.accessibilityIdentifier("club-add-friend")
            }
        }
    }
    /// Messages with the invite written in, so a phone number is all it takes (the share sheet where Messages is not set up).
    private func textInvite() {
        guard !sharing, !texting else { return }
        Task {
            guard let text = await hub.prepareTextInvite() else {
                if !hub.cloud.on { hub.say("Texting invites needs iCloud. Sign in to iCloud in Settings, then try again.") }
                return
            }
            shareText = text
            if MessageComposer.canSend { texting = true } else { sharing = true }
        }
    }
    private func startSharePlay() {
        guard calls.active else { hub.say("Start a FaceTime call with your friends, then tap this again."); return }
        do { try MultiplayerService.shared.startSharePlay(); hub.say("Your call can see the game now. Everyone who wants to play gets an invite.") }
        catch { hub.say(error.localizedDescription) }
    }

    private var settingsSection: some View {
        section("Settings") {
            Toggle("Appear offline", isOn: $hub.invisible).tint(IslandUI.lime).accessibilityIdentifier("club-appear-offline")
            Toggle("Do not disturb", isOn: $hub.doNotDisturb).tint(IslandUI.lime).accessibilityIdentifier("club-dnd")
            Text("Friends who invite you see \"Busy\" and no banner appears.").font(IslandUI.font(12)).foregroundStyle(.white.opacity(0.5))
            Text("Your Game Center friends who have MotionSports appear here.").font(IslandUI.font(12)).foregroundStyle(.white.opacity(0.5))
        }
    }

    // MARK: pieces

    private func leaderAction(_ action: () throws -> Void) {
        do { try action() } catch { hub.say(error.localizedDescription) }
    }

    private func join(_ invite: HubInvite) {
        if MultiplayerService.shared.lobby != nil, !MultiplayerService.shared.isNearby, (MultiplayerService.shared.lobby?.participants.count ?? 1) > 1 { confirmJoin = invite }
        else { hub.accept(invite) }
    }

    private func section<C: View>(_ title: String, badge: Int? = nil, @ViewBuilder _ content: () -> C) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(spacing: 8) {
                Text(title.uppercased()).font(IslandUI.font(12, bold: true)).tracking(1.6).foregroundStyle(IslandUI.lime)
                if let badge, badge > 0 { Text("\(badge)").font(IslandUI.font(12, bold: true)).foregroundStyle(IslandUI.navy).padding(.horizontal, 7).padding(.vertical, 2).background(IslandUI.lime, in: Capsule()) }
            }
            content()
        }
    }
    private func empty(_ text: String) -> some View { Text(text).font(IslandUI.font(14)).foregroundStyle(.white.opacity(0.5)).padding(.vertical, 4) }
    private func avatar(_ name: String, dot: Color?) -> some View {
        Text(String(name.prefix(1)).uppercased()).font(IslandUI.font(18, bold: true)).foregroundStyle(IslandUI.navy)
            .frame(width: 42, height: 42).background(Circle().fill(Color(hue: Double(abs(name.hashValue) % 360) / 360, saturation: 0.45, brightness: 0.95)))
            .overlay(alignment: .bottomTrailing) { if let dot { Circle().fill(dot).frame(width: 13, height: 13).overlay(Circle().stroke(IslandUI.dark, lineWidth: 2.5)) } }
    }
    private func bigButton(_ title: String) -> some View {
        Text(title).font(IslandUI.font(18, bold: true)).foregroundStyle(IslandUI.navy).frame(maxWidth: .infinity, minHeight: 50).background(IslandUI.lime, in: Capsule())
    }
    private func smallButton(_ title: String, filled: Bool) -> some View {
        Text(title).font(IslandUI.font(15, bold: true)).foregroundStyle(filled ? IslandUI.navy : .white).padding(.horizontal, 16).frame(minHeight: 38)
            .background(filled ? IslandUI.lime : Color.white.opacity(0.12), in: Capsule())
    }
    private func rowButton(_ icon: String, _ title: String, _ subtitle: String) -> some View {
        HStack(spacing: 12) {
            Image(systemName: icon).font(.system(size: 18, weight: .bold)).frame(width: 42, height: 42).background(.white.opacity(0.1), in: Circle())
            VStack(alignment: .leading, spacing: 2) { Text(title).font(IslandUI.font(16, bold: true)); Text(subtitle).font(IslandUI.font(12)).foregroundStyle(.white.opacity(0.6)).multilineTextAlignment(.leading) }
            Spacer(); Image(systemName: "chevron.right").font(.system(size: 13, weight: .bold)).foregroundStyle(.white.opacity(0.4))
        }
        .padding(10).background(.white.opacity(0.06), in: RoundedRectangle(cornerRadius: 14, style: .continuous))
    }
}

/// Messages, with the invite already written: the player only picks who (a contact or any phone number) and taps Send.
struct MessageComposer: UIViewControllerRepresentable {
    let body: String
    static var canSend: Bool { MFMessageComposeViewController.canSendText() }
    func makeCoordinator() -> Coordinator { Coordinator() }
    func makeUIViewController(context: Context) -> MFMessageComposeViewController {
        let vc = MFMessageComposeViewController(); vc.body = body; vc.messageComposeDelegate = context.coordinator; return vc
    }
    func updateUIViewController(_ controller: MFMessageComposeViewController, context: Context) {}
    final class Coordinator: NSObject, MFMessageComposeViewControllerDelegate {
        func messageComposeViewController(_ controller: MFMessageComposeViewController, didFinishWith result: MessageComposeResult) {
            MainActor.assumeIsolated {
                if result == .sent { ClubHub.shared.say("Invite sent! They tap the link or type the code to join you.") }
                controller.dismiss(animated: true)
            }
        }
    }
}

struct ShareSheet: UIViewControllerRepresentable {
    let items: [Any]
    func makeUIViewController(context: Context) -> UIActivityViewController { UIActivityViewController(activityItems: items, applicationActivities: nil) }
    func updateUIViewController(_ controller: UIActivityViewController, context: Context) {}
}

/// The in-game invite notification: a banner over whatever the phone is showing, like a console invite pop-up. It lives in a
/// window of its own above everything (InviteBannerWindow), is held while a match or a load is on, and runs a 2-minute
/// countdown. One tap on Join and you are in your friend's party, in the Plaza.
struct InviteBannerHost: View {
    var hub = ClubHub.shared
    var chat = PartyChat.shared
    var body: some View {
        VStack(spacing: 8) {
            if let invite = hub.banner { InviteBanner(hub: hub, invite: invite).transition(.move(edge: .top).combined(with: .opacity)) }
            if let who = hub.joining, !hub.heldForGame { JoiningPill(hub: hub, who: who).transition(.move(edge: .top).combined(with: .opacity)) }
            else if let knock = hub.cloud.knocking, !hub.heldForGame { KnockPill(hub: hub, text: knock.stage).transition(.move(edge: .top).combined(with: .opacity)) }
            else if !hub.notice.isEmpty, !hub.hubOpen { NoticePill(hub: hub).transition(.opacity) }
            // in-game chat over every screen (the strip takes touches only while it is open)
            if !hub.hubOpen { PartyChatStrip(chat: chat).padding(.top, chat.stripOpen ? 44 : 48) }
        }
        .padding(.horizontal, 12).padding(.top, 6)
        .frame(maxWidth: 560)
        .animation(.spring(response: 0.4, dampingFraction: 0.8), value: hub.banner?.inviteID)
        .animation(.easeInOut(duration: 0.25), value: hub.joining)
        .allowsHitTesting(hub.banner != nil || ((hub.joining != nil || hub.cloud.knocking != nil) && !hub.heldForGame) || !hub.notice.isEmpty || (chat.stripOpen && chat.available))
    }
}

/// The invite banner's own window, above every other window on the phone (the app's sheets, the Friends list, the Plaza drawn on
/// the phone, Apple's sheets): an invite can never be hidden behind something. Only the banner itself takes touches; everything
/// around it goes through to the app.
@MainActor enum InviteBannerWindow {
    private(set) static var window: UIWindow?
    static func install() {
        guard window == nil, let scene = UIApplication.shared.connectedScenes.compactMap({ $0 as? UIWindowScene })
            .first(where: { $0.session.role == .windowApplication }) else { return }
        let w = PassthroughWindow(windowScene: scene)
        w.windowLevel = UIWindow.Level(rawValue: UIWindow.Level.alert.rawValue + 2)
        w.backgroundColor = .clear
        let root = UIViewController(); root.view = PassthroughView(); root.view.backgroundColor = .clear
        let host = UIHostingController(rootView: InviteBannerHost())
        host.view.backgroundColor = .clear
        host.sizingOptions = .intrinsicContentSize
        root.addChild(host); root.view.addSubview(host.view); host.didMove(toParent: root)
        host.view.translatesAutoresizingMaskIntoConstraints = false
        NSLayoutConstraint.activate([
            host.view.topAnchor.constraint(equalTo: root.view.safeAreaLayoutGuide.topAnchor),
            host.view.centerXAnchor.constraint(equalTo: root.view.centerXAnchor),
            host.view.widthAnchor.constraint(lessThanOrEqualTo: root.view.widthAnchor),
        ])
        let fill = host.view.widthAnchor.constraint(equalTo: root.view.widthAnchor); fill.priority = .defaultHigh; fill.isActive = true
        w.rootViewController = root
        w.isHidden = false
        window = w
    }
}
/// Touches that land on nothing of its own go to the windows below.
final class PassthroughWindow: UIWindow {
    override func hitTest(_ point: CGPoint, with event: UIEvent?) -> UIView? {
        // (a window with nothing of its own under the touch answers itself: that touch is for the windows below too)
        guard let hit = super.hitTest(point, with: event), hit !== self, hit !== rootViewController?.view else { return nil }
        return hit
    }
}
final class PassthroughView: UIView {
    override func hitTest(_ point: CGPoint, with event: UIEvent?) -> UIView? {
        let hit = super.hitTest(point, with: event)
        return hit === self ? nil : hit
    }
}

struct InviteBanner: View {
    let hub: ClubHub
    let invite: HubInvite
    var body: some View {
        TimelineView(.periodic(from: .now, by: 0.5)) { _ in
            VStack(spacing: 10) {
                HStack(spacing: 12) {
                    Text(String(invite.from.name.prefix(1)).uppercased()).font(IslandUI.font(20, bold: true)).foregroundStyle(IslandUI.navy)
                        .frame(width: 46, height: 46).background(Circle().fill(IslandUI.lime))
                    VStack(alignment: .leading, spacing: 2) {
                        Text(invite.from.name).font(IslandUI.font(17, bold: true))
                        Text(invite.line).font(IslandUI.font(13)).foregroundStyle(.white.opacity(0.75))
                    }
                    Spacer(minLength: 0)
                    if hub.invites.count > 1 { Text("+\(hub.invites.count - 1)").font(IslandUI.font(13, bold: true)).padding(.horizontal, 8).padding(.vertical, 3).background(.white.opacity(0.15), in: Capsule()) }
                }
                HStack(spacing: 10) {
                    Button { hub.accept(invite) } label: {
                        Text("Join").font(IslandUI.font(17, bold: true)).foregroundStyle(IslandUI.navy).frame(maxWidth: .infinity, minHeight: 44).background(IslandUI.lime, in: Capsule())
                    }.accessibilityIdentifier("invite-banner-join")
                    Button { hub.snooze(invite) } label: {
                        Text("Not now").font(IslandUI.font(16, bold: true)).frame(maxWidth: .infinity, minHeight: 44).background(.white.opacity(0.14), in: Capsule())
                    }.accessibilityIdentifier("invite-banner-later")
                }
                GeometryReader { g in
                    Capsule().fill(.white.opacity(0.15)).overlay(alignment: .leading) { Capsule().fill(IslandUI.lime).frame(width: g.size.width * hub.remaining(invite)) }
                }.frame(height: 4)
            }
            .padding(14)
            .background(IslandUI.dark.opacity(0.97), in: RoundedRectangle(cornerRadius: 22, style: .continuous))
            .overlay(RoundedRectangle(cornerRadius: 22, style: .continuous).strokeBorder(.white.opacity(0.2), lineWidth: 1.5))
            .shadow(color: .black.opacity(0.35), radius: 14, y: 6)
        }
        .foregroundStyle(.white).preferredColorScheme(.dark)
        .contentShape(RoundedRectangle(cornerRadius: 22))
        .onTapGesture { hub.hubOpen = true }
        .accessibilityElement(children: .contain).accessibilityIdentifier("invite-banner")
    }
}

private struct JoiningPill: View {
    let hub: ClubHub
    let who: String
    private var text: String {
        switch hub.joinStage {
        case .later?: "You'll join \(who) in the Plaza"
        case .waiting?: "Waiting for \(who)…"
        default: "Joining \(who)…"
        }
    }
    var body: some View {
        HStack(spacing: 10) {
            if hub.joinStage != .later { ProgressView().tint(IslandUI.navy) }
            Text(text).font(IslandUI.font(15, bold: true)).lineLimit(1).minimumScaleFactor(0.8)
            Button("Cancel") { hub.cancelJoin() }.font(IslandUI.font(14, bold: true)).padding(.leading, 6)
        }
        .foregroundStyle(IslandUI.navy).padding(.horizontal, 16).frame(minHeight: 44).background(IslandUI.lime, in: Capsule())
        .accessibilityIdentifier("club-joining")
    }
}

/// Dropping in on a friend or joining with a code: waiting for the host to let you in.
private struct KnockPill: View {
    let hub: ClubHub
    let text: String
    var body: some View {
        HStack(spacing: 10) {
            ProgressView().tint(IslandUI.navy)
            Text(text).font(IslandUI.font(15, bold: true)).lineLimit(1).minimumScaleFactor(0.8)
            Button("Cancel") { hub.cloud.cancelKnock() }.font(IslandUI.font(14, bold: true)).padding(.leading, 6)
        }
        .foregroundStyle(IslandUI.navy).padding(.horizontal, 16).frame(minHeight: 44).background(IslandUI.lime, in: Capsule())
        .accessibilityIdentifier("club-knocking")
    }
}

private struct NoticePill: View {
    let hub: ClubHub
    var body: some View {
        Text(hub.notice).font(IslandUI.font(14, bold: true)).foregroundStyle(IslandUI.navy).multilineTextAlignment(.center)
            .padding(.horizontal, 16).padding(.vertical, 10).background(IslandUI.lime, in: RoundedRectangle(cornerRadius: 16, style: .continuous))
            .task(id: hub.notice) { try? await Task.sleep(for: .seconds(4)); hub.clearNotice() }
            .accessibilityIdentifier("club-notice")
    }
}
