using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

namespace GolfArcade.Tennis
{
    /// HAND CLEARANCE (work/hand-clearance): the hero's collision proxy, fitted automatically from the skinned body
    /// and from whatever garments and accessories the hero wears. Nothing in here is tuned per hero or per garment.
    ///
    /// One proxy per deforming bone (pelvis, spine, chest, neck, head, clavicles, arms, hands, every finger
    /// phalanx, thighs, shins, feet). Each proxy is a "radial capsule": a segment along the bone with two
    /// hemispherical caps, and a table of surface distances measured along straight rays from that core
    /// (rows = position along the bone / polar angle on the caps, columns = angle around the bone in the
    /// cross-section's own ellipse). The table is measured by casting the rays against the rest-pose triangles
    /// skinned to that bone, so every bump of the real body (nose, ears, buttocks, knee) is in it.
    ///
    /// Two tables per proxy: R = body and garments together (the farthest surface along the ray: the outside of
    /// the clothes), Rb = the bare body. A garment's offset is therefore measured from the garment mesh itself:
    /// put on a bigger shirt and the torso proxy is bigger, with no number to change.
    public sealed class HeroClearanceProxy
    {
        public enum Part { Pelvis, Torso, Neck, Head, Clavicle, UpperArm, Forearm, Hand, Finger, Thigh, Shin, Foot }

        public sealed class Capsule
        {
            public string name; public Transform bone; public Part part; public int side;   // -1 left, 0 centre, 1 right
            public Vector3 a, axis, e1, e2; public float length, ea, eb;
            public int K, J, M, Rows;
            public float[] R, Rb;
            public float[] offset;   // R - Rb per node: what the garments add (the manifest reports it)
            public Vector3 midLocal; public float boundLocal;
            // per-frame world cache
            public Matrix4x4 toLocal, toWorld; public Vector3 midWorld; public float scale, bound;
            // largest surface distance from the core; the core segment in world space; per table row the largest radius of it and its neighbours
            public float maxR; public Vector3 aW, bW; public float[] rowMax;
            public int verts, garmentNodes;
            public object MemberwiseCopy() => MemberwiseClone();
        }

        public readonly List<Capsule> capsules = new List<Capsule>();
        readonly Dictionary<Transform, Capsule> byBone = new Dictionary<Transform, Capsule>();
        public Capsule Of(Transform bone) => bone && byBone.TryGetValue(bone, out var c) ? c : null;
        public string Report { get; private set; } = "";
        public int GarmentCount { get; private set; }
        /// Fit time at load (ms), for the COST report.
        public double FitMs { get; private set; }
        /// True when the tables came from an earlier hero with the same body and garment meshes.
        public bool Cached { get; private set; }
        static readonly Dictionary<string, List<Capsule>> cache = new Dictionary<string, List<Capsule>>();
        /// Drops the shared tables (a garment mesh was edited in place, e.g. by a test).
        public static void ClearCache() { lock (cache) cache.Clear(); }
        string CacheKey()
        {
            var sb = new System.Text.StringBuilder();
            foreach (var s in sources) { if (!s.mesh) return null; sb.Append(s.mesh.GetInstanceID()).Append(':').Append(s.v.Length).Append('|'); }
            return sb.ToString();
        }

        // ---------------------------------------------------------------- which bones become proxies
        static readonly (HumanBodyBones bone, Part part, int side)[] Layout =
        {
            (HumanBodyBones.Hips, Part.Pelvis, 0), (HumanBodyBones.Spine, Part.Torso, 0), (HumanBodyBones.Chest, Part.Torso, 0),
            (HumanBodyBones.UpperChest, Part.Torso, 0), (HumanBodyBones.Neck, Part.Neck, 0), (HumanBodyBones.Head, Part.Head, 0),
            (HumanBodyBones.LeftShoulder, Part.Clavicle, -1), (HumanBodyBones.RightShoulder, Part.Clavicle, 1),
            (HumanBodyBones.LeftUpperArm, Part.UpperArm, -1), (HumanBodyBones.RightUpperArm, Part.UpperArm, 1),
            (HumanBodyBones.LeftLowerArm, Part.Forearm, -1), (HumanBodyBones.RightLowerArm, Part.Forearm, 1),
            (HumanBodyBones.LeftHand, Part.Hand, -1), (HumanBodyBones.RightHand, Part.Hand, 1),
            (HumanBodyBones.LeftUpperLeg, Part.Thigh, -1), (HumanBodyBones.RightUpperLeg, Part.Thigh, 1),
            (HumanBodyBones.LeftLowerLeg, Part.Shin, -1), (HumanBodyBones.RightLowerLeg, Part.Shin, 1),
            (HumanBodyBones.LeftFoot, Part.Foot, -1), (HumanBodyBones.RightFoot, Part.Foot, 1),
        };
        public static IEnumerable<(HumanBodyBones bone, int side)> FingerBones()
        {
            for (var b = HumanBodyBones.LeftThumbProximal; b <= HumanBodyBones.LeftLittleDistal; b++) yield return (b, -1);
            for (var b = HumanBodyBones.RightThumbProximal; b <= HumanBodyBones.RightLittleDistal; b++) yield return (b, 1);
        }
        /// A vertex counts for a proxy when at least this much of its skin weight follows that proxy's bone.
        public const float Share = .3f;

        // ---------------------------------------------------------------- vertex sources (body + garments) in body bind space
        public sealed class Source
        {
            public string name; public bool garment; public Vector3[] v; public int[] t; public Mesh mesh;
            public int[][] proxy; public float[][] weight;   // per vertex: proxies it follows (index into capsules) and how much
            public int[] dominant;                           // per vertex: the proxy it follows most, -1 none
        }
        public readonly List<Source> sources = new List<Source>();

        readonly MatchHeroLook look;
        readonly Transform[] proxyBoneOf;   // capsule index -> bone (also before capsules are fitted)
        /// Part / side / name of every proxy index, also where no capsule could be fitted (a bone with too little skin):
        /// skin that follows such a bone still belongs to that limb.
        public Part[] partAt; public int[] sideAt; public string[] nameAt;
        public Transform BoneAt(int i) => proxyBoneOf[i];
        public int IndexOf(Transform bone) => Array.IndexOf(proxyBoneOf, bone);
        public bool IsArm(int index, int side) => index >= 0 && sideAt[index] == side && (partAt[index] == Part.Clavicle || partAt[index] == Part.UpperArm || partAt[index] == Part.Forearm || partAt[index] == Part.Hand || partAt[index] == Part.Finger);

        /// background: the heavy ray fitting runs on a worker thread (the hero appears at once; the clearance switches on
        /// when Ready, usually within a few frames). Mesh data and transforms are read here, on the calling (main) thread.
        public HeroClearanceProxy(MatchHeroLook look, bool background = false)
        {
            this.look = look;
            var timer = System.Diagnostics.Stopwatch.StartNew();
            var bones = new List<(Transform, Part, int, string)>();
            foreach (var (b, part, side) in Layout) { var t = look.Bone(b); if (t) bones.Add((t, part, side, b.ToString())); }
            foreach (var (b, side) in FingerBones()) { var t = look.Bone(b); if (t) bones.Add((t, Part.Finger, side, b.ToString())); }
            proxyBoneOf = new Transform[bones.Count];
            for (int i = 0; i < bones.Count; i++) proxyBoneOf[i] = bones[i].Item1;
            partAt = bones.Select(b => b.Item2).ToArray(); sideAt = bones.Select(b => b.Item3).ToArray(); nameAt = bones.Select(b => b.Item4).ToArray();
            Collect();
            // everything the fit needs from Unity, gathered now
            bindAt = new Matrix4x4[bones.Count]; childAt = new Vector3?[bones.Count];
            for (int i = 0; i < bones.Count; i++)
            {
                bindAt[i] = BindOf(bones[i].Item1);
                var child = ChildAlongChain(bones[i].Item1, bones[i].Item2);
                if (child) childAt[i] = bindAt[i].MultiplyPoint3x4(BindOf(child).inverse.MultiplyPoint3x4(Vector3.zero));   // the child joint, in this bone's space
            }
            string key = CacheKey();
            List<Capsule> shared = null;
            lock (cache) if (key != null) cache.TryGetValue(key, out shared);
            if (shared != null)
            {
                Install(bones, shared); Cached = true;
                timer.Stop(); FitMs = timer.Elapsed.TotalMilliseconds; Finish();
                return;
            }
            void Work()
            {
                var fitted = FitAll(bones);
                if (key != null) lock (cache) cache[key] = fitted;
                Install(bones, fitted);
                timer.Stop(); FitMs = timer.Elapsed.TotalMilliseconds;
            }
            if (!background) { Work(); Finish(); }
            else pending = System.Threading.Tasks.Task.Run(Work);
        }
        Matrix4x4[] bindAt; Vector3?[] childAt;
        System.Threading.Tasks.Task pending; bool finished;
        /// The tables are fitted (always true for a synchronous build). Call from the main thread.
        public bool Ready
        {
            get
            {
                if (finished) return true;
                if (pending == null || !pending.IsCompleted) return false;
                if (pending.IsFaulted) { Debug.LogException(pending.Exception); pending = null; return false; }
                Finish(); return true;
            }
        }
        void Install(List<(Transform, Part, int, string)> bones, List<Capsule> fitted)
        {
            var list = new List<Capsule>(bones.Count);
            for (int i = 0; i < bones.Count; i++)
            {
                var c = i < fitted.Count && fitted[i] != null ? (Capsule)fitted[i].MemberwiseCopy() : null;
                if (c != null) c.bone = bones[i].Item1;
                list.Add(c);
            }
            lock (capsules) { capsules.Clear(); capsules.AddRange(list); }
        }
        void Finish()
        {
            finished = true; byBone.Clear();
            foreach (var c in capsules) if (c != null) byBone[c.bone] = c;
            var sb = new System.Text.StringBuilder();
            foreach (var c in capsules) if (c != null) sb.Append($"{c.name}:{c.verts}v,{c.length * 1000:0}mm,garm{c.garmentNodes} ");
            Report = sb.ToString();
            Refresh();
        }
        List<Capsule> FitAll(List<(Transform, Part, int, string)> bones)
        {
            var vertsOf = new List<Vector3>[bones.Count]; var trisOf = new List<(Source, int)>[bones.Count];
            for (int i = 0; i < bones.Count; i++) { vertsOf[i] = new List<Vector3>(); trisOf[i] = new List<(Source, int)>(); }
            foreach (var s in sources)
            {
                if (!s.garment) for (int i = 0; i < s.v.Length; i++) foreach (int p in s.proxy[i]) vertsOf[p].Add(s.v[i]);
                for (int f = 0; f + 2 < s.t.Length; f += 3)
                {
                    var a = s.proxy[s.t[f]]; var b = s.proxy[s.t[f + 1]]; var c = s.proxy[s.t[f + 2]];
                    if (!s.garment) { foreach (int p in a) if (Array.IndexOf(b, p) >= 0 && Array.IndexOf(c, p) >= 0) trisOf[p].Add((s, f)); continue; }
                    // garment triangles: every bone any corner follows (a garment is a thin shell; a wider envelope is the safe side)
                    foreach (int p in a) trisOf[p].Add((s, f));
                    foreach (int p in b) if (Array.IndexOf(a, p) < 0) trisOf[p].Add((s, f));
                    foreach (int p in c) if (Array.IndexOf(a, p) < 0 && Array.IndexOf(b, p) < 0) trisOf[p].Add((s, f));
                }
            }
            var fitted = new List<Capsule>(bones.Count);
            for (int i = 0; i < bones.Count; i++) fitted.Add(Fit(i, bones[i].Item1, bones[i].Item2, bones[i].Item3, bones[i].Item4, vertsOf[i], trisOf[i]));
            return fitted;
        }

        int ProxyIndex(Transform t)
        {
            // the nearest ancestor that is a proxy bone (Toes -> Foot, Jaw/Eyes -> Head, twist helpers -> their limb)
            for (var x = t; x; x = x.parent)
            {
                int i = Array.IndexOf(proxyBoneOf, x);
                if (i >= 0) return i;
                if (x == look.transform) break;
            }
            return -1;
        }

        /// The body and every worn garment/accessory, with per-vertex proxy weights, in the body's mesh (bind) space.
        void Collect()
        {
            sources.Clear(); GarmentCount = 0;
            var body = look.body; if (!body || !body.sharedMesh) return;
            var bodyMesh = body.sharedMesh;
            // The runtime body has the skin under V2 garments removed (triangles only). The proxy needs the full surface.
            var full = FullBody(look, bodyMesh);
            var bodyToWorldAtBind = body.transform.localToWorldMatrix;
            sources.Add(Build("body", false, body, full, Matrix4x4.identity));
            foreach (var r in look.GetComponentsInChildren<Renderer>(false))
            {
                if (!r || r == body || !r.enabled || !r.gameObject.activeInHierarchy) continue;
                if (!(r.name.StartsWith("Kit_") || r.name.StartsWith("Acc_"))) continue;
                Mesh mesh = r is SkinnedMeshRenderer s ? s.sharedMesh : r.GetComponent<MeshFilter>()?.sharedMesh;
                if (!mesh || !mesh.isReadable) continue;
                // garment mesh space -> body mesh space (both are fixed children of the hero root)
                var rel = body.transform.worldToLocalMatrix * r.transform.localToWorldMatrix;
                Source src;
                if (r is SkinnedMeshRenderer sk) src = Build(r.name, true, sk, mesh, rel);
                else src = BuildRigid(r.name, r.transform, mesh);
                if (src != null) { sources.Add(src); GarmentCount++; }
            }
        }

        public static Mesh FullBody(MatchHeroLook look, Mesh runtime)
        {
            var f = typeof(MatchHeroLook).GetField("kitV2CoverSource", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
            var src = f?.GetValue(look) as Mesh;
            return src && src.isReadable && src.vertexCount == runtime.vertexCount ? src : runtime;
        }

        Source Build(string name, bool garment, SkinnedMeshRenderer r, Mesh mesh, Matrix4x4 meshToBody)
        {
            if (!mesh.isReadable) return null;
            var palette = r.bones; var weights = mesh.boneWeights;
            int n = mesh.vertexCount; if (weights.Length != n) return null;
            // palette index -> (proxy a, proxy b, t): ArmBlend_<a>_<b>_<n> twist helpers blend two palette bones
            var pa = new int[palette.Length]; var pb = new int[palette.Length]; var pt = new float[palette.Length];
            for (int i = 0; i < palette.Length; i++)
            {
                pa[i] = pb[i] = palette[i] ? ProxyIndex(palette[i]) : -1; pt[i] = 0;
                string bn = palette[i] ? palette[i].name : "";
                int k = bn.IndexOf("ArmBlend_", StringComparison.Ordinal);
                if (k < 0) continue;
                var parts = bn.Substring(k).Split('_');
                if (parts.Length < 4 || !int.TryParse(parts[1], out int ia) || !int.TryParse(parts[2], out int ib) || !int.TryParse(parts[3], out int it)) continue;
                pa[i] = ia < palette.Length && palette[ia] ? ProxyIndex(palette[ia]) : -1;
                pb[i] = ib < palette.Length && palette[ib] ? ProxyIndex(palette[ib]) : -1;
                pt[i] = it / 8f;
            }
            var v = mesh.vertices; var src = new Source { name = name, garment = garment, mesh = mesh, v = new Vector3[n], t = mesh.triangles, proxy = new int[n][], weight = new float[n][], dominant = new int[n] };
            var acc = new Dictionary<int, float>();
            for (int i = 0; i < n; i++)
            {
                src.v[i] = meshToBody.MultiplyPoint3x4(v[i]);
                acc.Clear(); var w = weights[i];
                void Add(int bone, float x)
                {
                    if (x <= 0 || bone < 0 || bone >= palette.Length) return;
                    if (pa[bone] >= 0) acc[pa[bone]] = (acc.TryGetValue(pa[bone], out var y) ? y : 0) + x * (1 - pt[bone]);
                    if (pb[bone] >= 0 && pt[bone] > 0) acc[pb[bone]] = (acc.TryGetValue(pb[bone], out var z) ? z : 0) + x * pt[bone];
                }
                Add(w.boneIndex0, w.weight0); Add(w.boneIndex1, w.weight1); Add(w.boneIndex2, w.weight2); Add(w.boneIndex3, w.weight3);
                int best = -1; float bw = 0; var ps = new List<int>(2); var ws = new List<float>(2);
                foreach (var kv in acc) { if (kv.Value > bw) { bw = kv.Value; best = kv.Key; } if (kv.Value >= Share) { ps.Add(kv.Key); ws.Add(kv.Value); } }
                // a loose garment (a skirt hem) can spread its weight over hips and both thighs, each under the share: it still
                // belongs to the bone it follows most
                if (garment && best >= 0 && !ps.Contains(best)) { ps.Add(best); ws.Add(bw); }
                src.proxy[i] = ps.ToArray(); src.weight[i] = ws.ToArray(); src.dominant[i] = best;
            }
            return src;
        }

        Source BuildRigid(string name, Transform t, Mesh mesh)
        {
            int p = ProxyIndex(t.parent); if (p < 0) return null;
            // rigidly attached (a cap on the head socket): mesh -> bone local now, -> body bind space through the bone's bind pose
            var rel = BindOf(proxyBoneOf[p]).inverse * proxyBoneOf[p].worldToLocalMatrix * t.localToWorldMatrix;
            var v = mesh.vertices; int n = v.Length;
            var src = new Source { name = name, garment = true, mesh = mesh, v = new Vector3[n], t = mesh.triangles, proxy = new int[n][], weight = new float[n][], dominant = new int[n] };
            for (int i = 0; i < n; i++) { src.v[i] = rel.MultiplyPoint3x4(v[i]); src.proxy[i] = new[] { p }; src.weight[i] = new[] { 1f }; src.dominant[i] = p; }
            return src;
        }

        /// body mesh space -> proxy bone local space (from the body's bind poses)
        Matrix4x4 BindOf(Transform bone)
        {
            var body = look.body; var palette = body.bones; var bind = body.sharedMesh.bindposes;
            int i = Array.IndexOf(palette, bone);
            if (i >= 0) return bind[i];
            // a bone with no skin of its own: through its nearest palette ancestor, using the current local offset
            var rel = Matrix4x4.identity;
            for (var x = bone; x && x != look.transform; x = x.parent)
            {
                int k = Array.IndexOf(palette, x);
                if (k >= 0) return rel * bind[k];
                rel = rel * Matrix4x4.TRS(x.localPosition, x.localRotation, x.localScale).inverse;
            }
            return Matrix4x4.identity;
        }

        // ---------------------------------------------------------------- fitting one proxy
        Capsule Fit(int index, Transform bone, Part part, int side, string name, List<Vector3> meshPts, List<(Source s, int f)> meshTris)
        {
            var bind = bindAt[index];
            var pts = new List<Vector3>(meshPts.Count);
            foreach (var p in meshPts) pts.Add(bind.MultiplyPoint3x4(p));
            if (pts.Count < 12) return null;
            var c = new Capsule { name = name, bone = bone, part = part, side = side, verts = pts.Count };
            bool finger = part == Part.Finger;
            c.M = finger ? 8 : part == Part.Hand || part == Part.Foot ? 16 : 32;
            c.J = finger ? 2 : 4;
            // axis: towards the child bone of the chain (the anatomical axis); the vertex cloud's main axis without one
            Vector3 centroid = Vector3.zero; foreach (var p in pts) centroid += p; centroid /= pts.Count;
            Vector3 axis = Vector3.zero;
            if (childAt[index].HasValue) axis = childAt[index].Value;   // towards the child joint
            if (axis.sqrMagnitude < 1e-6f) axis = Principal(pts, centroid);
            axis.Normalize();
            // cross-section frame
            float sxx = 0, sxy = 0, syy = 0; var tmp = Vector3.Cross(axis, Mathf.Abs(axis.y) < .9f ? Vector3.up : Vector3.right).normalized; var tmp2 = Vector3.Cross(axis, tmp);
            float smin = float.MaxValue, smax = float.MinValue;
            foreach (var p in pts)
            {
                var d = p - centroid; float s = Vector3.Dot(d, axis); smin = Mathf.Min(smin, s); smax = Mathf.Max(smax, s);
                float x = Vector3.Dot(d, tmp), y = Vector3.Dot(d, tmp2); sxx += x * x; sxy += x * y; syy += y * y;
            }
            float ang = .5f * Mathf.Atan2(2 * sxy, sxx - syy);
            c.e1 = (Mathf.Cos(ang) * tmp + Mathf.Sin(ang) * tmp2).normalized; c.e2 = Vector3.Cross(axis, c.e1).normalized;
            float v1 = 0, v2 = 0; foreach (var p in pts) { var d = p - centroid; v1 += Sq(Vector3.Dot(d, c.e1)); v2 += Sq(Vector3.Dot(d, c.e2)); }
            c.ea = Mathf.Sqrt(v1 / pts.Count); c.eb = Mathf.Sqrt(v2 / pts.Count);
            float big = Mathf.Max(c.ea, c.eb, 1e-4f); c.ea = Mathf.Max(c.ea, big * .4f) / big; c.eb = Mathf.Max(c.eb, big * .4f) / big;
            // the core segment: the cloud's extent along the axis, shortened at each end by part of the end radius so the caps round it
            float len = smax - smin;
            float r0 = EndRadius(pts, centroid, axis, smin, len), r1 = EndRadius(pts, centroid, axis, smax, len);
            float c0 = Mathf.Min(.7f * r0, .4f * len), c1 = Mathf.Min(.7f * r1, .4f * len);
            c.axis = axis; c.a = centroid + axis * (smin + c0); c.length = Mathf.Max(1e-4f, len - c0 - c1);
            c.K = finger ? 2 : Mathf.Clamp(Mathf.CeilToInt(c.length / .02f), 3, 16);
            c.Rows = 2 * c.J + c.K + 1;
            // triangles skinned to this bone (every corner follows it)
            var tris = new List<(Vector3, Vector3, Vector3, bool)>(meshTris.Count);
            foreach (var (s, f) in meshTris)
                tris.Add((bind.MultiplyPoint3x4(s.v[s.t[f]]), bind.MultiplyPoint3x4(s.v[s.t[f + 1]]), bind.MultiplyPoint3x4(s.v[s.t[f + 2]]), s.garment));
            float reach = 0; foreach (var p in pts) reach = Mathf.Max(reach, DistToSegment(c, p));
            float maxRay = reach * 2.2f + .02f;
            // bin triangles by node cell
            int cells = c.Rows * c.M; var bins = new List<int>[cells]; for (int i = 0; i < cells; i++) bins[i] = new List<int>(8);
            for (int f = 0; f < tris.Count; f++)
            {
                var (p0, p1, p2, _) = tris[f];
                float rlo = float.MaxValue, rhi = float.MinValue; var th = new float[4];
                int k = 0;
                foreach (var p in new[] { p0, p1, p2, (p0 + p1 + p2) / 3 })
                {
                    Param(c, p, out float row, out float col, out _);
                    rlo = Mathf.Min(rlo, row); rhi = Mathf.Max(rhi, row); th[k++] = col;
                }
                // angular span with wrap-around
                Array.Sort(th); float gap = th[0] + c.M - th[3]; int gi = 3;
                for (int q = 0; q < 3; q++) if (th[q + 1] - th[q] > gap) { gap = th[q + 1] - th[q]; gi = q; }
                float clo = th[(gi + 1) % 4], chi = gi == 3 ? th[3] : th[gi] + c.M;
                bool pole = rlo < 1.01f || rhi > c.Rows - 2.01f;   // near a cap pole every column meets
                if (pole || chi - clo > c.M * .5f) { clo = 0; chi = c.M; }
                for (int r = Mathf.Max(0, Mathf.FloorToInt(rlo)); r <= Mathf.Min(c.Rows - 1, Mathf.CeilToInt(rhi)); r++)
                    for (int q = Mathf.FloorToInt(clo); q <= Mathf.CeilToInt(chi); q++)
                        bins[r * c.M + ((q % c.M) + c.M) % c.M].Add(f);
            }
            c.R = new float[cells]; c.Rb = new float[cells]; c.offset = new float[cells];
            var okR = new bool[cells]; var okB = new bool[cells];
            for (int r = 0; r < c.Rows; r++)
                for (int q = 0; q < c.M; q++)
                {
                    Ray(c, r, q, out var o, out var dir);
                    float far = -1, farB = -1;
                    foreach (int f in bins[r * c.M + q])
                    {
                        var (p0, p1, p2, g) = tris[f];
                        float t = Hit(o, dir, p0, p1, p2, maxRay);
                        if (t <= 0) continue;
                        if (t > far) far = t;
                        if (!g && t > farB) farB = t;
                    }
                    int id = r * c.M + q;
                    if (farB > 0) { c.Rb[id] = farB; okB[id] = true; }
                    if (far > 0) { c.R[id] = far; okR[id] = true; }
                }
            Fill(c, c.Rb, okB);
            for (int i = 0; i < cells; i++) if (!okR[i] || c.R[i] < c.Rb[i]) { c.R[i] = Mathf.Max(c.R[i], c.Rb[i]); okR[i] = true; }
            for (int i = 0; i < cells; i++) { c.offset[i] = c.R[i] - c.Rb[i]; if (c.offset[i] > .0015f) c.garmentNodes++; }
            // bound
            c.midLocal = c.a + c.axis * (c.length * .5f);
            foreach (var x in c.R) c.maxR = Mathf.Max(c.maxR, x);
            c.rowMax = new float[c.Rows];
            for (int r = 0; r < c.Rows; r++)
                for (int rr = Mathf.Max(0, r - 1); rr <= Mathf.Min(c.Rows - 1, r + 1); rr++)
                    for (int q = 0; q < c.M; q++) c.rowMax[r] = Mathf.Max(c.rowMax[r], c.R[rr * c.M + q]);
            for (int r = 0; r < c.Rows; r++) for (int q = 0; q < c.M; q++) { Ray(c, r, q, out var o, out var dir); c.boundLocal = Mathf.Max(c.boundLocal, ((o + dir * c.R[r * c.M + q]) - c.midLocal).magnitude); }
            return c;
        }

        static float Sq(float x) => x * x;
        Transform ChildAlongChain(Transform bone, Part part)
        {
            HumanBodyBones? next = null;
            for (int i = 0; i < (int)HumanBodyBones.LastBone; i++) if (look.Bone((HumanBodyBones)i) == bone) { next = NextOf((HumanBodyBones)i); break; }
            if (next == null) return null;
            var t = look.Bone(next.Value);
            if (!t && next == HumanBodyBones.UpperChest) t = look.Bone(HumanBodyBones.Neck);
            return t;
        }
        static HumanBodyBones? NextOf(HumanBodyBones b)
        {
            switch (b)
            {
                case HumanBodyBones.Hips: return HumanBodyBones.Spine;
                case HumanBodyBones.Spine: return HumanBodyBones.Chest;
                case HumanBodyBones.Chest: return HumanBodyBones.UpperChest;
                case HumanBodyBones.UpperChest: return HumanBodyBones.Neck;
                case HumanBodyBones.Neck: return HumanBodyBones.Head;
                case HumanBodyBones.LeftShoulder: return HumanBodyBones.LeftUpperArm;
                case HumanBodyBones.RightShoulder: return HumanBodyBones.RightUpperArm;
                case HumanBodyBones.LeftUpperArm: return HumanBodyBones.LeftLowerArm;
                case HumanBodyBones.RightUpperArm: return HumanBodyBones.RightLowerArm;
                case HumanBodyBones.LeftLowerArm: return HumanBodyBones.LeftHand;
                case HumanBodyBones.RightLowerArm: return HumanBodyBones.RightHand;
                case HumanBodyBones.LeftHand: return HumanBodyBones.LeftMiddleProximal;
                case HumanBodyBones.RightHand: return HumanBodyBones.RightMiddleProximal;
                case HumanBodyBones.LeftUpperLeg: return HumanBodyBones.LeftLowerLeg;
                case HumanBodyBones.RightUpperLeg: return HumanBodyBones.RightLowerLeg;
                case HumanBodyBones.LeftLowerLeg: return HumanBodyBones.LeftFoot;
                case HumanBodyBones.RightLowerLeg: return HumanBodyBones.RightFoot;
                case HumanBodyBones.LeftFoot: return HumanBodyBones.LeftToes;
                case HumanBodyBones.RightFoot: return HumanBodyBones.RightToes;
            }
            if (b >= HumanBodyBones.LeftThumbProximal && b <= HumanBodyBones.RightLittleDistal)
            {
                int k = (b - HumanBodyBones.LeftThumbProximal) % 3;
                return k < 2 ? b + 1 : (HumanBodyBones?)null;
            }
            return null;
        }
        static Vector3 Principal(List<Vector3> pts, Vector3 c)
        {
            var v = new Vector3(.3f, .9f, .2f).normalized;
            for (int it = 0; it < 12; it++)
            {
                var w = Vector3.zero; foreach (var p in pts) { var d = p - c; w += d * Vector3.Dot(d, v); }
                if (w.sqrMagnitude < 1e-12f) break; v = w.normalized;
            }
            return v;
        }
        static float EndRadius(List<Vector3> pts, Vector3 c, Vector3 axis, float s, float len)
        {
            float band = Mathf.Max(.004f, len * .12f), sum = 0; int n = 0;
            foreach (var p in pts)
            {
                var d = p - c; float t = Vector3.Dot(d, axis);
                if (Mathf.Abs(t - s) > band) continue; sum += (d - axis * t).magnitude; n++;
            }
            return n > 0 ? sum / n : 0;
        }
        static float DistToSegment(Capsule c, Vector3 p)
        {
            float s = Mathf.Clamp(Vector3.Dot(p - c.a, c.axis), 0, c.length);
            return (p - (c.a + c.axis * s)).magnitude;
        }
        static void Fill(Capsule c, float[] R, bool[] ok)
        {
            // around each row first, then rows from their neighbours towards the poles
            var rowOk = new bool[c.Rows];
            for (int r = 0; r < c.Rows; r++)
            {
                int any = -1; for (int q = 0; q < c.M; q++) if (ok[r * c.M + q]) { any = q; break; }
                if (any < 0) continue; rowOk[r] = true;
                for (int q = 0; q < c.M; q++)
                {
                    if (ok[r * c.M + q]) continue;
                    int lo = q, hi = q, dl = 0, dh = 0;
                    while (!ok[r * c.M + lo]) { lo = (lo - 1 + c.M) % c.M; dl++; }
                    while (!ok[r * c.M + hi]) { hi = (hi + 1) % c.M; dh++; }
                    float t = dl / (float)(dl + dh);
                    R[r * c.M + q] = Mathf.Lerp(R[r * c.M + lo], R[r * c.M + hi], t);
                }
            }
            for (int pass = 0; pass < c.Rows; pass++)
                for (int r = 0; r < c.Rows; r++)
                {
                    if (rowOk[r]) continue;
                    int src = r > 0 && rowOk[r - 1] ? r - 1 : r + 1 < c.Rows && rowOk[r + 1] ? r + 1 : -1;
                    if (src < 0) continue;
                    // towards a pole the surface closes in: keep the neighbour's radius (conservative)
                    for (int q = 0; q < c.M; q++) R[r * c.M + q] = R[src * c.M + q];
                    rowOk[r] = true;
                }
            for (int i = 0; i < R.Length; i++) { if (!ok[i]) ok[i] = true; if (float.IsNaN(R[i])) R[i] = 0; }
        }
        static float Hit(Vector3 o, Vector3 d, Vector3 a, Vector3 b, Vector3 c, float len)
        {
            var e1 = b - a; var e2 = c - a; var h = Vector3.Cross(d, e2); float det = Vector3.Dot(e1, h);
            if (Mathf.Abs(det) < 1e-14f) return -1;
            float inv = 1 / det; var s = o - a; float u = Vector3.Dot(s, h) * inv; if (u < -1e-4f || u > 1.0001f) return -1;
            var q = Vector3.Cross(s, e1); float w = Vector3.Dot(d, q) * inv; if (w < -1e-4f || u + w > 1.0001f) return -1;
            float t = Vector3.Dot(e2, q) * inv; return t > 0 && t <= len ? t : -1;
        }

        // ---------------------------------------------------------------- the parameterisation
        /// Ray of node (row, column) in bone-local space.
        static void Ray(Capsule c, float row, float col, out Vector3 origin, out Vector3 dir)
        {
            float th = col / c.M * 2 * Mathf.PI;
            var perp = (c.e1 * (c.ea * Mathf.Cos(th)) + c.e2 * (c.eb * Mathf.Sin(th))).normalized;
            if (row <= c.J)
            {
                float phi = row / c.J * .5f * Mathf.PI; origin = c.a;
                dir = -c.axis * Mathf.Cos(phi) + perp * Mathf.Sin(phi);
            }
            else if (row >= c.J + c.K)
            {
                float phi = (c.Rows - 1 - row) / c.J * .5f * Mathf.PI; origin = c.a + c.axis * c.length;
                dir = c.axis * Mathf.Cos(phi) + perp * Mathf.Sin(phi);
            }
            else { origin = c.a + c.axis * ((row - c.J) / c.K * c.length); dir = perp; }
        }
        /// Point (bone-local) -> continuous (row, column) and its distance from the core along that ray. Returns the unit ray direction.
        static Vector3 Param(Capsule c, Vector3 p, out float row, out float col, out float dist)
        {
            var v = p - c.a; float s = Vector3.Dot(v, c.axis);
            Vector3 w;
            if (s < 0) w = v;
            else if (s > c.length) w = p - (c.a + c.axis * c.length);
            else w = v - c.axis * s;
            dist = w.magnitude;
            float x = Vector3.Dot(w, c.e1), y = Vector3.Dot(w, c.e2);
            float th = Atan2(y / c.eb, x / c.ea); if (th < 0) th += 2 * Mathf.PI;
            col = th / (2 * Mathf.PI) * c.M;
            if (s < 0)
            {
                float cos = dist > 1e-7f ? Mathf.Clamp(-s / dist, -1, 1) : 1;
                row = Mathf.Acos(cos) / (.5f * Mathf.PI) * c.J;
            }
            else if (s > c.length)
            {
                float cos = dist > 1e-7f ? Mathf.Clamp((s - c.length) / dist, -1, 1) : 1;
                row = c.Rows - 1 - Mathf.Acos(cos) / (.5f * Mathf.PI) * c.J;
            }
            else row = c.J + s / c.length * c.K;
            return dist > 1e-7f ? w / dist : c.e1;
        }
        static float Atan2(float y, float x)
        {
            // |error| < 0.005 rad; the tables are sampled every 11 degrees or more
            float ax = Mathf.Abs(x), ay = Mathf.Abs(y);
            float a = Mathf.Min(ax, ay) / (Mathf.Max(ax, ay) + 1e-20f); float s = a * a;
            float r = ((-0.0464964749f * s + 0.15931422f) * s - 0.327622764f) * s * a + a;
            if (ay > ax) r = 1.57079637f - r; if (x < 0) r = 3.14159274f - r; if (y < 0) r = -r;
            return r;
        }
        static float Lookup(Capsule c, float[] R, float row, float col)
        {
            row = Mathf.Clamp(row, 0, c.Rows - 1.0001f);
            int r0 = (int)row; float fr = row - r0;
            int q0 = (int)col; float fq = col - q0; q0 %= c.M; int q1 = (q0 + 1) % c.M;
            float a = R[r0 * c.M + q0] + (R[r0 * c.M + q1] - R[r0 * c.M + q0]) * fq;
            float b = R[(r0 + 1) * c.M + q0] + (R[(r0 + 1) * c.M + q1] - R[(r0 + 1) * c.M + q0]) * fq;
            return a + (b - a) * fr;
        }

        // ---------------------------------------------------------------- runtime
        public void Refresh()
        {
            foreach (var c in capsules)
            {
                if (c == null) continue;
                c.toWorld = c.bone.localToWorldMatrix; c.toLocal = c.bone.worldToLocalMatrix;
                c.midWorld = c.toWorld.MultiplyPoint3x4(c.midLocal);
                c.scale = c.toWorld.GetColumn(0).magnitude; c.bound = c.boundLocal * c.scale;
                c.aW = c.toWorld.MultiplyPoint3x4(c.a); c.bW = c.toWorld.MultiplyPoint3x4(c.a + c.axis * c.length);
            }
        }
        public void Refresh(Capsule c)
        {
            c.toWorld = c.bone.localToWorldMatrix; c.toLocal = c.bone.worldToLocalMatrix;
            c.midWorld = c.toWorld.MultiplyPoint3x4(c.midLocal); c.scale = c.toWorld.GetColumn(0).magnitude; c.bound = c.boundLocal * c.scale;
            c.aW = c.toWorld.MultiplyPoint3x4(c.a); c.bW = c.toWorld.MultiplyPoint3x4(c.a + c.axis * c.length);
        }
        /// Signed depth (m, > 0 inside) of a world point in one proxy, and the world direction that takes it out.
        /// Full table evaluations since start (profiling).
        public static int Lookups;
        public static float Depth(Capsule c, Vector3 world, bool garments, out Vector3 push)
        {
            // farther from the core segment than the largest radius: certainly outside (cheap, no table lookup)
            float abx = c.bW.x - c.aW.x, aby = c.bW.y - c.aW.y, abz = c.bW.z - c.aW.z, wx = world.x - c.aW.x, wy = world.y - c.aW.y, wz = world.z - c.aW.z;
            float ab2 = abx * abx + aby * aby + abz * abz, t = ab2 > 1e-12f ? (wx * abx + wy * aby + wz * abz) / ab2 : 0;
            if (t < 0) t = 0; else if (t > 1) t = 1;
            float dx = wx - abx * t, dy = wy - aby * t, dz = wz - abz * t, d2 = dx * dx + dy * dy + dz * dz, far = c.maxR * c.scale;
            if (d2 > far * far) { push = Vector3.zero; return far - Mathf.Sqrt(d2); }
            if (t > 0 && t < 1 && c.rowMax != null)
            {
                // along the core: the widest of the nearest table rows is the bound
                float tr = c.J + t * c.K; int r0 = (int)tr; float rm = Mathf.Max(c.rowMax[r0], c.rowMax[Mathf.Min(c.Rows - 1, r0 + 1)]) * c.scale;
                if (d2 > rm * rm) { push = Vector3.zero; return rm - Mathf.Sqrt(d2); }
            }
            Lookups++;
            var p = c.toLocal.MultiplyPoint3x4(world);
            var dir = Param(c, p, out float row, out float col, out float dist);
            float R = Lookup(c, garments ? c.R : c.Rb, row, col);
            push = c.toWorld.MultiplyVector(dir); float m = push.magnitude; if (m > 1e-9f) push /= m;
            return (R - dist) * c.scale;
        }
        /// The proxy's surface point along the same ray (world), for proofs and tests.
        public static Vector3 Surface(Capsule c, Vector3 world, bool garments)
        {
            var p = c.toLocal.MultiplyPoint3x4(world);
            var dir = Param(c, p, out float row, out float col, out float dist);
            float R = Lookup(c, garments ? c.R : c.Rb, row, col);
            return c.toWorld.MultiplyPoint3x4(p + dir * (R - dist));
        }
        /// Every node's surface point in world space (debug drawing / proof renders).
        public IEnumerable<Vector3> SurfacePoints(Capsule c, bool garments)
        {
            var R = garments ? c.R : c.Rb;
            for (int r = 0; r < c.Rows; r++) for (int q = 0; q < c.M; q++) { Ray(c, r, q, out var o, out var d); yield return c.toWorld.MultiplyPoint3x4(o + d * R[r * c.M + q]); }
        }
    }
}
