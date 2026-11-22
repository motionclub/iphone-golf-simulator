import Observation
import SwiftUI
import UIKit

// DAILY SHARE (Adnan 2026-11-21): after the Daily Hole in One, "Challenge a friend" opens THE FRIEND CHALLENGE sheet
// (FriendChallenge.swift; mockup ArtDir/ui/daily-challenge-ui-mockups/concepts/03-friend-challenge.html). Share challenge sends
// the invite card as a picture and the message with the link, to Messages, Instagram, TikTok, X, Photos and the rest; Copy
// challenge link puts the link on the clipboard. Proof: work/daily-share-1121.
//
// Where it goes decides what goes (Adnan 11-21: "for messages card only, for socials it should include the 3 clips cut together"):
// Messages, Mail, WhatsApp, AirDrop get the card and the message; Instagram, TikTok, Snapchat, YouTube, X, Facebook and Threads
// get the three shots cut into one clip (ShotClips.cs → DailyShareClips → DailyShareComposer) and the message; Save to Photos
// keeps both. The tall clip goes to the phone-shaped apps, the wide one to X and Facebook.

@MainActor @Observable
final class DailyShare {
    static let shared = DailyShare()
    /// Film the shots and send the clip to the social apps (the card alone goes to Messages).
    static let includeClip = true

    enum Phase: Equatable { case idle, filming, making(Double), ready, failed }
    private(set) var phase: Phase = .idle
    /// This run's result (a same-day replay shares the run just played).
    private(set) var result: HoleInOneResult?
    private(set) var wide: URL?
    private(set) var tall: URL?
    /// Share was tapped while the clip was still being made: the sheet opens as soon as it is ready.
    private(set) var waitingToShare = false
    @ObservationIgnored private var composing: Task<Void, Never>?
    /// Seams for tests.
    @ObservationIgnored var clips: DailyShareClips = .shared
    @ObservationIgnored var includeClip = DailyShare.includeClip
    @ObservationIgnored var present: @MainActor ([Any], String) -> Void = DailyShare.presentSheet
    @ObservationIgnored var copy: @MainActor (String) -> Void = { UIPasteboard.general.string = $0 }
    @ObservationIgnored var top: @MainActor () -> Int? = { DailyHoleInOne.shared.standing?.top }

    init() {}

    var info: FriendChallengeInfo? { result.map { FriendChallengeInfo(day: $0.day, total: $0.total) } }
    /// The message that is shared: the Friend Challenge line and the link.
    var message: String? { result.map { DailyShareText.message($0) } }
    /// The message as the sheet previews it (the mockup's "Message preview", without the link).
    var messagePreview: String? { result.map { DailyShareText.messageBody($0) } }
    var link: String { DailyShareText.appLink }

    /// A Daily Hole in One is starting.
    func begin(day: Int) {
        composing?.cancel(); composing = nil
        result = nil; wide = nil; tall = nil; waitingToShare = false
        phase = includeClip ? .filming : .idle
        guard includeClip else { return }
        clips.reset()
        clips.onClip = { [weak self] _ in Task { @MainActor in self?.clipArrived() } }
        clips.install()
    }
    /// Unity may load after `begin`: try the plugin again on its events (a no-op once installed).
    func unityEvent() { if includeClip, phase == .filming { clips.install() } }

    /// Unity's "holeInOne" event: the three shots are scored.
    func finished(_ result: HoleInOneResult) {
        self.result = result
        guard includeClip else { return }
        if phase == .idle { phase = .filming }
        clipArrived()
        Task { @MainActor in
            try? await Task.sleep(for: .seconds(4))
            if phase == .filming, self.result == result { makeClip() }
        }
    }

    // MARK: share

    /// Share challenge: the card for Messages, the clip for the social apps, the message for all of them. A tap while the clip
    /// is still being made opens the sheet when it is ready; with no footage the card goes everywhere.
    func share() {
        guard let message, let info else { return }
        if includeClip {
            switch phase {
            case .making: waitingToShare = true; return
            case .filming: waitingToShare = true; makeClip(); return   // (with no footage, makeClip shares the card at once)
            default: break
            }
        }
        waitingToShare = false
        var items: [Any] = []
        let clip = includeClip ? wide : nil
        if let card = Self.cardFile(info) { items.append(DailyShareCardItem(card: card, clipToSocials: clip != nil)) }
        if let clip { items.append(DailyShareVideoItem(wide: clip, tall: { [weak self] in self?.tall })) }
        items.append(DailyShareTextItem(message: message))
        present(items, message)
    }
    /// What Share challenge says while the clip is being made for it.
    var shareTitle: String {
        guard waitingToShare else { return "Share challenge" }
        if case .making(let p) = phase { return "Making your clip… \(Int(p * 100))%" }
        return "Making your clip…"
    }
    /// Copy challenge link.
    func copyLink() { copy(link) }

    /// The card as a PNG in tmp/DailyShare ("MotionSports-Daily-Hole-in-One-Nov-15.png").
    static func cardFile(_ info: FriendChallengeInfo) -> URL? {
        guard let data = FriendChallengeCard.image(info)?.pngData() else { return nil }
        let url = DailyShareClips.folder.appendingPathComponent("MotionSports-Daily-Hole-in-One-\(DailyShareText.formatted(day: info.day, "MMM-d")).png")
        do { try data.write(to: url); return url } catch { return nil }
    }

    // MARK: the clip (off by default)

    private func clipArrived() {
        guard result != nil, phase == .filming else { return }
        if clips.finished.count >= DailyHoleInOne.shotCount { makeClip() }
    }
    private func makeClip() {
        guard let result, phase == .filming else { return }
        let shots = clips.finished
        guard !shots.isEmpty else { phase = .failed; if waitingToShare { share() }; return }
        phase = .making(0)
        let card = DailyShareCard(result, top: top())
        let folder = DailyShareClips.folder
        composing = Task.detached(priority: .userInitiated) { [weak self] in
            do {
                let wide = try await DailyShareComposer.compose(clips: shots, card: card, shape: .wide, to: folder.appendingPathComponent("MotionSports-Daily-\(card.number).mp4")) { p in
                    Task { @MainActor in self?.progress(p) }
                }
                await self?.made(wide: wide)
            } catch {
                NSLog("[DailyShare] clip failed: %@", String(describing: error))
                await self?.made(wide: nil)
                return
            }
            if let tall = try? await DailyShareComposer.compose(clips: shots, card: card, shape: .tall, to: folder.appendingPathComponent("MotionSports-Daily-\(card.number)-tall.mp4")) {
                await self?.madeTall(tall)
            }
        }
    }
    private func progress(_ p: Double) { if case .making = phase { phase = .making(p) } }
    private func madeTall(_ url: URL) { tall = url }
    func made(wide: URL?) {
        self.wide = wide; phase = wide == nil ? .failed : .ready
        if waitingToShare { share() }
    }

    #if DEBUG
    /// For screen proofs and tests: a finished round without Unity.
    func debugShow(_ result: HoleInOneResult?, phase: Phase = .idle, waiting: Bool = false) { self.result = result; self.phase = phase; waitingToShare = waiting }
    #endif

    // MARK: the share sheet

    static func presentSheet(_ items: [Any], _ message: String) {
        let sheet = UIActivityViewController(activityItems: items, applicationActivities: nil)
        sheet.completionWithItemsHandler = { type, done, _, error in
            Analytics.track("daily_share", ["to": type?.rawValue ?? "none", "done": done ? "1" : "0", "error": error.map { "\($0)" } ?? ""])
        }
        guard let host = topController() else { return }
        if let pop = sheet.popoverPresentationController { pop.sourceView = host.view; pop.sourceRect = CGRect(x: host.view.bounds.midX, y: host.view.bounds.maxY - 80, width: 1, height: 1) }
        host.present(sheet, animated: true)
    }
    private static func topController() -> UIViewController? {
        let scenes = UIApplication.shared.connectedScenes.compactMap { $0 as? UIWindowScene }
        let window = scenes.filter { $0.session.role == .windowApplication }.flatMap(\.windows).first { $0.isKeyWindow }
            ?? scenes.flatMap(\.windows).first { $0.windowScene?.session.role == .windowApplication }
        var top = window?.rootViewController
        while let next = top?.presentedViewController { top = next }
        return top
    }
}

/// Where a share goes.
enum DailyShareDestination {
    /// The social apps get the clip (their activity types are their share extensions' bundle ids, or Apple's post types).
    nonisolated static func isSocial(_ type: UIActivity.ActivityType?) -> Bool {
        guard let type else { return false }
        let id = type.rawValue.lowercased()
        return DailyShareVideoItem.wantsTall(type)
            || ["twitter", "tweetie", "facebook", "barcelona", "threads", "reddit", "linkedin"].contains { id.contains($0) }
    }
}

/// The invite card: Messages and the rest, and Photos; not the social apps when they get the clip instead.
@MainActor final class DailyShareCardItem: NSObject, @preconcurrency UIActivityItemSource {
    let card: URL
    let clipToSocials: Bool
    init(card: URL, clipToSocials: Bool) { self.card = card; self.clipToSocials = clipToSocials }
    func activityViewControllerPlaceholderItem(_ controller: UIActivityViewController) -> Any { card }
    func activityViewController(_ controller: UIActivityViewController, itemForActivityType type: UIActivity.ActivityType?) -> Any? {
        clipToSocials && DailyShareDestination.isSocial(type) ? nil : card
    }
    func activityViewController(_ controller: UIActivityViewController, dataTypeIdentifierForActivityType type: UIActivity.ActivityType?) -> String { "public.png" }
}

/// The three shots cut together: the social apps (tall for the phone-shaped ones, wide for X and Facebook) and Photos.
@MainActor final class DailyShareVideoItem: NSObject, @preconcurrency UIActivityItemSource {
    let wide: URL
    /// The tall clip, once made (asked when a destination is picked; until then the wide one goes everywhere).
    let tall: @MainActor () -> URL?
    init(wide: URL, tall: @escaping @MainActor () -> URL?) { self.wide = wide; self.tall = tall }
    /// Instagram, TikTok, Snapchat and YouTube take the tall clip (their activity types are their bundle ids' extensions).
    nonisolated static func wantsTall(_ type: UIActivity.ActivityType?) -> Bool {
        guard let id = type?.rawValue.lowercased() else { return false }
        return ["instagram", "tiktok", "musically", "zhiliaoapp", "snapchat", "youtube"].contains { id.contains($0) }
    }
    func activityViewControllerPlaceholderItem(_ controller: UIActivityViewController) -> Any { wide }
    func activityViewController(_ controller: UIActivityViewController, itemForActivityType type: UIActivity.ActivityType?) -> Any? {
        guard DailyShareDestination.isSocial(type) || type == .saveToCameraRoll else { return nil }   // Messages: the card only
        guard Self.wantsTall(type) else { return wide }
        return tall() ?? wide
    }
    func activityViewController(_ controller: UIActivityViewController, dataTypeIdentifierForActivityType type: UIActivity.ActivityType?) -> String { "public.mpeg-4" }
}

/// The message (Messages, X, Mail, WhatsApp…). Not added to a saved photo.
@MainActor final class DailyShareTextItem: NSObject, @preconcurrency UIActivityItemSource {
    let message: String
    init(message: String) { self.message = message }
    func activityViewControllerPlaceholderItem(_ controller: UIActivityViewController) -> Any { message }
    func activityViewController(_ controller: UIActivityViewController, itemForActivityType type: UIActivity.ActivityType?) -> Any? {
        type == .saveToCameraRoll ? nil : message
    }
    func activityViewController(_ controller: UIActivityViewController, subjectForActivityType type: UIActivity.ActivityType?) -> String {
        "Beat my score in Daily Hole in One"
    }
}
