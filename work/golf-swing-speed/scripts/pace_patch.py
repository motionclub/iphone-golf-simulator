#!/usr/bin/env python3
"""pace_patch.py <Unity project root> [--check] [--revert]
GOLF SWING SPEED: the phone paces the golfer's downswing. Exact-line patch (other sessions edit these files):
  Scripts/Swing/MotionSwingDetector.cs  DownswingProgress (0 at the phone's top .. 1 at the ball, along the swing's arc)
  Scripts/Game/GolfGame.Native.cs       each downswing sample -> golfer.PaceDownswing(progress)
  Scripts/Game/GolferView.cs            the downswing follows the phone turn for turn (clip time from the club's own turn),
                                        no rewind at the phone's impact, follow-through at the pace actually swung,
                                        a full phone backswing counts as full even if the shown pose lags it
Idempotent: a file already carrying the patch is left alone. --check only reports. --revert takes exactly these edits back out
(each new block back to its old text), leaving every other session's edits in those files alone.
A path ending in .cs instead of a project root patches that one file (its name picks the edit set): used to stage the index copy.
"""
import sys, os

ROOT = sys.argv[1]
CHECK = '--check' in sys.argv
REVERT = '--revert' in sys.argv
S = os.path.join(ROOT, 'Assets', 'Scripts')

def patch(rel, edits, marker):
    if ROOT.endswith('.cs'):
        if os.path.basename(ROOT) != os.path.basename(rel): return
        p = ROOT
    else:
        p = os.path.join(S, rel)
    s = open(p).read()
    if REVERT:
        if marker not in s:
            print(f'{rel}: not patched'); return
        edits = [(new, old) for old, new in reversed(edits)]
    elif marker in s:
        print(f'{rel}: already patched'); return
    for old, new in edits:
        n = s.count(old)
        if n != 1:
            raise SystemExit(f'{rel}: anchor found {n}x:\n{old}')
        s = s.replace(old, new)
    if CHECK:
        print(f'{rel}: would patch ({len(edits)} edits)'); return
    open(p, 'w').write(s)
    print(f'{rel}: {"reverted" if REVERT else "patched"} ({len(edits)} edits)')

# ---------------------------------------------------------------- detector
patch('Swing/MotionSwingDetector.cs', [
("""        public double Load { get; private set; }
""",
"""        public double Load { get; private set; }

        /// While the phone comes down: how far it has turned from the top of its backswing back to address, along the swing's
        /// own arc: 0 at the top, 1 at the ball (more once past it). A golfer on screen follows this to meet the ball with the phone.
        public double DownswingProgress { get; private set; }
        double topTurn;
"""),
("""            peakAngle = peakSpeed = downswingStart = swingStart = backswingLoad = 0;
""",
"""            peakAngle = peakSpeed = downswingStart = swingStart = backswingLoad = 0;
            DownswingProgress = topTurn = 0;
"""),
("""                        var axis = RotationAxis(reference, attitude);
                        if (Vector3.Dot(axis, swingAxis) >= 0) swingAxis = axis;
                    }
""",
"""                        var axis = RotationAxis(reference, attitude);
                        if (Vector3.Dot(axis, swingAxis) >= 0) swingAxis = axis;
                        topTurn = AlongTheArc ? angle : TurnAbout(reference, attitude, swingAxis);
                    }
"""),
("""                        backswingLoad = LoadFor(peakAngle);
                        Load = backswingLoad;
                        return SwingEvent.Loaded(Load);
""",
"""                        backswingLoad = LoadFor(peakAngle);
                        Load = backswingLoad;
                        DownswingProgress = Progress(angle, attitude);
                        return SwingEvent.Loaded(Load);
"""),
("""                case SwingPhase.Downswing:
                    peakSpeed = Math.Max(peakSpeed, speed);
""",
"""                case SwingPhase.Downswing:
                    peakSpeed = Math.Max(peakSpeed, speed);
                    DownswingProgress = Progress(angle, attitude);
"""),
("""        double LoadFor(double angle) => Math.Min(1, Math.Max(0, angle / FullBackswing));
""",
"""        double LoadFor(double angle) => Math.Min(1, Math.Max(0, angle / FullBackswing));

        /// DownswingProgress for the phone at `attitude`: the turn back from the top, as a share of the top's turn from address.
        double Progress(double angle, Quaternion attitude)
        {
            double turn = AlongTheArc ? angle : TurnAbout(reference, attitude, swingAxis);
            return topTurn > 1e-3 ? Math.Max(0, (topTurn - turn) / topTurn) : 1;
        }
"""),
], 'DownswingProgress')

# ---------------------------------------------------------------- game: feed the golfer each downswing sample
patch('Game/GolfGame.Native.cs', [
("""            var e = detector.Ingest(sample.time,q,rate,gravity);
            if(e==null) return;
""",
"""            var e = detector.Ingest(sample.time,q,rate,gravity);
            // the golfer's downswing follows the phone's, turn for turn, so the club meets the ball on the sample the phone does
            if (detector.Phase == SwingPhase.Downswing) golfer.PaceDownswing((float)detector.DownswingProgress, sample.time);
            if(e==null) return;
"""),
], 'PaceDownswing')

# ---------------------------------------------------------------- golfer view
patch('Game/GolferView.cs', [
# fields
("""        float swingU, swingRate, throughV, throughSeconds, finishTime;
""",
"""        float swingU, swingRate, throughV, throughSeconds, finishTime;
        // A phone swing paces its own downswing (PaceDownswing): the club is as far along its path from the top to the ball as
        // the phone is through the player's turn, so it meets the ball on the sample the phone does, which is the shot's impact (the
        // clock above only runs the swings nothing paces: touch, replays, other players). downArc is the clip time at even
        // shares of the club's path; strikeAt / strikeClip time the paced downswing for the follow-through's pace.
        float pace = -1, paceAt, paceStartShare, strikeAt, strikeClip;
        // the phone's last two downswing samples (its own clock) and the least lag seen between its clock and this frame's
        double paceT0, paceT1, paceLag; float paceP0;
        // the paced downswing's own clip pace (clip seconds a second) over its last frames, which the follow-through carries on
        float paceRate, paceShownAt;
        float[] downArc;
        readonly Dictionary<string, float[]> downArcs = new();
"""),
# SetClub: measure the clip's turn (after the clip, landmarks and club mesh are set; Show re-poses afterwards)
("""            Play(c, turn ? 0f : .2f);
            modelGo.transform.localRotation = baseRot;
            if (phase == 4) { phase = 0; time = 0; }
            Show(Mathf.Min(time, TopTime));
""",
"""            Play(c, turn ? 0f : .2f);
            modelGo.transform.localRotation = baseRot;
            downArc = DownArc(wanted, c);
            pace = -1;
            if (phase == 4) { phase = 0; time = 0; }
            Show(Mathf.Min(time, TopTime));
"""),
# helpers after DownswingTime
("""        float DownswingTime(float u) => TopTime + (ImpactTime - TopTime) * Mathf.Pow(Mathf.Clamp01(u), Accel);
""",
"""        float DownswingTime(float u) => TopTime + (ImpactTime - TopTime) * Mathf.Pow(Mathf.Clamp01(u), Accel);

        const int ArcSteps = 32;

        /// The clip's downswing as clip time at even shares of the club's travel from the top to the ball (ArcSteps + 1 entries):
        /// the club head's path in the golfer's own frame, measured once per clip. (Its path, not the shaft's turn: a putter hardly
        /// turns, it rocks.) Null without a club to measure.
        float[] DownArc(string name, AnimationClip c)
        {
            if (downArcs.TryGetValue(name, out var arc)) return arc;
            downArcs[name] = null;
            if (spectator || !modelGo || ImpactTime - TopTime < .05f) return null;
            var grip = System.Array.Find(modelGo.GetComponentsInChildren<Transform>(true), t => t.name == "Club");
            if (!grip || !(ClubHeadWorld() is Vector3 head)) return null;
            var tip = grip.InverseTransformPoint(head);
            if (tip.sqrMagnitude < 1e-6f) return null;
            var root = modelGo.transform; var pos = root.localPosition; var rot = root.localRotation;
            var times = new float[ArcSteps + 1]; var turned = new float[ArcSteps + 1]; Vector3 last = default;
            for (int i = 0; i <= ArcSteps; i++)
            {
                times[i] = Mathf.Lerp(TopTime, ImpactTime, i / (float)ArcSteps);
                c.SampleAnimation(modelGo, times[i]);
                var at = root.InverseTransformPoint(grip.TransformPoint(tip));
                turned[i] = i == 0 ? 0 : turned[i - 1] + (at - last).magnitude;
                last = at;
            }
            root.localPosition = pos; root.localRotation = rot;
            if (turned[ArcSteps] < .02f) return null;   // hardly moves: nothing to follow
            arc = new float[ArcSteps + 1];
            for (int i = 0, j = 0; i <= ArcSteps; i++)
            {
                float want = turned[ArcSteps] * i / ArcSteps;
                while (j < ArcSteps - 1 && turned[j + 1] < want) j++;
                float span = turned[j + 1] - turned[j];
                arc[i] = Mathf.Lerp(times[j], times[j + 1], span > 1e-6f ? Mathf.Clamp01((want - turned[j]) / span) : 0);
            }
            return downArcs[name] = arc;
        }

        /// Clip time at `share` of the club's path from the top (0) to the ball (1).
        float ArcTime(float share)
        {
            float x = Mathf.Clamp01(share) * ArcSteps; int i = Mathf.Min(ArcSteps - 1, (int)x);
            return Mathf.Lerp(downArc[i], downArc[i + 1], x - i);
        }

        /// The share of the club's path from the top that clip time `t` has reached (ArcTime's inverse).
        float ArcShare(float t)
        {
            if (t <= downArc[0]) return 0;
            for (int i = 0; i < ArcSteps; i++)
                if (t <= downArc[i + 1]) return (i + Mathf.InverseLerp(downArc[i], downArc[i + 1], t)) / ArcSteps;
            return 1;
        }

        /// The phone's own downswing, 0 at its top to 1 at the ball (MotionSwingDetector.DownswingProgress), every sample while it
        /// comes down: the club follows it turn for turn instead of its own clock, so it meets the ball on the sample the phone
        /// does. (It never runs back, and samples that stop for a moment hand the swing back to the clock.)
        public void PaceDownswing(float progress, double sampleTime)
        {
            if (!hasModel || downArc == null || phase == 4) return;
            double lag = Time.timeAsDouble - sampleTime;
            if (pace < 0) { paceLag = lag; paceT1 = sampleTime - .01; paceP0 = progress; }
            else { paceLag = System.Math.Min(paceLag, lag); paceP0 = pace; }
            paceT0 = paceT1; paceT1 = sampleTime;
            pace = Mathf.Max(pace, progress); paceAt = Time.time;
        }

        /// The phone's progress at this frame's moment: the samples come at 100 Hz and a frame takes whatever arrived since the
        /// last (one or two, 0-10 ms old), so the newest is carried on along the last two's pace to the frame's time on the phone's
        /// clock (this frame's time less the least lag seen); otherwise the club would step unevenly frame to frame.
        float PaceNow()
        {
            double ahead = System.Math.Min(.02, System.Math.Max(0, Time.timeAsDouble - paceLag - paceT1));
            double span = paceT1 - paceT0;
            float rate = span > 1e-4 ? (float)((pace - paceP0) / span) : 0;
            return pace + Mathf.Max(0, rate) * (float)ahead;
        }
"""),
# ShowLoad: a new backswing drops any pace left from the last swing
("""            shownLoad = load;
            if (phase == 3 && hasModel) { Crossfade(0.3f); phase = 0; loadVelocity = 0; Show(0); }
""",
"""            shownLoad = load;
            if (phase == 0) pace = -1;
            if (phase == 3 && hasModel) { Crossfade(0.3f); phase = 0; loadVelocity = 0; Show(0); }
"""),
# Strike: a full phone backswing is full even when the shown pose lags it; the phone's impact never rewinds the club
("""            float f = Mathf.Clamp01(time / Mathf.Max(0.01f, TopTime));
""",
"""            // (the backswing asked for, not only the pose shown, while the pose is following it: it trails the phone a little, and
            // a full turn is a full swing. A backswing the pose never followed, a touch tap's, stays the tap it was.)
            float f = Mathf.Clamp01(time / Mathf.Max(0.01f, TopTime));
            if (phase == 0 && f >= .75f * loadTarget) f = Mathf.Max(f, Mathf.Clamp01(loadTarget));
"""),
("""            if (atImpact) {
                // The real club has reached the ball. Never schedule a second downswing.
                fade = 0; Weigh(); throughV = 0; phase = 5;
                Show(ImpactTime);
                return 0;
            }
""",
"""            if (atImpact) {
                // The real club has reached the ball. Never schedule a second downswing.
                pace = -1;
                if (phase == 5) return 0;   // the club got there first and is on its way through: carry on, never back to the ball
                if (phase == 2)
                {
                    // the follow-through leaves the ball at the pace the club actually came down (a phone swing's own), and
                    // finishes as far as the downswing's backswing earned
                    finishTime = swingFinish;
                    float down = Time.time - strikeAt;
                    // (a paced downswing's own last pace, so the club leaves the ball as fast as it came to it; else its average)
                    float rate = paceRate > 0 ? paceRate / Accel : down > .02f ? (ImpactTime - strikeClip) / down : swingRate * (ImpactTime - TopTime);
                    rate = Mathf.Clamp(rate, (ImpactTime - TopTime) / .5f, (ImpactTime - TopTime) / .16f);
                    throughSeconds = Mathf.Clamp((finishTime - ImpactTime) * EaseOut / Mathf.Max(0.01f, rate * Accel), 0.35f, 1.6f);
                    if (time > ImpactTime && finishTime > ImpactTime)
                    {
                        // (already a touch past the ball: the follow-through goes on from there)
                        float x = Mathf.Clamp01((time - ImpactTime) / (finishTime - ImpactTime));
                        fade = 0; Weigh(); throughV = 1 - Mathf.Pow(1 - x, 1 / EaseOut); phase = 5;
                        ShowThrough();
                        return 0;
                    }
                }
                fade = 0; Weigh(); throughV = 0; phase = 5;
                Show(ImpactTime);
                return 0;
            }
"""),
("""            Crossfade(full ? 0.07f : 0.12f);   // from the backswing pose into the downswing's
            phase = 2;
            Show(DownswingTime(swingU));
            return seconds;
""",
"""            Crossfade(full ? 0.07f : 0.12f);   // from the backswing pose into the downswing's
            phase = 2;
            swingFinish = finishTime; strikeAt = Time.time; strikeClip = DownswingTime(swingU);
            paceRate = 0; paceShownAt = Time.time;
            if (downArc != null) paceStartShare = ArcShare(strikeClip);
            Show(DownswingTime(swingU));
            if (pace >= 0) ShowPaced();
            return seconds;
"""),
("""        public void Settle()
        {
""",
"""        float swingFinish;

        /// The downswing where the phone's turn has it: as far along the club's path as the phone is through its own turn (from where
        /// this downswing started), never back, and waiting at the ball for the phone's impact.
        void ShowPaced()
        {
            float share = paceStartShare + (1 - paceStartShare) * PaceNow();
            // (a phone a moment ahead of its impact sample carries the club a little on through the ball at the downswing's last
            // pace rather than holding it there: the impact then takes the follow-through on from where the club is)
            float t = share <= 1 ? ArcTime(share) : ImpactTime + Mathf.Min(share - 1, .1f) * (ImpactTime - ArcTime(.9f)) * 10;
            t = Mathf.Max(time, t);
            float dt = Time.time - paceShownAt;
            if (dt > 1e-4f) { float r = (t - time) / dt; paceRate = paceRate > 0 ? Mathf.Lerp(paceRate, r, .5f) : r; paceShownAt = Time.time; }
            swingU = Mathf.Pow(Mathf.Clamp01((t - TopTime) / Mathf.Max(1e-4f, ImpactTime - TopTime)), 1 / Accel);
            Show(t);
        }

        public void Settle()
        {
            pace = -1;
"""),
# Update: phase 2 paced
("""                case 2:
                    swingU += swingRate * dt;
""",
"""                case 2:
                    if (pace >= 0 && Time.time - paceAt > .2f) pace = -1;   // the phone went quiet: the clock carries the swing on
                    if (pace >= 0) break;   // paced in LateUpdate, once every Update has taken this frame's samples
                    swingU += swingRate * dt;
"""),
# LateUpdate: the paced downswing, after every Update has taken this frame's phone samples
("""            if (footwork != null && hasModel) footwork.Tick(""",
"""            if (hasModel && phase == 2 && pace >= 0) ShowPaced();   // (the phone's downswing, with this frame's samples in)
            if (footwork != null && hasModel) footwork.Tick("""),
], 'PaceDownswing')
