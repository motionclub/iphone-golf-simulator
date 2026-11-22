import SwiftUI
import UIKit

/// Putting the game on a TV (11-21, Adnan: "mirroring/airplaying while in the app should be super simple").
///
/// iOS lets no app start Screen Mirroring: only Control Center can, and the AirPlay button apps get (AVRoutePickerView) carries a
/// video player's picture or the sound, never the game. So this is the shortest way there is: one sheet, used everywhere the game
/// needs a TV, that shows the two taps in Control Center, watches for the TV, says its name and then carries on by itself (the match
/// starts, the pause ends). Golf and bowling also offer "Play on this phone". Before, each place said it in its own words, in text,
/// and starting tennis on a phone with no TV opened a screen the phone never showed (TennisMenu .connect is a TV-only screen).
@MainActor @Observable
final class TVConnect {
    static let shared = TVConnect()

    struct Request: Identifiable {
        let id = UUID()
        var title: String
        /// The sport that wants the TV (nil: just connecting, from the menu's TV button).
        var sport: Sport?
        /// Runs once the TV is there (the sheet has said so and closed).
        var onConnected: (@MainActor () -> Void)?
        /// Golf and bowling: play on this phone instead (shown only when set).
        var onPhone: (@MainActor () -> Void)?
        /// Not now.
        var onCancel: (@MainActor () -> Void)?
    }

    private(set) var request: Request?
    /// Set the moment the TV arrives: "Connected to <name>" shows for a beat before the sheet closes.
    private(set) var connectedName: String?
    /// How long "Connected to …" stays up before the game carries on.
    static let connectedBeat: Duration = .milliseconds(1200)

    /// Shows the sheet, unless a TV is already there (then `onConnected` runs at once).
    func present(title: String = "Put the game on your TV", sport: Sport? = nil,
                 onConnected: (@MainActor () -> Void)? = nil, onPhone: (@MainActor () -> Void)? = nil, onCancel: (@MainActor () -> Void)? = nil) {
        SportsDisplays.shared.refresh()
        if SportsSession.shared.displayConnected { request = nil; onConnected?(); return }
        connectedName = nil
        let r = Request(title: title, sport: sport, onConnected: onConnected, onPhone: onPhone, onCancel: onCancel)
        request = r
        SportsDiagnostics.write("tv connect sheet shown sport=\(sport?.rawValue ?? "-")")
        watch(r.id)
    }

    func cancel() {
        guard let r = request else { return }
        request = nil; connectedName = nil
        r.onCancel?()
    }

    func playOnPhone() {
        guard let r = request else { return }
        request = nil; connectedName = nil
        r.onPhone?()
    }

    /// The TV arrives through the external display scene (SportsExternalScene sets displayConnected); a refresh now and then also
    /// catches a scene that connected without its delegate being called.
    private func watch(_ id: UUID) {
        Task { @MainActor [weak self] in
            var ticks = 0
            while let self, let r = self.request, r.id == id, self.connectedName == nil {
                if ticks % 4 == 0 { SportsDisplays.shared.refresh() }
                ticks += 1
                if SportsSession.shared.displayConnected { await self.arrived(r); return }
                try? await Task.sleep(for: .milliseconds(250))
            }
        }
    }

    private func arrived(_ r: Request) async {
        connectedName = Self.screenName()
        SportsDiagnostics.write("tv connect sheet: connected to \(connectedName ?? "?")")
        UINotificationFeedbackGenerator().notificationOccurred(.success)
        try? await Task.sleep(for: Self.connectedBeat)
        guard request?.id == r.id else { return }
        request = nil; connectedName = nil
        r.onConnected?()
    }

    /// The receiver's name from the audio route (it follows the picture): "Living Room", "Adnan's MacBook Pro", or a cable's.
    static func screenName() -> String {
        let name = SportsTiming.currentTV()
        return SportsTiming.currentLink() == .unknown || name.isEmpty || name == "screen" ? "your TV" : name
    }

    #if DEBUG
    /// Snapshots: the sheet as it looks while looking, or once connected.
    func debugShow(sport: Sport?, connected: String? = nil, phone: Bool = false) {
        let none: (@MainActor () -> Void)? = nil
        let stay: (@MainActor () -> Void)? = { }
        request = Request(title: "Put the game on your TV", sport: sport, onConnected: none, onPhone: phone ? stay : none, onCancel: none)
        connectedName = connected
    }
    #endif
}

/// The sheet: the two taps, shown moving, then "Looking for your TV…" until it is there.
struct ConnectTVSheet: View {
    let request: TVConnect.Request
    @Bindable var connect = TVConnect.shared
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 18) {
                Text(request.title).font(MotionBrand.font(.extraBoldItalic, 34)).lineLimit(2).minimumScaleFactor(0.6)
                Text("Your phone stays the controller.").font(MotionBrand.font(.medium, 17)).foregroundStyle(MotionBrand.n300)
                MirrorDemo().scaleEffect(0.82).frame(maxWidth: .infinity).frame(height: 246)
                VStack(alignment: .leading, spacing: 12) {
                    step(1, "Swipe down from the top-right corner")
                    step(2, "Tap Screen Mirroring", icon: "rectangle.on.rectangle")
                    step(3, "Pick your TV")
                }
                status
                if request.onPhone != nil {
                    Button { connect.playOnPhone() } label: { Text("Play on this phone") }
                        .buttonStyle(MotionButtonStyle(kind: .secondary)).accessibilityIdentifier("tv-connect-phone")
                }
                Button { connect.cancel() } label: { Text("Not now") }
                    .buttonStyle(MotionButtonStyle(kind: .ghost)).frame(maxWidth: .infinity)
                    .accessibilityIdentifier("tv-connect-cancel")
                Text("On a Mac: turn on AirPlay Receiver in System Settings › General › AirDrop & Handoff, on the same Wi-Fi.")
                    .font(MotionBrand.font(.medium, 13)).foregroundStyle(MotionBrand.n300).fixedSize(horizontal: false, vertical: true)
            }
            .foregroundStyle(.white)
            .padding(.horizontal, 22).padding(.top, 24).padding(.bottom, 30)
        }
        .scrollIndicators(.hidden)
        .background(MotionBrand.background.ignoresSafeArea())
        .preferredColorScheme(.dark)
        .accessibilityIdentifier("tv-connect")
    }

    private func step(_ n: Int, _ text: String, icon: String? = nil) -> some View {
        HStack(spacing: 12) {
            Text("\(n)").font(MotionBrand.font(.extraBold, 15)).foregroundStyle(MotionBrand.navyInk)
                .frame(width: 28, height: 28).background(MotionBrand.gold, in: Circle())
            Text(text).font(MotionBrand.font(.semiBold, 18))
            if let icon {
                Image(systemName: icon).font(.system(size: 16, weight: .bold)).foregroundStyle(MotionBrand.navyInk)
                    .frame(width: 34, height: 34).background(.white, in: RoundedRectangle(cornerRadius: 9, style: .continuous))
            }
        }
    }

    @ViewBuilder private var status: some View {
        HStack(spacing: 12) {
            if let name = connect.connectedName {
                Image(systemName: "checkmark.circle.fill").font(.system(size: 24, weight: .bold)).foregroundStyle(MotionBrand.success)
                Text("Connected to \(name)").font(MotionBrand.font(.extraBold, 18)).lineLimit(1).minimumScaleFactor(0.7)
                    .accessibilityIdentifier("tv-connect-done")
            } else {
                ProgressView().tint(.white)
                Text("Looking for your TV…").font(MotionBrand.font(.semiBold, 17)).foregroundStyle(MotionBrand.n300)
            }
            Spacer(minLength: 0)
        }
        .padding(16).frame(maxWidth: .infinity, alignment: .leading)
        .background(MotionBrand.navyInk.opacity(0.55), in: RoundedRectangle(cornerRadius: 18, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 18, style: .continuous).strokeBorder(connect.connectedName == nil ? .white.opacity(0.25) : MotionBrand.success, lineWidth: 1.5))
        .animation(.spring(response: 0.35, dampingFraction: 0.85), value: connect.connectedName)
    }
}

/// A drawn iPhone doing the two taps, on a loop: a finger pulls Control Center down from the top-right corner, taps the Screen
/// Mirroring tile, then picks the TV from the list.
private struct MirrorDemo: View {
    static let loop = 5.0
    var body: some View {
        TimelineView(.animation) { tl in
            let t = tl.date.timeIntervalSinceReferenceDate.truncatingRemainder(dividingBy: Self.loop)
            frame(t)
        }
        .accessibilityElement().accessibilityLabel("Swipe down from the top-right corner, tap Screen Mirroring, then pick your TV.")
    }

    private func frame(_ t: Double) -> some View {
        let w: CGFloat = 156, h: CGFloat = 290
        // 0–1.0 s the finger pulls down · 1.0–2.4 s Control Center, the mirroring tile is tapped at 1.9 · 2.4–4.2 s the TV list, the TV
        // tapped at 3.4 · 4.2–5 s rest
        let pull = smooth((t - 0.15) / 0.8)
        let center = t >= 0.9 && t < 4.4 ? 1.0 : 0
        let list = t >= 2.4 && t < 4.4
        let tileTap = t >= 1.8 && t < 2.4
        let tvTap = t >= 3.3 && t < 4.4
        // the finger's position in the phone's frame
        let finger: CGPoint? = {
            if t < 1.0 { return CGPoint(x: w - 22, y: 8 + pull * 70) }
            if t < 2.4 { return CGPoint(x: 41, y: 128) }
            if t < 4.2 { return CGPoint(x: w / 2 + 20, y: 108) }
            return nil
        }()
        return ZStack(alignment: .topLeading) {
            // the screen: the game's menu, dimmed while Control Center is over it
            LinearGradient(colors: [MotionBrand.royal, MotionBrand.navyDeep], startPoint: .top, endPoint: .bottom)
            VStack(alignment: .leading, spacing: 4) {
                Text("PLAY").font(MotionBrand.font(.extraBoldItalic, 30)).foregroundStyle(MotionBrand.navyInk)
                    .padding(.horizontal, 10).background(MotionBrand.gold)
                Text("TENNIS · GOLF · BOWLING").font(MotionBrand.font(.semiBold, 8)).foregroundStyle(.white.opacity(0.8))
            }.padding(14).frame(width: w, height: h, alignment: .bottomLeading)
            Color.black.opacity(0.45 * center)
            if center > 0 && !list { controlCenter(w: w, tapped: tileTap).transition(.opacity) }
            if list { tvList(w: w, tapped: tvTap) }
            if let f = finger {
                Circle().fill(.white.opacity(0.85)).frame(width: 26, height: 26)
                    .overlay(Circle().strokeBorder(MotionBrand.gold, lineWidth: 3))
                    .scaleEffect(tileTap || tvTap ? 0.8 : 1)
                    .shadow(color: .black.opacity(0.35), radius: 4, y: 2)
                    .position(f)
            }
        }
        .frame(width: w, height: h)
        .clipShape(RoundedRectangle(cornerRadius: 26, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 26, style: .continuous).strokeBorder(.white, lineWidth: 4))
        .overlay(alignment: .top) { Capsule().fill(.black).frame(width: 46, height: 12).padding(.top, 8) }   // the island
        .shadow(color: MotionBrand.shadowInk.opacity(0.5), radius: 14, y: 10)
    }

    private func controlCenter(w: CGFloat, tapped: Bool) -> some View {
        let tile = (w - 36) / 2
        return VStack(spacing: 8) {
            HStack(spacing: 8) {
                RoundedRectangle(cornerRadius: 14).fill(.white.opacity(0.22)).frame(width: tile, height: tile)
                RoundedRectangle(cornerRadius: 14).fill(.white.opacity(0.22)).frame(width: tile, height: tile)
            }
            HStack(spacing: 8) {
                // Screen Mirroring
                RoundedRectangle(cornerRadius: 12).fill(tapped ? MotionBrand.gold : .white.opacity(0.3)).frame(width: tile / 2 - 4 + tile / 2, height: 34)
                    .overlay(Image(systemName: "rectangle.on.rectangle").font(.system(size: 16, weight: .bold)).foregroundStyle(tapped ? MotionBrand.navyInk : .white))
                    .overlay(RoundedRectangle(cornerRadius: 12).strokeBorder(MotionBrand.gold, lineWidth: tapped ? 0 : 2))
                RoundedRectangle(cornerRadius: 12).fill(.white.opacity(0.22)).frame(width: tile, height: 34)
            }
        }
        .padding(.top, 46).padding(.horizontal, 14)
    }

    private func tvList(w: CGFloat, tapped: Bool) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("Screen Mirroring").font(.system(size: 11, weight: .bold)).foregroundStyle(.white).padding(.bottom, 2)
            row("Living Room TV", picked: tapped)
            row("Bedroom", picked: false)
        }
        .padding(10).frame(width: w - 22, alignment: .leading)
        .background(.white.opacity(0.2), in: RoundedRectangle(cornerRadius: 14))
        .padding(.top, 70).padding(.leading, 11)
    }

    private func row(_ name: String, picked: Bool) -> some View {
        HStack(spacing: 6) {
            Image(systemName: "appletv.fill").font(.system(size: 10, weight: .bold))
            Text(name).font(.system(size: 11, weight: .semibold)).lineLimit(1)
            Spacer(minLength: 0)
            if picked { Image(systemName: "checkmark").font(.system(size: 10, weight: .black)) }
        }
        .foregroundStyle(picked ? MotionBrand.navyInk : .white)
        .padding(.horizontal, 8).frame(height: 26)
        .background(picked ? MotionBrand.gold : .white.opacity(0.12), in: RoundedRectangle(cornerRadius: 8))
    }

    private func smooth(_ x: Double) -> Double { let c = min(1, max(0, x)); return c * c * (3 - 2 * c) }
}

/// The TV button on the menu when it plays on the phone (no TV yet): one tap opens the sheet.
struct ConnectTVChip: View {
    var body: some View {
        Button { TVConnect.shared.present() } label: {
            Label("Connect TV", systemImage: "tv").font(MotionBrand.font(.extraBold, 15)).labelStyle(.titleAndIcon)
                .foregroundStyle(MotionBrand.navyInk).padding(.horizontal, 14).frame(height: 38)
                .background(MotionBrand.gold, in: Capsule()).overlay(Capsule().strokeBorder(.white, lineWidth: 2.5))
                .shadow(color: MotionBrand.shadowInk.opacity(0.4), radius: 6, y: 4)
        }
        .buttonStyle(.plain).accessibilityIdentifier("tv-connect-chip")
    }
}
