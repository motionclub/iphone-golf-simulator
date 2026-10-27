import AVFoundation
import SwiftUI

/// One illustrated how-to card: a title, a few short steps, and a small animated diagram.
struct HowToCard: Identifiable, Equatable {
    enum Art: Equatable { case mirror, mac, stand, swing, backhand, serve, golfStance, golfSwing, golfAim, golfClubs }
    let id: String
    let title: String
    let steps: [String]
    let art: Art
    /// The SF Symbol beside the title in the guide.
    var icon = "lightbulb.fill"
}

/// The how-to guide (main menu → How to play) and the cards the loading screen cycles through.
enum HowTo {
    static let connectTV = HowToCard(id: "tv", title: "Connect to your TV", steps: [
        "Open Control Center on your iPhone (swipe down from the top right).",
        "Tap Screen Mirroring and choose your Apple TV or AirPlay TV.",
        "Keep the phone unlocked and on the same Wi-Fi — it is your racket.",
    ], art: .mirror, icon: "tv")
    static let connectMac = HowToCard(id: "mac", title: "Play on a MacBook", steps: [
        "On the Mac: System Settings → General → AirDrop & Handoff → turn on AirPlay Receiver.",
        "On the iPhone: Control Center → Screen Mirroring → choose the Mac.",
        "Put the Mac where you can see it from 2 m away, full screen, lid open.",
    ], art: .mac, icon: "laptopcomputer")
    static let stand = HowToCard(id: "stand", title: "Stand and hold", steps: [
        "Stand about 2 m back, facing the screen, with room to swing.",
        "Hold the phone like a racket handle, screen facing the TV for forehands.",
        "Point the back of the phone at the TV once to lock the court direction.",
    ], art: .stand, icon: "figure.stand")
    static let swing = HowToCard(id: "swing", title: "Forehand", steps: [
        "Your player runs to the ball, and sprints on its own for a hard one.",
        "Swing as the ball rises to the top of its bounce.",
        "The ball goes where you swing: face the racket left, straight or right as you hit. Timing sets the pace.",
    ], art: .swing)
    static let backhand = HowToCard(id: "backhand", title: "Backhand", steps: [
        "Ball on your other side? Turn the phone so the camera faces the TV.",
        "Swing across your body — the game picks the side from where the ball is.",
        "Timing beats a harder swing: right on the ball flies fastest.",
    ], art: .backhand)
    static let serve = HowToCard(id: "serve", title: "Serve", steps: [
        "Press TOSS as the meter crosses the middle — green is a perfect toss.",
        "Swing down hard as the ball peaks.",
        "Every serve you swing at goes in. Hit it at the very top for a rocket serve.",
    ], art: .serve)

    static let pages = [connectTV, connectMac, stand, swing, backhand, serve]

    /// What the loading screen cycles through for a sport.
    static func loadingCards(_ sport: Sport) -> [HowToCard] {
        sport == .golf ? [connectTV, connectMac] + GolfLesson.cards : pages
    }
}

// MARK: - Loading tips

/// One tip for the loading screen. `kind` is its topic ("Technique", "Setup"…), `title` the card's headline.
struct GameTip: Equatable {
    enum Kind: String {
        case technique, strategy, setup, party
        var title: String {
            switch self { case .technique: "Technique"; case .strategy: "Strategy"; case .setup: "Setup"; case .party: "Party" }
        }
    }
    let kind: Kind
    let title: String
    let text: String
}

/// What the loading screen teaches. Every line here is checked against how the game plays:
/// distance in golf comes from the length of the backswing (speed only has to be committed),
/// and tennis shot quality is mostly timing.
enum GameTips {
    static func tips(for sport: Sport) -> [GameTip] {
        switch sport { case .golf: golf; case .bowling: bowling; default: tennis }
    }
    /// Any index; it wraps, so a caller can keep counting.
    static func tip(_ sport: Sport, at index: Int) -> GameTip {
        let all = tips(for: sport)
        return all[((index % all.count) + all.count) % all.count]
    }

    private static func t(_ kind: GameTip.Kind, _ title: String, _ text: String) -> GameTip { GameTip(kind: kind, title: title, text: text) }

    static let golf: [GameTip] = [
        t(.technique, "Backswing sets distance", "How far back you take the phone sets the distance: hip-high is about 60%, up behind you is full power."),
        t(.technique, "Smooth beats hard", "You don't have to swing hard. A smooth, committed swing through the ball carries full distance."),
        t(.technique, "Tap, then swing", "Tap the swing button and swing: it starts at once, from wherever you are holding the phone. Tap it again to cancel."),
        t(.technique, "Free do-overs", "Tap the button again, or stop short on the way through, and the swing resets with no stroke lost. Tap it and go again."),
        t(.technique, "Shape your shot", "Twisting the phone open or closed bends the ball: open slices right, closed hooks left."),
        t(.technique, "Square the face", "Keep the phone's face square. A twist of more than about 10° starts to curve the shot."),
        t(.technique, "Smooth tempo", "Smooth tempo, a square face and a committed swing together earn a PERFECT strike."),
        t(.technique, "Commit to it", "A tentative downswing is graded THIN and flies low. Take it back, then go through."),
        t(.technique, "Line up first", "Touching the aim pad or club arrows after you tap resets the swing. Line up first, then tap the button."),
        t(.technique, "Tiny putts", "Putting uses tiny strokes. A 3-foot putt is only about a fifth of a full putting stroke."),
        t(.strategy, "Read the wind", "Check the wind arrow and MPH badge before you pick a club, and aim off for a strong crosswind."),
        t(.strategy, "Play it safe", "Water and lava cost a stroke. Play short of trouble with a safer club."),
        t(.strategy, "Stay in bounds", "Out of bounds costs a stroke and you replay from the same spot. Aim away from the edges."),
        t(.strategy, "Escape the sand", "Bunkers rob most clubs of about 40% of their speed. Take a wedge and just get out."),
        t(.strategy, "Club up in the rough", "Rough takes 10–15% off your swing. Take one more club than the yardage says."),
        t(.strategy, "Know your clubs", "Full-swing yards: Driver 240, Hybrid 190, 5 Iron 175, 7 Iron 150, 9 Iron 125, Pitching Wedge 100."),
        t(.strategy, "Read the break", "On the green, the beads on the slope grid drift the way the ball will break. Read them before you putt."),
        t(.strategy, "Mind the ice", "Frozen lakes are slick. A ball landing on the ice keeps skidding, so land short of it."),
        t(.strategy, "Avoid obstacles", "Trees, rocks, walls and windmill blades knock the ball. Aim to miss them."),
        t(.setup, "Give yourself room", "Clear a full swing's room around you, and keep the phone in a firm grip."),
        t(.setup, "Any grip works", "Any grip works in golf. Tapping the swing button learns how you hold the phone, so pick a stance that's comfortable."),
        t(.setup, "Get on the TV", "Mirror your phone first: Control Center → Screen Mirroring, then pick your TV or Mac."),
        t(.setup, "Play on a Mac", "Playing on a Mac? Turn on AirPlay Receiver in System Settings → General → AirDrop & Handoff."),
        t(.party, "Who plays next", "In party golf, everyone tees off first. After that, whoever is farthest from the hole plays next."),
        t(.party, "Stay ready", "A party turn left idle for 60 seconds costs a stroke, so keep the phone ready."),
        t(.party, "React with emotes", "Waiting for your turn? Tap an emote to react while a friend's shot is in the air."),
    ]

    /// Bowling (PLAN_PhonePlay §5, bowling V2): the bowler walks up at a steady pace and you swing with them; the swing makes power,
    /// letting go as your arm passes the bottom makes control, and a wrist turn at release makes the hook.
    static let bowling: [GameTip] = [
        t(.technique, "Hold, then swing", "Press and hold the ball, then swing with your bowler's steps: push away, back, and through."),
        t(.technique, "Let go at the bottom", "Let go just as your arm swings through the bottom, by your ankle. That's a PERFECT release."),
        t(.technique, "Add some hook", "Turn your wrist into a handshake as you let go to curve the ball into the pocket."),
        t(.technique, "Straight is fine", "No wrist turn rolls the ball straight. Turn the other way for a backup ball."),
        t(.technique, "Feel the swing", "Your phone ticks at the top of your backswing and buzzes as your arm comes through the bottom: let go then."),
        t(.technique, "Don't hang on", "Hold on as your arm rises and the ball goes late: lofted and pulled off line."),
        t(.technique, "Not too early", "Let go in your first steps, before you swing, and the ball drops behind you. That ball counts zero."),
        t(.strategy, "Hit the pocket", "Aim between the 1 and 3 pins (1 and 2 if you bowl left-handed). A hook carries more pins there."),
        t(.strategy, "Pick up spares", "Move along the approach to line up with the pins left standing before you throw again."),
        t(.setup, "Give yourself room", "Clear some space around you and keep a firm grip on the controller."),
        t(.party, "Pass the phone", "Taking turns? Pass the phone between frames, after the ball comes back."),
        t(.party, "No TV? No problem", "Bowling plays right on your phone: the lane fills the screen and the ball sits at the bottom."),
        t(.strategy, "Beat the computer", "Exhibition pits you against Rookie Ray, Steady Sam, Lucky Lou or Pro Pia. Pick on the venue screen."),
    ]

    static let tennis: [GameTip] = [
        t(.technique, "Time it with the rings", "Swing as the rings close on the ball. Shot quality is mostly timing, not effort."),
        t(.technique, "On time beats hard", "Swing effort barely changes the pace. A smooth swing on time beats a hard swing that's late."),
        t(.technique, "Early or late?", "The TV shows EARLY or LATE after a mistimed hit, and its speed. Right on the ball is your fastest shot."),
        t(.technique, "It learns your lag", "Swinging LATE every time? Keep playing: the game learns your lag in three or four swings."),
        t(.technique, "Aim with your swing", "The ball goes where you swing: finish with the racket face toward the left, middle or right of the screen."),
        t(.technique, "Hit it deep", "Timing picks the depth too: on the ball lands deep, a mistimed swing sits up short for your opponent."),
        t(.technique, "No grip change", "The side the ball is on picks forehand or backhand, so you don't need to flip your grip."),
        t(.technique, "Add topspin", "A low, flat swing slices. A swing with lift hits topspin."),
        t(.technique, "Supercharge it", "Three GREAT hits in a row charge a SUPERCHARGED shot: faster and almost dead accurate."),
        t(.technique, "Toss it true", "Serving: tap TOSS exactly as the meter's ticker crosses the middle. Off-centre tosses scatter the ball."),
        t(.technique, "Serve at the peak", "After the toss, swing as the power bar peaks for a rocket serve. Off the peak it still goes in, just slower."),
        t(.strategy, "Auto-run", "Your player runs for you, and sprints on its own for a ball that is hard to reach."),
        t(.strategy, "Just swing", "Your player always gets to the ball. Your job is when you swing and which way."),
        t(.strategy, "Dive as a last resort", "Dive saves a wide ball but costs stamina and needs a couple of seconds to recharge. Use it as a last resort."),
        t(.strategy, "Save your stamina", "Stamina drains while you sprint and refills when you stand still. Recover between points."),
        t(.strategy, "Push them back", "Deep balls push your opponent back; short balls invite an attack."),
        t(.strategy, "Mix it up", "Stronger rivals hunt your weaker side. Mix up your shots."),
        t(.strategy, "Recover to the middle", "Get back toward the middle of the court after every shot."),
        t(.strategy, "Work the corners", "Left, then right: a clean hit into one corner and then the other runs your rival ragged. Swing way too early or late and it sails out."),
        t(.strategy, "Celebrate", "Win a point? Tap an emote on your phone to celebrate."),
        t(.setup, "Court scan", "For the court scan, stand about 2.5 m from the screen with the rear camera pointing at it."),
        t(.setup, "Keep tracking clear", "Blank walls or a covered lens can stop tracking. Keep the rear camera clear and the room lit."),
        t(.setup, "Fix TV delay", "TV picture delayed? Turn on your TV's Game Mode, then run Settings → Controls → Swing timing check."),
        t(.setup, "Moved the TV?", "Moved the TV? Settings → Controls → Court direction → Set again."),
        t(.setup, "Lefty?", "Left-handed? Set Plays to Left in Settings → Controls."),
        t(.setup, "Fit the screen", "TV cropping the picture? Settings → Display → Screen edge margin pulls it back in."),
        t(.setup, "Phone = racket", "Keep your phone unlocked and in your hand. It is your racket."),
        t(.setup, "Pausing", "To pause during a point, hold the pause icon for about half a second."),
    ]
}

// MARK: - The guide (Settings → Guide)

/// A topic in Settings → Guide: a short deck of cards, paged on the How to Play screen.
enum GuideDeck: String, CaseIterable, Identifiable {
    case golf, tennis, setup, better
    var id: String { rawValue }
    var rowID: String { "guide-\(rawValue)" }
    init?(rowID: String) {
        guard rowID.hasPrefix("guide-"), let deck = GuideDeck(rawValue: String(rowID.dropFirst(6))) else { return nil }
        self = deck
    }
    var title: String {
        switch self {
        case .golf: "How to Play Golf"; case .tennis: "How to Play Tennis"
        case .setup: "Setup & Troubleshooting"; case .better: "Play Better"
        }
    }
    var detail: String {
        switch self {
        case .golf: "Aiming, tap to swing, power, clubs, wind and putting."
        case .tennis: "Timing, aiming, serving, diving and scoring."
        case .setup: "Connect a screen, set up each game, and fix common problems."
        case .better: "Habits and best practices that help in both games."
        }
    }
    var cards: [HowToCard] {
        switch self {
        case .golf: HowTo.golfGuide
        case .tennis: HowTo.tennisGuide
        case .setup: HowTo.setupGuide
        case .better: HowTo.betterGuide
        }
    }
}

extension HowTo {
    static let golfGuide: [HowToCard] = [
        HowToCard(id: "gg-goal", title: "The goal", steps: [
            "Play every hole in as few strokes as you can. The lowest total wins.",
            "Each hole has a par, the strokes a good player takes. Your score shows against par: E, +1, −1 and so on.",
            "A round is one whole course: Cliffside and Magma Open have 5 holes, Wild Isles has 6.",
            "One under par is a birdie and two under is an eagle. One over is a bogey.",
        ], art: .golfStance, icon: "flag.fill"),
        HowToCard(id: "gg-shot", title: "Taking a shot", steps: [
            "Drag the AIM pad, or tap its arrows, to point your shot. The map shows where the ball should land.",
            "Use the arrows beside the CLUB card to change club. The game starts you on one that reaches the target.",
            "Tap READY if it asks, then tap the swing button. It turns green and says SWING! straight away.",
            "Settle the phone in your stance and swing back and through. Tap the button again before contact to cancel the swing.",
            "Changing the aim or club after you tap resets the swing, and so does a swing left alone for 12 seconds. Line up first, then tap the button.",
        ], art: .golfSwing, icon: "figure.golf"),
        HowToCard(id: "gg-power", title: "Distance and power", steps: [
            "How far you take the phone back sets how far the ball goes. Hip-high is about 60%, and the phone up behind you is full power.",
            "Your downswing only has to be firm and committed. Swinging harder than that adds no distance.",
            "Stop short on the way through, or tap the button again, and the swing resets without costing a stroke. Tap it and go again.",
            "A tentative, pushed swing is graded THIN: low, with little spin.",
        ], art: .golfSwing, icon: "speedometer"),
        HowToCard(id: "gg-strike", title: "A clean strike", steps: [
            "Keep the phone's face square through the swing. Twisting it more than about 10° starts to bend the ball.",
            "Twisted open it slices right, and twisted closed it hooks left (the other way if you play left-handed).",
            "A smooth tempo, a square face and a committed swing together earn a PERFECT strike, with a little extra ball speed.",
            "Strikes are graded PERFECT!, GREAT!, GOOD or THIN.",
        ], art: .golfSwing, icon: "checkmark.seal.fill"),
        HowToCard(id: "gg-clubs", title: "Choosing a club", steps: [
            "Full-swing yards: Driver 240, Hybrid 190, 5 Iron 175, 7 Iron 150, 9 Iron 125.",
            "Pitching Wedge 100, Sand Wedge 80, Lob Wedge 50. The Chipper and Putter finish about 25 yards away.",
            "A half backswing goes about half as far, so a long club can still play a shorter shot.",
            "Into the wind, or from the rough, take one more club. The putter comes out on its own on the green.",
        ], art: .golfClubs, icon: "bag.fill"),
        HowToCard(id: "gg-course", title: "Reading the course", steps: [
            "The wind badge shows speed in MPH and an arrow relative to your aim. Allow for it, especially on long shots.",
            "Water and lava cost a stroke, and you drop back from where you hit. Out of bounds costs a stroke and you replay from the same spot.",
            "Bunkers cost most clubs about 40% of their speed, so use a wedge. Rough costs 10–15%.",
            "Trees, rocks, walls and windmill blades knock the ball, and frozen lakes keep it skidding.",
        ], art: .golfAim, icon: "wind"),
        HowToCard(id: "gg-putt", title: "Putting", steps: [
            "On the green a slope grid appears. The beads drift the way the ball will break.",
            "Putts use tiny strokes. Distance grows with the square of your backswing, so a 3-foot putt is only about a fifth of a full stroke.",
            "There is no curve on a putt, so keep the face quiet and the stroke smooth.",
        ], art: .golfAim, icon: "scope"),
        HowToCard(id: "gg-party", title: "Party golf", steps: [
            "Party golf takes 2–4 players: Pass the Phone on one phone, Nearby with phones in the same room, or Online with Game Center.",
            "Everyone tees off first. After that, whoever is farthest from the hole plays. An idle turn costs a stroke after 60 seconds.",
            "While a friend's shot is in the air, tap an emote to react.",
        ], art: .golfClubs, icon: "person.3.fill"),
    ]

    static let tennisGuide: [HowToCard] = [
        HowToCard(id: "tg-goal", title: "The goal", steps: [
            "Quick Match: pick a rival, a difficulty and a length (3 games, 1 set or best of 3). Campaign: the Island Circuit, 10 rivals, where each win unlocks the next. Training: a free rally with your coach.",
            "Scoring is real tennis: 15, 30, 40, deuce and advantage. A full set is 6 games, won by two, with a tiebreak at 6–6.",
            "Practice first with Coach Ray's tutorial: forehand, backhand, aim, serve, then a point.",
        ], art: .swing, icon: "sportscourt.fill"),
        HowToCard(id: "tg-move", title: "Moving", steps: [
            "Your player runs to the ball for you, and sprints on its own for a hard one.",
            "Standing still on a wide shot usually hands your opponent the point.",
            "Sprinting drains stamina, and tired legs run slower. Stamina refills when you stand still and resets each point.",
            "Settings → Controls → Step to cross court sets how far you walk for the full width of the court.",
        ], art: .stand, icon: "figure.walk"),
        HowToCard(id: "tg-hit", title: "Hitting the ball", steps: [
            "Swing as the rings close on the ball, after it bounces. Timing is most of shot quality.",
            "Swinging harder barely changes the pace. A smooth swing on time beats a hard one that's late.",
            "The TV shows EARLY or LATE after a mistimed hit, with the ball's speed. Swung too soon? Your player holds the racket back and still hits it, just slower.",
            "The side the ball is on picks forehand or backhand. Your grip only matters for balls right at your body.",
        ], art: .swing, icon: "figure.tennis"),
        HowToCard(id: "tg-aim", title: "Aim and depth", steps: [
            "The ball goes where you swing: finish with the racket face toward the left of the screen, square to it, or toward the right.",
            "There is a wide straight middle, so a normal swing goes straight. Turn further for a sharper angle.",
            "Timing sets pace and depth: right on the ball is a fast, deep drive; mistimed is a slow ball that lands short.",
            "A low, flat swing slices the ball. A swing with lift hits topspin.",
        ], art: .backhand, icon: "arrow.left.and.right"),
        HowToCard(id: "tg-serve", title: "Serving", steps: [
            "Your phone shows DEUCE or AD, a target box and a big TOSS button. Tap the box to aim, or use the arrows to walk along the baseline.",
            "Tap TOSS exactly as the ticker on the TV's toss meter crosses the middle. The closer to the middle, the better the toss.",
            "Swing overhead as the power bar peaks at the top of the toss for a rocket serve. Off the peak it still goes in, just slower.",
            "A clean toss puts it right where you aimed; a loose one wanders, but stays in the box.",
        ], art: .serve, icon: "arrow.up.circle.fill"),
        HowToCard(id: "tg-extras", title: "Dive, supercharge and emotes", steps: [
            "Tap DIVE to reach a wide ball. It only works with a ball coming, costs stamina and needs about 2.5 seconds to recharge.",
            "Three GREAT or better hits in a row make the third a SUPERCHARGED shot, faster and almost dead accurate. A dive resets the streak.",
            "After you win a point, tap an emote on your phone to celebrate.",
            "Hold the pause icon for about half a second to pause.",
        ], art: .swing, icon: "bolt.fill"),
    ]

    static let setupGuide: [HowToCard] = [
        HowTo.connectTV,
        HowTo.connectMac,
        HowToCard(id: "sg-golf", title: "Golf setup", steps: [
            "Golf needs no scan or camera. Allow Motion when asked, since your swings are read from it.",
            "Stand with room to swing and hold the phone however is comfortable. Any grip works.",
            "For each shot: aim, pick a club, tap the swing button, then swing. Tap it again to cancel.",
        ], art: .golfStance, icon: "figure.golf"),
        HowToCard(id: "sg-tennis", title: "Tennis setup", steps: [
            "Stand about 2.5 m from the screen and point the phone's rear camera at it. Hold still until the court direction locks. After that, any grip or angle works.",
            "Next comes a quick timing check that measures your screen's picture delay. Swing with the bouncing ball, or skip it.",
            "Then tap Ready to play. Settings → Controls can redo the court direction or the timing check at your next match.",
        ], art: .stand, icon: "figure.tennis"),
        HowToCard(id: "sg-permissions", title: "Permissions", steps: [
            "Motion: lets the phone read your swings in both games.",
            "Camera: used by tennis only, to track where the phone is. Images are processed on your phone and are not recorded or uploaded.",
            "Online play needs a Game Center sign-in. Nearby play needs your friends' phones in the same room (no shared Wi-Fi needed).",
        ], art: .mirror, icon: "camera.fill"),
        HowToCard(id: "sg-fix", title: "Fixing common problems", steps: [
            "Golf swing not registering? Tap the swing button first, settle the phone in your stance, and don't touch the aim pad or club arrows after you tap.",
            "Tennis tracking dropping out? Keep the rear camera uncovered, point it at a room with some detail rather than a blank wall, and keep the lights on.",
            "Swings always early or late? Turn on your TV's Game Mode and run Settings → Controls → Swing timing check.",
            "Moved the TV, or steering feels off? Settings → Controls → Court direction → Set again. Left-handed? Set Plays to Left.",
            "TV cropping the picture? Settings → Display → Screen edge margin.",
        ], art: .mirror, icon: "wrench.and.screwdriver.fill"),
        HowToCard(id: "sg-friends", title: "Playing with friends", steps: [
            "Pass the Phone: 2–4 players share one phone and one screen.",
            "Nearby: friends in the same room, each with their own phone. Online: Quick Match or Play with Friends through Game Center.",
            "Golf has up to 4 players and tennis has 2. A lobby holds up to 4 people including spectators.",
        ], art: .mirror, icon: "person.3.fill"),
    ]

    static let betterGuide: [HowToCard] = [
        HowToCard(id: "bg-habits", title: "Good habits", steps: [
            "Clear space around you before every game, and keep a firm grip on the phone. A wrist strap is a good idea.",
            "Keep the phone unlocked and on the same Wi-Fi as your TV or Mac for the whole game.",
            "Warm up in Training (tennis) or the first hole (golf) before a real match.",
            "Read the tips on the loading screen. They change every time.",
        ], art: .stand, icon: "checkmark.circle.fill"),
        HowToCard(id: "bg-golf", title: "Golf checklist", steps: [
            "Check the wind and the map, then choose a club that lands where you want.",
            "Aim first. Then tap the swing button and swing. Tap it again to cancel.",
            "Take it back as far as the distance you want, then swing through smoothly.",
            "Keep the face square for a PERFECT strike, and play safe near water, lava and out of bounds.",
        ], art: .golfSwing, icon: "list.bullet.clipboard.fill"),
        HowToCard(id: "bg-tennis", title: "Tennis checklist", steps: [
            "Get back toward the middle after every shot, and step toward a wide ball early.",
            "Swing as the rings close, and trust a smooth swing over a hard one.",
            "Use depth and aim: deep to push your opponent back, short to attack, and away from their stronger side.",
            "Serve with a calm toss. A good toss and a smooth swing beat risky aim.",
        ], art: .swing, icon: "list.bullet.clipboard.fill"),
        HowToCard(id: "bg-feel", title: "Make it comfortable", steps: [
            "Settings → Display: 120 fps on the phone is smoother but uses more battery. Reduce motion shows still pictures instead of moving backdrops.",
            "Settings → Audio: turn Haptics and Sound on or off to taste.",
            "Settings → Accessibility: larger text on the phone remote.",
            "Settings → Gameplay: match intros and hole flyovers can be shortened or turned off.",
        ], art: .mirror, icon: "slider.horizontal.3"),
    ]
}

/// Optional setup before the interactive practice, aim and hole lesson.
enum GolfLesson {
    static let cards = [
        HowToCard(id: "g-stance", title: "Set up", steps: [
            "Hold the phone like a club grip — we’ll practice, aim, then play a friendly hole.",
        ], art: .golfStance),
    ]
}


/// A muted, looping b-roll clip from MenuVideo, aspect-filled, with its poster frame behind it
/// (shown alone when motion is reduced, while the clip loads, and in snapshots).
struct LoopingVideo: View {
    let clip: String
    var playing = true
    var aspectFit = false
    /// Snapshots (ImageRenderer cannot draw a player layer) show the poster frames.
    nonisolated(unsafe) static var stillsOnly = false
    var body: some View {
        let still = Self.stillsOnly || SportsSession.shared.reduceMotion || !playing
        // Fill exactly the space offered: an aspect-filled image must not widen its container
        // (that pushed titles laid over the video off the edge).
        Color.clear
            .overlay {
                if let poster = UIImage(named: "\(clip).jpg") {
                    Image(uiImage: poster).resizable().scaledToFill()
                } else {
                    LinearGradient(colors: [Arcade.skyDeep, Arcade.navyDeep], startPoint: .top, endPoint: .bottom)
                }
            }
            .overlay {
                if !still, let url = Bundle.main.url(forResource: clip, withExtension: "mp4") {
                    LoopingPlayer(url: url).id(clip)
                }
            }
            .clipped()
    }
}

struct LoopingPlayer: UIViewRepresentable {
    let url: URL
    var playing = true
    var aspectFit = false
    final class PlayerView: UIView {
        override static var layerClass: AnyClass { AVPlayerLayer.self }
        var looper: AVPlayerLooper?
        var player: AVQueuePlayer?
    }
    func makeUIView(context: Context) -> PlayerView {
        let view = PlayerView()
        let player = AVQueuePlayer()
        player.isMuted = true
        player.preventsDisplaySleepDuringVideoPlayback = false
        view.looper = AVPlayerLooper(player: player, templateItem: AVPlayerItem(url: url))
        view.player = player
        let layer = view.layer as! AVPlayerLayer
        layer.player = player; layer.videoGravity = aspectFit ? .resizeAspect : .resizeAspectFill
        view.backgroundColor = .clear
        if playing { player.play() }
        return view
    }
    func updateUIView(_ view: PlayerView, context: Context) { if playing { view.player?.play() } else { view.player?.pause() } }
    static func dismantleUIView(_ view: PlayerView, coordinator: ()) { view.player?.pause(); view.looper = nil }
}
