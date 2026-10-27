using System;
using System.Collections.Generic;
using UnityEngine;

namespace GolfArcade.Bowling
{
    /// Bowling, P0 greybox (PLAN_Bowling.md §12). Builds Club Lanes, runs the turn loop for one
    /// lane and 1-4 players taking turns, and plays every ball through the real systems: the
    /// fixed-tempo approach, the release window, the lane integrator, PhysX pin action and the
    /// USBC score sheet.
    ///
    /// Controller-agnostic: `Move`, `SetHold` and the swing fields are driven by the keyboard in
    /// the editor, by `Autoplay` for proof films, and (P1) by the phone through NativeSportsSession.
    public sealed partial class BowlingGame : MonoBehaviour
    {
        public enum Phase { Setup, Hold, Approach, Rolling, Pins, Result, Sweep, GameOver, Replay }

        public struct Shot
        {
            public float Board, Speed, Rpm, Axis, Timing;
            public Shot(float board, float speed, float rpm, float axis, float timing) { Board = board; Speed = speed; Rpm = rpm; Axis = axis; Timing = timing; }
        }

        public Phase Flow { get; private set; }
        public bool Initialized { get; private set; }
        public int Current { get; private set; }
        public readonly List<string> Players = new List<string> { "You" };
        public BowlingScore[] Scores { get; private set; }
        public OilPattern Oil = OilPattern.House;

        /// The swing the controller measured (P1 fills these from the phone).
        public float SwingSpeed = 7.4f, RevRpm = 260, AxisDeg = 35;
        /// The launch turn the swing's direction aimed (degrees, + = right; BowlingSwingDetector.AimFromSwing). 0 without a phone swing.
        public float SwingAimDeg;
        /// The last ball's aim, as the player made it (the swing plus the editor's aim keys), for the phone: degrees, + = right.
        public float LastAimDeg { get; private set; }
        /// Degrees added to every ball's launch direction (proof films steer the ball to show the follow-through follows its path; 0 in play).
        public float LaunchBiasDeg;
        public float DisplayLatency;                       // seconds, subtracted from the thumb lift (TV delay; fixed-tempo input only)
        /// True when the phone's motion measures the swing (false: keyboard, autoplay or touch).
        public bool MotionInput;
        /// Bowling V2 (PLAN_PhonePlay_NoTV_GolfBowling.md §5): with the phone's motion, the player's own swing is the clock. The walk
        /// is time-warped so the slide plants as the arm passes the bottom, and the release is graded against that moment (never
        /// against the picture, so a TV's delay does not matter and the phone needs no screen). Keyboard and autoplay keep the
        /// fixed-tempo approach.
        public bool SelfTimed => MotionInput && !IsCpu(Current) && IsLocal(Current);
        /// Computer bowlers (exhibition): skill 0..1 per player index; a missing or negative entry is a person.
        public readonly List<float> CpuSkill = new List<float>();
        public bool IsCpu(int player) => player < CpuSkill.Count && CpuSkill[player] >= 0;
        readonly System.Random cpuRng = new System.Random();
        /// The clean release is just after the arm passes the bottom (the ball leaves at the ankle as the arm starts to rise).
        public const float ReleaseAfterBottom = .06f;
        public Func<double> Clock = () => Time.realtimeSinceStartupAsDouble;
        readonly BowlingSwingDetector detector = new BowlingSwingDetector();
        public BowlingSwingDetector.Reading LastReading { get; private set; }
        public readonly Queue<Shot> Autoplay = new Queue<Shot>();
        public event Action<BowlingThrow, PinAction> BallFinished;
        /// Self-timed swing cues for the phone's haptics: "top" (the arm turns forward), "bottom" (it passes the bottom: let go now).
        /// They confirm the player's own swing; nothing waits on them.
        public event Action<string> Cue;
        /// The game is over: one "key=value;..." line for the phone's own player (index 0), for XP and stats (Swift BowlingGameStats).
        public event Action<string> GameFinished;
        int[] gutters, splitsConverted, bestStreak;
        bool cuedTop, cuedBottom;

        public float Board => boards[Current];
        public bool Holding { get; private set; }
        public BowlingThrow LastThrow { get; private set; }
        /// A player's game in "key=value;..." form: score, strikes, spares, open frames, gutters, splits converted, best strike run,
        /// how many bowled, where they finished, the venue.
        public string Summary(int player)
        {
            var s = Scores[player];
            int strikes = 0, spares = 0, opens = 0;
            for (int f = 0; f < BowlingScore.Frames; f++)
                for (int b = 0; b < (f == 9 ? 3 : 2); b++) { string m = s.Mark(f, b); if (m == "X") strikes++; else if (m == "/") spares++; }
            for (int f = 0; f < 9; f++) if (!s.IsStrike(f) && !s.IsSpare(f)) opens++;
            if (s.Mark(9, 0) != "X" && s.Mark(9, 1) != "/") opens++;
            int rank = 1; for (int i = 0; i < Players.Count; i++) if (i != player && Scores[i].Total > s.Total) rank++;
            return string.Join(";", "score=" + s.Total, "strikes=" + strikes, "spares=" + spares, "opens=" + opens, "gutters=" + gutters[player],
                "splits=" + splitsConverted[player], "streak=" + bestStreak[player], "players=" + Players.Count, "rank=" + rank,
                "venue=" + BowlingVenue.Current.ToString().ToLowerInvariant());
        }

        /// The camera that draws the lane (the session points it at the TV, or at the phone in phone play).
        public Camera GameplayCamera => cam;
        /// The pins standing for the ball about to be bowled (BowlingLeave mask).
        public int StandingPins => standing;
        public PinAction LastAction { get; private set; }

        float[] boards, aims;
        Camera cam;
        BowlingHud hud;
        readonly List<BowlingHero> heroes = new List<BowlingHero>();
        /// Optional: which players are the female hero (index = player). Default alternates male/female.
        public readonly List<bool> PlayerFemale = new List<bool>();
        BowlingHero Bowler => heroes.Count > Current ? heroes[Current] : null;
        bool reacted, walkedBack, reactShot;
        readonly System.Random clipRng = new System.Random();
        BowlingPinDeck deck;
        GameObject ballView, sweepBar;
        BowlingPinsetter setter;
        /// The ball the player sees (proof tools pose it for stills).
        public GameObject BallView => ballView;
        readonly GameObject[] pinViews = new GameObject[10];
        int standing = BowlingLeave.All;
        Vector3[] pinPositions; Quaternion[] pinRotations;
        readonly List<BallState> laneRecord = new List<BallState>();
        float holdT, approachT, playT, phaseT, releaseAt, followClipTime;
        bool foulSlide, released;
        Quaternion ballSpin = Quaternion.identity;
        Vector3 releaseHand;
        Vector3 camPos, camLook;
        int seed = 1;

        void Start()
        {
            cam = new GameObject("BowlingCamera").AddComponent<Camera>();
            cam.tag = "MainCamera"; cam.fieldOfView = 38; cam.nearClipPlane = .05f; cam.farClipPlane = 80;
            cam.gameObject.AddComponent<AudioListener>();   // (the TV session adds its recorder tap to it)
            cam.clearFlags = CameraClearFlags.SolidColor; cam.backgroundColor = MotionSports.Brand.BrandColors.N900;
            venue = BowlingVenue.Build(transform, cam);
            sound = BowlingAudio.Create(this, BowlingVenue.Current);
            // the neighbouring lanes are racked too (dressing only; their pins never move)
            for (int lane = BowlingAlleyKit.FirstLane; lane <= BowlingAlleyKit.LastLane; lane++)
                if (lane != 0)   // the whole kit bank is racked
                    for (int i = 1; i <= 10; i++)
                    {
                        var p = BowlingArt.Pin(transform);
                        p.name = "NeighbourPin";
                        p.transform.SetPositionAndRotation(BowlingLane.PinSpot(i) + Vector3.right * lane * BowlingClubLanes.LanePitch, Quaternion.Euler(0, 37 * i, 0));
                    }

            ballView = BowlingArt.Ball(transform);
            for (int i = 0; i < 10; i++) { pinViews[i] = BowlingArt.Pin(transform); pinViews[i].name = "Pin" + (i + 1); }
            sweepBar = GameObject.CreatePrimitive(PrimitiveType.Cube);
            Destroy(sweepBar.GetComponent<Collider>());
            sweepBar.transform.SetParent(transform, false);
            sweepBar.transform.localScale = new Vector3(2 * BowlingLane.KickbackX - .04f, .09f, .05f);   // kickback to kickback (it clears the gutters too)
            sweepBar.GetComponent<MeshRenderer>().sharedMaterial = BowlingAlley.Lit(new Color(.75f, .76f, .78f), .7f);
            setter = BowlingPinsetter.Build(transform);
            aimGuide = AimGuide(transform);
            BowlingHero.Ground = GroundY;

            deck = new BowlingPinDeck();
            NewGame(Players.ToArray());
            SnapCamera();
            StartCoroutine(RenderReflections());
            Initialized = true;
        }

        BowlingClubLanes.Venue venue;
        BowlingAudio sound;
        GameObject aimGuide;

        /// The aim on the lane (Wii-style, Adnan 10-27 "make aiming more intuitive"): a dotted gold line from where the ball is set
        /// down along the line it will leave on, with an arrowhead, shown while this phone's bowler stands at the stance.
        static GameObject AimGuide(Transform parent)
        {
            var verts = new List<Vector3>(); var tris = new List<int>();
            void Quad(Vector3 a, Vector3 b, Vector3 c, Vector3 d) { int i = verts.Count; verts.Add(a); verts.Add(b); verts.Add(c); verts.Add(d); tris.AddRange(new[] { i, i + 1, i + 2, i, i + 2, i + 3 }); }
            // 10-27 feel pass: out to 12 m (was 6, mostly behind the bowler's head; a 1.4° swing aim now moves the tip ~30 cm), wider
            const float w = .03f, dash = .26f, end = 12f;
            for (float z = .45f; z < end - .5f; z += .6f) Quad(new Vector3(-w, 0, z), new Vector3(-w, 0, z + dash), new Vector3(w, 0, z + dash), new Vector3(w, 0, z));
            int k = verts.Count;
            verts.Add(new Vector3(-.12f, 0, end - .45f)); verts.Add(new Vector3(0, 0, end)); verts.Add(new Vector3(.12f, 0, end - .45f));
            tris.AddRange(new[] { k, k + 1, k + 2 });
            var mesh = new Mesh { name = "AimGuide" };
            mesh.SetVertices(verts); mesh.SetTriangles(tris, 0); mesh.RecalculateNormals(); mesh.RecalculateBounds();
            var go = new GameObject("AimGuide");
            go.transform.SetParent(parent, false);
            go.AddComponent<MeshFilter>().sharedMesh = mesh;
            var r = go.AddComponent<MeshRenderer>();
            r.sharedMaterial = BowlingAlleyKit.Emissive(MotionSports.Brand.BrandColors.Gold, 1.1f);   // (2.2 bloomed to white)
            r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off; r.receiveShadows = false;
            go.SetActive(false);
            return go;
        }

        /// 10-27 feel pass: the arrow points up the board line while the bowler sets up (straight: the aim is in the swing now), then
        /// turns live with the forward swing (the way the swing is heading, eased) until the ball leaves the hand.
        void PlaceAimGuide(float dt)
        {
            if (!aimGuide) return;
            bool setup = Flow == Phase.Setup || Flow == Phase.Hold, swinging = Flow == Phase.Approach && !released;
            bool show = (setup || swinging) && !IsCpu(Current) && IsLocal(Current) && Bowler && Bowler.Remaining < LongWalkMetres;
            if (aimGuide.activeSelf != show) aimGuide.SetActive(show);
            float want = AimDeg + (swinging && SelfTimed ? BowlingSwingDetector.AimFromSwing(detector.SwingAimDeg) : 0);
            guideDeg = !show || !swinging ? want : Mathf.Lerp(guideDeg, want, 1 - Mathf.Exp(-dt / .06f));
            if (!show) return;
            // 6 mm over the lacquer (clear of it in the depth buffer at every distance the cameras see it from)
            aimGuide.transform.SetPositionAndRotation(new Vector3(BowlingLane.BoardX(Board), .006f, .1f), Quaternion.Euler(0, guideDeg, 0));
        }
        float guideDeg;

        /// The lane and pin reflections: rendered once the venue, pins and lights are all in place.
        System.Collections.IEnumerator RenderReflections()
        {
            yield return null;
            if (venue?.Probe) venue.Probe.RenderProbe();
            if (venue?.PinProbe) venue.PinProbe.RenderProbe();
        }

        /// A new game for these players (1-4), taking turns frame by frame on the one lane.
        public void NewGame(IList<string> players)
        {
            if (players != null && players.Count > 0 && !ReferenceEquals(players, Players)) { Players.Clear(); Players.AddRange(players); }
            Scores = new BowlingScore[Players.Count];
            boards = new float[Players.Count];
            aims = new float[Players.Count];
            for (int i = 0; i < Players.Count; i++) { Scores[i] = new BowlingScore(); boards[i] = 20; }
            gutters = new int[Players.Count]; splitsConverted = new int[Players.Count]; bestStreak = new int[Players.Count];
            Current = 0;
            // one real hero per player: the bowler at the approach, the others waiting by the ball return
            foreach (var h in heroes) if (h) Destroy(h.gameObject);
            heroes.Clear();
            for (int i = 0; i < Players.Count; i++)
            {
                bool female = i < PlayerFemale.Count ? PlayerFemale[i] : i % 2 == 1;
                var at = i == 0 ? StartSpot(boards[i]) : WaitSpot(i);
                heroes.Add(BowlingHero.Spawn(transform, female, at, i == 0 ? 0 : WaitYaw));
                if (i > 0 && heroes[i]) Send(heroes[i], at, WaitYaw, sit: true);
            }
            hud?.Dispose();
            hud = new BowlingHud(cam, Players);
            FreshRack();
            EnterSetup();
        }

        void OnDestroy() { deck?.Dispose(); }

        // ------------------------------------------------------------------ controller API

        /// The phone's controls: ignored while a computer bowler is up.
        public void PlayerMove(float boardsDelta) { if (!IsCpu(Current) && IsLocal(Current)) Move(boardsDelta); }
        /// The phone's lane slider (10-27 feel pass: "it takes a while to move side to side"): stand on this board, wherever it is.
        public void PlayerBoard(float board) { if (!IsCpu(Current) && IsLocal(Current)) Move(board - Board); }
        public void PlayerHold(bool down)
        {
            if (down && Flow == Phase.Replay) { EndReplay(); return; }   // a tap on the ball skips the replay
            if (down && Flow != Phase.Approach && LongWalk && SkipWalks()) return;   // ... and a walk to or from the lounge
            if ((!IsCpu(Current) && IsLocal(Current)) || !down && Holding) SetHold(down);
        }

        /// The phone's aim: degrees to turn the line the ball leaves on (+ = toward the bowler's right).
        public void PlayerAim(float degDelta) { if (!IsCpu(Current) && IsLocal(Current)) AimBy(degDelta); }
        /// Turns the aim (setup only), in quarter degrees, up to MaxAim either way.
        public void AimBy(float degDelta)
        {
            if (Flow != Phase.Setup) return;
            aims[Current] = Mathf.Clamp(Mathf.Round((aims[Current] + degDelta) * 4) / 4, -MaxAim, MaxAim);
        }
        /// About 1 m either way at the pins (18.3 m down the lane): every pocket and corner-pin angle from any board.
        public const float MaxAim = 3f;
        /// The set-up aim (degrees, + = right): the editor's Z/C keys (the phone aims with the swing itself since the 10-27 feel
        /// pass; its old AIM row's bowlAim still lands here). Computer bowlers aim by board only.
        public float AimDeg => IsCpu(Current) ? 0 : aims[Current];

        public void Move(float boardsDelta)
        {
            if (Flow != Phase.Setup) return;
            boards[Current] = Mathf.Clamp(Mathf.Round((boards[Current] + boardsDelta) * 2) / 2, 3, 37);
        }

        public void SetHold(bool down)
        {
            if (Holding == down) return;
            // still walking up to the approach (a side-step along it does not wait: the hold starts, the pushaway waits for the feet)
            if (down && Flow == Phase.Setup && Bowler && !Bowler.Arrived && Bowler.Remaining >= SideStepHold) return;
            if (down && Flow == Phase.Setup && LoungeWalker() != null) return;     // a friend still crossing behind the approach (under the camera)
            Holding = down;
            if (down && Flow == Phase.Setup) { Flow = Phase.Hold; holdT = 0; detector.Begin(Clock()); cuedTop = cuedBottom = false; }
            else if (!down && Flow == Phase.Hold) { Flow = Phase.Setup; detector.Cancel(); Bowler?.PlayClip(BowlingClips.Abort); }   // the authored abort: only before the approach
            else if (!down && Flow == Phase.Approach && !released && heldThrow == null)
            {
                // once the approach has started it cannot be cancelled: a thumb lift in the first steps is the goofy drop (SelfTimedError)
                if (SelfTimed) Release(SelfTimedError(Clock()));
                else Release(approachT - DisplayLatency - BowlingApproach.IdealRelease);
            }
        }

        // ------------------------------------------------------------------ flow

        void EnterSetup()
        {
            Flow = Phase.Setup; holdT = approachT = 0; released = false; heldThrow = null; foulSlide = false;
            walkedBack = false; reacted = false; reactShot = false;
            hud.Speed(0);
            for (int i = 0; i < Players.Count; i++) hud.Score(i, Scores[i], i == Current);
            if (Players.Count > 1) hud.Leader(Leader());
            var s = Scores[Current];
            hud.Status($"{Players[Current]} · Frame {Mathf.Min(10, s.Frame + 1)} · Ball {s.Ball + 1} · Board {Board:0.#}");
            // a computer bowler plans its ball from the lane and the pins standing, then bowls it like the autoplay
            if (IsCpu(Current) && IsLocal(Current)) { Autoplay.Clear(); Autoplay.Enqueue(BowlingCpu.Plan(CpuSkill[Current], standing, Oil, cpuRng)); }
        }

        /// One phone motion sample (CoreMotion attitude + device rotation rate) while the ball is held.
        public void NativeMotion(double time, float qx, float qy, float qz, float qw, float rx, float ry, float rz)
        {
            if (IsCpu(Current) || !IsLocal(Current)) return;
            if (Flow == Phase.Hold || (Flow == Phase.Approach && !released)) detector.Ingest(time, qx, qy, qz, qw, rx, ry, rz);
        }

        /// What the phone's controller screen shows: phase|player|frame|ball|board|grade|mph|hook°|rpm|standing pins|mine (1: this
        /// phone bowls now; 0: a friend's phone or the computer does)|walking (1: a walk to or from the lounge, a tap skips it)|aim° (the
        /// last ball's, from the swing's direction).
        public string NativeState
        {
            get
            {
                var s = Scores[Current];
                return string.Join("|", Flow, Players[Current], Mathf.Min(10, s.Frame + 1), s.Ball + 1, Board.ToString("0.#", System.Globalization.CultureInfo.InvariantCulture),
                    LastThrow.Grade, (LastThrow.Speed * 2.237f).ToString("0.0", System.Globalization.CultureInfo.InvariantCulture),
                    LastThrow.AxisDeg.ToString("0", System.Globalization.CultureInfo.InvariantCulture), LastThrow.RevRpm.ToString("0", System.Globalization.CultureInfo.InvariantCulture),
                    BowlingLeave.Numbers(standing), IsLocal(Current) && !IsCpu(Current) ? "1" : "0",
                    LongWalk ? "1" : "0", LastAimDeg.ToString("0.##", System.Globalization.CultureInfo.InvariantCulture));
            }
        }

        /// The thumb lift against the player's own arm: seconds after the clean moment (the bottom + ReleaseAfterBottom); on the way
        /// down it is the time still to go, past the bottom the time since. Forgiving: once the bowler is past the first steps the
        /// ball always goes down the lane (at worst early or late, never a slip or a foul). Only a lift in the first steps, before any
        /// forward swing, drops it. A swing the phone did not read is timed on the bowler's own beat instead.
        float SelfTimedError(double lift)
        {
            float e;
            if (detector.ForwardSwing) e = detector.SinceBottom(lift) - ReleaseAfterBottom;
            else if (approachT < BowlingApproach.SwingBottom) return -(BowlingRelease.MissWindow + .3f);
            else e = approachT - DisplayLatency - BowlingApproach.IdealRelease;
            return Mathf.Clamp(e, -BowlingRelease.MissWindow, BowlingRelease.MissWindow);
        }

        /// Self-timed: the thumb lift was graded on the player's own arm; the bowler lets the ball go on the approach's own beat
        /// (the ideal release, shifted by the grade, as a remote bowler does), so the walk-up keeps the computer's cadence.
        BowlingThrow? heldThrow;
        /// The slowest ball a self-timed swing gives (m/s, ~12 mph): an easy swing still gets the ball to the pins.
        const float SelfTimedMinSpeed = 6.9f;   // 10-27 (Adnan "way more sensitivity"): 5.4 → 6.3; feel pass ("easy to put a good amount of power"): 6.9, ~15.4 mph
        /// A hold pressed while the bowler is still side-stepping this close to the spot is taken (metres; a whole lane is ~0.9).
        const float SideStepHold = .6f;

        void Release(float timingError)
        {
            if (SelfTimed && detector.Active)
            {
                var r = detector.Measure(Clock());
                LastReading = r;
                if (detector.ForwardSwing) { SwingSpeed = Mathf.Max(SelfTimedMinSpeed, r.BallSpeed); RevRpm = r.RevRpm; AxisDeg = r.AxisDeg; SwingAimDeg = r.AimDeg; }
                else { SwingSpeed = 7.4f; RevRpm = 150; AxisDeg = 10; SwingAimDeg = 0; }   // the phone did not read a swing: a plain ball
            }
            else SwingAimDeg = 0;
            // the player's aim (the swing's direction, the editor's keys) turns the whole line; the release's own scatter stays on top
            LastAimDeg = Mathf.Clamp(AimDeg + SwingAimDeg, -MaxAim, MaxAim);
            var th = BowlingRelease.Resolve(new BowlingSwing
            {
                Board = Board, Speed = SwingSpeed, RevRpm = RevRpm, AxisDeg = AxisDeg,
                TimingError = timingError, AimDeg = LastAimDeg, Seed = seed++,
            });
            th.LaunchDeg += LaunchBiasDeg;
            if (SelfTimed && !th.Dropped) heldThrow = th; else Deliver(th);
        }

        /// The ball leaves the hand: this phone's own release, or another phone's throw played here (network).
        void Deliver(BowlingThrow th)
        {
            released = true; releaseAt = approachT; heldThrow = null;
            netSendPending = Networked && IsLocal(Current);
            LastThrow = th;
            sound?.Release(th);
            foulSlide = th.Foul;
            if (Bowler && Bowler.ApproachActive)
            {
                float ct = Bowler.ClipTime > 0 ? Bowler.ClipTime : approachT;
                string variant = BowlingClips.ForRelease(th, ct, clipRng);
                if (th.Grade == ReleaseGrade.Perfect || th.Grade == ReleaseGrade.Good) variant = BowlingClips.BodyEnglish(th.LaunchDeg) ?? variant;
                followClipTime = ct;
                Bowler.PlayClip(variant, ct);
            }
            releaseHand = ballView.transform.position;
            laneRecord.Clear();
            if (th.Dropped)
            {
                // The ball slips out on the backswing and rolls back up the approach (a Wii classic).
                var s = new BallState { Position = releaseHand, Velocity = new Vector3(0, 0, -1.4f), Phase = BallPhase.Air };
                for (int i = 0; i < 90; i++)
                {
                    s.Velocity.y -= 9.81f / 60; s.Position += s.Velocity / 60;
                    if (s.Position.y < BowlingLane.BallRadius) { s.Position.y = BowlingLane.BallRadius; s.Velocity.y = -s.Velocity.y * .2f; s.Velocity.z *= .97f; }
                    s.Spin = new Vector3(s.Velocity.z / BowlingLane.BallRadius, 0, 0);
                    laneRecord.Add(s);
                }
                deck.Begin(new BallState { Phase = BallPhase.Pit }, standing, pinPositions, pinRotations);
            }
            else
            {
                var end = BowlingBall.Roll(th.Launch(), Oil, laneRecord);
                deck.Begin(end, standing, pinPositions, pinRotations);
            }
            // the follow-through goes the way the ball goes: the swinging arm is turned (about the vertical) toward the real path of the ball over its first ~3 m
            if (Bowler && laneRecord.Count > 3)
            {
                var p0 = laneRecord[0].Position; float headingDeg = 0;
                for (int i = 1; i < laneRecord.Count; i++)
                    if (laneRecord[i].Position.z - p0.z >= 3f) { headingDeg = Mathf.Atan2(laneRecord[i].Position.x - p0.x, laneRecord[i].Position.z - p0.z) * Mathf.Rad2Deg; break; }
                Bowler.SetFollowThrough(headingDeg, followClipTime);
            }
            Flow = Phase.Rolling; playT = 0; ballSpin = Quaternion.identity;
            hud.Speed(th.Speed * 2.237f);
        }

        void Update()
        {
            if (!Initialized) return;
            float dt = Time.deltaTime;
            KeyboardInput(dt);
            AutoplayInput(dt);
            NetworkUpdate();
            // the phone held upright (no TV): a taller view, so the whole lane and the pins fit the narrow screen
            cam.fieldOfView = cam.aspect < 1 ? 56 : 38;
            hud.Tick();
            phaseT += dt;

            switch (Flow)
            {
                case Phase.Setup:
                    PoseBowler(0, false);
                    hud.Status($"{Players[Current]} · Frame {Mathf.Min(10, Scores[Current].Frame + 1)} · Ball {Scores[Current].Ball + 1} · Board {Board:0.#}");
                    break;
                case Phase.Hold:
                    if (!Bowler || Bowler.Arrived) holdT += dt;
                    PoseBowler(0, false);
                    if (holdT >= BowlingApproach.HoldToStart) { Flow = Phase.Approach; approachT = 0; Bowler?.PlayClip(BowlingClips.Shot, 0, false, true); }
                    break;
                case Phase.Approach:
                    approachT += dt;   // one steady walk-up for everyone (the computer's cadence)
                    if (SelfTimed && detector.ForwardSwing && !cuedTop) { cuedTop = true; Cue?.Invoke("top"); }
                    if (SelfTimed && detector.PastBottom && !cuedBottom) { cuedBottom = true; Cue?.Invoke("bottom"); }
                    PoseBowler(approachT, false, dt);
                    // the graded throw leaves the hand on the bowler's beat
                    if (heldThrow is BowlingThrow held)
                    {
                        if (approachT >= BowlingApproach.IdealRelease + GradeTiming(held.Grade)) Deliver(held);
                    }
                    else if (SelfTimed)
                    {
                        // still holding as the bowler's hand comes through: the ball goes with the bowler's own release (a clean one
                        // unless the player's own forward swing says early or late; never held into a foul)
                        if (approachT >= BowlingApproach.IdealRelease + BowlingRelease.MissWindow)
                            Release(detector.ForwardSwing ? SelfTimedError(Clock()) : BowlingRelease.PerfectWindow + .02f);
                    }
                    else if (remoteBall == null && approachT - DisplayLatency > BowlingApproach.IdealRelease + BowlingRelease.MissWindow) Release(approachT - DisplayLatency - BowlingApproach.IdealRelease);   // (another phone's ball lets go on its own time)
                    break;
                case Phase.Rolling:
                case Phase.Pins:
                    approachT += dt;
                    PoseBowler(approachT, foulSlide, dt);
                    PlayBall(dt);
                    break;
                case Phase.Result:
                    approachT += dt;
                    PoseBowler(approachT, foulSlide, dt);
                    if (phaseT > ResultHold) { if (replayDue) BeginReplay(); else BeginSweep(); }
                    break;
                case Phase.Replay:
                    approachT += dt;
                    PoseBowler(approachT, foulSlide, dt);
                    PlayReplay(dt);
                    break;
                case Phase.Sweep:
                    Sweep();
                    break;
            }
            PlaceAimGuide(dt);
            Shoot(dt);
        }

        /// The on-screen arm: the approach's ideal swing, pulled 30 % toward the player's own swing.
        float ArmDeg(float t)
        {
            float ideal = BowlingApproach.ArmAngle(t);
            if (!MotionInput || !detector.Active) return ideal;
            float phone = BowlingApproach.ArmAngle(0) + detector.AngleDeg;
            return Mathf.Lerp(ideal, phone, .3f);
        }

        // ------------------------------------------------------------------ the bowler (real hero)

        const float WaitYaw = 0;
        float ResultHold => reactShot ? 2.8f : 1.9f;

        Vector3 StartSpot(float board) => new Vector3(BowlingHero.BodyX(board), 0, BowlingApproach.StartZ);
        /// Where a waiting player sits: on the lounge settee behind the approach (out of the bowler's
        /// shot, in the reaction shot), one place each.
        Vector3 WaitSpot(int player) => new Vector3(-1.1f + .75f * player, 0, BowlingClubLanes.LoungeZ + .3f);

        /// Where the walk between the lounge and the approach crosses the sofa row: the gap the game pair's own sofas and table
        /// leave (BowlingAlleyKit.Place hides them), left of the console and the ball return.
        public const float AisleX = 0, AisleSide = .27f;
        /// The front edge of the players' settee dais (BowlingVenue.Settee), at approach level; the lounge floor in front of it is a step down.
        const float DaisFront = BowlingClubLanes.LoungeZ + 1f;

        /// The way between the lounge and the approach (Adnan 10-27: "they walk through obstacles"): along the dais to the aisle, down
        /// onto the lounge floor, straight up the aisle between the sofas, up the settee step, then to the spot. Null when both ends are
        /// on the same side. Only the waypoints still ahead of `from` are returned (the route is re-planned when the board moves).
        public static List<Vector3> Route(Vector3 from, Vector3 to)
        {
            float back = BowlingAlleyKit.ApproachBack - .2f;
            bool fromLounge = from.z < back, toLounge = to.z < back;
            if (fromLounge == toLounge) return null;
            float floor = BowlingAlleyKit.SetteeFloor;
            var seat = fromLounge ? from : to;
            // two sides of the aisle, so the next bowler going up and the last one coming back pass each other (10-27 film: they met
            // on the centre line and walked through each other)
            float x = AisleX + (fromLounge ? -AisleSide : AisleSide);
            var path = new List<Vector3>
            {
                new Vector3(seat.x, 0, DaisFront - .45f),   // square in front of the seat (not cutting along the settee's front)
                new Vector3(x, 0, DaisFront - .15f), new Vector3(x, floor, DaisFront + .2f),
                new Vector3(x, floor, BowlingAlleyKit.ApproachBack - .2f), new Vector3(x, 0, BowlingAlleyKit.ApproachBack + .25f),
            };
            if (!fromLounge) path.Reverse();
            path.RemoveAll(p => fromLounge ? p.z < from.z + .05f : p.z > from.z - .05f);
            return path;
        }

        /// The floor under a walker: the approach and the players' dais at 0, the lounge floor between them one step (.18 m) down, each
        /// step taken over a quarter metre (BowlingHero.Ground).
        public static float GroundY(Vector3 p)
        {
            float back = BowlingAlleyKit.ApproachBack, floor = BowlingAlleyKit.SetteeFloor;
            if (p.z > back - .25f) return Mathf.Lerp(floor, 0, Mathf.InverseLerp(back - .25f, back, p.z));
            if (p.z < DaisFront + .25f) return Mathf.Lerp(0, floor, Mathf.InverseLerp(DaisFront, DaisFront + .25f, p.z));
            return floor;
        }

        /// Sends a hero walking (round the furniture when the walk crosses between the lounge and the approach).
        void Send(BowlingHero h, Vector3 to, float yaw, bool sit = false)
        {
            if (!h) return;
            h.WalkTo(to, yaw, sit, (to - h.Target).sqrMagnitude > .0004f ? Route(h.Position, to) : null);
        }

        /// A hero is on a walk worth skipping (to or from the lounge; not a side-step along the approach).
        public bool LongWalk
        {
            get { foreach (var h in heroes) if (h && h.Remaining > LongWalkMetres) return true; return false; }
        }
        const float LongWalkMetres = .9f;

        /// Adnan 10-27: the walks between the lounge and the lane can be skipped (a tap on the ball): everyone is where they were going.
        /// Returns true when a long walk was cut short (that tap is used up; a side-step just finishes).
        public bool SkipWalks()
        {
            bool skipped = LongWalk;
            foreach (var h in heroes) if (h) h.Snap();
            return skipped;
        }

        /// Poses the bowler for approach time t (≤ 0: stance at the start spot, walking/side-stepping there first).
        void PoseBowler(float t, bool foul, float dt = 0)
        {
            var h = Bowler; if (!h) return;
            if (t <= 0)
            {
                Send(h, StartSpot(Board), 0);
                if (h.HasClips && h.Arrived) h.EnsureStance();
                h.ArmDeg = h.Arrived && !h.HasClips ? BowlingApproach.ArmAngle(0) : float.NaN;   // the ball at the chest once they are set
                h.Balance = 0;
                h.Ball = ballView.transform; ballView.SetActive(true);
                return;
            }
            if (h.HasClips)
            {
                // the authored shot clip carries the whole body (the hips run the approach inside it): the root stays at the stance until the clip ends
                if (h.ApproachActive) h.Drive(StartSpot(Board), 0, 0);
                h.ArmDeg = float.NaN; h.Balance = 0;
                h.Ball = released ? null : ballView.transform;
                return;
            }
            float z = BowlingApproach.BodyZ(t, foul), zPrev = BowlingApproach.BodyZ(Mathf.Max(0, t - Mathf.Max(dt, 1e-3f)), foul);
            float groundSpeed = dt > 0 ? (z - zPrev) / Mathf.Max(dt, 1e-3f) : 0;
            if (!walkedBack) h.Drive(new Vector3(BowlingHero.BodyX(Board), 0, z), 0, Mathf.Max(0, groundSpeed));
            // the arm: the swing until the follow-through has been held, then the clip's own arms again
            bool swinging = t < BowlingApproach.FollowThroughEnd + .9f;
            h.ArmDeg = swinging ? (released ? BowlingApproach.ArmAngle(Mathf.Min(t, BowlingApproach.FollowThroughEnd)) : ArmDeg(t)) : float.NaN;
            h.Balance = swinging ? Mathf.Clamp01((t - BowlingApproach.PushawayExtended) / .4f) : 0;
            h.Ball = released ? null : ballView.transform;
        }

        /// A reaction for the result, then the walk back up the approach (or to the ball return when the frame is over).
        void ReactAndWalkBack(BowlingHud.Praise praise, int knocked, string kind = null)
        {
            var h = Bowler; if (!h) return;
            // the authored reaction for the result (the feminine set, both heroes); the standard emotes remain the fallback
            string authored = kind != null ? BowlingClips.Reaction(kind, clipRng) : null;
            if (authored != null && h.PlayClip(authored)) { reacted = true; return; }
            string emote = praise == BowlingHud.Praise.Big ? (UnityEngine.Random.value < .5f ? "EmoteFistPump" : "EmoteJumpJoy")
                : praise == BowlingHud.Praise.Nice ? "EmoteFistPump"
                : praise == BowlingHud.Praise.Bad || knocked <= 3 ? "EmoteSlump" : null;
            if (emote != null) h.React(emote);
            reacted = true;
        }

        void PlayBall(float dt)
        {
            playT += dt;
            if (Flow == Phase.Rolling)
            {
                // Pin action is simulated in slices while the ball is still on the lane.
                float laneTime = laneRecord.Count / 60f;
                int budget = Mathf.CeilToInt(1100 * dt / Mathf.Max(.4f, laneTime * .8f));
                deck.Advance(Mathf.Max(8, budget));
                // network: this phone's ball goes to the others as soon as its pinfall is known (they score it with ours)
                if (netSendPending && deck.Result != null) { netSendPending = false; SendThrow(LastThrow, deck.Result.StandingAfter); }

                int i = Mathf.Min(laneRecord.Count - 1, Mathf.FloorToInt(playT * 60));
                var s = laneRecord[i];
                Vector3 p = s.Position;
                // Blend from the hand to the integrator over the first 0.12 s (the greybox arm does not reach the lane).
                float blend = Mathf.Clamp01(playT / .12f);
                ballView.transform.position = Vector3.Lerp(releaseHand, p, blend);
                if (s.Spin.sqrMagnitude > 1e-6f) ballSpin = Quaternion.AngleAxis(s.Spin.magnitude * dt * Mathf.Rad2Deg, s.Spin.normalized) * ballSpin;
                ballView.transform.rotation = ballSpin;
                sound?.Rolling(laneRecord, playT, deck.Result);
                if (i >= laneRecord.Count - 1)
                {
                    if (!deck.Advance(1 << 16)) return;
                    LastAction = deck.Result;
                    Flow = Phase.Pins; playT = 0;
                    if (IsLocal(Current) && !IsCpu(Current)) Cue?.Invoke("crash:" + LastAction.Knocked);   // the phone rumbles with the pins
                    sound?.Pins(LastAction);
                }
                return;
            }

            var frames = LastAction.Frames;
            int k = Mathf.Min(frames.Count - 1, Mathf.FloorToInt(playT * 60));
            var f = frames[k];
            for (int n = 0; n < 10; n++)
            {
                if (!pinViews[n].activeSelf) continue;
                pinViews[n].transform.SetPositionAndRotation(f.Pins[n], f.PinRotations[n]);
            }
            ballView.SetActive(f.BallLive);
            if (f.BallLive) ballView.transform.SetPositionAndRotation(f.Ball, f.BallRotation * ballSpin);
            if (k >= frames.Count - 1) Score();
        }

        void Score()
        {
            var th = LastThrow; var act = LastAction;
            var s = Scores[Current];
            int before = s.PinsStanding;
            // network: every phone scores the ball with the bowler's own pinfall (its physics is the truth), so all the sheets agree
            int after = authAfter >= 0 ? authAfter : act.StandingAfter; authAfter = -1; ballsBowled++;
            int knocked = Mathf.Min(BowlingLeave.Count(standing & ~after), before);
            if (after != act.StandingAfter)
                for (int i = 0; i < 10; i++) if (!BowlingLeave.Standing(after, i + 1) && BowlingLeave.Standing(act.StandingAfter, i + 1)) pinViews[i].SetActive(false);
            s.Roll(knocked, th.Foul);
            BallFinished?.Invoke(th, act);
            hud.Score(Current, s, true);

            // Brand voice: one word and a bang for the big moments, a short "you" subline.
            string sub = th.Grade switch
            {
                ReleaseGrade.Perfect => "Perfect release.", ReleaseGrade.Good => "Good release.",
                ReleaseGrade.Early => "A touch early.", ReleaseGrade.Late => "Late. You lofted it.",
                ReleaseGrade.Drop => "It slipped on the backswing!", _ => "You held it too long.",
            };
            const float Hold = 1.9f;
            var praise = BowlingHud.Praise.Good;
            void Show(string word, string line, BowlingHud.Praise tier) { praise = tier; hud.Banner(word, line, Hold, tier); }
            string kind = null;
            if (th.Foul) { Show("FOUL!", "Over the line. That ball scores 0.", BowlingHud.Praise.Bad); kind = "Foul"; }
            else if (th.Dropped) Show("OOPS!", sub, BowlingHud.Praise.Bad);
            else if (knocked == 10 && before == 10)
            {
                string streak = BowlingLeave.Streak(s.StrikeStreak);
                kind = streak != null ? "Turkey" : "Strike";
                venue?.Fx?.Strike();
                Show(streak != null ? streak.ToUpper() + "!" : "STRIKE!", sub, BowlingHud.Praise.Big);
            }
            else if (knocked == before && before < 10)
            {
                Show(previousLeaveWasSplit ? "SPLIT CONVERTED!" : "SPARE!", sub, previousLeaveWasSplit ? BowlingHud.Praise.Big : BowlingHud.Praise.Nice);
                kind = previousLeaveWasSplit ? "ConvertedSplit" : "Spare";
            }
            else if (laneRecord.Count > 0 && laneRecord[laneRecord.Count - 1].Phase == BallPhase.Pit && knocked == 0) { Show("GUTTER", sub, BowlingHud.Praise.Good); kind = "Gutter"; }
            else
            {
                bool frameGoesOn = before == 10 && !s.Complete && s.Ball > 0 && !s.FreshRack;
                string leave = frameGoesOn ? BowlingLeave.Name(after) : null;
                Show(leave != null ? leave.ToUpper() : knocked == 0 ? "MISS" : $"{knocked} PIN{(knocked == 1 ? "" : "S")}", sub, BowlingHud.Praise.Good);
                kind = frameGoesOn && BowlingLeave.Numbers(after) == "7-10" ? "SevenTen" : frameGoesOn && BowlingLeave.IsSplit(after) ? "Split" : knocked == 0 ? "Miss" : null;
            }
            previousLeaveWasSplit = before == 10 && !s.FreshRack && s.Ball > 0 && BowlingLeave.IsSplit(after);
            if (kind == "Gutter") gutters[Current]++;
            if (kind == "ConvertedSplit") splitsConverted[Current]++;
            bestStreak[Current] = Mathf.Max(bestStreak[Current], s.StrikeStreak);
            if (Players.Count > 1) hud.Leader(Leader());
            sound?.Result(kind, knocked, s.StrikeStreak, before == 10 && s.Ball > 0 && !s.FreshRack);
            ReactAndWalkBack(praise, knocked, kind);
            reactShot = praise == BowlingHud.Praise.Big || praise == BowlingHud.Praise.Nice;
            // the big ones get a slow-motion replay of the pins (a strike, a streak, a split picked up)
            replayDue = (kind == "Strike" || kind == "Turkey" || kind == "ConvertedSplit") && LastAction != null && LastAction.Frames.Count > 10;
            standing = after;
            Flow = Phase.Result; phaseT = 0;
        }

        void BeginSweep()
        {
            Flow = Phase.Sweep; phaseT = 0;
            ballView.SetActive(false);
            sound?.Sweep();
            var s = Scores[Current];
            // the bowler turns and walks back up the approach (or, when the frame is over and a friend is up, to the ball return)
            walkedBack = true;
            bool handOver = (s.Complete || s.Ball == 0) && Players.Count > 1;
            if (Bowler) { Bowler.ArmDeg = float.NaN; Bowler.Balance = 0; Bowler.Ball = null; Send(Bowler, handOver ? WaitSpot(Current) : StartSpot(Board), handOver ? WaitYaw : 0, sit: handOver); }
            bool fresh = s.FreshRack || s.Complete || s.Ball == 0;
            // The pinsetter (real machine): the deck lifts the pins that are still standing, the sweep bar drops in front of the rest and pushes the fallen pins into the pit, then
            // the bar goes back up and the standing pins are set down on their spots again (or, when the frame is over, a fresh rack is lowered). Every pin keeps its own transform until then.
            sweepFresh = fresh;
            System.Array.Clear(pitFall, 0, 10);
            for (int i = 0; i < 10; i++)
            {
                sweepFallen[i] = !BowlingLeave.Standing(standing, i + 1);
                sweepStartPos[i] = pinViews[i].transform.position; sweepStartRot[i] = pinViews[i].transform.rotation;
                // pins that already left the deck (the pit) are gone
                if (!pinViews[i].activeSelf) sweepFallen[i] = true;
            }
            if (fresh) standing = BowlingLeave.All;
            pinPositions = new Vector3[10]; pinRotations = new Quaternion[10];
            for (int i = 0; i < 10; i++)
            {
                if (sweepFallen[i]) { pinPositions[i] = BowlingLane.PinSpot(i + 1); pinRotations[i] = Quaternion.Euler(0, 37 * i, 0); continue; }
                var p = sweepStartPos[i]; p.y = 0;
                pinPositions[i] = p; pinRotations[i] = Quaternion.Euler(0, sweepStartRot[i].eulerAngles.y, 0);   // where the standing pins will be set down
            }
            if (fresh) { pinPositions = null; pinRotations = null; }
        }

        readonly bool[] sweepFallen = new bool[10];
        readonly Vector3[] sweepStartPos = new Vector3[10];
        readonly Quaternion[] sweepStartRot = new Quaternion[10];
        bool sweepFresh;
        // timeline (s): the setting table comes down and grips the standing pins, lifts them; the bar comes down, sweeps,
        // goes up; the table sets the pins down, lets go and goes home. A new frame: the table carries the old rack up
        // into the machine and brings ten fresh pins down instead.
        const float SweepGrip = .3f, SweepLift = .6f, SweepBarDown = .85f, SweepGo0 = .85f, SweepGo1 = 1.75f, SweepBarUp = 2.1f, SweepSetDown = 2.55f, SweepRelease = 2.65f, SweepEnd = 3.1f;
        const float SweepLiftHeight = .42f, SweepCarry = .45f;   // pins held clear of the bar; how far above home the old rack goes

        /// The setting table's height at sweep time t.
        float TableY(float t)
        {
            float g = BowlingPinsetter.Grip, home = BowlingPinsetter.Home;
            if (t < SweepGrip) return Mathf.Lerp(home, g, Sm(t / SweepGrip));
            if (!sweepFresh)
            {
                if (t < SweepLift) return Mathf.Lerp(g, g + SweepLiftHeight, Sm((t - SweepGrip) / (SweepLift - SweepGrip)));
                if (t < SweepBarUp) return g + SweepLiftHeight;
                if (t < SweepSetDown) return Mathf.Lerp(g + SweepLiftHeight, g, Sm((t - SweepBarUp) / (SweepSetDown - SweepBarUp)));
            }
            else
            {
                if (t < SweepBarDown) return Mathf.Lerp(g, home + SweepCarry, Sm((t - SweepGrip) / (SweepBarDown - SweepGrip)));
                if (t < SweepBarUp) return home + SweepCarry;
                if (t < SweepSetDown) return Mathf.Lerp(home + SweepCarry, g, Sm((t - SweepBarUp) / (SweepSetDown - SweepBarUp)));
            }
            if (t < SweepRelease) return g;
            return Mathf.Lerp(g, home, Sm((t - SweepRelease) / (SweepEnd - .05f - SweepRelease)));
        }

        static float Sm(float x) { x = Mathf.Clamp01(x); return x * x * (3 - 2 * x); }

        void Sweep()
        {
            float t = phaseT;
            float homeZ = BowlingLane.FoulToHeadPin - .45f, pitZ = BowlingLane.LaneEnd + .25f;
            // the sweep bar: down in front of the pins (they are lifted clear), forward along the deck, up, back to its home
            float barY, barZ;
            if (t < SweepGo0) { barY = Mathf.Lerp(.9f, .05f, Sm((t - SweepLift) / (SweepBarDown - SweepLift))); barZ = homeZ; }
            else if (t < SweepGo1) { barY = .05f; barZ = Mathf.Lerp(homeZ, pitZ, Sm((t - SweepGo0) / (SweepGo1 - SweepGo0))); }
            else { barY = Mathf.Lerp(.05f, .9f, Sm((t - SweepGo1) / (SweepBarUp - SweepGo1))); barZ = t < SweepBarUp ? pitZ : homeZ; }
            sweepBar.transform.position = new Vector3(0, barY, barZ);
            float tableY = TableY(t);
            setter.Y = tableY;
            bool held = t >= SweepGrip && t < SweepRelease;                      // the cups have the pins' heads
            float pinBase = BowlingPinsetter.PinBase(tableY);
            if (t >= SweepBarDown) PushFallenPins(barZ + .03f);
            for (int i = 0; i < 10; i++)
            {
                var pv = pinViews[i]; var tr = pv.transform;
                if (sweepFallen[i]) continue;
                // standing pin: it waits for the table, then rides in its cup (straightened, centred under the cup), and is
                // set down where it stood (a new frame: carried up into the machine and replaced)
                if (!held) continue;
                var up = Quaternion.Euler(0, sweepStartRot[i].eulerAngles.y, 0);
                float settle = Sm((t - SweepGrip) / (SweepLift - SweepGrip));
                if (!sweepFresh)
                {
                    var spot = pinPositions[i];
                    tr.position = new Vector3(Mathf.Lerp(sweepStartPos[i].x, spot.x, settle), Mathf.Max(0, pinBase), Mathf.Lerp(sweepStartPos[i].z, spot.z, settle));
                    tr.rotation = Quaternion.Slerp(sweepStartRot[i], up, settle);
                }
                else if (t < SweepBarUp)
                {
                    tr.position = new Vector3(sweepStartPos[i].x, Mathf.Max(sweepStartPos[i].y, pinBase), sweepStartPos[i].z);
                    tr.rotation = Quaternion.Slerp(sweepStartRot[i], up, settle);
                    if (pinBase > BowlingPinsetter.Home - BowlingPinsetter.Grip + .1f) pv.SetActive(false);   // up inside the machine
                }
            }
            if (sweepFresh && t >= SweepBarUp)
            {
                // ten fresh pins come down out of the machine in the table's cups and are set on the spots
                for (int i = 0; i < 10; i++)
                {
                    var pv = pinViews[i]; if (!pv.activeSelf) pv.SetActive(true);
                    var spot = BowlingLane.PinSpot(i + 1);
                    pv.transform.SetPositionAndRotation(new Vector3(spot.x, held ? Mathf.Max(0, pinBase) : 0, spot.z), Quaternion.Euler(0, 37 * i, 0));
                }
            }
            if (t < SweepEnd) return;
            sweepBar.transform.position = new Vector3(0, .9f, homeZ);
            setter.Y = BowlingPinsetter.Home;
            if (sweepFresh) FreshRack();
            else for (int i = 0; i < 10; i++)
            {
                if (sweepFallen[i]) { pinViews[i].SetActive(false); continue; }
                pinViews[i].SetActive(true); pinViews[i].transform.SetPositionAndRotation(pinPositions[i], pinRotations[i]);
            }

            var s = Scores[Current];
            bool frameOver = s.Complete || s.Ball == 0;
            if (frameOver)
            {
                int next = Current;
                for (int k = 1; k <= Players.Count; k++)
                {
                    int c = (Current + k) % Players.Count;
                    if (!Scores[c].Complete) { next = c; break; }
                }
                if (Scores[next].Complete) { Flow = Phase.GameOver; hud.Banner("WINNER!", $"{Players[Leader()]} takes it with {Scores[Leader()].Total}.", 30, BowlingHud.Praise.Big); GameOver(); return; }
                if (next != Current) { FreshRack(); }
                Current = next;
                Send(Bowler, StartSpot(Board), 0);   // the next bowler walks up from the lounge
                for (int i = 0; i < heroes.Count; i++) if (i != Current && heroes[i]) Send(heroes[i], WaitSpot(i), WaitYaw, sit: true);
            }
            EnterSetup();
        }

        readonly float[] pitFall = new float[10];

        /// The sweep bar shoves the fallen pins along the deck as solid bodies: each keeps its own lie, its near end at the bar, and
        /// rides up against any pin it runs into (no two pins in the same space); off the deck's end it falls into the pit, nose
        /// first, and is gone once it drops below the deck edge (out of sight).
        void PushFallenPins(float bar)
        {
            var order = new List<int>(10);
            for (int i = 0; i < 10; i++) if (sweepFallen[i] && pinViews[i].activeSelf) order.Add(i);
            order.Sort((a, b) => PinBounds(a).min.z.CompareTo(PinBounds(b).min.z));
            var placed = new List<Bounds>(10);
            float dt = Time.deltaTime;
            foreach (int i in order)
            {
                var tr = pinViews[i].transform;
                var bb = PinBounds(i);
                if (pitFall[i] > 0 || (bb.center.z > BowlingLane.LaneEnd && bar >= bb.min.z - .05f))   // (only once the bar gets to it)
                {
                    // into the pit: it tips over the edge and drops
                    pitFall[i] += 9.81f * dt;
                    tr.position += new Vector3(0, -pitFall[i] * dt, 1.2f * dt);
                    tr.Rotate(Vector3.right * 240f * dt, Space.World);
                    if (tr.position.y < -.3f) pinViews[i].SetActive(false);
                    continue;
                }
                float front = bar;
                foreach (var o in placed)
                    if (bb.min.x < o.max.x - .01f && bb.max.x > o.min.x + .01f && bb.max.z > o.min.z && bb.min.z < o.max.z + .02f) front = Mathf.Max(front, o.max.z);
                if (bb.min.z < front) { float push = front - bb.min.z; tr.position += Vector3.forward * push; bb.center += Vector3.forward * push; }
                placed.Add(bb);
            }
        }

        Bounds PinBounds(int i)
        {
            var rs = pinViews[i].GetComponentsInChildren<MeshRenderer>();
            Bounds b = default; bool any = false;
            foreach (var r in rs) { if (!r.enabled) continue; if (!any) { b = r.bounds; any = true; } else b.Encapsulate(r.bounds); }
            return any ? b : new Bounds(pinViews[i].transform.position, Vector3.one * .12f);
        }

        bool previousLeaveWasSplit;

        // ------------------------------------------------------------------ the replay

        bool replayDue;
        public const float ReplaySpeed = .4f;

        /// The pin action again, slow, from a low side camera (skippable with a tap on the ball).
        void BeginReplay()
        {
            replayDue = false; Flow = Phase.Replay; phaseT = 0; playT = 0;
            hud.Banner("REPLAY", "Tap the ball to skip", 1.6f, BowlingHud.Praise.Good);
            SnapCamera();
        }

        void PlayReplay(float dt)
        {
            playT += dt * ReplaySpeed;
            var frames = LastAction.Frames;
            int k = Mathf.Min(frames.Count - 1, Mathf.FloorToInt(playT * 60));
            var f = frames[k];
            for (int n = 0; n < 10; n++)
            {
                if (!BowlingLeave.Standing(LastAction.StandingBefore, n + 1)) continue;
                pinViews[n].SetActive(true);
                pinViews[n].transform.SetPositionAndRotation(f.Pins[n], f.PinRotations[n]);
            }
            ballView.SetActive(f.BallLive);
            if (f.BallLive) ballView.transform.SetPositionAndRotation(f.Ball, f.BallRotation * ballSpin);
            if (k >= frames.Count - 1 || playT > 3.2f) EndReplay();
        }

        void EndReplay()
        {
            if (Flow != Phase.Replay) return;
            // the pins as they finished (the sweep reads them)
            var last = LastAction.Frames[LastAction.Frames.Count - 1];
            for (int n = 0; n < 10; n++)
                if (BowlingLeave.Standing(LastAction.StandingBefore, n + 1)) pinViews[n].transform.SetPositionAndRotation(last.Pins[n], last.PinRotations[n]);
            ballView.SetActive(false);
            BeginSweep(); SnapCamera();
        }

        int Leader()
        {
            int best = 0;
            for (int i = 1; i < Players.Count; i++) if (Scores[i].Total > Scores[best].Total) best = i;
            return best;
        }

        void FreshRack()
        {
            standing = BowlingLeave.All; pinPositions = null; pinRotations = null;
            for (int i = 0; i < 10; i++)
            {
                pinViews[i].SetActive(true);
                pinViews[i].transform.SetPositionAndRotation(BowlingLane.PinSpot(i + 1), Quaternion.Euler(0, 37 * i, 0));
            }
        }

        // ------------------------------------------------------------------ camera

        void TargetShot(out Vector3 pos, out Vector3 look)
        {
            float x = BowlingLane.BoardX(Board);
            switch (Flow)
            {
                case Phase.Rolling when laneRecord.Count > 0 && !LastThrow.Dropped:
                {
                    // after the ball from the moment it leaves the hand: behind the bowler (the approach shot) the camera turns down the
                    // lane with the ball and eases in; once the ball is well away it cuts to the low chase behind it (it never flies
                    // over the bowler: their head, the follow-through and each venue's ceiling stay clear)
                    var b = laneRecord[Mathf.Min(laneRecord.Count - 1, Mathf.FloorToInt(playT * 60))].Position;
                    if (b.z > 13.5f) { pos = new Vector3(0, .95f, 14.8f); look = new Vector3(0, .12f, BowlingLane.FoulToHeadPin + .4f); return; }
                    if (b.z < ChaseFrom)
                    {
                        float z0 = BowlingApproach.BodyZ(releaseAt, foulSlide) - 4.4f;
                        pos = new Vector3(x * .4f, 2.15f, z0 + Mathf.Min(1f, Mathf.Max(0, b.z) * .18f));
                        look = new Vector3(Mathf.Lerp(x * .2f, b.x * .4f, Sm(b.z / 2)), .1f, b.z + 7); return;
                    }
                    float u = Sm((b.z - ChaseFrom) / 6f);
                    pos = new Vector3(b.x * .5f, Mathf.Lerp(1.05f, .62f, u), b.z - Mathf.Lerp(3.3f, 2.6f, u)); look = new Vector3(b.x * .4f, .1f, b.z + 6); return;
                }
                case Phase.Result when reactShot && phaseT > .8f && Bowler:
                {
                    // the reaction shot: looking back up the lane at the bowler, the gallery and the lounge behind them
                    var h = Bowler.Position;
                    pos = new Vector3(h.x + .6f, 1.4f, h.z + 3.4f); look = new Vector3(h.x, 1.05f, h.z - 3); return;
                }
                case Phase.Pins:
                case Phase.Result:
                    pos = new Vector3(0, .95f, 14.8f); look = new Vector3(0, .12f, BowlingLane.FoulToHeadPin + .4f); return;
                case Phase.Replay:
                {
                    // low on the lane in front of the deck (inside the kickbacks, under the masking), easing in as the pins go
                    float u = Sm(playT / 3f);
                    pos = new Vector3(Mathf.Lerp(.42f, .3f, u), .32f, BowlingLane.FoulToHeadPin - Mathf.Lerp(1.15f, .8f, u)); look = new Vector3(-.05f, .18f, BowlingLane.FoulToHeadPin + .35f); return;
                }
                case Phase.Sweep:
                    pos = new Vector3(0, 1.1f, 13.6f); look = new Vector3(0, .2f, BowlingLane.FoulToHeadPin + .4f); return;
                case Phase.Approach:
                case Phase.Rolling:
                {
                    float z = BowlingApproach.BodyZ(approachT, foulSlide);
                    pos = new Vector3(x * .4f, 2.15f, z - 4.4f); look = new Vector3(x * .2f, .3f, z + 11); return;
                }
                default:
                    // someone walking between the lounge and the lane passes right under the camera: look back at the bowler from
                    // the lane instead (the lounge behind them) until they are clear
                    if (Flow == Phase.Setup && Bowler && LoungeWalker() != null)
                    {
                        // from just in front of the stance (clear of the lounge and the gallery), watching them walk up to it
                        var h = Bowler.Position;
                        pos = new Vector3(BowlingHero.BodyX(Board) + 1.2f, 1.55f, BowlingApproach.StartZ + 2.4f); look = new Vector3(h.x, 1.0f, Mathf.Min(h.z, BowlingApproach.StartZ - .5f)); return;
                    }
                    // Wii-style: high behind the bowler, who stands to one side of the frame; the pins stay in view.
                    pos = new Vector3(x * .35f, 2.4f, BowlingApproach.StartZ - 4.8f); look = new Vector3(x * .15f, .2f, 12); return;
            }
        }

        const float ChaseFrom = 6f;   // the ball's distance down the lane (m) where the shot cuts from behind the bowler to the chase

        /// A hero walking in the stretch between the lounge and the stance (where the setup camera stands), or null.
        BowlingHero LoungeWalker()
        {
            foreach (var h in heroes) if (h && !h.Arrived && h.Position.z < BowlingApproach.StartZ - 1.8f) return h;
            return null;
        }

        void SnapCamera() { TargetShot(out camPos, out camLook); cam.transform.SetPositionAndRotation(camPos, Quaternion.LookRotation(camLook - camPos)); }

        void Shoot(float dt)
        {
            TargetShot(out var pos, out var look);
            bool cut = (pos - camPos).sqrMagnitude > 25;   // big jumps are cuts, not pans
            float k = cut ? 1 : 1 - Mathf.Exp(-dt * (Flow == Phase.Rolling ? 12 : 6));   // (the ball cam keeps up with the ball)
            camPos = Vector3.Lerp(camPos, pos, k); camLook = Vector3.Lerp(camLook, look, k);
            cam.transform.SetPositionAndRotation(camPos, Quaternion.LookRotation(camLook - camPos));
        }

        // ------------------------------------------------------------------ input

        /// Editor keyboard play (off for proof films that drive the phone path: Space up would drop every held ball).
        public bool KeyboardEnabled = true;

        void KeyboardInput(float dt)
        {
            if (Autoplay.Count > 0 || !Application.isEditor || !KeyboardEnabled) return;
            if (Input.GetKey(KeyCode.LeftArrow) || Input.GetKey(KeyCode.A)) Move(+8 * dt); // boards count from the right
            if (Input.GetKey(KeyCode.RightArrow) || Input.GetKey(KeyCode.D)) Move(-8 * dt);
            if (Input.GetKey(KeyCode.Z)) AimBy(-2 * dt);
            if (Input.GetKey(KeyCode.C)) AimBy(+2 * dt);
            if (Input.GetKeyDown(KeyCode.UpArrow)) SwingSpeed = Mathf.Min(9.5f, SwingSpeed + .3f);
            if (Input.GetKeyDown(KeyCode.DownArrow)) SwingSpeed = Mathf.Max(4, SwingSpeed - .3f);
            if (Input.GetKeyDown(KeyCode.Q)) AxisDeg = Mathf.Min(70, AxisDeg + 10);
            if (Input.GetKeyDown(KeyCode.E)) AxisDeg = Mathf.Max(-60, AxisDeg - 10);
            if (Input.GetKeyDown(KeyCode.R)) RevRpm = Mathf.Min(450, RevRpm + 40);
            if (Input.GetKeyDown(KeyCode.F)) RevRpm = Mathf.Max(0, RevRpm - 40);
            SetHold(Input.GetKey(KeyCode.Space));
        }

        float autoMoveT;
        void AutoplayInput(float dt)
        {
            if (Autoplay.Count == 0 || !IsLocal(Current)) return;   // (another phone bowls its own players)
            var shot = Autoplay.Peek();
            switch (Flow)
            {
                case Phase.Setup:
                    SwingSpeed = shot.Speed; RevRpm = shot.Rpm; AxisDeg = shot.Axis;
                    float d = shot.Board - Board;
                    if (Mathf.Abs(d) > .25f) { Move(Mathf.Sign(d) * Mathf.Min(Mathf.Abs(d), Mathf.Max(.5f, 10 * dt))); autoMoveT = 0; return; }   // (Move rounds to half boards: at least one half-board a frame)
                    autoMoveT += dt;
                    if (autoMoveT > .5f) SetHold(true);
                    break;
                case Phase.Approach:
                    if (approachT >= BowlingApproach.IdealRelease + shot.Timing) { SetHold(false); Autoplay.Dequeue(); }
                    break;
            }
            // A shot that never lets go is a foul: the game releases it, so move on to the next plan.
            if (Flow == Phase.Rolling && Holding) { Holding = false; Autoplay.Dequeue(); }
        }
    }
}
