import AVFoundation
import SwiftUI
import XCTest
@testable import GolfArcade

/// DAILY SHARE (DailyShareText / DailyShareClips / DailyShareComposer / DailyShare): the Wordle-style message, where each shot
/// is cut, frames from Unity into per-shot files (right way up), the shared clip in both shapes, and the one tap that shares.
@MainActor
final class DailyShareTests: XCTestCase {
    private let example = HoleInOneResult(day: 20261121, total: 2402, shots: [1000, 734, 668], feet: [0, 7.9, 16.1])

    // MARK: the message

    func testMessageIsTheFriendChallenge() {
        XCTAssertEqual(DailyShareText.number(day: 20261115), 1, "the first Daily Hole in One is #1")
        XCTAssertEqual(DailyShareText.number(day: 20261121), 7)
        XCTAssertEqual(DailyShareText.number(day: 20261201), 17, "across a month end")
        XCTAssertEqual(DailyShareText.shortDate(day: 20261121), "NOV 21")
        XCTAssertEqual(DailyShareText.message(example), "I got 2,402 in Daily Hole in One. Same three shots. Your turn.\nhttps://apps.apple.com/app/id6820719910",
                       "the mockup's line, and the link on its own line for destinations that show no preview")
        XCTAssertEqual(DailyShareText.messageBody(example), "I got 2,402 in Daily Hole in One. Same three shots. Your turn.")
        let info = FriendChallengeInfo(day: 20261115, total: 2355)
        XCTAssertEqual(info.longDate, "Nov 15, 2026"); XCTAssertEqual(info.shortDate, "Nov 15"); XCTAssertEqual(info.score, "2,355")
        XCTAssertEqual(DailyShareText.closes, "Closes at midnight ET", "the day changes at 12 midnight Eastern (DailyHoleInOne.day)")
    }

    func testOneSquarePerShot() {
        XCTAssertEqual(DailyShareText.square(points: 1000, feet: 0), "⛳")
        XCTAssertEqual(DailyShareText.square(points: 800, feet: 0.2), "🟩", "a lip-out is not a hole in one")
        XCTAssertEqual(DailyShareText.square(points: 717, feet: 9.9), "🟩")
        XCTAssertEqual(DailyShareText.square(points: 700, feet: 10), "🟨")
        XCTAssertEqual(DailyShareText.square(points: 500, feet: 29.9), "🟨")
        XCTAssertEqual(DailyShareText.square(points: 400, feet: 30), "🟧")
        XCTAssertEqual(DailyShareText.square(points: 0, feet: -1), "🟥", "water, lava or out of bounds")
        XCTAssertEqual(DailyShareText.squares(HoleInOneResult(day: 20261121, total: 1, shots: [0, 1000, 280], feet: [-1, 0, 75])), "🟥⛳🟧")
        XCTAssertEqual(DailyShareText.shotWords(points: 1000, feet: 0), "HOLE IN ONE!")
        XCTAssertEqual(DailyShareText.shotWords(points: 734, feet: 7.94), "7.9 FT")
        XCTAssertEqual(DailyShareText.shotWords(points: 0, feet: -1), "NO SCORE")
        // the text names no hole and no pin: it spoils nothing for a friend
        let text = DailyShareText.message(example)
        for word in ["Cliffside", "Caldera", "Spiral", "hole 8", " ft", "FT"] { XCTAssertFalse(text.contains(word), word) }
    }

    // MARK: where a shot is cut

    func testShotKeepsBackswingToJustAfterTheRest() {
        let url = URL(fileURLWithPath: "/tmp/x.mp4")
        // a short shot: one piece, 1 s before the strike to 1.3 s after the rest
        var clip = DailyShotClip(shot: 0, url: url, contact: 3, rest: 6, end: 9, feet: 4, points: 760, holed: false)
        XCTAssertEqual(clip.keep().count, 1)
        XCTAssertEqual(clip.keep()[0].lowerBound, 2.0, accuracy: 1e-9); XCTAssertEqual(clip.keep()[0].upperBound, 7.3, accuracy: 1e-9)
        // a long flight: the swing and the landing, with a cut between, never longer than 5.6 s
        clip.rest = 12; clip.end = 15
        let parts = clip.keep()
        XCTAssertEqual(parts.count, 2)
        XCTAssertEqual(parts[0].lowerBound, 2.0, accuracy: 1e-9); XCTAssertEqual(parts[0].upperBound, 4.7, accuracy: 1e-9)
        XCTAssertEqual(parts[1].upperBound, 13.3, accuracy: 1e-9)
        XCTAssertEqual(parts[1].lowerBound, 10.4, accuracy: 1e-9)
        XCTAssertLessThanOrEqual(clip.kept, 5.6 + 1e-9)
        // no strike mark: the last seconds before the rest
        clip.contact = nil
        XCTAssertEqual(clip.keep().count, 1)
        XCTAssertEqual(clip.keep()[0].lowerBound, 8.8, accuracy: 1e-9); XCTAssertEqual(clip.keep()[0].upperBound, 13.3, accuracy: 1e-9)
        // no rest: to the end of the file
        clip = DailyShotClip(shot: 0, url: url, contact: 1, rest: nil, end: 4, feet: -1, points: 0, holed: false)
        XCTAssertEqual(clip.keep(), [0.0...4.0])
    }

    // MARK: Unity's frames into the shot files, and the shared clip

    /// A frame as Unity sends it: BGRA, bottom row first. Top half `top`, bottom half `bottom`.
    private func frame(top: (UInt8, UInt8, UInt8), bottom: (UInt8, UInt8, UInt8), w: Int = 320, h: Int = 180) -> [UInt8] {
        var bytes = [UInt8](repeating: 255, count: w * h * 4)
        for row in 0..<h {
            let c = row < h / 2 ? bottom : top   // row 0 is the picture's bottom
            for x in 0..<w { let i = (row * w + x) * 4; bytes[i] = c.2; bytes[i + 1] = c.1; bytes[i + 2] = c.0 }
        }
        return bytes
    }

    /// Plays three shots into `clips` the way Unity's ShotClips does: arm, frames at 30 a second, strike, rest, close.
    private func film(_ clips: DailyShareClips, seconds: Double = 3) async throws -> [DailyShotClip] {
        let done = expectation(description: "three shots closed"); done.expectedFulfillmentCount = 3
        clips.onClip = { _ in done.fulfill() }
        let red = frame(top: (230, 30, 30), bottom: (30, 30, 230))
        var t = 10.0
        for shot in 0..<3 {
            clips.receive(kind: 1, shot: Int32(shot), time: t, feet: 0, points: 0, holed: 0, bgra: nil, width: 0, height: 0, stride: 0)
            let frames = Int(seconds * 30)
            for f in 0..<frames {
                red.withUnsafeBytes { clips.receive(kind: 0, shot: -1, time: t, feet: 0, points: 0, holed: 0, bgra: $0.baseAddress, width: 320, height: 180, stride: 320 * 4) }
                if f == 20 { clips.receive(kind: 2, shot: Int32(shot), time: t, feet: 0, points: 0, holed: 0, bgra: nil, width: 0, height: 0, stride: 0) }
                if f == frames - 30 { clips.receive(kind: 3, shot: Int32(shot), time: t, feet: [0, 7.9, 16.1][shot], points: Int32(example.shots[shot]), holed: shot == 0 ? 1 : 0, bgra: nil, width: 0, height: 0, stride: 0) }
                t += 1.0 / 30
                try await Task.sleep(for: .milliseconds(2))
            }
            clips.receive(kind: 4, shot: Int32(shot), time: t, feet: 0, points: 0, holed: 0, bgra: nil, width: 0, height: 0, stride: 0)
            t += 2
        }
        await fulfillment(of: [done], timeout: 30)
        return clips.finished
    }

    private func pixel(_ url: URL, at seconds: Double, x: Double, y: Double) async throws -> (r: Int, g: Int, b: Int) {
        let gen = AVAssetImageGenerator(asset: AVURLAsset(url: url))
        gen.requestedTimeToleranceBefore = .zero; gen.requestedTimeToleranceAfter = .zero
        let (img, _) = try await gen.image(at: CMTime(seconds: seconds, preferredTimescale: 600))
        var px = [UInt8](repeating: 0, count: 4)
        let ctx = CGContext(data: &px, width: 1, height: 1, bitsPerComponent: 8, bytesPerRow: 4, space: CGColorSpace(name: CGColorSpace.sRGB)!,
                            bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue)!
        ctx.draw(img, in: CGRect(x: -x * Double(img.width), y: -(1 - y) * Double(img.height), width: Double(img.width), height: Double(img.height)))
        return (Int(px[0]), Int(px[1]), Int(px[2]))
    }

    func testFramesBecomeShotFilesTheRightWayUp() async throws {
        let clips = DailyShareClips(); clips.reset()
        let shots = try await film(clips)
        XCTAssertEqual(shots.map(\.shot), [0, 1, 2])
        let first = try XCTUnwrap(shots.first)
        XCTAssertEqual(first.contact ?? -1, 20.0 / 30, accuracy: 0.01, "the strike, in seconds from the shot's first frame")
        XCTAssertEqual(first.rest ?? -1, 60.0 / 30, accuracy: 0.01)
        XCTAssertEqual(first.end, 3, accuracy: 0.05)
        XCTAssertEqual(first.points, 1000); XCTAssertTrue(first.holed)
        XCTAssertEqual(shots[1].feet, 7.9, accuracy: 1e-9); XCTAssertEqual(shots[1].points, 734)
        // Unity's rows come bottom first: the file must show the red half on top
        let top = try await pixel(first.url, at: 1, x: 0.5, y: 0.2), bottom = try await pixel(first.url, at: 1, x: 0.5, y: 0.8)
        XCTAssertGreaterThan(top.r, 150); XCTAssertLessThan(top.b, 90)
        XCTAssertGreaterThan(bottom.b, 150); XCTAssertLessThan(bottom.r, 90)
        // a cancelled shot leaves nothing behind
        clips.receive(kind: 1, shot: 0, time: 100, feet: 0, points: 0, holed: 0, bgra: nil, width: 0, height: 0, stride: 0)
        clips.receive(kind: 5, shot: 0, time: 100, feet: 0, points: 0, holed: 0, bgra: nil, width: 0, height: 0, stride: 0)
        XCTAssertNil(clips.finished.first { $0.shot == 0 }, "re-arming a shot drops its old take")
    }

    func testClipHasTitleShotsAndEndCardInBothShapes() async throws {
        let clips = DailyShareClips(); clips.reset()
        let shots = try await film(clips)
        let card = DailyShareCard(example, top: 8)
        XCTAssertEqual(card.number, 7); XCTAssertEqual(card.date, "NOV 21")
        let dir = FileManager.default.temporaryDirectory.appendingPathComponent("DailyShareTests-\(UUID().uuidString)")
        try FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        for shape in DailyShareShape.allCases {
            let url = try await DailyShareComposer.compose(clips: shots, card: card, shape: shape, to: dir.appendingPathComponent("\(shape).mp4"))
            let asset = AVURLAsset(url: url)
            let tracks = try await asset.loadTracks(withMediaType: .video)
            let track = try XCTUnwrap(tracks.first)
            let size = try await track.load(.naturalSize)
            XCTAssertEqual(Int(size.width), shape.size.width); XCTAssertEqual(Int(size.height), shape.size.height)
            let duration = try await asset.load(.duration).seconds
            let expected = DailyShareComposer.titleSeconds + DailyShareComposer.endSeconds + shots.reduce(0) { $0 + $1.kept }
            XCTAssertEqual(duration, expected, accuracy: 0.35, "\(shape): title + the kept shots + the end card")
            XCTAssertLessThan(duration, 22, "a share clip stays short")
            // a shot frame is the game picture (red over blue); the end card is the navy card
            let inShot = try await pixel(url, at: DailyShareComposer.titleSeconds + 0.5, x: 0.5, y: shape == .wide ? 0.3 : 0.42)
            XCTAssertGreaterThan(inShot.r, 150, "\(shape): the shot's picture")
            let end = try await pixel(url, at: duration - 0.2, x: 0.05, y: 0.5)
            XCTAssertLessThan(end.r, 60); XCTAssertGreaterThan(end.b, 60, "\(shape): the navy end card")
        }
        try? FileManager.default.removeItem(at: dir)
    }

    // MARK: the one tap

    private let instagram = UIActivity.ActivityType("com.burbn.instagram.shareextension")
    private let tiktok = UIActivity.ActivityType("com.zhiliaoapp.musically.ShareExtension")
    private let x = UIActivity.ActivityType("com.atebits.Tweetie2.ShareExtension")
    private let whatsapp = UIActivity.ActivityType("net.whatsapp.WhatsApp.ShareExtension")

    func testWithNoClipTheCardGoesEverywhere() throws {
        let share = DailyShare()
        share.includeClip = false
        var presented: [[Any]] = []; var copied: [String] = []
        share.present = { items, _ in presented.append(items) }
        share.copy = { copied.append($0) }
        share.begin(day: 20261121)
        XCTAssertEqual(share.phase, .idle, "the clip is off: nothing is filmed")
        share.share()
        XCTAssertTrue(presented.isEmpty, "nothing to share before the round is scored")
        share.finished(example)
        share.share()
        let items = try XCTUnwrap(presented.first)
        XCTAssertEqual(presented.count, 1, "one tap, one sheet")
        XCTAssertEqual(items.count, 2, "the card and the message")
        let card = try XCTUnwrap(items.first as? DailyShareCardItem)
        let sheet = UIActivityViewController(activityItems: [], applicationActivities: nil)
        XCTAssertEqual(card.activityViewController(sheet, itemForActivityType: instagram) as? URL, card.card, "no clip: the card goes to the socials too")
        let image = try XCTUnwrap(UIImage(contentsOfFile: card.card.path))
        XCTAssertEqual(image.size.width * image.scale, 1052, accuracy: 1, "the 526-point card at 2×")
        let text = try XCTUnwrap(items.last as? DailyShareTextItem)
        XCTAssertEqual(text.message, DailyShareText.message(example))
        XCTAssertEqual(share.messagePreview, "I got 2,402 in Daily Hole in One. Same three shots. Your turn.")
        share.copyLink()
        XCTAssertEqual(copied, ["https://apps.apple.com/app/id6820719910"], "Copy challenge link")
    }

    /// Adnan 11-21: "for messages card only, for socials it should include the 3 clips cut together".
    func testMessagesGetTheCardSocialsGetTheClip() async throws {
        let share = DailyShare()
        let clips = DailyShareClips()
        share.clips = clips; share.includeClip = true
        var presented: [[Any]] = []
        share.present = { items, _ in presented.append(items) }
        share.copy = { _ in }
        share.top = { 8 }
        share.begin(day: 20261121)
        XCTAssertEqual(share.phase, .filming)
        _ = try await film(clips)
        share.finished(example)
        share.share()   // tapped while the clip is being made: the sheet opens when it is ready
        XCTAssertTrue(presented.isEmpty)
        XCTAssertTrue(share.shareTitle.hasPrefix("Making your clip"))
        for _ in 0..<300 where presented.isEmpty { try await Task.sleep(for: .milliseconds(100)) }
        XCTAssertEqual(share.phase, .ready)
        XCTAssertEqual(share.shareTitle, "Share challenge")
        let items = try XCTUnwrap(presented.first)
        XCTAssertEqual(presented.count, 1, "one tap, one sheet")
        let card = try XCTUnwrap(items.compactMap { $0 as? DailyShareCardItem }.first)
        let video = try XCTUnwrap(items.compactMap { $0 as? DailyShareVideoItem }.first)
        let text = try XCTUnwrap(items.compactMap { $0 as? DailyShareTextItem }.first)
        let sheet = UIActivityViewController(activityItems: [], applicationActivities: nil)
        func gets(_ type: UIActivity.ActivityType) -> (card: Bool, clip: URL?, text: Bool) {
            (card.activityViewController(sheet, itemForActivityType: type) != nil,
             video.activityViewController(sheet, itemForActivityType: type) as? URL,
             text.activityViewController(sheet, itemForActivityType: type) != nil)
        }
        // Messages and the other messengers: the card and the message, no clip
        for type in [UIActivity.ActivityType.message, .mail, .airDrop, whatsapp] {
            let g = gets(type); XCTAssertTrue(g.card, type.rawValue); XCTAssertNil(g.clip, type.rawValue); XCTAssertTrue(g.text, type.rawValue)
        }
        // the socials: the three shots cut together and the message, no card
        for type in [instagram, tiktok, x] {
            let g = gets(type); XCTAssertFalse(g.card, type.rawValue); XCTAssertNotNil(g.clip, type.rawValue); XCTAssertTrue(g.text, type.rawValue)
        }
        XCTAssertEqual(gets(x).clip, share.wide, "X gets the wide clip")
        for _ in 0..<1200 where share.tall == nil { try await Task.sleep(for: .milliseconds(100)) }
        XCTAssertEqual(gets(instagram).clip, share.tall, "Instagram and TikTok get the tall clip once it is made")
        XCTAssertEqual(gets(tiktok).clip, share.tall)
        // Photos keeps both, without the message
        let photos = gets(.saveToCameraRoll)
        XCTAssertTrue(photos.card); XCTAssertNotNil(photos.clip); XCTAssertFalse(photos.text)
    }

    func testWithNoFootageTheCardStillGoes() throws {
        let share = DailyShare()
        share.clips = DailyShareClips(); share.includeClip = true
        var presented: [[Any]] = []
        share.present = { items, _ in presented.append(items) }
        share.copy = { _ in }
        share.begin(day: 20261121)
        share.finished(example)
        share.share()
        XCTAssertEqual(presented.count, 1, "no footage: the card and the message at once, one sheet")
        XCTAssertEqual(share.phase, .failed)
        XCTAssertNotNil(presented.first?.first as? DailyShareCardItem)
        XCTAssertFalse(presented.first?.contains { $0 is DailyShareVideoItem } ?? true)
    }

    func testTallClipGoesToTikTokAndInstagram() {
        XCTAssertTrue(DailyShareVideoItem.wantsTall(UIActivity.ActivityType("com.burbn.instagram.shareextension")))
        XCTAssertTrue(DailyShareVideoItem.wantsTall(UIActivity.ActivityType("com.zhiliaoapp.musically.ShareExtension")))
        XCTAssertFalse(DailyShareVideoItem.wantsTall(.message))
        XCTAssertFalse(DailyShareVideoItem.wantsTall(.saveToCameraRoll))
        XCTAssertFalse(DailyShareVideoItem.wantsTall(UIActivity.ActivityType("com.atebits.Tweetie2.ShareExtension")), "X takes the wide clip")
        XCTAssertFalse(DailyShareVideoItem.wantsTall(nil))
    }

    // MARK: screen proof (DS_SNAP_DIR, else tmp/daily-share)

    /// The Friend Challenge on the phone: the round-done card's CHALLENGE A FRIEND, the sheet, and the card that is shared.
    func testFriendChallengeSnapshots() async throws {
        let s = SportsSession.shared, share = DailyShare.shared
        let saved = (s.sport, s.golfCourse, s.ready, s.paused, s.setupStage, s.golfPhase)
        defer {
            s.sport = saved.0; s.golfCourse = saved.1; s.ready = saved.2; s.paused = saved.3; s.setupStage = saved.4; s.golfPhase = saved.5
            s.debugSetHoleInOneDay(0); s.debugPhonePlay(false); share.debugShow(nil)
        }
        s.sport = "golf"; s.golfCourse = "magma"; s.ready = true; s.paused = false; s.setupStage = .playing
        s.debugSetHoleInOneDay(20261115); s.golfPhase = "RoundDone"
        var r = GolfControllerReading.waiting
        r.hole = 3; r.name = "Daily"; r.par = 3; r.yards = 50; r.wind = 0; r.clubIndex = 0; r.clubName = "Lob Wedge"; r.clubYards = 50
        s.golfController = r
        // the mockup's sample day: Nov 15, 1,000 + 718 + 637
        share.debugShow(HoleInOneResult(day: 20261115, total: 2355, shots: [1000, 718, 637], feet: [0, 7.9, 16.1]))
        try await save(GolfPhoneController(session: s), "01-round-done-challenge-a-friend")
        try await save(FriendChallengeSheet(share: share), "02-challenge-a-friend-sheet")
        share.debugShow(share.result, phase: .making(0.6), waiting: true)
        try await save(FriendChallengeSheet(share: share), "02b-sheet-making-the-clip")
        share.debugShow(share.result)
        let info = try XCTUnwrap(share.info)
        try await save(FriendChallengeCard(info: info, bubble: false).fixedSize(), "03-shared-card", size: CGSize(width: FriendChallengeCard.width, height: FriendChallengeCard.cardHeight))
        if let png = FriendChallengeCard.image(info)?.pngData() { try png.write(to: snapFolder.appendingPathComponent("04-shared-card-2x.png")) }
        s.debugPhonePlay(true)
        try await save(GolfPhoneController(session: s), "05-handheld-round-done", size: CGSize(width: 874, height: 402))
        s.debugPhonePlay(false); s.debugSetHoleInOneDay(0)
        try await save(GolfPhoneController(session: s), "06-ordinary-round-no-challenge")
    }

    private var snapFolder: URL { URL(fileURLWithPath: ProcessInfo.processInfo.environment["DS_SNAP_DIR"] ?? NSTemporaryDirectory() + "daily-share", isDirectory: true) }

    private func save<V: View>(_ view: V, _ name: String, size: CGSize = CGSize(width: 402, height: 874)) async throws {
        let folder = URL(fileURLWithPath: ProcessInfo.processInfo.environment["DS_SNAP_DIR"] ?? NSTemporaryDirectory() + "daily-share", isDirectory: true)
        try FileManager.default.createDirectory(at: folder, withIntermediateDirectories: true)
        let scene = try XCTUnwrap(UIApplication.shared.connectedScenes.compactMap { $0 as? UIWindowScene }.first)
        let host = UIHostingController(rootView: view)
        let window = UIWindow(windowScene: scene)
        window.frame = CGRect(origin: .zero, size: size); window.rootViewController = host; window.isHidden = false
        host.view.frame = window.bounds; host.view.layoutIfNeeded()
        try await Task.sleep(for: .seconds(0.8))
        let image = UIGraphicsImageRenderer(size: size).image { _ in host.view.drawHierarchy(in: window.bounds, afterScreenUpdates: true) }
        try XCTUnwrap(image.pngData()).write(to: folder.appendingPathComponent("\(name).png"))
        window.isHidden = true
    }
}
