using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEngine;
using Object = UnityEngine.Object;

namespace GolfArcade.Tennis
{
    /// LIVE POLO (2026-11-18; 11-19 retuned for a SLIM athletic fit: small flutter, no swing-out): a small cloth simulation for the male tennis polo's hem and sleeves.
    /// ~200 particles are real polo vertices (skinned exactly on the CPU each frame). Each one carries a
    /// damped offset from its skinned rest position, driven by the rest point's own acceleration (the cloth
    /// lags, flares when the body turns, overshoots and settles), pulled a little toward hanging straight
    /// down under gravity, coupled to its neighbours so the fabric moves as one piece, and kept outside
    /// the thighs and upper arms. TennisCloth adds the blended offsets per vertex (UV5 = 4 particle ids,
    /// UV6 = 4 weights from work/polo-shape-1118/build_cage.py). Off: POLO_CLOTH=0, or the global
    /// _ClothJiggleGlobal = 0 (the A/B film tool).
    [DefaultExecutionOrder(32000)]
    public sealed class PoloCloth : MonoBehaviour
    {
        public static bool Enabled => Environment.GetEnvironmentVariable("POLO_CLOTH") != "0";
        static readonly int CageId = Shader.PropertyToID("_Cage"), CageOnId = Shader.PropertyToID("_CageOn");
        static readonly int GlobalId = Shader.PropertyToID("_ClothJiggleGlobal");
        static float Env(string key, float fallback) =>
            float.TryParse(Environment.GetEnvironmentVariable(key), System.Globalization.NumberStyles.Float,
                System.Globalization.CultureInfo.InvariantCulture, out var v) ? v : fallback;

        // Tuning (env overrides for capture runs).
        public float hemHz = Env("POLO_HEM_HZ", 3.0f), sleeveHz = Env("POLO_SLEEVE_HZ", 4.0f), rootHz = 7f;
        public float zeta = Env("POLO_ZETA", .35f), gain = Env("POLO_GAIN", .55f), hang = Env("POLO_HANG", 0f);
        public float drag = Env("POLO_DRAG", .002f), hemMax = Env("POLO_HEM_MAX", .016f), sleeveMax = Env("POLO_SLEEVE_MAX", .008f), sleeveGain = Env("POLO_SLEEVE_GAIN", .35f);
        public float coupling = .3f, deadZone = Env("POLO_DEADZONE", 2f);
        public Vector4 Debug;
        public Vector3[] Rest => rest; public int[] Vertex => vertex; public Vector3[] Offset => off;   // x: max hem offset (m), y: max sleeve offset, z: max rest acceleration, w: collisions

        SkinnedMeshRenderer skin; Material[] materials; Transform[] bones; Matrix4x4[] bindposes;
        int count; int[] vertex, up, group, column; bool[] pinned; float[] frac; int[][] neighbours; int[] anchor;
        Vector3[] bindPos, bindNrm; BoneWeight[] weights;
        Vector3[] rest, restN, prev, velF, velPrev, accF, off, vel, scratch;
        readonly Vector4[] upload = new Vector4[256];
        (Transform a, Transform b, float r, int group)[] capsules;
        readonly Dictionary<int, Matrix4x4> boneMatrix = new();
        int[] usedBones; bool started; float[,] bindDist;

        public static void Attach(MatchHeroLook look, List<Object> owned)
        {
            if (!Enabled || !look || look.female || look.golfKit || !string.IsNullOrEmpty(look.kitSport) || look.kit == null) return;
            var asset = Resources.Load<TextAsset>("Tennis/KitsV2/Male/PoloCloth");
            var renderer = look.kit.FirstOrDefault(k => k && k.name == "Kit_Top");
            if (!asset || !renderer || !renderer.sharedMesh) return;
            var cloth = look.gameObject.AddComponent<PoloCloth>();
            if (!cloth.Load(asset.bytes, renderer, owned, look.body)) { Object.Destroy(cloth); return; }
        }

        bool Load(byte[] bytes, SkinnedMeshRenderer renderer, List<Object> owned, SkinnedMeshRenderer body)
        {
            using var data = new BinaryReader(new MemoryStream(bytes));
            if (data.ReadInt32() != 0x50434C54 || data.ReadInt32() != 1) return false;
            int vertices = data.ReadInt32(); count = data.ReadInt32();
            var mesh = renderer.sharedMesh;
            if (!mesh.isReadable || mesh.vertexCount < vertices || count > 256)
            {
                UnityEngine.Debug.LogWarning($"[PoloCloth] {mesh.name}: {mesh.vertexCount} vertices, cage expects {vertices}; live cloth off.");
                return false;
            }
            vertex = new int[count]; up = new int[count]; group = new int[count]; pinned = new bool[count]; frac = new float[count]; neighbours = new int[count][];
            for (int i = 0; i < count; i++)
            {
                vertex[i] = data.ReadInt32(); pinned[i] = data.ReadInt32() != 0; group[i] = data.ReadInt32(); frac[i] = data.ReadSingle();
                var raw = new[] { data.ReadInt32(), data.ReadInt32(), data.ReadInt32(), data.ReadInt32() };
                up[i] = raw[2];   // grid order: left, right, up (toward the pinned row), down
                neighbours[i] = raw.Where(n => n >= 0).ToArray();
            }
            var map = renderer.bones.Where(b => b).GroupBy(b => b.name).ToDictionary(g => g.Key, g => g.First());
            var root = renderer.rootBone ? renderer.rootBone.root : renderer.transform.root;
            var all = root.GetComponentsInChildren<Transform>(true).GroupBy(t => t.name).ToDictionary(g => g.Key, g => g.First());
            int capsuleCount = data.ReadInt32(); var caps = new List<(Transform, Transform, float, int)>();
            for (int i = 0; i < capsuleCount; i++)
            {
                string a = Encoding(data), b = Encoding(data); float r = data.ReadSingle();
                if (all.TryGetValue(a, out var ta) && all.TryGetValue(b, out var tb))
                    caps.Add((ta, tb, r, a.Contains("Leg") ? 0 : a.StartsWith("Left") ? 1 : 2));
            }
            capsules = caps.ToArray();
            int bound = data.ReadInt32();
            var ids = new Vector4[mesh.vertexCount]; var ws = new Vector4[mesh.vertexCount];
            for (int i = 0; i < bound; i++)
            {
                int v = data.ReadInt32();
                var id = new Vector4(data.ReadByte(), data.ReadByte(), data.ReadByte(), data.ReadByte());
                var w = new Vector4(data.ReadSingle(), data.ReadSingle(), data.ReadSingle(), data.ReadSingle());
                if (v < vertices) { ids[v] = id; ws[v] = w; }
            }
            if (!owned.Contains(mesh)) { mesh = Instantiate(mesh); mesh.name += " (polo cloth)"; owned.Add(mesh); renderer.sharedMesh = mesh; }
            mesh.SetUVs(5, ids); mesh.SetUVs(6, ws);

            skin = renderer; bones = renderer.bones; bindposes = mesh.bindposes;
            bindPos = mesh.vertices; bindNrm = mesh.normals; weights = mesh.boneWeights;
            usedBones = vertex.SelectMany(v => new[] { weights[v].boneIndex0, weights[v].boneIndex1, weights[v].boneIndex2, weights[v].boneIndex3 }).Distinct().ToArray();
            // Each torso particle hangs from the pinned particle at the top of its column.
            // Rest-pose clearance of every particle from every capsule (body bind space == polo bind space):
            // a capsule may push cloth back out to this clearance, never further (no bloat at rest).
            bindDist = new float[count, capsules.Length];
            for (int c = 0; c < capsules.Length; c++)
            {
                Vector3 A = Vector3.zero, Bp = Vector3.zero; bool found = false;
                if (body && body.sharedMesh)
                {
                    int ia = Array.IndexOf(body.bones, capsules[c].a), ib = Array.IndexOf(body.bones, capsules[c].b);
                    var bp = body.sharedMesh.bindposes;
                    if (ia >= 0 && ib >= 0) { A = bp[ia].inverse.GetColumn(3); Bp = bp[ib].inverse.GetColumn(3); found = true; }
                }
                for (int i = 0; i < count; i++)
                {
                    if (!found) { bindDist[i, c] = 0; continue; }
                    var q = bindPos[vertex[i]]; var ab = Bp - A; float t = Mathf.Clamp01(Vector3.Dot(q - A, ab) / ab.sqrMagnitude);
                    bindDist[i, c] = (q - (A + ab * t)).magnitude;
                }
            }
            anchor = new int[count];
            for (int i = 0; i < count; i++)
            {
                int k = i;
                for (int guard = 0; guard < 16 && up[k] >= 0; guard++) k = up[k];
                anchor[i] = k;
            }
            rest = new Vector3[count]; restN = new Vector3[count]; prev = new Vector3[count]; velF = new Vector3[count];
            velPrev = new Vector3[count]; accF = new Vector3[count]; off = new Vector3[count]; vel = new Vector3[count]; scratch = new Vector3[count];
            materials = renderer.sharedMaterials.Where(m => m && m.HasProperty("_JigOn")).ToArray();
            foreach (var m in materials) { m.SetFloat("_JigOn", 0); m.SetFloat(CageOnId, 1); m.SetVectorArray(CageId, upload); }
            if (Environment.GetEnvironmentVariable("POLO_FINISH") != "0") foreach (var m in materials) ApplyFinish(m);
            Shader.SetGlobalFloat(GlobalId, 1);
            UnityEngine.Debug.Log($"[PoloCloth] {mesh.name}: {count} particles, {bound} bound vertices, {capsules.Length} capsules");
            return materials.Length > 0;
        }

        /// Matte cotton piqué read at gameplay distance (2026-11-19 sweep "k"): large knit cells with thread shade kept,
        /// a wider value range and less flat fill so the folds and the body's form read, a counter to the warm venue grade.
        static void ApplyFinish(Material m)
        {
            void Set(string k, float v) { if (m.HasProperty(k) || k == "_KnitShow") m.SetFloat(k, v); }
            Set("_WeaveTile", m.GetFloat("_WeaveTile") * .18f); Set("_KnitShow", 1); Set("_FabricDetail", 2f); Set("_WeaveThread", .5f);
            Set("_Exposure", .80f); Set("_StyleSat", .95f); Set("_StyleValueCap", .62f); Set("_StyleFill", .03f); Set("_StyleRamp", .22f);
            Set("_Wrap", .10f); Set("_AOStrength", .75f); Set("_NormalStrength", .9f); Set("_Mottle", .08f); Set("_StyleSheen", .05f);
            Set("_StyleCool", .35f); Set("_RimStrength", .05f);
            // Double-sided: looking up a sleeve or under the hem shows the shirt's inside, never the court through hidden skin.
            if (m.HasProperty("_Cull") && Environment.GetEnvironmentVariable("POLO_TWO_SIDED") != "0") m.SetFloat("_Cull", 0);
        }

        static string Encoding(BinaryReader data) => System.Text.Encoding.UTF8.GetString(data.ReadBytes(data.ReadInt32()));

        void Skin()
        {
            boneMatrix.Clear();
            foreach (int b in usedBones) if (b >= 0 && b < bones.Length && bones[b]) boneMatrix[b] = bones[b].localToWorldMatrix * bindposes[b];
            for (int i = 0; i < count; i++)
            {
                var w = weights[vertex[i]]; var p = bindPos[vertex[i]]; var n = bindNrm[vertex[i]];
                Vector3 sp = Vector3.zero, sn = Vector3.zero;
                void Add(int b, float k) { if (k <= 0 || !boneMatrix.TryGetValue(b, out var m)) return; sp += m.MultiplyPoint3x4(p) * k; sn += m.MultiplyVector(n) * k; }
                Add(w.boneIndex0, w.weight0); Add(w.boneIndex1, w.weight1); Add(w.boneIndex2, w.weight2); Add(w.boneIndex3, w.weight3);
                rest[i] = sp; restN[i] = sn.normalized;
            }
        }

        void LateUpdate()
        {
            if (!skin || materials == null) return;
            float dt = Mathf.Clamp(Time.deltaTime, 1f / 240, 1f / 20);
            Skin();
            if (!started)
            {
                for (int i = 0; i < count; i++) { prev[i] = rest[i]; velF[i] = velPrev[i] = accF[i] = off[i] = vel[i] = Vector3.zero; }
                started = true; return;
            }
            float lp = 1 - Mathf.Exp(-dt / .05f), maxAcc = 0, hemPeak = 0, sleevePeak = 0; int hits = 0;
            for (int i = 0; i < count; i++)
                if ((rest[i] - prev[i]).sqrMagnitude > .25f * .25f) { started = false; return; }   // teleport / respawn
            for (int i = 0; i < count; i++)
            {
                var v = (rest[i] - prev[i]) / dt; prev[i] = rest[i];
                velF[i] = Vector3.Lerp(velF[i], v, lp);
                accF[i] = Vector3.Lerp(accF[i], (velF[i] - velPrev[i]) / dt, lp);
                velPrev[i] = velF[i];
                if (pinned[i]) { off[i] = vel[i] = Vector3.zero; continue; }
                var acc = Vector3.ClampMagnitude(accF[i], 60f); float am = acc.magnitude;
                acc = am > deadZone ? acc * ((am - deadZone) / am) : Vector3.zero;
                maxAcc = Mathf.Max(maxAcc, am);
                bool torso = group[i] == 0; float f = frac[i];
                float hz = Mathf.Lerp(rootHz, torso ? hemHz : sleeveHz, f), w = 2 * Mathf.PI * hz, k = w * w, c = 2 * zeta * w;
                // Target: trail behind steady motion (air drag), and on the torso hang a little toward plumb.
                var target = Vector3.ClampMagnitude(-velF[i] * drag * f, .03f);
                if (torso && anchor[i] != i)
                {
                    var a = rest[anchor[i]]; var d = rest[i] - a; float len = d.magnitude;
                    if (len > 1e-4f) target += (a + Vector3.Slerp(d / len, Vector3.down, hang * f) * len) - rest[i];
                }
                float g = (torso ? gain : sleeveGain) * Mathf.Pow(f, .7f), h = dt / 4;
                for (int s = 0; s < 4; s++)
                {
                    var force = -k * (off[i] - target) - c * vel[i] - acc * g;
                    vel[i] += force * h; off[i] += vel[i] * h;
                }
            }
            // Fabric coupling: neighbours share their motion.
            for (int i = 0; i < count; i++)
            {
                if (pinned[i] || neighbours[i].Length == 0) { scratch[i] = off[i]; continue; }
                var mean = Vector3.zero; foreach (int n in neighbours[i]) mean += off[n];
                scratch[i] = Vector3.Lerp(off[i], mean / neighbours[i].Length, coupling);
            }
            for (int i = 0; i < count; i++) off[i] = scratch[i];
            // Collisions and limits.
            for (int i = 0; i < count; i++)
            {
                if (pinned[i]) continue;
                bool torso = group[i] == 0;
                var p = rest[i] + Vector3.ClampMagnitude(off[i], torso ? hemMax * frac[i] : sleeveMax * frac[i]);
                bool collided = false;
                for (int c = 0; c < capsules.Length; c++)
                {
                    var cap = capsules[c];
                    if (torso ? cap.group != 0 : cap.group != group[i]) continue;
                    var a = cap.a.position; var ab = cap.b.position - a; float t = Mathf.Clamp01(Vector3.Dot(p - a, ab) / ab.sqrMagnitude);
                    var axis = a + ab * t; var d = p - axis; float dist = d.magnitude;
                    float r = Mathf.Min(cap.r, bindDist[i, c] - .002f);
                    if (dist < r && dist > 1e-5f)
                    {
                        var nrm = d / dist; p = axis + nrm * r; hits++; collided = true;
                        float vn = Vector3.Dot(vel[i], nrm); if (vn < 0) vel[i] -= nrm * vn;
                    }
                }
                var o = p - rest[i];
                float inward = Vector3.Dot(o, restN[i]);
                if (inward < -.006f) o -= restN[i] * (inward + .006f);
                // The flutter is capped small (slim fit), but a thigh or arm may always push the cloth out of the way.
                o = Vector3.ClampMagnitude(o, Mathf.Max(torso ? hemMax * frac[i] : sleeveMax * frac[i], collided ? .07f : 0));
                off[i] = o;
                if (torso) hemPeak = Mathf.Max(hemPeak, o.magnitude); else sleevePeak = Mathf.Max(sleevePeak, o.magnitude);
            }
            Debug = new Vector4(hemPeak, sleevePeak, maxAcc, hits);
            for (int i = 0; i < count; i++) upload[i] = off[i];
            foreach (var m in materials) m.SetVectorArray(CageId, upload);
        }
    }
}
