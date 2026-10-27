using UnityEngine;
using UnityEngine.Rendering.Universal;
using GolfArcade.Course;
using GolfArcade.Profile;
using GolfArcade.Shot;
using GolfArcade.Swing;
namespace GolfArcade.Game {
    public sealed partial class GolfGame {
        public static event System.Action ShotStruck;
        public bool NativeControlled { get; private set; }
        public bool NativeHasNextHole => Current == State.RoundDone && holeIndex + 1 < course.Holes.Length;
        /// The state the app's screens follow.
        public string NativePhase => Current.ToString();
        public static event System.Action NativeExitRequested;
        void RequestNativeExit() { enabled = false; NativeExitRequested?.Invoke(); }
        public Camera GameplayCamera => rig ? rig.Camera : null;
        public double TutorialHeading => heading;
        public GolfArcade.UI.Hud TutorialHud => hud;
        public int TutorialHole => holeIndex;
        public void PrepareNativeAddress(string courseKey = null) { var steps = PrepareNativeAddressSteps(courseKey); while (steps.MoveNext()) { } }
        /// PrepareNativeAddress with the first hole built a slice per step (it yields 0..1): a round launched from a plaza
        /// bay builds behind the plaza, which keeps drawing between the slices.
        public System.Collections.Generic.IEnumerator<float> PrepareNativeAddressSteps(string courseKey = null) {
            NativeControlled = true; controllerMapHole = -1;
            hud.HideMenu(); home = null;
            hud.HideCourses(); courses = null;
            hud.HideLocker(); stage?.Hide();
            if (bigScreen) bigScreen.enabled = false;
            SetFog(0);
            var selected = GolfArcade.Course.Course.ByKey(courseKey ?? "cliffside") ?? GolfArcade.Course.Course.Cliffside();
            setup = GameSetup.Solo(ProfileStore.Active, selected.Key);
            // the day's forecast round: the date is the seed, the same round for everyone that day
            if (DailyRound > 0) setup.Seed = DailyRound;
            deferFirstHole = true; StartRound(); deferFirstHole = false;
            if (firstHoleSteps != null)
            {
                var build = firstHoleSteps; firstHoleSteps = null;
                loadingHole = true;   // the frame loop stands still on the half-built hole
                try { while (build.MoveNext()) yield return build.Current; } finally { loadingHole = false; }
            }
            golfPresentation.Cancel(); pendingNativeIntro=true;
            BeginAim(false); hud.ShowPlayHud(true); RefreshControls();
            rig.SnapNext(); rig.ApplyFrame();
        }
        public void NativeContinue() {
            if(Current==State.Intro) { SkipPresentation(); return; }
            if (Current == State.Replay) { SkipReplay(); return; }
            if (Current == State.Result) { ContinueShotResult(); return; }
            if (Current != State.RoundDone || networkConfigured) return;   // (a multiplayer round's end belongs to the lobby)
            if (NativeHasNextHole) NextHole(); else PlayAgain();

        }
        /// The controller sheet's pause button: the app pauses the round and shows its pause screen.
        public static event System.Action NativePauseRequested;
        bool phoneController;
        Camera phoneBackdrop, phoneMapCamera;
        RenderTexture phoneMapTexture;
        object renderedPhoneMapFor;
        Vector3 renderedPhoneMapPosition;
        Quaternion renderedPhoneMapRotation;
        float renderedPhoneMapSize;

        /// Golf as it played on the standalone build: the course and its overlay on the TV, and the
        /// phone's own screen (display 0) the controller sheet: the map with the landing zones, the
        /// club card, the aim pad. The app brings Unity's phone window forward while a shot is lined
        /// up and played; its own screens stay for Ready, pause, the shot's result and the hole's end.
        public void NativePhoneController() {
            if (phoneController && hud.Controller != null && hud.Controller.Alive) return;
            // (a big-screen layout left over from the standalone app's setting has the sheet on the TV)
            if (hud.Controller != null) hud.LeaveControllerLayout();
            phoneController = true;
            if (!phoneBackdrop) {
                phoneBackdrop = new GameObject("Phone backdrop").AddComponent<Camera>();
                phoneBackdrop.transform.SetParent(transform, false);
                phoneBackdrop.gameObject.AddComponent<GolfArcade.UI.PhoneScreenOnly>();
                phoneBackdrop.clearFlags = CameraClearFlags.SolidColor; phoneBackdrop.backgroundColor = GolfArcade.UI.UiKit.Ground;
                phoneBackdrop.cullingMask = 0; phoneBackdrop.depth = -100; phoneBackdrop.targetDisplay = 0;
                var data = phoneBackdrop.GetUniversalAdditionalCameraData();
                data.renderShadows = false; data.renderPostProcessing = false; data.requiresDepthTexture = false; data.requiresColorTexture = false;
            }
            phoneBackdrop.enabled = true;
            if (!phoneMapCamera) {
                phoneMapCamera = new GameObject("Phone map camera").AddComponent<Camera>();
                phoneMapCamera.transform.SetParent(transform, false);
                phoneMapCamera.CopyFrom(minimapCamera);
                phoneMapCamera.enabled = false;
                var data = phoneMapCamera.GetUniversalAdditionalCameraData();
                data.renderShadows = false; data.renderPostProcessing = false; data.requiresDepthTexture = false; data.requiresColorTexture = false;
                var size = GolfArcade.UI.Hud.ControllerMapSize;
                phoneMapTexture = new RenderTexture((int)size.x, (int)size.y, 16);
                phoneMapCamera.targetTexture = phoneMapTexture;
            }
            hud.EnterPhoneController();
            var sheet = hud.Controller;
            sheet.OnClub = i => SelectClub(GolfArcade.Shot.GolfClubs.All[i]);
            sheet.SetScreen(true);
            sheet.Skip.Pressed = () => { if (Current is State.Replay or State.Result) SkipReplay(); else SkipPresentation(); };
            for (int i = 0; i < sheet.IntroEmotes.Length; i++) { int slot = i; sheet.IntroEmotes[i].Pressed = () => ChooseIntroEmote(slot); }
            // tap to swing: a tap starts the swing at once, a second tap cancels it
            sheet.StartSwing.Pressed = () => {
                if (NativeSwingTracking) { heldOnSheet = true; NativeReleaseSwing(); return; }
                NativeStartSwing(); heldOnSheet = NativeSwingTracking; if (heldOnSheet) Haptics.Tick();
            };
            sheet.StartSwing.Released = null;
            sheet.Pause.gameObject.SetActive(true);
            sheet.Pause.Pressed = () => NativePauseRequested?.Invoke();
            hud.PhoneMapCamera = phoneMapCamera;
            hud.Minimap.texture = phoneMapTexture; hud.TvMapTexture = minimapTexture;
            if (hole != null && Card != null) { hud.SetHole(hole.Number, hole.Par, hole.Length, hole.Picture, hole.Name); ShowScore(); }
            renderedPhoneMapFor = null;
            if (hole != null) FrameMinimap();
            ShowControllerForState();
            RefreshControls();
            if (Current == State.Aim) UpdateAimVisuals();
        }

        /// The phone card's map: the TV map's framing (`framed`, the whole hole and the shot), widened
        /// to the card's shape, drawn again only when that framing moves.
        void FramePhoneMap(Transform framed, float halfUp, float halfAcross) {
            if (!phoneMapCamera) return;
            float aspect = (float)phoneMapTexture.width / phoneMapTexture.height;
            phoneMapCamera.transform.SetPositionAndRotation(framed.position, framed.rotation);
            phoneMapCamera.farClipPlane = minimapCamera.farClipPlane;
            phoneMapCamera.orthographicSize = Mathf.Max(halfUp, halfAcross / aspect) * 1.14f;
            phoneMapCamera.aspect = aspect;
            if (renderedPhoneMapFor == hole && (renderedPhoneMapPosition - framed.position).sqrMagnitude <= .01f &&
                Quaternion.Angle(renderedPhoneMapRotation, framed.rotation) <= .1f &&
                Mathf.Abs(renderedPhoneMapSize - phoneMapCamera.orthographicSize) <= .01f) return;
            UnityEngine.Rendering.RenderPipeline.SubmitRenderRequest(phoneMapCamera,
                new UnityEngine.Rendering.Universal.UniversalRenderPipeline.SingleCameraRequest { destination = phoneMapTexture });
            renderedPhoneMapFor = hole; renderedPhoneMapPosition = framed.position; renderedPhoneMapRotation = framed.rotation; renderedPhoneMapSize = phoneMapCamera.orthographicSize;
        }

        public void NativeAim(float value) { if(Current==State.Aim) Nudge(Mathf.Clamp(value,-1,1)*AimTapDegrees); }
        public void NativeClub(int value) { if(Current==State.Aim) { NativeCancelSwing(); CycleClub(value); } }
        // The joystick uses the same axes as the phone's course map. Set the shot's
        // actual heading, so both the TV flight and the projected landing line agree.
        public void NativeAimDirection(float across,float forward) {
            if(Current!=State.Aim || !minimapCamera || float.IsNaN(across) || float.IsNaN(forward) ||
               float.IsInfinity(across) || float.IsInfinity(forward)) return;
            var direction=minimapCamera.transform.right*across+minimapCamera.transform.up*forward;
            direction.y=0;
            if(direction.sqrMagnitude<.01f) return;
            double desired=System.Math.Atan2(direction.x,direction.z)*180/System.Math.PI;
            // (in a multiplayer round too: the phone with the player up aims, and tells the host)
            Nudge(Mathf.DeltaAngle((float)heading,(float)desired));
        }
        [System.Serializable] public sealed class ControllerPoint {
            public float x,y;
            public ControllerPoint(Vector3 viewport) { x=viewport.x; y=viewport.y; }
        }
        [System.Serializable] public sealed class PartyControllerPlayer {
            public int seat; public string name; public bool controlled,canEmote; public string[] emotes;
        }
        [System.Serializable] public sealed class PartyControllerReading {
            public int turn; public long shotID; public string player,outcome,phase;
            public bool myTurn,shared,putt; public double resultSeconds,carry,roll,apex,total;
            public PartyControllerPlayer[] players;
        }
        [System.Serializable] public sealed class ControllerReading {
            public PartyControllerReading party;
            public int hole,holeId,par,clubIndex;
            public string name,clubName,mapImage;
            public double yards,wind,windDegrees,clubYards,aimDegrees;
            public ControllerPoint ball,pin,landing,direction;
            public ControllerPoint[] path,reach;
            /// A putt's meter marks on the map (25/50/75/100 %) and their feet; empty on a full shot.
            public ControllerPoint[] targets; public string[] targetLabels;
        }
        int controllerMapHole=-1;
        Vector3 controllerMapPosition;
        float controllerMapSize;
        RenderTexture controllerMapTarget;
        // Metadata/marks are sent at 4 Hz. Reuse the already-rendered HUD map: no new camera
        // renders. Read back and JPEG-encode it only when the map's cached framing changes.
        public ControllerReading NativeControllerReading() {
            if(hole==null || !hud || !minimapCamera) return null;
            bool putting = hole.LieAt(ballAt).IsPuttingSurface();
            var reading=new ControllerReading {
                hole=hole.PlayNumber,holeId=hole.Number,name=hole.Name,par=hole.Par,yards=ballAt.DistanceTo(hole.Pin),
                wind=Wind.SpeedMPH,windDegrees=Wind.RelativeTo(heading),
                clubIndex=System.Array.IndexOf(GolfArcade.Shot.GolfClubs.All,club),
                clubName=GolfArcade.Shot.GolfClubs.DisplayName(club),clubYards=GolfArcade.Shot.GolfClubs.ReferenceDistanceYards(club),
                aimDegrees=Mathf.DeltaAngle((float)ballAt.HeadingTo(putting ? hole.Pin : hole.RecommendedTarget(ballAt)),(float)heading),
                ball=new ControllerPoint(minimapCamera.WorldToViewportPoint(hud.Map.Ball)),
                pin=new ControllerPoint(minimapCamera.WorldToViewportPoint(hud.Map.Pin)),
                landing=new ControllerPoint(minimapCamera.WorldToViewportPoint(hud.Map.Landing)),
                path=ControllerPoints(hud.Map.Path),reach=ControllerPoints(hud.Map.Reach),
                direction=new ControllerPoint(minimapCamera.transform.InverseTransformDirection(AimDirection()))
            };
            if(hud.Map.TargetLabels.Count>0){
                reading.targets=ControllerPoints(hud.Map.Targets);reading.targetLabels=hud.Map.TargetLabels.ToArray();
            }
            if(minimapTexture && renderedMapHole==hole.Number &&
               (controllerMapHole!=hole.Number || controllerMapTarget!=minimapTexture ||
                controllerMapPosition!=minimapCamera.transform.position || controllerMapSize!=minimapCamera.orthographicSize)) {
                var previous=RenderTexture.active;
                var rt=RenderTexture.GetTemporary(256,Mathf.RoundToInt(256f/minimapCamera.aspect),0,RenderTextureFormat.ARGB32);
                Texture2D cpu=null;
                try {
                    Graphics.Blit(minimapTexture,rt);RenderTexture.active=rt;
                    cpu=new Texture2D(rt.width,rt.height,TextureFormat.RGB24,false);
                    cpu.ReadPixels(new Rect(0,0,rt.width,rt.height),0,0);cpu.Apply();
                    reading.mapImage=System.Convert.ToBase64String(cpu.EncodeToJPG(82));
                    controllerMapHole=hole.Number;controllerMapTarget=minimapTexture;
                    controllerMapPosition=minimapCamera.transform.position;controllerMapSize=minimapCamera.orthographicSize;
                } finally { RenderTexture.active=previous;RenderTexture.ReleaseTemporary(rt);if(cpu) Destroy(cpu); }
            }
            if(networkConfigured)FillPartyReading(reading);
            return reading;
        }
        ControllerPoint[] ControllerPoints(System.Collections.Generic.List<Vector3> points) {
            int count=Mathf.Min(24,points.Count);var output=new ControllerPoint[count];
            for(int i=0;i<count;i++) {
                int at=count<2?0:Mathf.RoundToInt(i*(points.Count-1f)/(count-1));
                output[i]=new ControllerPoint(minimapCamera.WorldToViewportPoint(points[at]));
            }
            return output;
        }
        public string NativeFeedback() {
            if(Current==State.RoundDone) return $"Round complete · {Card.Total} strokes · {Card.ToPar:+0;-0;0} to par";
            if(Current==State.Result) return ShotResultTitle + " · " + ShotStatistics;
            if(LastShot!=null && Current==State.HoleDone) return $"Carry {LastShot.Carry:F0} yd · Total {LastShot.Total:F0} yd · {LastShot.Lie}";
            return $"{Current} · {Swing.Phase} · Load {Swing.Detector.Load:P0}";
        }
        public void NativeSwing(float power) {
            if(Current!=State.Aim || !NativeShotReady) return;
            golfer.ShowLoad(power);
            OnImpact(new SwingImpact { Power=power, Backswing=power, PeakSpeed=power*16, Commit=1.2, DownswingSeconds=.25, TempoSeconds=.7 });
        }
        public bool NativeShotReady { get; private set; }
        /// Motion counts only while this is on: the player taps the swing button on the phone, and
        /// the shot ends it (as does a second tap, a new aim, a club change, a pause or a stretch with
        /// no backswing). Without it, handling the phone to aim or change club could be read as a swing.
        public bool NativeSwingTracking { get; private set; }
        /// The swing button's face: 0 tap to swing · 2 swinging, tap again to cancel (1, hold still, is retired:
        /// a tap starts the swing at once).
        public int NativeSwingState => NativeSwingTracking ? 2 : 0;
        public void RequireNativeReady() {
            NativeShotReady = false; needsReadyPose = false; NativeSwingTracking = false;
            Swing.Detector.Reset();
            RefreshSwingButton();
        }
        bool needsReadyPose;
        // The tap starts the swing at once. Its grip is the phone's pose on the first calm sample (the tap itself
        // jolts the phone), or on whatever sample comes GripMaxWaitSeconds after the tap: never a wait for stillness.
        const float GripStillRate = .8f, PuttGripStillRate = .3f;
        const double GripMaxWaitSeconds = .3;
        // A swing started and then left alone this long (the phone put down, a chat in the middle of a putt) resets.
        const double TapIdleSeconds = 12;
        double gripStillSince = -1, trackingSince = -1;
        int nativeLoadFrame = -1;
        /// The shot is lined up and can be aimed (and swung by touch). It does not start motion
        /// tracking: that waits for NativeStartSwing.
        public void NativeReady(System.Numerics.Quaternion? grip = null) {
            if (Current != State.Aim) return;
            NativeShotReady = true; NativeSwingTracking = false; Swing.Detector.UseReadyPose=true; needsReadyPose=true; gripStillSince=-1; Swing.Detector.Reset();
            if (grip.HasValue) CaptureNativeGrip(grip.Value);
            RefreshSwingButton();
        }
        /// The swing button tapped: begin reading the swing at once, whatever the phone is doing. The starting
        /// grip is the phone's pose as it settles from the tap (the one sent with the tap when it sends one).
        public void NativeStartSwing(System.Numerics.Quaternion? grip = null) {
            heldOnSheet = false; releasePending = false; CancelInvoke(nameof(FinishNativeRelease));
            if (Current != State.Aim || !NativeShotReady) return;
            NativeSwingTracking = true; Swing.Detector.UseReadyPose=true; needsReadyPose=true; gripStillSince=-1; trackingSince=-1; Swing.Detector.Reset();
            if (grip.HasValue) CaptureNativeGrip(grip.Value);
            RefreshSwingButton();
        }
        /// The swing button tapped again (or the old let-go). Before contact that resets the swing: the golfer back at the
        /// address, nothing hit, the button to be tapped again. Once the club is on its way down a
        /// let-go waits ReleaseGraceSeconds first, so a thumb that comes off at contact, or a
        /// release that reaches Unity a sample ahead of the impact, doesn't throw away a struck ball.
        public void NativeReleaseSwing() {
            if (!NativeSwingTracking || releasePending) return;
            if (Swing.Phase == SwingPhase.Downswing) { releasePending = true; Invoke(nameof(FinishNativeRelease), ReleaseGraceSeconds); return; }
            ResetHeldSwing();
        }
        public const float ReleaseGraceSeconds = .2f;
        bool releasePending, heldOnSheet;
        void FinishNativeRelease() {
            if (!releasePending) return;
            releasePending = false;
            if (Current == State.Aim && NativeSwingTracking) ResetHeldSwing();
        }
        void ResetHeldSwing() {
            NativeCancelSwing();
            if (heldOnSheet) Haptics.Warning();   // (the app's own button buzzes on the phone side)
            heldOnSheet = false;
            swingResetAt = Time.time;
        }
        float swingResetAt = -10;
        /// The TV's line while the swing button is not held: for a moment after a let-go, that it reset.
        string NativeIdleStatus => Time.time - swingResetAt < 2.5f
            ? "Swing cancelled — tap the swing button to go again"
            : "Line up your shot, then tap the swing button on your phone and swing";
        /// Back to waiting for the swing button, ending a backswing already begun.
        public void NativeCancelSwing() {
            if (!NativeSwingTracking) return;
            if (Swing.Phase is SwingPhase.Backswing or SwingPhase.Downswing) OnCancel();
            NativeSwingTracking = false; Swing.Detector.Reset();
            RefreshSwingButton();
        }
        void CaptureNativeGrip(System.Numerics.Quaternion q) {
            lastReadyGrip=q; Swing.Detector.SetReadyPose(q); needsReadyPose=false;
            RefreshSwingButton();
        }
        /// The button on the phone's controller sheet: shown while a motion shot is lined up.
        void RefreshSwingButton() {
            var sheet = hud != null ? hud.Controller : null;
            if (sheet == null || !sheet.Alive) return;
            sheet.SetSwingButton(NativeControlled && Current == State.Aim && NativeShotReady && !NativeSportsSession.Touch, NativeSwingState);
        }
        public void NativeMotion(in NativeSportsSession.Sample sample) {
            if(Current==State.Intro) {
                float speed=sample.rx*sample.rx+sample.ry*sample.ry+sample.rz*sample.rz;
                if(!float.IsNaN(speed) && !float.IsInfinity(speed) && speed>20) { presentationMotionConsumed=true; SkipPresentation(); }
                return;
            }
            if (Current != State.Aim || !NativeShotReady || !NativeSwingTracking) return; // Only a started swing counts: not follow-through, result-screen or handling motions.
            var q=new System.Numerics.Quaternion(sample.qx,sample.qy,sample.qz,sample.qw);
            var rate = new System.Numerics.Vector3(sample.rx,sample.ry,sample.rz);
            var gravity = new System.Numerics.Vector3(sample.gx,sample.gy,sample.gz);
            if(float.IsNaN(q.LengthSquared()) || float.IsInfinity(q.LengthSquared()) || q.LengthSquared()<.5f ||
               float.IsNaN(rate.LengthSquared()) || float.IsInfinity(rate.LengthSquared())) return;
            if (trackingSince < 0) trackingSince = sample.time;
            if (needsReadyPose) {
                // The swing is live from the tap. Its grip is the first calm pose (the tap's own jolt dies out
                // within a moment), and past GripMaxWaitSeconds the pose as it is: nothing waits for stillness.
                if (gripStillSince < 0) gripStillSince = sample.time;
                bool calm = rate.Length() <= (club == GolfClub.Putter ? PuttGripStillRate : GripStillRate);
                if (!calm && sample.time - gripStillSince < GripMaxWaitSeconds) return;
                CaptureNativeGrip(q);
                Debug.Log("[SportsMotion] Ready pose captured");
            }
            if (Swing.Phase is SwingPhase.Backswing or SwingPhase.Downswing) trackingSince = sample.time;
            else if (sample.time - trackingSince > TapIdleSeconds) { ResetHeldSwing(); return; }
            var detector = Swing.Detector;
            var before = detector.Phase;
            var e = detector.Ingest(sample.time,q,rate,gravity);
            // the golfer's downswing follows the phone's, turn for turn, so the club meets the ball on the sample the phone does
            if (detector.Phase == SwingPhase.Downswing) golfer.PaceDownswing((float)detector.DownswingProgress, sample.time);
            if(e==null) return;
            switch(e.Value.Kind) {
                case SwingEventKind.Load:
                    if (detector.Phase == SwingPhase.Downswing && before != SwingPhase.Downswing) {
                        ExperienceTrace.Begin("golf", "downswing-pose");
                        ExperienceTrace.NativeEvent("golf", "downswing-source", 0, sample.time);
                        golfer.Strike();
                    }
                    else if (detector.Phase == SwingPhase.Backswing && nativeLoadFrame != Time.frameCount) {
                        nativeLoadFrame = Time.frameCount;
                        OnLoad(e.Value.Load);
                    }
                    break;
                case SwingEventKind.Cancel: ExperienceTrace.Mark("golf", "cancel"); OnCancel(); break;
                case SwingEventKind.Impact:
                    var impact=e.Value.Impact;
                    Debug.Log($"[SportsMotion] golf impact speed={impact.PeakSpeed:F2} power={impact.Power:F2}");
                    if(NativeSportsSession.Left) { impact.FaceDegrees*=-1; impact.CurveDegrees*=-1; impact.StartLineDegrees*=-1; }
                    OnImpact(impact);
                    ExperienceTrace.NativeEvent("golf", "address-crossing-source", 0, sample.time); break;
            }
        }

    }
}
