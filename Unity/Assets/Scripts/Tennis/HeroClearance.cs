using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using Capsule = GolfArcade.Tennis.HeroClearanceProxy.Capsule;
using Part = GolfArcade.Tennis.HeroClearanceProxy.Part;

namespace GolfArcade.Tennis
{
    /// HAND CLEARANCE (work/hand-clearance): keeps hands, forearms, upper arms and the held racket/club out of the
    /// body and the clothes, on any clip, any hero and any garment. One solver, two outputs: HeroPoseSafety runs it
    /// after the animation every frame (tennis, golf, plaza), and the offline bake (Editor/HeroClearanceBake) runs the
    /// very same Solve frame by frame and writes the corrected arm tracks for the SceneKit lobby.
    ///
    /// What moves, in this order:
    ///  1. the grip: each hand (a two-hand grip and its prop as ONE group) translates by the smallest offset that takes
    ///     the hand, the held prop and the wrist end of the forearm out of the proxy (HeroClearanceProxy). Travel is
    ///     allowed per hand by the caller: 0 at racket/club contact, so contact position and time never change.
    ///     The arm follows with a two-bone IK that keeps both segment lengths and the elbow's side; the hand keeps its
    ///     world rotation, so fingers and grip are untouched.
    ///  2. the elbow: the whole arm swivels about the shoulder-wrist line (wrist fixed, elbow angle fixed, no flip)
    ///     by the smallest angle that takes the forearm and the outer upper arm out.
    ///  3. the prop: what is still inside after 1 and 2 turns the hand about the wrist (single-hand grips only).
    ///  4. a second hand on the same handle slides along the handle until the two hands no longer overlap.
    /// Corrections appear exactly when needed and are released smoothly (no pop), and the elbow swivel prefers the
    /// previous frame's solution, so it never jumps between sides.
    public sealed class HeroClearance
    {
        /// The only tuning numbers. They are about the solver, never about a hero or a garment.
        public static readonly float Margin = Tune("Margin", .004f);          // kept between the hand / forearm / prop and the outside of the clothes
        public static readonly float ForearmMargin = Tune("ForearmMargin", .001f);    // a forearm may rest against the shirt / thigh (it does in every idle)
        public static readonly float UpperArmMargin = Tune("UpperArmMargin", 0f);      // outer upper arm vs the bare body (sleeves and shirt may touch)
        public static readonly float MaxTravel = Tune("MaxTravel", .24f);         // grip translation a free hand may use
        public static readonly float MaxGroupTravel = Tune("MaxGroupTravel", .14f); // ... and a two-hand grip carrying its racket / club
        public static readonly float PropMargin = Tune("PropMargin", 0f);
        /// Anticipation: the pose the clip reaches this many seconds ahead (by the wrist's own velocity) already pulls the
        /// correction in, with these weights, so a hand swinging into a thigh is eased out before the contact, not snapped.
        public static readonly float AheadNear = Tune("AheadNear", .05f), AheadFar = Tune("AheadFar", .1f), AheadNearWeight = Tune("AheadNearWeight", .6f), AheadFarWeight = Tune("AheadFarWeight", .3f);       // the racket / club may touch the (fuller) proxy surface
        public static readonly float MaxSlide = Tune("MaxSlide", .03f);          // a two-hand grip's second hand along the handle
        public static readonly float MaxSwivel = Tune("MaxSwivel", 55f);          // elbow swivel, degrees either way
        public static readonly float MaxPropTurn = Tune("MaxPropTurn", 30f);        // a single-hand prop turned about the wrist, degrees
        public static readonly float Release = Tune("Release", .14f);           // s, time constant of a correction fading out
        public static readonly float SwivelRelease = Tune("SwivelRelease", .18f);
        public static readonly float SwivelRate = Tune("SwivelRate", 150f);       // degrees per second
        public static readonly float MaxShoulderShift = Tune("MaxShoulderShift", .045f); // m the clavicle may carry the shoulder joint
        public static readonly float ShoulderRate = Tune("ShoulderRate", .3f);    // m/s
        public static readonly float MaxHandSpeed = Tune("MaxHandSpeed", 0f);     // m/s cap on how fast a grip correction may change (0 = off: a cap lags deep intrusions)
        /// A nearly straight arm (elbow bend below this, degrees) keeps its length when the hand is carried out: the arm turns at
        /// the shoulder instead of kinking the elbow (near full extension a few mm of length is tens of degrees of elbow).
        public static readonly float StraightArm = Tune("StraightArm", 35f);
        /// Editor experiments only (CLEARANCE_<Name>=value); a player build always uses the defaults written here.
        static float Tune(string name, float value)
        {
#if UNITY_EDITOR
            var v = System.Environment.GetEnvironmentVariable("CLEARANCE_" + name);
            if (!string.IsNullOrEmpty(v) && float.TryParse(v, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out var f)) return f;
#endif
            return value;
        }

        public struct Request
        {
            /// 0..1 of MaxTravel each hand may move (0 = locked: racket/club contact, a planted contact)
            public float travelLeft, travelRight;
            /// The caller knows both hands hold the racket (two-hand backhand). Also detected from the pose.
            public bool twoHanded;
            public static Request Free => new Request { travelLeft = 1, travelRight = 1 };
        }

        public readonly HeroClearanceProxy proxy;
        readonly MatchHeroLook look;
        readonly Transform root;

        public struct Sample { public Transform bone; public Vector3 local; public float weight; public Vector3 world; }
        public sealed class Arm
        {
            public int side; public Transform clavicle, upper, lower, hand;
            public Sample[] handS, foreS, upperS;
            public Capsule[] obstacles;               // everything but this arm
            public List<Capsule> obstacleList;
            public Capsule[] ownCapsules;            // this arm (refreshed after it moves)
            public Vector3 travelApplied;            // root space
            public float swivelApplied;
            public Vector3 turnApplied;              // prop turn, root space axis * degrees
            public float slideApplied;
            public Vector3 shoulderApplied;          // hero space: how far the clavicle moved the shoulder joint
            public Vector3 lastUpperDir;             // the upper arm's direction last frame (hero space), before the swivel
            public float travel;
            public int lastFrame = -1;
            public bool limbNear;
            public Vector3 animW; public bool hasAnim;   // the clip's own wrist last frame (hero space): its velocity drives anticipation   // this frame a forearm / upper-arm sample came within reach of an obstacle
        }
        public sealed class Prop
        {
            public string name; public Transform grip; public Renderer[] renderers; public Vector3[] local; public bool[] handle;
            public Vector3 axisLocal; public float handleLength; public Vector3[] world;
        }
        public readonly Arm[] arms = new Arm[2];
        public readonly List<Prop> props = new List<Prop>();

        // diagnostics
        public float ResidualDepth { get; private set; }
        public float BeforeDepth { get; private set; }
        public string ResidualWhere { get; private set; } = "";
        public double LastMs { get; private set; }
        /// Last solve split: refresh+grip, translate, swivel, prop+slide, diagnostics (ms), and full table lookups.
        public (double refresh, double translate, double swivel, double prop, double diag, int lookups) Phase { get; private set; }

        public HeroClearance(MatchHeroLook look, bool background = false)
        {
            this.look = look; root = look.transform;
            proxy = new HeroClearanceProxy(look, background);
            if (proxy.Ready) Build();
        }
        bool built;
        /// The proxy is fitted and the arms are sampled (a background fit finishes a few frames after the hero appears).
        public bool Ready => built || proxy.Ready && Build();
        bool Build()
        {
            for (int s = 0; s < 2; s++) arms[s] = BuildArm(s == 0 ? -1 : 1);
            BuildProps();
            return built = true;
        }

        Arm BuildArm(int side)
        {
            bool L = side < 0;
            var a = new Arm
            {
                side = side,
                clavicle = look.Bone(L ? HumanBodyBones.LeftShoulder : HumanBodyBones.RightShoulder),
                upper = look.Bone(L ? HumanBodyBones.LeftUpperArm : HumanBodyBones.RightUpperArm),
                lower = look.Bone(L ? HumanBodyBones.LeftLowerArm : HumanBodyBones.RightLowerArm),
                hand = look.Bone(L ? HumanBodyBones.LeftHand : HumanBodyBones.RightHand),
            };
            var own = new List<Capsule>(); var obst = new List<Capsule>();
            foreach (var c in proxy.capsules)
            {
                if (c == null) continue;
                bool mine = c.side == side && (c.part == Part.Clavicle || c.part == Part.UpperArm || c.part == Part.Forearm || c.part == Part.Hand || c.part == Part.Finger);
                (mine ? own : obst).Add(c);
            }
            a.ownCapsules = own.ToArray(); a.obstacles = obst.ToArray(); a.obstacleList = obst;
            // sample points: skin vertices following each hand / finger / forearm / upper-arm bone most, spread out
            var body = proxy.sources.Count > 0 ? proxy.sources[0] : null;
            if (body == null || !a.hand) { a.handS = a.foreS = a.upperS = new Sample[0]; return a; }
            // every hand / finger bone of this side, also one too small for a capsule of its own (a thumb root)
            var hs = new List<Sample>();
            for (int i = 0; i < proxy.partAt.Length; i++)
            {
                if (proxy.sideAt[i] != side || (proxy.partAt[i] != Part.Hand && proxy.partAt[i] != Part.Finger)) continue;
                var t = proxy.BoneAt(i);
                int n = proxy.partAt[i] == Part.Hand ? 6 : proxy.nameAt[i].Contains("Distal") ? 2 : 1;
                hs.AddRange(Pick(body, i, t, n, 0, 1));
            }
            a.handS = hs.ToArray();
            var fc = proxy.Of(a.lower); var uc = proxy.Of(a.upper);
            // forearm: away from the elbow crease (the own upper arm overlaps it by nature)
            a.foreS = fc != null ? Pick(body, proxy.IndexOf(a.lower), a.lower, 10, .18f, 1.1f, a.hand).ToArray() : new Sample[0];
            a.upperS = uc != null ? Pick(body, proxy.IndexOf(a.upper), a.upper, 6, .5f, 1.1f, a.lower).ToArray() : new Sample[0];
            return a;
        }

        /// n farthest-point samples among the body vertices that follow `proxyIndex` most, between `from` and `to`
        /// of the way from the bone to `next` (all when next is null).
        List<Sample> Pick(HeroClearanceProxy.Source body, int proxyIndex, Transform bone, int n, float from, float to, Transform next = null)
        {
            var bindposes = look.body.sharedMesh.bindposes; var palette = look.body.bones;
            int bi = Array.IndexOf(palette, bone); var res = new List<Sample>();
            if (bi < 0) return res;
            var bind = bindposes[bi];
            Vector3 tip = Vector3.zero; float len = 0;
            if (next) { int ni = Array.IndexOf(palette, next); if (ni >= 0) { tip = bind.MultiplyPoint3x4(bindposes[ni].inverse.MultiplyPoint3x4(Vector3.zero)); len = tip.magnitude; } }
            var cand = new List<Vector3>();
            for (int i = 0; i < body.v.Length; i++)
            {
                if (body.dominant[i] != proxyIndex) continue;
                var p = bind.MultiplyPoint3x4(body.v[i]);
                if (len > 1e-4f) { float u = Vector3.Dot(p, tip) / (len * len); if (u < from || u > to) continue; }
                cand.Add(p);
            }
            if (cand.Count == 0) return res;
            // farthest point sampling from the candidate farthest from the bone origin
            var dist = new float[cand.Count]; int cur = 0; float far = -1;
            for (int i = 0; i < cand.Count; i++) { float d = cand[i].sqrMagnitude; if (d > far) { far = d; cur = i; } }
            for (int i = 0; i < cand.Count; i++) dist[i] = float.MaxValue;
            for (int k = 0; k < n && k < cand.Count; k++)
            {
                float u = len > 1e-4f ? Vector3.Dot(cand[cur], tip) / (len * len) : 1;
                res.Add(new Sample { bone = bone, local = cand[cur], weight = Mathf.Clamp01(u) });
                int best = -1; float bd = -1;
                for (int i = 0; i < cand.Count; i++) { float d = (cand[i] - cand[cur]).sqrMagnitude; if (d < dist[i]) dist[i] = d; if (dist[i] > bd) { bd = dist[i]; best = i; } }
                if (best < 0 || bd < 1e-8f) break; cur = best;
            }
            return res;
        }

        void BuildProps()
        {
            props.Clear();
            if (look.racketGrip)
            {
                var g = look.racketGrip; var pts = new List<Vector3>(); var rs = new List<Renderer>();
                foreach (var f in g.GetComponentsInChildren<MeshFilter>(true))
                {
                    if (!f.sharedMesh || !f.sharedMesh.isReadable || f.name.Contains("Collider")) continue;
                    var r = f.GetComponent<Renderer>(); if (r) rs.Add(r);
                    var m = g.worldToLocalMatrix * f.transform.localToWorldMatrix;
                    foreach (var v in f.sharedMesh.vertices) pts.Add(m.MultiplyPoint3x4(v));
                }
                var p = MakeProp("racket", g, rs.ToArray(), pts, look.stringUpLocal);
                if (p != null) props.Add(p);
            }
            Transform club = null;
            foreach (var t in look.GetComponentsInChildren<Transform>(true)) if (t.name == "Club") { club = t; break; }
            if (club)
                foreach (var r in look.GetComponentsInChildren<SkinnedMeshRenderer>(true))
                {
                    if (!r.name.StartsWith("CLUB_") || !r.sharedMesh || !r.sharedMesh.isReadable) continue;
                    int bi = Array.IndexOf(r.bones, club); var pts = new List<Vector3>();
                    var m = bi >= 0 ? r.sharedMesh.bindposes[bi] : club.worldToLocalMatrix * r.transform.localToWorldMatrix;
                    foreach (var v in r.sharedMesh.vertices) pts.Add(m.MultiplyPoint3x4(v));
                    var p = MakeProp(r.name, club, new Renderer[] { r }, pts, Vector3.zero);
                    if (p != null) props.Add(p);
                }
        }

        Prop MakeProp(string name, Transform grip, Renderer[] rs, List<Vector3> pts, Vector3 axisHint)
        {
            if (pts.Count < 4) return null;
            // the handle axis: from the grip origin to the far end of the prop
            Vector3 far = pts[0]; foreach (var p in pts) if (p.sqrMagnitude > far.sqrMagnitude) far = p;
            var axis = axisHint.sqrMagnitude > .5f ? axisHint.normalized : far.normalized;
            if (Vector3.Dot(axis, far) < 0) axis = -axis;
            var pick = new List<Vector3>(); var dist = new float[pts.Count]; int cur = 0;
            for (int i = 0; i < pts.Count; i++) dist[i] = float.MaxValue;
            for (int k = 0; k < 28; k++)
            {
                pick.Add(pts[cur]); int best = -1; float bd = -1;
                for (int i = 0; i < pts.Count; i++) { float d = (pts[i] - pts[cur]).sqrMagnitude; if (d < dist[i]) dist[i] = d; if (dist[i] > bd) { bd = dist[i]; best = i; } }
                if (best < 0 || bd < 1e-8f) break; cur = best;
            }
            float total = Vector3.Dot(far, axis);
            var prop = new Prop { name = name, grip = grip, renderers = rs, local = pick.ToArray(), axisLocal = axis, handleLength = Mathf.Max(.1f, total * .3f) };
            prop.handle = new bool[prop.local.Length]; prop.world = new Vector3[prop.local.Length];
            for (int i = 0; i < prop.local.Length; i++) prop.handle[i] = Vector3.Dot(prop.local[i], axis) < prop.handleLength;
            return prop;
        }

        // ================================================================ per frame
        static readonly List<Capsule> near = new List<Capsule>(64);
        Prop held; int holder = -1; bool both;

        /// dt: seconds since the previous solved frame of a continuous playback; 0 (or negative) starts fresh
        /// (a diagnostic sample, a clip change) and applies the solution without smoothing.
        public void Solve(Request q, float dt)
        {
            var timer = System.Diagnostics.Stopwatch.StartNew();
            if (!Ready) { ResidualDepth = 0; LastMs = 0; return; }
            long t0 = timer.ElapsedTicks; int lookups0 = HeroClearanceProxy.Lookups;
            proxy.Refresh();
            FindGrip(q);
            arms[0].travel = q.travelLeft; arms[1].travel = q.travelRight;
            long t1 = timer.ElapsedTicks;
            BeforeDepth = Diagnostics ? Measure(false) : 0;
            long t1b = timer.ElapsedTicks;
            // 1. grips
            if (held != null && both)
            {
                float travel = Mathf.Min(q.travelLeft, q.travelRight);
                Translate(new[] { arms[holder], arms[1 - holder] }, held, travel, dt);
            }
            else
            {
                int first = holder >= 0 ? holder : 1;
                for (int k = 0; k < 2; k++)
                {
                    var arm = arms[k == 0 ? first : 1 - first];
                    float travel = arm.side < 0 ? q.travelLeft : q.travelRight;
                    Translate(new[] { arm }, holder >= 0 && arm == arms[holder] ? held : null, travel, dt);
                }
            }
            long t2 = timer.ElapsedTicks;
            // 2. elbows
            for (int k = 0; k < 2; k++) Swivel(arms[k], dt);
            // 2b. a forearm / upper arm still inside (a raised cross-body arm with the wrist held): the clavicle opens a little
            for (int k = 0; k < 2; k++) Shoulder(arms[k], dt);
            long t3 = timer.ElapsedTicks;
            // 3. a single-hand prop still inside
            if (held != null && !both) TurnProp(arms[holder], held, holder == 0 ? q.travelLeft : q.travelRight, dt);
            // 4. second hand on the same handle
            if (held != null && both) Slide(arms[1 - holder], arms[holder], held, Mathf.Min(q.travelLeft, q.travelRight), dt);
            long t4 = timer.ElapsedTicks;
            ResidualDepth = Diagnostics ? Measure(true) : 0;
            long t5 = timer.ElapsedTicks;
            double f = 1000.0 / System.Diagnostics.Stopwatch.Frequency;
            Phase = ((t1 - t0) * f, (t2 - t1b) * f, (t3 - t2) * f, (t4 - t3) * f, (t1b - t1 + t5 - t4) * f, HeroClearanceProxy.Lookups - lookups0);
            if (Trace && (ResidualDepth > .01f || TraceAll))
                UnityEngine.Debug.Log($"[ClearanceTrace] residual {ResidualDepth * 1000:0.0} {ResidualWhere} applied L {arms[0].travelApplied:F3} sw {arms[0].swivelApplied:0.0} sl {arms[0].slideApplied:F3} turn {arms[0].turnApplied:F1} R {arms[1].travelApplied:F3} sw {arms[1].swivelApplied:0.0} sl {arms[1].slideApplied:F3} turn {arms[1].turnApplied:F1} elbows {Vector3.Angle(arms[0].lower.position - arms[0].upper.position, arms[0].hand.position - arms[0].lower.position):0.0}/{Vector3.Angle(arms[1].lower.position - arms[1].upper.position, arms[1].hand.position - arms[1].lower.position):0.0} held {(held != null ? held.name : "-")} both {both} travel {q.travelLeft:0.00}/{q.travelRight:0.00}");
            timer.Stop(); LastMs = timer.Elapsed.TotalMilliseconds;
        }

        /// Which prop is in which hand in the current pose (Solve does this itself).
        public void DetectGrip(bool twoHanded = false) => FindGrip(new Request { twoHanded = twoHanded });
        public Prop HeldProp => held;
        public int HolderSide => holder >= 0 ? arms[holder].side : 1;
        public bool TwoHandGrip => both;
        public Prop HeldPropAny()
        {
            if (held != null) return held;
            foreach (var p in props) foreach (var r in p.renderers) if (r && r.enabled && r.gameObject.activeInHierarchy) return p;
            return null;
        }

        void FindGrip(Request q)
        {
            held = null; holder = -1; both = false;
            float best = .16f;
            foreach (var p in props)
            {
                bool on = false; foreach (var r in p.renderers) if (r && r.enabled && r.gameObject.activeInHierarchy) { on = true; break; }
                if (!on) continue;
                for (int s = 0; s < 2; s++)
                {
                    if (!arms[s].hand) continue;
                    float d = Vector3.Distance(arms[s].hand.position, p.grip.position);
                    if (d < best) { best = d; held = p; holder = s; }
                }
            }
            if (held == null) return;
            var other = arms[1 - holder].hand; if (!other) return;
            var o = held.grip.position; var ax = held.grip.TransformDirection(held.axisLocal).normalized;
            float along = Vector3.Dot(other.position - o, ax);
            float off = (other.position - o - ax * along).magnitude;
            // the other hand on the handle (two-hand grip) or anywhere on the frame / shaft (a cradle, the ready hold)
            float span = 0; foreach (var l in held.local) span = Mathf.Max(span, Vector3.Dot(l, held.axisLocal));
            span *= Mathf.Abs(held.grip.lossyScale.x);
            both = q.twoHanded && off < .14f || along > -.08f && along < span + .04f && off < .09f;
            if (!both)
            {
                // or the other hand touches the prop anywhere (cradling the head, steadying the shaft): meant to touch
                var oa = arms[1 - holder]; Place(oa.handS); Place(held);
                for (int i = 0; i < oa.handS.Length && !both; i++)
                    foreach (var w in held.world) if ((w - oa.handS[i].world).sqrMagnitude < .06f * .06f) { both = true; break; }
            }
        }

        // ---------------------------------------------------------------- sampling
        void Place(Sample[] s)
        {
            Transform last = null; Matrix4x4 m = default;
            for (int i = 0; i < s.Length; i++)
            {
                if (s[i].bone != last) { last = s[i].bone; m = last.localToWorldMatrix; }
                s[i].world = m.MultiplyPoint3x4(s[i].local);
            }
        }
        void Place(Prop p)
        {
            var m = p.grip.localToWorldMatrix;
            for (int i = 0; i < p.local.Length; i++) p.world[i] = m.MultiplyPoint3x4(p.local[i]);
        }
        static void Gather(Capsule[] from, Vector3 centre, float radius, List<Capsule> into)
        {
            into.Clear();
            foreach (var c in from) { float r = c.bound + radius; if ((c.midWorld - centre).sqrMagnitude < r * r) into.Add(c); }
        }
        /// Deepest violation (m, margin included) of a point among capsules; push = direction out.
        static float Worst(List<Capsule> cs, Vector3 p, bool garment, float margin, out Vector3 push, out Capsule which)
        {
            float worst = 0; push = Vector3.zero; which = null;
            for (int i = 0; i < cs.Count; i++)
            {
                var c = cs[i]; float r = c.bound + margin;
                if ((c.midWorld - p).sqrMagnitude > r * r) continue;
                float d = HeroClearanceProxy.Depth(c, p, garment, out var n) + margin;
                if (d > worst) { worst = d; push = n; which = c; }
            }
            return worst;
        }
        static bool Excluded(Prop prop, int i, Capsule c, int holderSide, bool both)
        {
            // the handle sits in the hands and against the holding forearm by design
            // the head / shaft: the holding hand, and with two hands on it (a grip, a cradle) the other hand too, touch it by design
            if (!prop.handle[i]) return (c.side == holderSide || both) && (c.part == Part.Hand || c.part == Part.Finger);
            if (c.part == Part.Hand || c.part == Part.Finger || c.part == Part.Forearm) return c.side == holderSide || both;
            return false;
        }

        // ---------------------------------------------------------------- 1. grip translation
        // ---------------------------------------------------------------- virtual arms
        // Where every sample of a grip arm lands for a wrist translation T, with the elbow placed by the same two-bone IK the
        // pose then gets. Candidate moves are judged on the whole arm, so a hand fix can never push the forearm into the chest.
        sealed class Virtual
        {
            public Arm a; public Vector3 S, E, W; public float u, l;
            public Vector3[] hand = new Vector3[0], fore = new Vector3[0], upper = new Vector3[0];
            public float[] fore0 = new float[0], upper0 = new float[0];   // their intrusion before any move: the swivel's job, only never made worse
        }
        readonly Virtual[] virt = { new Virtual(), new Virtual() }; int virtCount;
        struct Sym { public float xx, xy, xz, yy, yz, zz; }
        Sym gnA; Vector3 gnB;
        /// The translation that best satisfies every intruding point at once: (sum n n^T + damping) dT = sum n d.
        Vector3 GaussNewtonStep()
        {
            var A = gnA; float tr = A.xx + A.yy + A.zz; if (tr < 1e-9f) return Vector3.zero;
            float l = tr * .02f; A.xx += l; A.yy += l; A.zz += l;
            float c00 = A.yy * A.zz - A.yz * A.yz, c01 = A.xz * A.yz - A.xy * A.zz, c02 = A.xy * A.yz - A.xz * A.yy;
            float det = A.xx * c00 + A.xy * c01 + A.xz * c02; if (Mathf.Abs(det) < 1e-12f) return Vector3.zero;
            float c11 = A.xx * A.zz - A.xz * A.xz, c12 = A.xy * A.xz - A.xx * A.yz, c22 = A.xx * A.yy - A.xy * A.xy;
            var b = gnB; float inv = 1 / det;
            return new Vector3(c00 * b.x + c01 * b.y + c02 * b.z, c01 * b.x + c11 * b.y + c12 * b.z, c02 * b.x + c12 * b.y + c22 * b.z) * inv;
        }
        readonly List<Capsule> cand = new List<Capsule>(48);
        float[] capWorst = new float[64]; Vector3[] capDir = new Vector3[64];

        static Vector3 ElbowFor(Virtual v, Vector3 Wt)
        {
            var delta = Wt - v.S; float d = Mathf.Clamp(delta.magnitude, Mathf.Abs(v.u - v.l) + .00001f, v.u + v.l - .00001f);
            if (d < .0001f) return v.E;
            var axis = delta.normalized; var hinge = Vector3.Cross(v.E - v.S, v.W - v.E);
            // exactly as HeroPoseSafety.Solve: least elbow motion, the hinge's side when that is ill-defined (no flip)
            var pole = HeroPoseSafety.Pole(v.E - v.S, hinge, axis, v.u);
            if (pole.sqrMagnitude < 1e-12f) return v.E;
            float along = (v.u * v.u - v.l * v.l + d * d) / (2 * d);
            return v.S + axis * along + pole * Mathf.Sqrt(Mathf.Max(0, v.u * v.u - along * along));
        }
        static void Copy(Sample[] src, ref Vector3[] dst) { if (dst.Length != src.Length) dst = new Vector3[src.Length]; for (int i = 0; i < src.Length; i++) dst[i] = src[i].world; }

        /// Deepest violation at translation T (hands and prop: absolute; forearm and upper arm: only what T adds). With push,
        /// fills the per-obstacle deepest pushes (capWorst / capDir) for the iterative step.
        // Each sample is paired once with the few obstacles it can reach (within PairSlack of the capsule's widest surface);
        // every evaluation walks only those pairs. Rebuilt when the move has gone further than the slack.
        struct Pair { public byte kind, arm; public short sample, cap; }   // kind: 0 hand, 1 forearm, 2 upper arm, 3 prop
        readonly List<Pair> pairs = new List<Pair>(256); Vector3 pairBase; bool pairsValid;
        static readonly (float tau, float weight)[] Ahead = { (AheadNear, AheadNearWeight), (AheadFar, AheadFarWeight) };
        float pairExtra;   // extra pairing slack this frame: covers the look-ahead, so anticipation reuses the same pairs
        const float PairSlack = .08f;
        float PairSlackNow => Residual ? .04f : PairSlack;   // the residual pass only fixes small leftovers: a tighter pairing
        static bool Reaches(Capsule c, Vector3 x, float slack)
        {
            float r = c.bound + slack; if ((c.midWorld - x).sqrMagnitude > r * r) return false;
            var ab = c.bW - c.aW; float t = Mathf.Clamp01(Vector3.Dot(x - c.aW, ab) / Mathf.Max(1e-12f, ab.sqrMagnitude));
            float far = c.maxR * c.scale + slack; return (x - (c.aW + ab * t)).sqrMagnitude < far * far;
        }
        Vector3 ahead;   // anticipation: where the clip will have carried the hand a moment from now (0 normally)
        void Pose(Virtual v, Vector3 T, out Vector3 Et, out Quaternion Rf, out Quaternion Ru)
        {
            var Wt = v.W + T + ahead; Et = ElbowFor(v, Wt);
            Rf = Quaternion.FromToRotation(v.W - v.E, Wt - Et); Ru = Quaternion.FromToRotation(v.E - v.S, Et - v.S);
        }
        void BuildPairs(Vector3 T, Prop prop)
        {
            Builds++; pairs.Clear(); pairBase = T + ahead; pairsValid = true; float slack = PairSlackNow + pairExtra + Margin;
            for (int vi = 0; vi < virtCount; vi++)
            {
                var v = virt[vi]; Pose(v, T, out var Et, out var Rf, out var Ru);
                // the arm's own bounding sphere at T (shoulder to fingertips): only obstacles touching it can pair
                var lo = v.S; var hi = v.S;
                foreach (var p in v.hand) { lo = Vector3.Min(lo, p + T + ahead); hi = Vector3.Max(hi, p + T + ahead); }
                var centre = (lo + hi) * .5f; float rad = (hi - lo).magnitude * .5f + slack;
                for (int k = 0; k < cand.Count; k++)
                {
                    var c = cand[k];
                    float cr = c.bound + rad; if ((c.midWorld - centre).sqrMagnitude > cr * cr) continue;
                    for (int i = 0; i < v.hand.Length; i++) if (Reaches(c, v.hand[i] + T + ahead, slack)) pairs.Add(new Pair { kind = 0, arm = (byte)vi, sample = (short)i, cap = (short)k });
                    for (int i = 0; i < v.fore.Length; i++) if (Reaches(c, Et + Rf * (v.fore[i] - v.E), slack)) pairs.Add(new Pair { kind = 1, arm = (byte)vi, sample = (short)i, cap = (short)k });
                    for (int i = 0; i < v.upper.Length; i++) if (Reaches(c, v.S + Ru * (v.upper[i] - v.S), slack)) pairs.Add(new Pair { kind = 2, arm = (byte)vi, sample = (short)i, cap = (short)k });
                }
            }
            if (prop != null)
                for (int k = 0; k < cand.Count; k++)
                    for (int i = 0; i < prop.world.Length; i++)
                        if (!Excluded(prop, i, cand[k], arms[holder].side, both) && Reaches(cand[k], prop.world[i] + T + ahead, slack)) pairs.Add(new Pair { kind = 3, sample = (short)i, cap = (short)k });
        }
        readonly Vector3[] poseE = new Vector3[2]; readonly Quaternion[] poseRf = new Quaternion[2], poseRu = new Quaternion[2];

        /// Deepest violation at translation T (hands and prop: absolute; upper arm: only what T adds). With push, fills the
        /// per-obstacle deepest pushes (capWorst / capDir) and the Gauss-Newton system for the step.
        public static int EvalCalls, PairsBuilt, Builds;   // profiling
        float Eval(Vector3 T, Prop prop, bool push)
        {
            EvalCalls++;
            float keepWithin = (PairSlackNow + pairExtra) * .8f;
            if (!pairsValid || (T + ahead - pairBase).sqrMagnitude > keepWithin * keepWithin) BuildPairs(T, prop);
            float worst = 0;
            if (push) { for (int k = 0; k < cand.Count; k++) { capWorst[k] = 0; capDir[k] = Vector3.zero; } gnA = default; gnB = Vector3.zero; }
            for (int vi = 0; vi < virtCount; vi++) Pose(virt[vi], T, out poseE[vi], out poseRf[vi], out poseRu[vi]);
            for (int pi = 0; pi < pairs.Count; pi++)
            {
                var pr = pairs[pi]; var c = cand[pr.cap]; Vector3 x; bool garment = true; float add;
                switch (pr.kind)
                {
                    case 0: x = virt[pr.arm].hand[pr.sample] + T + ahead; add = Margin; break;
                    case 1: { var v = virt[pr.arm]; x = poseE[pr.arm] + poseRf[pr.arm] * (v.fore[pr.sample] - v.E); add = ForearmMargin; break; }
                    case 2: { var v = virt[pr.arm]; x = v.S + poseRu[pr.arm] * (v.upper[pr.sample] - v.S); garment = false; add = UpperArmMargin - Mathf.Max(0, v.upper0[pr.sample]); break; }
                    default: x = prop.world[pr.sample] + T + ahead; add = PropMargin; break;
                }
                float d = HeroClearanceProxy.Depth(c, x, garment, out var n) + add;
                if (d <= 0) continue;
                if (d > worst) worst = d;
                if (!push) continue;
                int k = pr.cap; if (d > capWorst[k]) { capWorst[k] = d; capDir[k] = n; }
                // Gauss-Newton: each intruding point wants n.dT >= d
                gnA.xx += n.x * n.x; gnA.xy += n.x * n.y; gnA.xz += n.x * n.z; gnA.yy += n.y * n.y; gnA.yz += n.y * n.z; gnA.zz += n.z * n.z; gnB += n * d;
            }
            return worst;
        }

        Prop heldForPairs;
        void Capture(Arm[] group)
        {
            virtCount = 0; pairsValid = false;
            foreach (var a in group)
            {
                if (!a.hand) continue;
                var v = virt[virtCount++]; v.a = a; a.limbNear = false;
                Place(a.handS); Place(a.foreS); Place(a.upperS);
                Copy(a.handS, ref v.hand); Copy(a.foreS, ref v.fore); Copy(a.upperS, ref v.upper);
                v.S = a.upper.position; v.E = a.lower.position; v.W = a.hand.position; v.u = Vector3.Distance(v.S, v.E); v.l = Vector3.Distance(v.E, v.W);
                if (v.fore0.Length != v.fore.Length) v.fore0 = new float[v.fore.Length];
                if (v.upper0.Length != v.upper.Length) v.upper0 = new float[v.upper.Length];
            }
            // the upper arm's own intrusion now, so a move is only charged for what it adds (from the pairs, built at T = 0)
            for (int vi = 0; vi < virtCount; vi++) System.Array.Clear(virt[vi].upper0, 0, virt[vi].upper0.Length);
            BuildPairs(Vector3.zero, heldForPairs);
            foreach (var pr in pairs)
                if (pr.kind == 2)
                {
                    var v = virt[pr.arm];
                    float d = HeroClearanceProxy.Depth(cand[pr.cap], v.upper[pr.sample], false, out _) + UpperArmMargin;
                    if (d > v.upper0[pr.sample]) v.upper0[pr.sample] = d;
                }
            foreach (var pr in pairs)
                if (pr.kind == 1 || pr.kind == 2)
                {
                    var v = virt[pr.arm];
                    if (Reaches(cand[pr.cap], pr.kind == 1 ? v.fore[pr.sample] : v.upper[pr.sample], (Residual ? .02f : PairSlack) + Margin)) v.a.limbNear = true;
                }
        }

        void Translate(Arm[] group, Prop prop, float travel, float dt)
        {
            travel = Mathf.Clamp01(travel) * (group.Length > 1 ? MaxGroupTravel : MaxTravel);
            var g0 = group[0];
            if (prop != null) Place(prop);
            // obstacles near the grip arms (shoulder to fingertips) and the prop, minus the group's own arms
            Vector3 lo = Vector3.positiveInfinity, hi = Vector3.negativeInfinity;
            foreach (var a in group)
            {
                if (!a.hand) continue; Place(a.handS);
                lo = Vector3.Min(lo, a.upper.position); hi = Vector3.Max(hi, a.upper.position);
                foreach (var smp in a.handS) { lo = Vector3.Min(lo, smp.world); hi = Vector3.Max(hi, smp.world); }
            }
            if (prop != null) foreach (var w in prop.world) { lo = Vector3.Min(lo, w); hi = Vector3.Max(hi, w); }
            var centre = (lo + hi) * .5f; float radius = (hi - lo).magnitude * .5f + travel + Margin;
            Gather(g0.obstacles, centre, radius, near); cand.Clear(); cand.AddRange(near);
            if (group.Length > 1) cand.RemoveAll(c => Array.IndexOf(group[1].ownCapsules, c) >= 0);
            if (capWorst.Length < cand.Count) { capWorst = new float[cand.Count * 2]; capDir = new Vector3[cand.Count * 2]; }
            // the clip's wrist velocity (for the anticipation below), known before pairing so one pairing covers the look-ahead
            var vel = Vector3.zero;
            if (dt > 0 && g0.hasAnim) vel = root.TransformVector((root.InverseTransformPoint(g0.hand.position) - g0.animW) / dt);
            g0.animW = root.InverseTransformPoint(g0.hand.position); g0.hasAnim = true;
            pairExtra = !Residual && travel > 0 && vel.sqrMagnitude > .01f ? Mathf.Min(vel.magnitude * AheadFar, .12f) : 0;
            heldForPairs = prop; Capture(group);
            // A continuous tracker, not a fresh choice every frame: start from last frame's correction (in the hero's space),
            // push out along the obstacles' own directions until clear, and when clear relax back towards the authored pose at
            // the release rate (only as far as stays clear). The correction is a smooth function of the motion: no pops, no
            // jumping between solutions, and a still pose keeps a still correction.
            const float clear = .0002f;
            var T = dt > 0 ? root.TransformVector(g0.travelApplied) : Vector3.zero;
            if (T.magnitude > travel) T = Vector3.ClampMagnitude(T, travel);
            if (T.sqrMagnitude > 0) T = Reach(group, T);
            if (travel > 0 && cand.Count > 0)
            {
                float v = Push(group, prop, travel, ref T, clear);
                if (v > Margin + .001f && T.sqrMagnitude > 1e-8f)
                {
                    // last frame's correction can hold the hand on the wrong side once the pose has moved on: solve from the
                    // authored pose too and keep it when it is clearly better
                    var F = Vector3.zero; float vf = Push(group, prop, travel, ref F, clear);
                    if (vf < v - .001f) { T = F; v = vf; }
                }
                if (v <= clear && T.sqrMagnitude > 1e-10f)
                {
                    // relax towards the authored pose, never into an intrusion
                    float keep = dt > 0 ? Mathf.Exp(-dt / Release) : 0;
                    var relaxed = Reach(group, T * keep);
                    if (Eval(relaxed, prop, false) <= clear) T = relaxed;
                    else
                    {
                        float kLo = keep, kHi = 1;
                        for (int b = 0; b < 2; b++) { float m = (kLo + kHi) * .5f; if (Eval(Reach(group, T * m), prop, false) <= clear) kHi = m; else kLo = m; }
                        if (kHi < .97f) T = Reach(group, T * kHi);   // no creeping by a hair every frame in a still pose
                    }
                }
                if (Trace && v > Margin)
                    UnityEngine.Debug.Log($"[ClearanceTrace] side {g0.side} travel {travel:0.000} T {T:F3} v {v * 1000:0.0} cand {string.Join(",", cand.Select(c => c.name))}");
            }
            else T = Vector3.zero;
            // anticipation: the clip's wrist velocity says where the grip will be a moment from now
            // (only when something is within reach now, or the look-ahead carries the hand further than the pairing slack)
            if (!Residual && travel > 0 && cand.Count > 0 && vel.sqrMagnitude > .01f && (pairs.Count > 0 || vel.magnitude * AheadFar > PairSlack))
            {
                var sum = T;
                foreach (var (tau, w) in Ahead)
                {
                    ahead = Vector3.ClampMagnitude(vel * tau, .12f);
                    var Tk = T; float vk = Push(group, prop, travel, ref Tk, .0002f);
                    sum += (Tk - T) * w;
                }
                ahead = Vector3.zero;
                T = Reach(group, Vector3.ClampMagnitude(sum, travel));
            }
            var applied = root.InverseTransformVector(T);
            // the grip correction changes at most MaxHandSpeed: when the solver switches to a better solution (or a deep intrusion
            // appears) the hand glides there over a few frames instead of snapping
            if (dt > 0 && MaxHandSpeed > 0) applied = g0.travelApplied + Vector3.ClampMagnitude(applied - g0.travelApplied, MaxHandSpeed * dt / Mathf.Max(1e-6f, root.lossyScale.x));
            foreach (var a in group) a.travelApplied = applied;
            var world = root.TransformVector(applied);
            if (world.sqrMagnitude < 1e-10f) return;
            world = Reach(group, world);
            // never flip an elbow: a move whose IK would turn the elbow's hinge past 90 degrees from the clip's is shortened
            for (int i = 0; i < 6 && Flips(world); i++) world = Reach(group, world * .6f);   // (cannot happen with the hinge pole; kept as a guard)
            foreach (var a in group)
            {
                var rot = a.hand.rotation; var target = a.hand.position + world;
                HeroPoseSafety.Solve(a.upper, a.lower, a.hand, target);
                a.hand.rotation = rot;
                foreach (var c in a.ownCapsules) proxy.Refresh(c);
            }
            if (prop != null && holder >= 0 && !prop.grip.IsChildOf(arms[holder].hand)) prop.grip.position += world;
        }

        /// Damped least-squares pushes from T until clear (or no progress). Returns the remaining violation.
        float Push(Arm[] group, Prop prop, float travel, ref Vector3 T, float clear)
        {
            float v = Eval(T, prop, true);
            for (int it = 0; it < 5 && v > clear; it++)
            {
                // one damped least-squares step over every intruding point (a crease: thigh and hip together), and the
                // per-obstacle deepest push as the fallback when that stalls
                var step = GaussNewtonStep();
                var next = Reach(group, Vector3.ClampMagnitude(T + step * 1.05f, travel));
                float vn = Eval(next, prop, true);
                if (vn >= v - 1e-5f)
                {
                    Eval(T, prop, true); step = Vector3.zero;
                    for (int k = 0; k < cand.Count; k++) if (capWorst[k] > 0) step += capDir[k] * capWorst[k];
                    next = Reach(group, Vector3.ClampMagnitude(T + step * 1.05f, travel)); vn = Eval(next, prop, true);
                    if (vn >= v - 1e-5f) break;   // no progress either way: keep the better one
                }
                T = next; v = vn;
            }
            return v;
        }

        bool Flips(Vector3 T)
        {
            for (int vi = 0; vi < virtCount; vi++)
            {
                var v = virt[vi]; var hinge = Vector3.Cross(v.E - v.S, v.W - v.E);
                if (hinge.sqrMagnitude < 1e-8f || Vector3.Angle(v.E - v.S, v.W - v.E) < 20) continue;   // a straight arm has no hinge to flip
                var Wt = v.W + T; var Et = ElbowFor(v, Wt);
                if (Vector3.Dot(hinge, Vector3.Cross(Et - v.S, Wt - Et)) < 0) return true;
            }
            return false;
        }

        /// The translation, kept inside every grip arm's reach: a hand pushed past a straight arm swings round the shoulder
        /// instead (the arm lifts away from the body) rather than losing the push.
        static Vector3 Reach(Arm[] group, Vector3 T)
        {
            for (int pass = 0; pass < (group.Length > 1 ? 4 : 1); pass++)
                foreach (var a in group)
                {
                    var S = a.upper.position; var W = a.hand.position;
                    float u = Vector3.Distance(S, a.lower.position), l = Vector3.Distance(a.lower.position, W);
                    float now = Vector3.Distance(S, W);
                    var to = W + T - S; float d = to.magnitude; if (d < 1e-6f) continue;
                    if (Vector3.Angle(a.lower.position - S, W - a.lower.position) < StraightArm) { T = S + to * (now / d) - W; continue; }
                    // never more bend than the clip already has: a straight arm may stay straight (no sudden elbow kink)
                    float far = Mathf.Max(u + l - .003f, now), close = Mathf.Abs(u - l) + .003f;
                    if (d > far) T = S + to * (far / d) - W;
                    else if (d < close) T = S + to * (close / d) - W;
                }
            return T;
        }

        static bool Reachable(Arm a, Vector3 target)
        {
            float u = Vector3.Distance(a.upper.position, a.lower.position), l = Vector3.Distance(a.lower.position, a.hand.position);
            float d = Vector3.Distance(a.upper.position, target);
            return d < u + l - .002f && d > Mathf.Abs(u - l) + .002f;
        }

        // ---------------------------------------------------------------- 2. elbow swivel
        readonly List<Capsule> swivelNear = new List<Capsule>(32);
        Vector3[] foreRest = new Vector3[0], upperRest = new Vector3[0]; float[] upperBase = new float[0];
        static readonly float[] SwivelSteps = { 12f, 6f, 3f, 1.5f };
        const float SwivelGain = .01f;   // Total() units: (0.3 mm)^2 * 1e5
        readonly List<Capsule> shoulderNear = new List<Capsule>(32);
        /// The clavicle carries the shoulder joint a few cm (the wrist stays exactly where it is, the elbow is re-solved), when the
        /// forearm or the outer upper arm is still inside after the swivel: what a raised cross-body arm (a golf follow-through,
        /// arms crossed) needs. The general form of the old female-golf "open the shoulder" fix.
        void Shoulder(Arm a, float dt)
        {
            if (!a.hand || !a.clavicle || MaxShoulderShift <= 0) return;
            bool held = a.shoulderApplied.sqrMagnitude > 1e-8f;
            // only an arm whose hand is held in place needs it (a free hand is carried out by the grip move)
            if (!held && (!a.limbNear || a.travel > .05f)) return;
            Place(a.foreS); Place(a.upperS);
            Vector3 S = a.upper.position, E = a.lower.position, W = a.hand.position;
            float u = Vector3.Distance(S, E), l = Vector3.Distance(E, W);
            Gather(a.obstacles, (S + W) * .5f, Vector3.Distance(S, W) * .5f + .15f, shoulderNear);
            if (shoulderNear.Count == 0 && !held) return;
            var hinge = Vector3.Cross(E - S, W - E);
            float Cost(Vector3 shift, out Vector3 push)
            {
                var S2 = S + shift; var delta = W - S2; float d = Mathf.Clamp(delta.magnitude, Mathf.Abs(u - l) + .00001f, u + l - .00001f);
                var axis = delta.normalized; var pole = HeroPoseSafety.Pole(E - S, hinge, axis, u);
                float along = (u * u - l * l + d * d) / (2 * d); var E2 = S2 + axis * along + pole * Mathf.Sqrt(Mathf.Max(0, u * u - along * along));
                var Ru = Quaternion.FromToRotation(E - S, E2 - S2); var Rf = Quaternion.FromToRotation(W - E, W - E2);
                float cost = 0; push = Vector3.zero;
                foreach (var smp in a.foreS) { float dd = Worst(shoulderNear, E2 + Rf * (smp.world - E), true, ForearmMargin, out var n, out _); if (dd > 0) { cost += dd * dd; push += n * dd; } }
                foreach (var smp in a.upperS) { float dd = Worst(shoulderNear, S2 + Ru * (smp.world - S), false, UpperArmMargin, out var n, out _); if (dd > 0) { cost += dd * dd; push += n * dd; } }
                return cost;
            }
            float c0 = Cost(Vector3.zero, out var dir);
            var prev = root.TransformVector(a.shoulderApplied);
            var best = Vector3.zero; float bestCost = c0;
            if (held) { float ch = Cost(prev, out _); if (ch <= bestCost) { best = prev; bestCost = ch; } }
            if (c0 > 1e-8f && dir.sqrMagnitude > 1e-12f)
            {
                dir.Normalize();
                foreach (float m in ShoulderSteps)
                {
                    var shift = dir * (MaxShoulderShift * m); float cs = Cost(shift, out _);
                    if (cs < bestCost - 1e-7f) { bestCost = cs; best = shift; }
                }
            }
            // only a real gain (half the intrusion energy) is worth moving the shoulder; then change at most ShoulderRate
            if (bestCost > c0 * .5f && !held) best = Vector3.zero;
            var target = root.InverseTransformVector(best);
            if (dt > 0) target = a.shoulderApplied + Vector3.ClampMagnitude(target - a.shoulderApplied, ShoulderRate * dt / Mathf.Max(1e-6f, root.lossyScale.x));
            a.shoulderApplied = target;
            var world = root.TransformVector(target);
            if (world.sqrMagnitude < 1e-10f) return;
            // turn the clavicle so the shoulder joint lands at S + world, then put the wrist back exactly
            var C = a.clavicle.position; var from = S - C; var to = S + world - C;
            if (from.sqrMagnitude < 1e-8f || to.sqrMagnitude < 1e-8f) return;
            var ur = a.upper.rotation; var lr = a.lower.rotation; var hr = a.hand.rotation;
            a.clavicle.rotation = Quaternion.FromToRotation(from, to) * a.clavicle.rotation;
            a.upper.rotation = ur; a.lower.rotation = lr;
            HeroPoseSafety.Solve(a.upper, a.lower, a.hand, W); a.hand.rotation = hr;
            foreach (var c in a.ownCapsules) proxy.Refresh(c);
        }
        static readonly float[] ShoulderSteps = { .33f, .67f, 1f };

        void Swivel(Arm a, float dt)
        {
            if (!a.hand || a.foreS.Length == 0) return;
            // nothing near the forearm or upper arm and no swivel held: nothing to do
            if (!a.limbNear && Mathf.Abs(a.swivelApplied) < .01f && a.travelApplied.sqrMagnitude < 1e-8f) { a.swivelApplied = 0; return; }
            Place(a.foreS); Place(a.upperS);
            var S = a.upper.position; var W = a.hand.position; var axis = W - S;
            if (axis.sqrMagnitude < 1e-6f) return; axis.Normalize();
            if (foreRest.Length < a.foreS.Length) foreRest = new Vector3[a.foreS.Length];
            if (upperRest.Length < a.upperS.Length) upperRest = new Vector3[a.upperS.Length];
            for (int i = 0; i < a.foreS.Length; i++) foreRest[i] = a.foreS[i].world - S;
            for (int i = 0; i < a.upperS.Length; i++) upperRest[i] = a.upperS[i].world - S;
            if (upperBase.Length < a.upperS.Length) upperBase = new float[a.upperS.Length];
            // obstacles in reach of the swung arm: a sphere round the shoulder through the elbow
            float reach = Vector3.Distance(S, a.lower.position) + .05f;
            var elbowMid = (S + W) * .5f; float rad = Mathf.Max(reach, Vector3.Distance(S, W) * .5f + .12f);
            Gather(a.obstacles, elbowMid, rad, swivelNear);
            for (int i = 0; i < a.upperS.Length; i++) upperBase[i] = Mathf.Max(0, Worst(swivelNear, S + upperRest[i], false, UpperArmMargin, out _, out _));
            // nothing near: the desired swivel is 0, and a held one still eases out below (no snap)
            float peak = 0;
            float Cost(float deg)
            {
                var r = Quaternion.AngleAxis(deg, axis); float cost = 0;
                for (int i = 0; i < a.foreS.Length; i++)
                {
                    float d = Worst(swivelNear, S + r * foreRest[i], true, ForearmMargin, out _, out _);
                    cost += d * d; if (d > peak) peak = d;
                }
                for (int i = 0; i < a.upperS.Length; i++)
                {
                    // the upper arm is only charged for what the swivel adds (it can sit in the armpit / against the bust by nature)
                    float d = Worst(swivelNear, S + r * upperRest[i], false, UpperArmMargin, out _, out _) - upperBase[i];
                    if (d < 0) d = 0;
                    cost += d * d; if (d + Margin > peak) peak = d + Margin;
                }
                return cost;
            }
            // Continuous like the grip: start at last frame's swivel, walk downhill in small steps (intrusion first, then a
            // gentle pull back to the authored elbow), and when clear relax towards it only as far as it stays clear.
            float cur = dt > 0 ? Mathf.Clamp(a.swivelApplied, -MaxSwivel, MaxSwivel) : 0;
            float Total(float deg) => Cost(deg) * 1e5f + deg * deg * 2e-6f;
            float applied;
            float cc = Cost(cur);
            if (cc <= 1e-9f)
            {
                applied = cur;
                if (Mathf.Abs(cur) > .01f)
                {
                    float relaxed = cur * (dt > 0 ? Mathf.Exp(-dt / SwivelRelease) : 0);
                    applied = Cost(relaxed) <= 1e-9f ? relaxed : cur;
                }
            }
            else if (peak <= ForearmMargin + .0005f && Mathf.Abs(cur) < .01f) applied = 0;   // only the margin band, nothing held: leave the authored elbow
            else
            {
                float best = Total(cur);
                foreach (float step in SwivelSteps)
                    for (int rep = 0; rep < 3; rep++)
                    {
                        float up = Mathf.Min(MaxSwivel, cur + step), dn = Mathf.Max(-MaxSwivel, cur - step);
                        float tu = Total(up), td = Total(dn);
                        // move only for a real gain (~0.3 mm of intrusion): numerical noise must not make the elbow dither
                        if (tu < best - SwivelGain && tu <= td) { best = tu; cur = up; }
                        else if (td < best - SwivelGain) { best = td; cur = dn; }
                        else break;
                    }
                applied = cur;
                if (Trace) UnityEngine.Debug.Log($"[ClearanceTrace] swivel side {a.side} from {(dt > 0 ? a.swivelApplied : 0):0.0} cost0 {cc * 1e6f:0.0} -> {cur:0.0} cost {Cost(cur) * 1e6f:0.0} peak {peak * 1000:0.0}mm near {swivelNear.Count}");
            }
            // the elbow turns at most this fast: a swivel only moves the elbow (never the hand), so easing it costs no clearance at the hand
            // capped at SwivelRate plus twice the arm's own turning speed in the clip: a still pose stays still, a swing can follow
            var upperDir = root.InverseTransformDirection(a.lower.position - a.upper.position);
            float own = dt > 0 && a.lastUpperDir.sqrMagnitude > .5f ? Vector3.Angle(upperDir, a.lastUpperDir) / dt : 0;
            a.lastUpperDir = upperDir.normalized;
            if (dt > 0) { float lim = (SwivelRate + 2 * own) * dt, from = Mathf.Clamp(a.swivelApplied, -MaxSwivel, MaxSwivel); applied = Mathf.Clamp(applied, from - lim, from + lim); }
            a.swivelApplied = applied;
            if (Mathf.Abs(applied) < 1e-4f) return;
            var rot = a.hand.rotation;
            a.upper.rotation = Quaternion.AngleAxis(applied, axis) * a.upper.rotation;
            a.hand.rotation = rot;
            foreach (var c in a.ownCapsules) proxy.Refresh(c);
        }

        // ---------------------------------------------------------------- 3. prop turn
        void TurnProp(Arm a, Prop p, float travel, float dt)
        {
            float limit = MaxPropTurn * Mathf.Clamp01(travel);
            var W = a.hand.position; Place(p);
            Gather(a.obstacles, W, Mathf.Abs(p.grip.lossyScale.x) * 1f + .2f, near);
            Vector3 turn = Vector3.zero;   // world axis * degrees
            if (limit > 0 && near.Count > 0)
            {
                var rel = new Vector3[p.world.Length]; for (int i = 0; i < rel.Length; i++) rel[i] = p.world[i] - W;
                for (int it = 0; it < 4; it++)
                {
                    var R = turn.sqrMagnitude > 1e-10f ? Quaternion.AngleAxis(turn.magnitude, turn.normalized) : Quaternion.identity;
                    Vector3 torque = Vector3.zero; float lever = 0, worst = 0;
                    for (int i = 0; i < rel.Length; i++)
                    {
                        if (p.handle[i]) continue;
                        var x = W + R * rel[i];
                        float deep = 0; Vector3 dir = Vector3.zero;
                        foreach (var c in near)
                        {
                            if (Excluded(p, i, c, a.side, false)) continue;
                            float r = c.bound + Margin; if ((c.midWorld - x).sqrMagnitude > r * r) continue;
                            float d = HeroClearanceProxy.Depth(c, x, true, out var n) + Margin;
                            if (d > deep) { deep = d; dir = n; }
                        }
                        if (deep <= 0) continue;
                        var arm = x - W; torque += Vector3.Cross(arm, dir * deep); lever = Mathf.Max(lever, arm.magnitude); worst = Mathf.Max(worst, deep);
                    }
                    if (worst < .0002f || torque.sqrMagnitude < 1e-12f) break;
                    float deg = Mathf.Rad2Deg * worst / Mathf.Max(.05f, lever) * 1.1f;
                    turn = Vector3.ClampMagnitude(turn + torque.normalized * deg, limit);
                }
            }
            var desired = root.InverseTransformVector(turn); var applied = desired;
            if (dt > 0 && a.turnApplied.sqrMagnitude > desired.sqrMagnitude)
                applied = Vector3.Lerp(a.turnApplied, desired, 1 - Mathf.Exp(-dt / Release));
            a.turnApplied = applied;
            var w = root.TransformVector(applied);
            if (w.sqrMagnitude < 1e-8f) return;
            var q = Quaternion.AngleAxis(w.magnitude, w.normalized);
            a.hand.rotation = q * a.hand.rotation;
            if (!p.grip.IsChildOf(a.hand)) { p.grip.position = W + q * (p.grip.position - W); p.grip.rotation = q * p.grip.rotation; }
            foreach (var c in a.ownCapsules) proxy.Refresh(c);
        }

        // ---------------------------------------------------------------- 4. second hand along the handle
        void Slide(Arm second, Arm first, Prop p, float travel, float dt)
        {
            if (!second.hand) return;
            Place(second.handS);
            var ax = p.grip.TransformDirection(p.axisLocal).normalized;
            var mine = new List<Capsule>(); foreach (var c in first.ownCapsules) if (c.part == Part.Hand || c.part == Part.Finger) mine.Add(c);
            float limit = MaxSlide * Mathf.Clamp01(travel), s = 0;
            if (limit > 0)
                for (int it = 0; it < 4; it++)
                {
                    float worst = 0;
                    foreach (var smp in second.handS)
                    {
                        float d = Worst(mine, smp.world + ax * s, true, .001f, out var n, out _);
                        float along = Vector3.Dot(n, ax); if (d > 0 && Mathf.Abs(along) > .2f) worst = Mathf.Max(worst, d / Mathf.Abs(along) * Mathf.Sign(along));
                    }
                    if (Mathf.Abs(worst) < .0002f) break;
                    // only ever away from the first hand along the handle
                    float away = Mathf.Sign(Vector3.Dot(second.hand.position - first.hand.position, ax));
                    s = Mathf.Clamp(s + Mathf.Abs(worst) * away, -limit, limit);
                }
            float applied = s;
            if (dt > 0 && Mathf.Abs(second.slideApplied) > Mathf.Abs(s)) applied = Mathf.Lerp(second.slideApplied, s, 1 - Mathf.Exp(-dt / Release));
            second.slideApplied = applied;
            if (Mathf.Abs(applied) < 1e-5f) return;
            var rot = second.hand.rotation; var target = second.hand.position + ax * applied;
            if (Reachable(second, target)) { HeroPoseSafety.Solve(second.upper, second.lower, second.hand, target); second.hand.rotation = rot; }
        }

        // ---------------------------------------------------------------- report
        /// Deepest hand / forearm / prop sample inside the proxy (no margin), m.
        public float Measure(bool keepWhere)
        {
            if (!Ready) return 0;
            float worst = 0; string where = "";
            foreach (var a in arms)
            {
                if (!a.hand) continue;
                Place(a.handS); Place(a.foreS);
                var centre = (a.hand.position + a.lower.position) * .5f;
                Gather(a.obstacles, centre, Vector3.Distance(a.hand.position, a.lower.position) * .5f + .26f, near);
                if (near.Count == 0) continue;
                foreach (var s in a.handS) { float d = Worst(near, s.world, true, 0, out _, out var c); if (d > worst) { worst = d; where = (a.side < 0 ? "L" : "R") + "hand>" + c?.name; } }
                foreach (var s in a.foreS) { float d = Worst(near, s.world, true, 0, out _, out var c); if (d > worst) { worst = d; where = (a.side < 0 ? "L" : "R") + "fore>" + c?.name; } }
            }
            if (keepWhere) ResidualWhere = where;
            return worst;
        }

        /// Offline searches (the track bake's body step): every hand, forearm and held-prop sample against the proxy with the
        /// solver's own exclusions. Returns the deepest violation (m); sum = the summed violation (a smoother search cost).
        public float MeasureAll(out float sum, float margin = 0)
        {
            sum = 0; if (!Ready) return 0;
            proxy.Refresh(); FindGrip(new Request());
            float worst = 0;
            foreach (var a in arms)
            {
                if (!a.hand) continue;
                Place(a.handS); Place(a.foreS);
                var centre = (a.hand.position + a.lower.position) * .5f;
                Gather(a.obstacles, centre, Vector3.Distance(a.hand.position, a.lower.position) * .5f + .26f, near);
                for (int pass = 0; pass < 2; pass++)
                    foreach (var s in pass == 0 ? a.handS : a.foreS)
                    {
                        float d = Worst(near, s.world, true, margin, out _, out _);
                        if (d > 0) { sum += d; worst = Mathf.Max(worst, d); }
                    }
            }
            if (held != null && holder >= 0)
            {
                Place(held); var a = arms[holder];
                Vector3 lo = Vector3.positiveInfinity, hi = Vector3.negativeInfinity; foreach (var w in held.world) { lo = Vector3.Min(lo, w); hi = Vector3.Max(hi, w); }
                Gather(a.obstacles, (lo + hi) * .5f, (hi - lo).magnitude * .5f + .05f, near);
                for (int i = 0; i < held.world.Length; i++)
                    foreach (var c in near)
                    {
                        if (Excluded(held, i, c, a.side, both)) continue;
                        float d = HeroClearanceProxy.Depth(c, held.world[i], true, out _) + margin;
                        if (d > 0) { sum += d; worst = Mathf.Max(worst, d); }
                    }
            }
            return worst;
        }

        // ---------------------------------------------------------------- one call per displayed frame
        struct State { public Vector3 t; public float sw; public Vector3 turn; public float slide; public Vector3 sh; }
        readonly State[] snapshot = new State[2]; int snapFrame = int.MinValue;
        /// Called before Solve with the frame number: a second solve in the same frame (a re-evaluated pose) starts from
        /// the state the frame began with, so smoothing never runs twice.
        public void BeginFrame(int frame)
        {
            if (!built) return;
            if (frame == snapFrame)
                for (int i = 0; i < 2; i++) { arms[i].travelApplied = snapshot[i].t; arms[i].swivelApplied = snapshot[i].sw; arms[i].turnApplied = snapshot[i].turn; arms[i].slideApplied = snapshot[i].slide; arms[i].shoulderApplied = snapshot[i].sh; }
            else
            {
                for (int i = 0; i < 2; i++) snapshot[i] = new State { t = arms[i].travelApplied, sw = arms[i].swivelApplied, turn = arms[i].turnApplied, slide = arms[i].slideApplied, sh = arms[i].shoulderApplied };
                snapFrame = frame;
            }
        }
        /// Diagnostics (BeforeDepth) cost a full extra measurement: off in the game.
        public bool Diagnostics;
        /// Bake-first: the pose already carries the baked correction (HeroClearanceTracks), so this pass only solves what is left
        /// (blends, transitions). It skips the anticipation look-ahead (onsets are baked and smoothed offline).
        public bool Residual;
        /// Logs why a grip could not be cleared (development only).
        public bool Trace, TraceAll;

        /// Forget the smoothing state (a new clip, a teleport).
        public void Reset() { foreach (var a in arms) { if (a == null) continue; a.shoulderApplied = Vector3.zero; a.hasAnim = false; a.travelApplied = Vector3.zero; a.swivelApplied = 0; a.turnApplied = Vector3.zero; a.slideApplied = 0; } }
    }
}
