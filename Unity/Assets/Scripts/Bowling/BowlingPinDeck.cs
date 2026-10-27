using System.Collections.Generic;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace GolfArcade.Bowling
{
    /// One frame of the recorded pin action (60 Hz): the ball and all ten pins.
    public struct DeckFrame
    {
        public Vector3 Ball;
        public Quaternion BallRotation;
        public bool BallLive;
        public Vector3[] Pins;
        public Quaternion[] PinRotations;
    }

    /// What a sound hits during the pin action (BowlingAudio renders the crash from these).
    public enum ImpactKind { BallPin, PinPin, PinKickback, PinDeck, BallPit, PinPit }

    /// One impact, found from a body's change of velocity between physics steps.
    public struct PinImpact
    {
        public float Time;          // seconds since the action began (the playback clock: frame k is at k / 60)
        public ImpactKind Kind;
        public float Strength;      // the jump in speed, m/s
        public float X;             // across the lane, m (the stereo position)
        public int Pin;             // 1..10, 0 for the ball
    }

    public sealed class PinAction
    {
        public readonly List<DeckFrame> Frames = new List<DeckFrame>();
        public readonly List<PinImpact> Impacts = new List<PinImpact>();
        public int StandingBefore, StandingAfter;        // pin masks (BowlingLeave)
        public int Knocked => BowlingLeave.Count(StandingBefore & ~StandingAfter);
        public float SettleTime;
        public bool BallTouchedPins;
        public int Escaped;                              // pins that left the deck through the walls (bug check)
    }

    /// The pin deck: PhysX bodies in their own physics scene, stepped by script only during the
    /// pin action (PLAN_Bowling.md §6.2). The whole action is simulated at once and recorded, so
    /// the host knows the pinfall immediately and the TV, replays and other players just play
    /// the recording back.
    ///
    /// Pins are tuned to be lively (Adnan, 10-24): they fly, spin, rebound off the kickbacks and
    /// knock each other over. Strikes still need a good pocket hit; see the carry gate.
    public sealed class BowlingPinDeck : System.IDisposable
    {
        public const float Step = 1f / 240;
        public const int RecordEvery = 4;                 // 60 Hz playback
        public const float MaxTime = 4.5f, MinTime = 1.6f;
        public const float DownTilt = 30;                 // a pin tilted more than this is down

        /// Tuning, shared by every deck. The carry harness sweeps these.
        public static class Tuning
        {
            // carry gate sweeps r5/r6 (10-26, 250 throws a bucket): softer pins and kickbacks and a ball that grips the pins
            // separate a good pocket hit (~80 % strikes) from light, high, Brooklyn and nose hits, in the real-world ranges
            public static float PinBounce = .35f, PinFriction = .10f;
            public static float BallBounce = .30f, BallFriction = .285f;
            public static float DeckFriction = .30f, DeckBounce = .15f;
            public static float KickbackBounce = .35f, KickbackFriction = .12f;
            public static float PinAngularDamping = .15f, PinLinearDamping = .02f;
            public static float BallMass = BowlingLane.BallMass;   // the deck may weigh the ball differently from the lane (carry tuning)
            public static int SolverIterations = 20, VelocityIterations = 10;
        }

        static int decks;   // (two games in one editor, the network proof: each deck gets its own scene)
        readonly Scene scene;
        readonly PhysicsScene physics;
        readonly bool ownsScene;
        readonly GameObject root;
        readonly Rigidbody ball;
        readonly Rigidbody[] pins = new Rigidbody[10];
        readonly Transform cushion;

        /// Builds the deck in `scene` (it must have its own local physics). With no scene, a
        /// runtime-only physics scene is created (play mode).
        public BowlingPinDeck(Scene? target = null)
        {
            if (target.HasValue) scene = target.Value;
            else { scene = SceneManager.CreateScene("BowlingPinDeck" + (++decks > 1 ? " " + decks : ""), new CreateSceneParameters(LocalPhysicsMode.Physics3D)); ownsScene = true; }
            physics = scene.GetPhysicsScene();
            root = new GameObject("BowlingPinDeck");
            SceneManager.MoveGameObjectToScene(root, scene);

            var deckMat = Material(Tuning.DeckFriction, Tuning.DeckBounce);
            var kickMat = Material(Tuning.KickbackFriction, Tuning.KickbackBounce, PhysicsMaterialCombine.Maximum);
            var cushionMat = Material(.9f, 0, PhysicsMaterialCombine.Minimum, PhysicsMaterialCombine.Maximum);
            float w = BowlingLane.HalfWidth, g = BowlingLane.GutterWidth, end = BowlingLane.LaneEnd;
            float start = BowlingLane.DeckStart - 4f;
            // Lane bed and pin deck (top at y = 0). Solid and thick, so a pin pushed down by the ball cannot pass through.
            Box("Deck", new Vector3(0, -.5f, (start + end) / 2), new Vector3(2 * w, 1f, end - start), deckMat);
            // Gutters beside the deck (flat channels, lower than the deck).
            foreach (float s in new[] { -1f, 1f })
            {
                Box("Gutter", new Vector3(s * (w + g / 2), -BowlingLane.GutterDepth - .5f, (start + end) / 2), new Vector3(g, 1f, end - start), deckMat);
                // Kickbacks: the side plates the pins rebound from.
                // They run from below the pit up to the masking, so nothing leaves the lane sideways.
                Box("Kickback", new Vector3(s * (BowlingLane.KickbackX + .05f), .35f, (BowlingLane.FoulToHeadPin - .6f + end + 1.2f) / 2),
                    new Vector3(.1f, 1.6f, end + 1.2f - (BowlingLane.FoulToHeadPin - .6f)), kickMat);
            }
            // The pit behind the deck and the rear cushion (a heavy curtain: it soaks up pins and the ball).
            Box("Pit", new Vector3(0, -.80f, end + .5f), new Vector3(2 * (BowlingLane.KickbackX + .1f), 1f, 1.2f), cushionMat);
            cushion = Box("Cushion", new Vector3(0, .35f, end + 1.1f), new Vector3(2 * (BowlingLane.KickbackX + .1f), 1.6f, .3f), cushionMat).transform;
            // A masking roof over the deck so the odd flier comes back down.
            Box("Masking", new Vector3(0, 1.2f, (BowlingLane.FoulToHeadPin - .6f + end + 1.2f) / 2), new Vector3(2 * (BowlingLane.KickbackX + .1f), .2f, end + 1.2f - (BowlingLane.FoulToHeadPin - .6f)), kickMat);

            var pinMat = Material(Tuning.PinFriction, Tuning.PinBounce, PhysicsMaterialCombine.Maximum);
            var hulls = BowlingArt.PinHulls();
            for (int i = 0; i < 10; i++)
            {
                var go = new GameObject("Pin" + (i + 1));
                go.transform.SetParent(root.transform, false);
                foreach (var hull in hulls)
                {
                    var mc = go.AddComponent<MeshCollider>();
                    mc.sharedMesh = hull; mc.convex = true; mc.sharedMaterial = pinMat;
                }
                var rb = go.AddComponent<Rigidbody>();
                rb.mass = BowlingLane.PinMass;
                rb.centerOfMass = new Vector3(0, BowlingLane.PinCentreOfMass, 0);
                float tip = BowlingLane.PinMass * BowlingLane.PinGyration * BowlingLane.PinGyration;
                rb.inertiaTensor = new Vector3(tip, BowlingLane.PinAxialInertia, tip);
                rb.inertiaTensorRotation = Quaternion.identity;
                rb.linearDamping = Tuning.PinLinearDamping;
                rb.angularDamping = Tuning.PinAngularDamping;
                rb.maxAngularVelocity = 60;
                rb.solverIterations = Tuning.SolverIterations;
                rb.solverVelocityIterations = Tuning.VelocityIterations;
                rb.collisionDetectionMode = CollisionDetectionMode.ContinuousSpeculative;
                rb.sleepThreshold = .002f;
                pins[i] = rb;
            }

            var b = new GameObject("Ball");
            b.transform.SetParent(root.transform, false);
            var sc = b.AddComponent<SphereCollider>();
            sc.radius = BowlingLane.BallRadius; sc.sharedMaterial = Material(Tuning.BallFriction, Tuning.BallBounce);
            ball = b.AddComponent<Rigidbody>();
            ball.mass = Tuning.BallMass;
            ball.inertiaTensor = Vector3.one * Tuning.BallMass * BowlingLane.BallGyration * BowlingLane.BallGyration;
            ball.inertiaTensorRotation = Quaternion.identity;
            ball.maxAngularVelocity = 150;
            ball.angularDamping = 0; ball.linearDamping = 0;
            ball.solverIterations = Tuning.SolverIterations;
            ball.collisionDetectionMode = CollisionDetectionMode.ContinuousDynamic;
            b.SetActive(false);
        }

        static PhysicsMaterial Material(float friction, float bounce,
            PhysicsMaterialCombine bounceCombine = PhysicsMaterialCombine.Average, PhysicsMaterialCombine frictionCombine = PhysicsMaterialCombine.Average)
            => new PhysicsMaterial { dynamicFriction = friction, staticFriction = friction * 1.2f, bounciness = bounce, bounceCombine = bounceCombine, frictionCombine = frictionCombine };

        GameObject Box(string name, Vector3 centre, Vector3 size, PhysicsMaterial mat)
        {
            var go = new GameObject(name);
            go.transform.SetParent(root.transform, false);
            go.transform.localPosition = centre;
            var c = go.AddComponent<BoxCollider>();
            c.size = size; c.sharedMaterial = mat;
            return go;
        }

        /// Places the standing pins. `positions` (optional) keeps pins where the last ball left them.
        public void Rack(int standing, Vector3[] positions = null, Quaternion[] rotations = null)
        {
            for (int i = 0; i < 10; i++)
            {
                var rb = pins[i];
                bool up = BowlingLeave.Standing(standing, i + 1);
                rb.gameObject.SetActive(up);
                if (!up) continue;
                rb.transform.SetPositionAndRotation(positions != null ? positions[i] : BowlingLane.PinSpot(i + 1),
                    rotations != null ? Quaternion.Euler(0, rotations[i].eulerAngles.y, 0) : Quaternion.Euler(0, 37 * i, 0));
                rb.linearVelocity = Vector3.zero; rb.angularVelocity = Vector3.zero;
            }
        }

        /// A ball rolling (no slip) at the start of the deck whose centre crosses the head-pin
        /// line on `board` with `angle` degrees of entry (moving left). Used by the carry gate.
        public static BallState Arrival(float board, float angle, float speed)
        {
            float a = angle * Mathf.Deg2Rad, r = BowlingLane.BallRadius;
            float back = BowlingLane.FoulToHeadPin - BowlingLane.DeckStart;
            var v = new Vector3(-Mathf.Sin(a), 0, Mathf.Cos(a)) * speed;
            var p = new Vector3(BowlingLane.BoardX(board) + Mathf.Tan(a) * back, r, BowlingLane.DeckStart);
            return new BallState { Position = p, Velocity = v, Spin = new Vector3(v.z / r, 0, -v.x / r), Phase = BallPhase.Deck };
        }

        // The action in progress (Begin → Advance until it returns true).
        PinAction action;
        BallState arrival;
        bool live, done;
        float t, quiet, contactAt;
        int step;
        // impact detection: each body's velocity before the step, and when it last made a sound
        readonly Vector3[] pinV = new Vector3[10];
        readonly float[] pinLastHit = new float[10], jumps = new float[10];
        Vector3 ballV; float ballLastHit;
        const float HitThreshold = .22f, HitGap = .03f;

        public PinAction Result => done ? action : null;
        public bool Running => action != null && !done;

        /// Starts the pin action for a ball arriving on the deck (`arrival` is the lane
        /// integrator's state at DeckStart; any other phase means no ball reaches the pins).
        public void Begin(BallState arrivalState, int standing, Vector3[] positions = null, Quaternion[] rotations = null)
        {
            Rack(standing, positions, rotations);
            action = new PinAction { StandingBefore = standing };
            arrival = arrivalState;
            live = arrival.Phase == BallPhase.Deck;
            ball.gameObject.SetActive(live);
            if (live)
            {
                ball.transform.SetPositionAndRotation(arrival.Position, Quaternion.identity);
                ball.linearVelocity = arrival.Velocity;
                ball.angularVelocity = arrival.Spin;
            }
            Physics.SyncTransforms();
            t = 0; quiet = 0; contactAt = -1; step = 0; done = false;
            for (int i = 0; i < 10; i++) { pinV[i] = pins[i].linearVelocity; pinLastHit[i] = -1; }
            ballV = live ? ball.linearVelocity : Vector3.zero; ballLastHit = -1;
        }

        /// Runs up to `maxSteps` physics steps. Spread over frames while the ball is still
        /// rolling down the lane, so the release never hitches. True once the pins settle.
        public bool Advance(int maxSteps)
        {
            if (action == null || done) return done;
            for (int n = 0; n < maxSteps; n++, step++)
            {
                if (step % RecordEvery == 0) action.Frames.Add(Capture(live ? ball.position : arrival.Position, live ? ball.rotation : Quaternion.identity, live));
                if (t >= MaxTime) { Finish(); return true; }

                physics.Simulate(Step);
                t += Step;
                Listen();
                // Into the pit or the cushion: the ball is out of play (it never comes back onto the deck).
                if (live && (ball.position.y < -.12f || ball.position.z > BowlingLane.LaneEnd + .8f))
                {
                    live = false; ball.gameObject.SetActive(false);
                    action.Impacts.Add(new PinImpact { Time = t, Kind = ImpactKind.BallPit, Strength = ballV.magnitude, X = ball.position.x });
                }

                bool moving = false;
                for (int i = 0; i < 10; i++)
                {
                    var p = pins[i];
                    if (!p.gameObject.activeSelf) continue;
                    if (contactAt < 0 && p.linearVelocity.sqrMagnitude > .01f) { contactAt = t; action.BallTouchedPins = true; }
                    if (p.linearVelocity.sqrMagnitude > .0025f || p.angularVelocity.sqrMagnitude > .04f) moving = true;
                }
                quiet = moving ? 0 : quiet + Step;
                bool ballDone = !live || ball.position.z > BowlingLane.LaneEnd;
                if (ballDone && quiet > .35f && t > (contactAt < 0 ? .9f : contactAt + MinTime))
                {
                    action.Frames.Add(Capture(arrival.Position, Quaternion.identity, false));
                    Finish(); return true;
                }
            }
            return false;
        }

        /// Finds this step's impacts: a body whose velocity jumped by more than gravity explains was hit.
        /// What it hit is read from where it is: the ball nearby, another pin that also jumped, a kickback
        /// beside it, the deck under it, the pit behind.
        void Listen()
        {
            var g = Physics.gravity * Step;
            float ballJump = 0;
            if (live)
            {
                var v = ball.linearVelocity; ballJump = (v - ballV - g).magnitude; ballV = v;
            }
            // two passes: every pin's jump first, so a pin-on-pin hit is seen from both pins
            for (int i = 0; i < 10; i++)
            {
                jumps[i] = 0;
                if (!pins[i].gameObject.activeSelf) continue;
                var v = pins[i].linearVelocity; jumps[i] = (v - pinV[i] - g).magnitude; pinV[i] = v;
            }
            for (int i = 0; i < 10; i++)
            {
                float jump = jumps[i];
                if (jump < HitThreshold || t - pinLastHit[i] < HitGap) continue;
                pinLastHit[i] = t;
                var pos = pins[i].worldCenterOfMass;
                ImpactKind kind;
                if (live && ballJump > HitThreshold * .5f && (ball.position - pos).sqrMagnitude < .09f) kind = ImpactKind.BallPin;
                else if (pos.y < -.05f || pos.z > BowlingLane.LaneEnd + .05f) kind = ImpactKind.PinPit;
                else if (Mathf.Abs(pos.x) > BowlingLane.KickbackX - .14f) kind = ImpactKind.PinKickback;
                else
                {
                    kind = ImpactKind.PinDeck;
                    for (int j = 0; j < 10; j++)
                        if (j != i && jumps[j] >= HitThreshold && (pins[j].worldCenterOfMass - pos).sqrMagnitude < .16f) { kind = ImpactKind.PinPin; break; }
                }
                action.Impacts.Add(new PinImpact { Time = t, Kind = kind, Strength = jump, X = pos.x, Pin = i + 1 });
            }
        }

        void Finish()
        {
            action.SettleTime = t;
            action.StandingAfter = Standing(action.StandingBefore, out action.Escaped);
            done = true;
        }

        /// The whole pin action at once (tests, the carry gate, the host).
        public PinAction Simulate(BallState arrivalState, int standing, Vector3[] positions = null, Quaternion[] rotations = null)
        {
            Begin(arrivalState, standing, positions, rotations);
            while (!Advance(1 << 16)) { }
            return action;
        }

        DeckFrame Capture(Vector3 ballPos, Quaternion ballRot, bool ballLive)
        {
            var f = new DeckFrame { Ball = ballPos, BallRotation = ballRot, BallLive = ballLive, Pins = new Vector3[10], PinRotations = new Quaternion[10] };
            for (int i = 0; i < 10; i++) { f.Pins[i] = pins[i].transform.position; f.PinRotations[i] = pins[i].transform.rotation; }
            return f;
        }

        /// Pins still standing: upright within DownTilt and still on the deck.
        int Standing(int before, out int escaped)
        {
            int mask = 0; escaped = 0;
            for (int i = 0; i < 10; i++)
            {
                if (!BowlingLeave.Standing(before, i + 1)) continue;
                var tr = pins[i].transform;
                Vector3 p = tr.position;
                if (Mathf.Abs(p.x) > BowlingLane.KickbackX + .05f || p.z > BowlingLane.LaneEnd + 1.3f || p.y < -.6f || p.y > 1.2f || float.IsNaN(p.x))
                {
                    escaped++;
                    Debug.LogWarning($"[BowlingPinDeck] pin {i + 1} escaped the deck at {p}");
                }
                bool onDeck = Mathf.Abs(p.x) < BowlingLane.HalfWidth && p.z < BowlingLane.LaneEnd && p.y > -.02f;
                bool upright = Vector3.Angle(tr.up, Vector3.up) < DownTilt;
                if (onDeck && upright) mask |= 1 << i;
            }
            return mask;
        }

        public void PinPose(out Vector3[] positions, out Quaternion[] rotations)
        {
            positions = new Vector3[10]; rotations = new Quaternion[10];
            for (int i = 0; i < 10; i++) { positions[i] = pins[i].transform.position; rotations[i] = pins[i].transform.rotation; }
        }

        public void Dispose()
        {
            if (root) Object.DestroyImmediate(root);
            if (ownsScene && scene.IsValid()) SceneManager.UnloadSceneAsync(scene);
        }
    }
}
