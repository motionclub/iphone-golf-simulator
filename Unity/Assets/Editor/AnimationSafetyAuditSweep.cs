using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text;
using GolfArcade.Game;
using GolfArcade.Tennis;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Playables;
using Object = UnityEngine.Object;

namespace GolfArcade.EditorTools
{
    /// HAND CLEARANCE sweep (work/hand-clearance): ONE command over every clip x hero x kit at 60 Hz.
    ///   Unity -batchmode -projectPath <clone> -executeMethod GolfArcade.EditorTools.AnimationSafetyAudit.Sweep
    /// Each frame is posed three times through the game's own pipeline (tennis driver tweaks / golf swing clearance and
    /// grip, garment correctives): RAW (no clearance), BEFORE (the 2026-10-15 HeroPoseSafety, LegacyHeroPoseSafety) and
    /// AFTER (HeroPoseSafety = HeroClearance). BEFORE and AFTER are measured on the real meshes, not on the proxy:
    ///   BODY   hand / finger / forearm skin and the held prop inside the FULL body (covered skin included), own arm excluded, mm
    ///   CLOTH  the same points behind a garment's OUTER surface (own sleeve / glove excluded), mm, per garment
    ///   PART   which body part / garment is entered
    /// plus per clip: racket/club drift at contact, elbow/shoulder angular-velocity spikes and elbow flips against RAW, and the
    /// solver's cost per call. Writes <out>/sweep.csv (one row per frame and mode), <out>/clips.json, <out>/summary.json and
    /// renders of each context's worst frames (BEFORE vs AFTER, same camera).
    /// Env: SWEEP_OUT, SWEEP_CONTEXTS (tennis_male,tennis_female,golf_male,golf_female), SWEEP_CLIPS (substrings),
    ///      SWEEP_HZ (60), SWEEP_WORST (20 per context), SWEEP_RENDER (1), SWEEP_GROW (m: push Kit_Top outward, the NEW_GARMENT gate),
    ///      SWEEP_MODES (raw,before,after), SWEEP_FREE (1: also the empty-handed plaza set on each kit)
    [InitializeOnLoad]
    public static partial class AnimationSafetyAudit
    {
        const string SweepFlag = "AnimationSafetyAuditSweep";
        static IEnumerator sweep; static int sweepFrame = -1;
        static AnimationSafetyAudit() { EditorApplication.update += SweepTick; }
        static string Env(string k, string d) { var v = Environment.GetEnvironmentVariable(k); return string.IsNullOrEmpty(v) ? d : v; }
        static string F(float x) => x.ToString("0.###", CultureInfo.InvariantCulture);

        public static void Sweep()
        {
            EditorUtility.audioMasterMute = true;   // every run muted (Adnan, 10-17)
            sweep = null; sweepFrame = -1;
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            SessionState.SetBool(SweepFlag, true); EditorApplication.isPlaying = true;
        }
        static void SweepTick()
        {
            if (!SessionState.GetBool(SweepFlag, false) || !EditorApplication.isPlaying || sweepFrame == Time.frameCount) return;
            EditorUtility.audioMasterMute = true; AudioListener.volume = 0;
            sweepFrame = Time.frameCount;
            if (sweep == null) sweep = SweepMain();
            try { if (!sweep.MoveNext()) SweepDone(0); } catch (Exception e) { Debug.LogException(e); SweepDone(1); }
        }
        static void SweepDone(int code) { SessionState.SetBool(SweepFlag, false); if (Application.isBatchMode) EditorApplication.Exit(code); else EditorApplication.isPlaying = false; }

        // ================================================================ a uniform grid of triangles (rebuilt per frame on the region the hands are in)
        sealed class TriGrid
        {
            // a flat grid over the region the hands are in, filled by counting sort: no allocation per frame
            readonly float cell; public Vector3[] v; public int[] t;
            Vector3 origin; int nx, ny, nz; int[] start = new int[0], items = new int[0], cnt = new int[0];
            int[] tx0 = new int[0], tx1 = new int[0];   // per kept triangle: packed min / max cell
            public TriGrid(float cell) { this.cell = cell; }
            public void Build(Vector3[] verts, int[] tris, Bounds region, Func<int, bool> keep)
            {
                v = verts; t = tris; origin = region.min;
                nx = Mathf.Max(1, Mathf.CeilToInt(region.size.x / cell) + 1); ny = Mathf.Max(1, Mathf.CeilToInt(region.size.y / cell) + 1); nz = Mathf.Max(1, Mathf.CeilToInt(region.size.z / cell) + 1);
                int cells = nx * ny * nz, nt = tris.Length / 3;
                if (cnt.Length < cells + 1) { cnt = new int[cells + 1]; start = new int[cells + 1]; } else Array.Clear(cnt, 0, cells + 1);
                if (tx0.Length < nt) { tx0 = new int[nt]; tx1 = new int[nt]; }
                var mn0 = region.min; var mx0 = region.max; int total = 0;
                for (int i = 0; i < nt; i++)
                {
                    tx0[i] = -1;
                    if (keep != null && !keep(i)) continue;
                    Vector3 a = v[t[i * 3]], b = v[t[i * 3 + 1]], c = v[t[i * 3 + 2]];
                    float mnx = Mathf.Min(a.x, Mathf.Min(b.x, c.x)), mny = Mathf.Min(a.y, Mathf.Min(b.y, c.y)), mnz = Mathf.Min(a.z, Mathf.Min(b.z, c.z));
                    float mxx = Mathf.Max(a.x, Mathf.Max(b.x, c.x)), mxy = Mathf.Max(a.y, Mathf.Max(b.y, c.y)), mxz = Mathf.Max(a.z, Mathf.Max(b.z, c.z));
                    if (mxx < mn0.x || mxy < mn0.y || mxz < mn0.z || mnx > mx0.x || mny > mx0.y || mnz > mx0.z) continue;
                    int x0 = Cl((mnx - origin.x) / cell, nx), y0 = Cl((mny - origin.y) / cell, ny), z0 = Cl((mnz - origin.z) / cell, nz);
                    int x1 = Cl((mxx - origin.x) / cell, nx), y1 = Cl((mxy - origin.y) / cell, ny), z1 = Cl((mxz - origin.z) / cell, nz);
                    tx0[i] = (x0 << 20) | (y0 << 10) | z0; tx1[i] = (x1 << 20) | (y1 << 10) | z1;
                    for (int x = x0; x <= x1; x++) for (int y = y0; y <= y1; y++) for (int z = z0; z <= z1; z++) { cnt[(x * ny + y) * nz + z]++; total++; }
                }
                int run = 0; for (int k = 0; k < cells; k++) { start[k] = run; run += cnt[k]; cnt[k] = 0; } start[cells] = run;
                if (items.Length < total) items = new int[total + total / 4];
                for (int i = 0; i < nt; i++)
                {
                    if (tx0[i] < 0) continue;
                    int x0 = tx0[i] >> 20, y0 = (tx0[i] >> 10) & 1023, z0 = tx0[i] & 1023, x1 = tx1[i] >> 20, y1 = (tx1[i] >> 10) & 1023, z1 = tx1[i] & 1023;
                    for (int x = x0; x <= x1; x++) for (int y = y0; y <= y1; y++) for (int z = z0; z <= z1; z++) { int k = (x * ny + y) * nz + z; items[start[k] + cnt[k]++] = i; }
                }
            }
            static int Cl(float f, int n) { int i = (int)Mathf.Floor(f); return i < 0 ? 0 : i >= n ? n - 1 : i; }
            [ThreadStatic] static int stamp; [ThreadStatic] static int[] seen;   // per thread: the queries run in parallel
            /// nearest triangle within r that `skip` does not reject: index or -1
            public int Nearest(Vector3 p, float r, bool[] skip, out Vector3 q, out Vector3 bary)
            {
                if (seen == null || seen.Length < t.Length / 3) { seen = new int[Math.Max(t.Length / 3, 300000)]; stamp = 0; }
                stamp++; int best = -1; float bd = r * r; q = default; bary = default;
                int x0 = Cl((p.x - r - origin.x) / cell, nx), y0 = Cl((p.y - r - origin.y) / cell, ny), z0 = Cl((p.z - r - origin.z) / cell, nz);
                int x1 = Cl((p.x + r - origin.x) / cell, nx), y1 = Cl((p.y + r - origin.y) / cell, ny), z1 = Cl((p.z + r - origin.z) / cell, nz);
                for (int x = x0; x <= x1; x++) for (int y = y0; y <= y1; y++) for (int z = z0; z <= z1; z++)
                        {
                            int k = (x * ny + y) * nz + z;
                            for (int j = start[k], e = start[k + 1]; j < e; j++)
                            {
                                int i = items[j];
                                if (seen[i] == stamp) continue; seen[i] = stamp;
                                if (skip != null && skip[i]) continue;
                                var c = Closest(p, v[t[i * 3]], v[t[i * 3 + 1]], v[t[i * 3 + 2]], out var bc);
                                float d = (c - p).sqrMagnitude; if (d < bd) { bd = d; best = i; q = c; bary = bc; }
                            }
                        }
                return best;
            }
            /// first hit of the segment p -> p + d * len (d unit) with a triangle `skip` does not reject: distance or -1
            public float Ray(Vector3 p, Vector3 d, float len, bool[] skip, out int tri)
            {
                tri = -1; if (seen == null || seen.Length < t.Length / 3) { seen = new int[Math.Max(t.Length / 3, 300000)]; stamp = 0; }
                stamp++; float best = -1; var e = p + d * len;
                int x0 = Cl((Mathf.Min(p.x, e.x) - origin.x) / cell, nx), y0 = Cl((Mathf.Min(p.y, e.y) - origin.y) / cell, ny), z0 = Cl((Mathf.Min(p.z, e.z) - origin.z) / cell, nz);
                int x1 = Cl((Mathf.Max(p.x, e.x) - origin.x) / cell, nx), y1 = Cl((Mathf.Max(p.y, e.y) - origin.y) / cell, ny), z1 = Cl((Mathf.Max(p.z, e.z) - origin.z) / cell, nz);
                for (int x = x0; x <= x1; x++) for (int y = y0; y <= y1; y++) for (int z = z0; z <= z1; z++)
                        {
                            int k = (x * ny + y) * nz + z;
                            for (int j = start[k], end = start[k + 1]; j < end; j++)
                            {
                                int i = items[j]; if (seen[i] == stamp) continue; seen[i] = stamp;
                                if (skip != null && skip[i]) continue;
                                Vector3 a = v[t[i * 3]], b = v[t[i * 3 + 1]], c = v[t[i * 3 + 2]];
                                var e1 = b - a; var e2 = c - a; var h = Vector3.Cross(d, e2); float det = Vector3.Dot(e1, h);
                                if (Mathf.Abs(det) < 1e-14f) continue;
                                float inv = 1 / det; var sv = p - a; float u = Vector3.Dot(sv, h) * inv; if (u < 0 || u > 1) continue;
                                var q = Vector3.Cross(sv, e1); float w = Vector3.Dot(d, q) * inv; if (w < 0 || u + w > 1) continue;
                                float tt = Vector3.Dot(e2, q) * inv; if (tt > 0 && tt <= len && (best < 0 || tt < best)) { best = tt; tri = i; }
                            }
                        }
                return best;
            }
            static Vector3 Closest(Vector3 p, Vector3 a, Vector3 b, Vector3 c, out Vector3 bc)
            {
                var ab = b - a; var ac = c - a; var ap = p - a; float d1 = Vector3.Dot(ab, ap), d2 = Vector3.Dot(ac, ap);
                if (d1 <= 0 && d2 <= 0) { bc = new Vector3(1, 0, 0); return a; }
                var bp = p - b; float d3 = Vector3.Dot(ab, bp), d4 = Vector3.Dot(ac, bp);
                if (d3 >= 0 && d4 <= d3) { bc = new Vector3(0, 1, 0); return b; }
                float vc = d1 * d4 - d3 * d2; if (vc <= 0 && d1 >= 0 && d3 <= 0) { float vv = d1 / (d1 - d3); bc = new Vector3(1 - vv, vv, 0); return a + vv * ab; }
                var cp = p - c; float d5 = Vector3.Dot(ab, cp), d6 = Vector3.Dot(ac, cp);
                if (d6 >= 0 && d5 <= d6) { bc = new Vector3(0, 0, 1); return c; }
                float vb = d5 * d2 - d1 * d6; if (vb <= 0 && d2 >= 0 && d6 <= 0) { float ww = d2 / (d2 - d6); bc = new Vector3(1 - ww, 0, ww); return a + ww * ac; }
                float va = d3 * d6 - d5 * d4; if (va <= 0 && (d4 - d3) >= 0 && (d5 - d6) >= 0) { float ww = (d4 - d3) / ((d4 - d3) + (d5 - d6)); bc = new Vector3(0, 1 - ww, ww); return b + ww * (c - b); }
                float den = 1 / (va + vb + vc); float v2 = vb * den, w2 = vc * den; bc = new Vector3(1 - v2 - w2, v2, w2); return a + ab * v2 + ac * w2;
            }
        }

        // ================================================================ ground truth on the real meshes
        sealed class Garment { public float[] restOff; public SkinnedMeshRenderer r; public Mesh bake = new Mesh(); public int[] tris; public bool[] outer; public bool[][] skip, skipGrip; public bool[] skipHandle; public string name; public Vector3[] v, n; }
        public struct Hit { public float depth; public string where; public Vector3 p, normal, q; public int tri; public bool cloth; }
        public sealed class FrameTruth
        {
            public Hit[] body = new Hit[4], cloth = new Hit[4];   // L hand, R hand, L forearm, R forearm
            public Hit propBody, propCloth;
            public float Worst => Mathf.Max(MaxBody, MaxCloth);
            public float MaxBody => Mathf.Max(body.Max(h => h.depth), propBody.depth);
            public float MaxCloth => Mathf.Max(cloth.Max(h => h.depth), propCloth.depth);
            public Hit WorstHit()
            {
                Hit w = default;
                foreach (var h in body.Concat(cloth).Append(propBody).Append(propCloth)) if (h.depth > w.depth) w = h;
                return w;
            }
        }
        sealed class Truth
        {
            public MatchHeroLook look; public SkinnedMeshRenderer body; public Mesh bake = new Mesh(); public int[] fullTris; public Vector3[] bv, bn;
            public int[] vDom; public HeroClearanceProxy.Part[] partOf; public int[] sideOf; public string[] nameOf;
            public int[][] pts = new int[4][];   // hand L, hand R, fore L, fore R (body vertex ids)
            public bool[][] skipBody = new bool[2][]; public bool[] skipBodyHandle;
            public bool[][] skipBodyGrip = new bool[2][];   // hands in a two-hand grip interlock by design: own arm + the other hand   // per side: own arm; handle: both hands + forearms
            public List<Garment> garments = new List<Garment>();
            public TriGrid bodyGrid = new TriGrid(.02f); public TriGrid clothGrid = new TriGrid(.02f);
            public Vector3[] clothV, clothN; public int[] clothT, clothTriG; public float[] clothOff; public bool[][] clothSkip, clothSkipGrip; public bool[] clothSkipHandle;
        }

        static Truth PrepareTruth(MatchHeroLook look, HeroClearance clr)
        {
            var T = new Truth { look = look, body = look.body };
            var mesh = look.body.sharedMesh; var full = HeroClearanceProxy.FullBody(look, mesh);
            T.fullTris = full.triangles;
            var src = clr.proxy.sources[0]; int nv = mesh.vertexCount;
            T.vDom = src.dominant; T.partOf = new HeroClearanceProxy.Part[nv]; T.sideOf = new int[nv]; T.nameOf = new string[clr.proxy.capsules.Count];
            for (int i = 0; i < clr.proxy.capsules.Count; i++) T.nameOf[i] = clr.proxy.nameAt[i];
            var px = clr.proxy;
            bool Arm(int v, int side) => px.IsArm(T.vDom[v], side);
            bool Kind(int v, int side, bool hand)
            {
                int d = T.vDom[v]; if (d < 0 || px.sideAt[d] != side) return false;
                return hand ? px.partAt[d] == HeroClearanceProxy.Part.Hand || px.partAt[d] == HeroClearanceProxy.Part.Finger : px.partAt[d] == HeroClearanceProxy.Part.Forearm;
            }
            // test points: one body vertex per 8 mm (hands) / 10 mm (forearms) voxel, rest pose (penetrations are wider than that)
            var bindV = src.v;
            for (int k = 0; k < 4; k++)
            {
                int side = k % 2 == 0 ? -1 : 1; bool hand = k < 2; float vox = hand ? .008f : .010f;
                var seen = new HashSet<long>(); var list = new List<int>();
                for (int i = 0; i < nv; i++)
                {
                    if (!Kind(i, side, hand)) continue;
                    var p = bindV[i]; long key = ((long)Mathf.FloorToInt(p.x / vox) + 100000) * 400000L * 400000L + ((long)Mathf.FloorToInt(p.y / vox) + 100000) * 400000L + (Mathf.FloorToInt(p.z / vox) + 100000);
                    if (seen.Add(key)) list.Add(i);
                }
                T.pts[k] = list.ToArray();
            }
            int nt = T.fullTris.Length / 3;
            for (int s = 0; s < 2; s++)
            {
                int side = s == 0 ? -1 : 1; var skip = new bool[nt];
                for (int f = 0; f < nt; f++) skip[f] = Arm(T.fullTris[f * 3], side) || Arm(T.fullTris[f * 3 + 1], side) || Arm(T.fullTris[f * 3 + 2], side);
                T.skipBody[s] = skip;
            }
            for (int s2 = 0; s2 < 2; s2++)
            {
                int side = s2 == 0 ? -1 : 1, other = -side; var skip = (bool[])T.skipBody[s2].Clone();
                for (int f = 0; f < nt; f++) if (!skip[f]) for (int e = 0; e < 3; e++) if (Kind(T.fullTris[f * 3 + e], other, true)) { skip[f] = true; break; }
                T.skipBodyGrip[s2] = skip;
            }
            T.skipBodyHandle = new bool[nt];
            for (int f = 0; f < nt; f++)
                for (int e = 0; e < 3; e++) { int v = T.fullTris[f * 3 + e]; if (Kind(v, -1, true) || Kind(v, 1, true) || Kind(v, -1, false) || Kind(v, 1, false)) T.skipBodyHandle[f] = true; }
            // garments: outer surface classified in the rest pose (vertex normal away from the nearest body skin)
            var bodyHash = new Dictionary<long, List<int>>(); const float hc = .03f;
            long HK(Vector3 p) => ((long)Mathf.FloorToInt(p.x / hc) + 1000) * 4000000L + ((long)Mathf.FloorToInt(p.y / hc) + 1000) * 2000L + (Mathf.FloorToInt(p.z / hc) + 1000);
            for (int i = 0; i < nv; i++) { long k = HK(bindV[i]); if (!bodyHash.TryGetValue(k, out var l)) bodyHash[k] = l = new List<int>(); l.Add(i); }
            foreach (var gs in clr.proxy.sources.Skip(1))
            {
                var r = look.GetComponentsInChildren<SkinnedMeshRenderer>(false).FirstOrDefault(x => x.name == gs.name && x.sharedMesh == gs.mesh);
                if (!r) continue;
                var g = new Garment { r = r, name = r.name, tris = gs.mesh.triangles };
                var rel = look.body.transform.worldToLocalMatrix * r.transform.localToWorldMatrix;
                var normals = gs.mesh.normals; var outerV = new bool[gs.v.Length]; g.restOff = new float[gs.v.Length];
                for (int i = 0; i < gs.v.Length; i++)
                {
                    var p = gs.v[i]; int best = -1; float bd = float.MaxValue;
                    for (int dx = -1; dx <= 1; dx++) for (int dy = -1; dy <= 1; dy++) for (int dz = -1; dz <= 1; dz++)
                            if (bodyHash.TryGetValue(HK(p + new Vector3(dx, dy, dz) * hc), out var l)) foreach (int j in l) { float d = (bindV[j] - p).sqrMagnitude; if (d < bd) { bd = d; best = j; } }
                    var n = i < normals.Length ? rel.MultiplyVector(normals[i]) : Vector3.zero;
                    outerV[i] = best < 0 || Vector3.Dot(n, p - bindV[best]) > 0;
                    g.restOff[i] = best < 0 ? .1f : Mathf.Sqrt(bd);
                }
                int gt = g.tris.Length / 3; g.outer = new bool[gt];
                for (int f = 0; f < gt; f++) g.outer[f] = (outerV[g.tris[f * 3]] ? 1 : 0) + (outerV[g.tris[f * 3 + 1]] ? 1 : 0) + (outerV[g.tris[f * 3 + 2]] ? 1 : 0) >= 2;
                g.skip = new bool[2][];
                for (int s = 0; s < 2; s++)
                {
                    int side = s == 0 ? -1 : 1; var skip = new bool[gt];
                    bool GArm(int v) => px.IsArm(gs.dominant[v], side);
                    for (int f = 0; f < gt; f++) skip[f] = !g.outer[f] || GArm(g.tris[f * 3]) || GArm(g.tris[f * 3 + 1]) || GArm(g.tris[f * 3 + 2]);
                    g.skip[s] = skip;
                }
                // in a two-hand grip the hands touch by design: the other hand's glove (any garment on that hand) is not "cloth" for this hand
                g.skipGrip = new bool[2][];
                for (int s = 0; s < 2; s++)
                {
                    int other = s == 0 ? 1 : -1; var skip = (bool[])g.skip[s].Clone();
                    for (int f = 0; f < gt && !g.r.name.StartsWith("Kit_"); f++)
                        for (int e = 0; e < 3; e++) { int d = gs.dominant[g.tris[f * 3 + e]]; if (d >= 0 && px.sideAt[d] == other && (px.partAt[d] == HeroClearanceProxy.Part.Hand || px.partAt[d] == HeroClearanceProxy.Part.Finger)) { skip[f] = true; break; } }
                    g.skipGrip[s] = skip;
                }
                g.skipHandle = new bool[gt];
                for (int f = 0; f < gt; f++)
                {
                    g.skipHandle[f] = !g.outer[f];
                    for (int e = 0; e < 3; e++) { int d = gs.dominant[g.tris[f * 3 + e]]; if (d >= 0 && (px.partAt[d] == HeroClearanceProxy.Part.Hand || px.partAt[d] == HeroClearanceProxy.Part.Finger || px.partAt[d] == HeroClearanceProxy.Part.Forearm)) g.skipHandle[f] = true; }
                }
                T.garments.Add(g);
            }
            // one combined cloth index
            int cv = 0, ct = 0; foreach (var g in T.garments) { cv += g.r.sharedMesh.vertexCount; ct += g.tris.Length; }
            T.clothV = new Vector3[cv]; T.clothN = new Vector3[cv]; T.clothT = new int[ct]; T.clothTriG = new int[ct / 3];
            T.clothSkip = new[] { new bool[ct / 3], new bool[ct / 3] }; T.clothSkipGrip = new[] { new bool[ct / 3], new bool[ct / 3] }; T.clothSkipHandle = new bool[ct / 3]; T.clothOff = new float[ct / 3];
            int vb = 0, tb = 0;
            for (int gi = 0; gi < T.garments.Count; gi++)
            {
                var g = T.garments[gi];
                for (int i = 0; i < g.tris.Length; i++) T.clothT[tb * 3 + i] = g.tris[i] + vb;
                for (int f = 0; f < g.tris.Length / 3; f++) { T.clothOff[tb + f] = Mathf.Max(g.restOff[g.tris[f * 3]], g.restOff[g.tris[f * 3 + 1]], g.restOff[g.tris[f * 3 + 2]]); T.clothTriG[tb + f] = gi; T.clothSkip[0][tb + f] = g.skip[0][f]; T.clothSkip[1][tb + f] = g.skip[1][f]; T.clothSkipGrip[0][tb + f] = g.skipGrip[0][f]; T.clothSkipGrip[1][tb + f] = g.skipGrip[1][f]; T.clothSkipHandle[tb + f] = g.skipHandle[f]; }
                vb += g.r.sharedMesh.vertexCount; tb += g.tris.Length / 3;
            }
            Debug.Log($"[Sweep] truth: body v{nv} tris {nt} pts hand {T.pts[0].Length}/{T.pts[1].Length} fore {T.pts[2].Length}/{T.pts[3].Length} garments " + string.Join(",", T.garments.Select(g => $"{g.name}:{g.outer.Count(x => x)}/{g.outer.Length} outer")));
            return T;
        }

        static void BakeWorld(SkinnedMeshRenderer r, Mesh m, ref Vector3[] v, ref Vector3[] n)
        {
            r.BakeMesh(m, true);
            var place = Matrix4x4.TRS(r.transform.position, r.transform.rotation, Vector3.one);
            v = m.vertices; n = m.normals;
            for (int i = 0; i < v.Length; i++) { v[i] = place.MultiplyPoint3x4(v[i]); if (i < n.Length) n[i] = place.MultiplyVector(n[i]).normalized; }
        }

        static readonly double[] prof = new double[6];   // bake, grid, arm queries, prop queries, pose, frames
        static FrameTruth MeasureTruth(Truth T, HeroClearance clr, List<(Vector3 p, bool handle)> prop)
        {
            var R = new FrameTruth(); var sw = System.Diagnostics.Stopwatch.StartNew();
            BakeWorld(T.body, T.bake, ref T.bv, ref T.bn);
            int vb = 0;
            foreach (var g in T.garments)
            {
                BakeWorld(g.r, g.bake, ref g.v, ref g.n);
                Array.Copy(g.v, 0, T.clothV, vb, g.v.Length); Array.Copy(g.n, 0, T.clothN, vb, Mathf.Min(g.n.Length, g.v.Length)); vb += g.v.Length;
            }
            var region = new Bounds(T.bv[T.pts[0].Length > 0 ? T.pts[0][0] : 0], Vector3.zero);
            for (int k = 0; k < 4; k++) foreach (int i in T.pts[k]) region.Encapsulate(T.bv[i]);
            foreach (var x in prop) region.Encapsulate(x.p);
            region.Expand(.13f);
            prof[0] += sw.Elapsed.TotalMilliseconds; sw.Restart();
            T.bodyGrid.Build(T.bv, T.fullTris, region, null);
            T.clothGrid.Build(T.clothV, T.clothT, region, null);
            prof[1] += sw.Elapsed.TotalMilliseconds; sw.Restart();
            Hit Test(Vector3 p, bool[] bodySkip, bool[] clothSkip, bool cloth)
            {
                var h = new Hit();
                var grid = cloth ? T.clothGrid : T.bodyGrid; var N = cloth ? T.clothN : T.bn; var tris = cloth ? T.clothT : T.fullTris; var skip = cloth ? clothSkip : bodySkip;
                int f = grid.Nearest(p, .012f, skip, out var q, out var bc);
                if (f < 0) f = grid.Nearest(p, .04f, skip, out q, out bc);   // depths are reported up to 40 mm
                if (f < 0) return h;
                // the face's own (geometric) normal: the skin's shading normals are smoothed over centimetres and lie at creases;
                // the vertex normals only orient it
                var V = cloth ? T.clothV : T.bv; Vector3 va = V[tris[f * 3]], vb2 = V[tris[f * 3 + 1]], vc = V[tris[f * 3 + 2]];
                var n = Vector3.Cross(vb2 - va, vc - va).normalized;
                if (Vector3.Dot(n, N[tris[f * 3]] + N[tris[f * 3 + 1]] + N[tris[f * 3 + 2]]) < 0) n = -n;
                var d = p - q; float s = Vector3.Dot(d, n), len = d.magnitude;
                // inside only when the point lies behind the face (not past an edge, where the sign means nothing)
                // under a garment = between its outer wall and the body: no deeper than that face stood off the skin at rest (+1 cm)
                if (s < 0 && (len < .0005f || -s >= .8f * len) && (!cloth || len <= T.clothOff[f] + .01f))
                {
                    h.depth = len; h.p = p; h.normal = n; h.q = q; h.tri = f; h.cloth = cloth;
                    if (cloth) h.where = T.garments[T.clothTriG[f]].name;
                    else { int dv = T.vDom[tris[f * 3]]; h.where = dv >= 0 ? T.nameOf[dv] : "?"; }
                }
                return h;
            }
            // Under a garment = the cloth lies between the point and the outside, along the skin's outward normal at the nearest
            // body point (a ray from the point outward meets the garment's outer wall). Pleats and flares do not fool it the way a
            // nearest-face sign does. Depth = how far out along that ray the cloth is (up to 40 mm).
            Hit Under(Vector3 p, bool[] bodySkip, bool[] clothSkip)
            {
                var h = new Hit();
                int f = T.bodyGrid.Nearest(p, .02f, bodySkip, out var q, out _);
                if (f < 0) f = T.bodyGrid.Nearest(p, .06f, bodySkip, out q, out _);
                if (f < 0) return h;
                Vector3 va = T.bv[T.fullTris[f * 3]], vb2 = T.bv[T.fullTris[f * 3 + 1]], vc = T.bv[T.fullTris[f * 3 + 2]];
                var n = Vector3.Cross(vb2 - va, vc - va).normalized;
                if (Vector3.Dot(n, T.bn[T.fullTris[f * 3]] + T.bn[T.fullTris[f * 3 + 1]] + T.bn[T.fullTris[f * 3 + 2]]) < 0) n = -n;
                var outDir = (p - q).sqrMagnitude > 1e-8f && Vector3.Dot(p - q, n) > 0 ? (p - q).normalized : n;
                float tHit = T.clothGrid.Ray(p, outDir, .04f, clothSkip, out int tri);
                if (tHit > 0) { h.depth = tHit; h.p = p; h.normal = outDir; h.q = p + outDir * tHit; h.tri = tri; h.cloth = true; h.where = T.garments[T.clothTriG[tri]].name; }
                return h;
            }
            clr.DetectGrip(); bool twoHand = clr.TwoHandGrip;
            for (int k = 0; k < 4; k++)
            {
                int s = k % 2; string who = (s == 0 ? "L" : "R") + (k < 2 ? "hand" : "fore");
                Hit wb = default, wc = default; var pts = T.pts[k]; object gate = new object();
                if (pts.Length > 0) System.Threading.Tasks.Parallel.ForEach(System.Collections.Concurrent.Partitioner.Create(0, pts.Length, 64), range =>
                {
                    Hit lb = default, lc = default;
                    for (int ii = range.Item1; ii < range.Item2; ii++)
                    {
                        var p = T.bv[pts[ii]];
                        var hb = Test(p, k < 2 && twoHand ? T.skipBodyGrip[s] : T.skipBody[s], null, false); if (hb.depth > lb.depth) lb = hb;
                        var hc = Under(p, T.skipBody[s], k < 2 && twoHand ? T.clothSkipGrip[s] : T.clothSkip[s]); if (hc.depth > lc.depth) lc = hc;
                    }
                    lock (gate) { if (lb.depth > wb.depth) wb = lb; if (lc.depth > wc.depth) wc = lc; }
                });
                if (wb.depth > 0) wb.where = who + ">" + wb.where; if (wc.depth > 0) wc.where = who + ">" + wc.where;
                R.body[k] = wb; R.cloth[k] = wc;
            }
            prof[2] += sw.Elapsed.TotalMilliseconds; sw.Restart();
            int holderSide = clr.HolderSide;
            object pgate = new object();
            if (prop.Count > 0) System.Threading.Tasks.Parallel.ForEach(System.Collections.Concurrent.Partitioner.Create(0, prop.Count, 32), range =>
            {
                Hit lb = default, lc = default;
                for (int pi = range.Item1; pi < range.Item2; pi++)
                {
                    var x = prop[pi];
                    // a second hand on the racket / club (two-hand grip, a cradle at the throat) is meant to touch it: both hands excluded
                    bool held2 = x.handle || clr.TwoHandGrip;
                    var bodySkip = held2 ? T.skipBodyHandle : T.skipBody[holderSide < 0 ? 0 : 1];
                    var clothSkip = held2 ? T.clothSkipHandle : T.clothSkip[holderSide < 0 ? 0 : 1];
                    var hb = Test(x.p, bodySkip, null, false); if (hb.depth > lb.depth) lb = hb;
                    var hc = Under(x.p, bodySkip, clothSkip); if (hc.depth > lc.depth) lc = hc;
                }
                lock (pgate)
                {
                    if (lb.depth > R.propBody.depth) { lb.where = "prop>" + lb.where; R.propBody = lb; }
                    if (lc.depth > R.propCloth.depth) { lc.where = "prop>" + lc.where; R.propCloth = lc; }
                }
            });
            prof[3] += sw.Elapsed.TotalMilliseconds;
            return R;
        }

        // ================================================================ contexts, clips and the game's pipelines
        sealed class Ctx
        {
            public string name; public bool golf, female; public GameObject root; public MatchHeroLook look; public HeroTennisDriver driver; public HeroGolfer golfer;
            public GolfSwingClearance golfClear; public LegacyHeroPoseSafety legacy; public HeroPoseSafety safety; public Truth truth;
            public MethodInfo openForehand, serveWrist; public List<(Transform t, string name)> clubs = new List<(Transform, string)>();
            public HeroClearanceTracks lib; public HeroClearanceTracks.Player player;   // bake-first (SWEEP_TRACKS=bake|use)
        }
        sealed class ClipJob
        {
            public string name; public AnimationClip clip; public HeroTennisDriver.Clip? id; public float contact = -1; public string club; public bool racket; public bool golfLocked; public float impact = -1;
            // one playable graph per clip: the bone bindings are built once (SampleAnimation rebuilds them on every call)
            public UnityEngine.Playables.PlayableGraph graph; public UnityEngine.Animations.AnimationClipPlayable play;
            public void Open(Animator animator)
            {
                if (graph.IsValid() || !animator || Env("SWEEP_GRAPH", "1") != "1") return;
                graph = UnityEngine.Playables.PlayableGraph.Create("Sweep " + name); graph.SetTimeUpdateMode(UnityEngine.Playables.DirectorUpdateMode.Manual);
                play = UnityEngine.Animations.AnimationClipPlayable.Create(graph, clip); play.SetApplyFootIK(false);
                var output = UnityEngine.Animations.AnimationPlayableOutput.Create(graph, "pose", animator); output.SetSourcePlayable(play);
            }
            public void Close() { if (graph.IsValid()) graph.Destroy(); }
        }

        static readonly Dictionary<string, string> GolfClub = new Dictionary<string, string> { { "Drive", "DRIVER" }, { "IronSwing", "IRON" }, { "HalfSwing", "IRON" }, { "Chip", "WEDGE" }, { "Putt", "PUTTER" } };
        static bool TennisStroke(HeroTennisDriver.Clip c) => (bool)typeof(HeroTennisDriver).GetMethod("IsStroke", BindingFlags.NonPublic | BindingFlags.Static).Invoke(null, new object[] { c });

        static Ctx MakeContext(string name)
        {
            var c = new Ctx { name = name, golf = name.StartsWith("golf"), female = name.EndsWith("female") };
            if (c.golf)
            {
                c.golfer = HeroGolfer.Build(null, new HeroLook { Female = c.female, Haircut = (int)HeroGolfer.Haircut.Bald, Skin = c.female ? new Color(.953f, .855f, .788f) : new Color(.949f, .816f, .686f), HairColor = new Color(.35f, .25f, .18f) });
                c.root = c.golfer.Root; c.golfClear = new GolfSwingClearance(c.golfer);
                foreach (var r in c.root.GetComponentsInChildren<Transform>(true)) if (r.name.StartsWith("CLUB_")) c.clubs.Add((r, r.name.Substring(5)));
            }
            else
            {
                var prefab = AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Resources/Tennis/Customization/Player" + (c.female ? "Female" : "Male") + ".prefab");
                c.root = Object.Instantiate(prefab); c.root.name = "Sweep " + prefab.name;
                c.driver = c.root.GetComponent<HeroTennisDriver>();
                if (c.driver) { c.driver.ResolvePerformanceClips(); c.driver.enabled = false; }
            }
            c.root.transform.SetPositionAndRotation(Vector3.zero, Quaternion.identity);
            c.look = c.root.GetComponent<MatchHeroLook>();
            // the animator only carries the sweep's own playable graph (the hero's controller is cleared on this copy)
            if (c.look.animator) { c.look.animator.runtimeAnimatorController = null; c.look.animator.enabled = true; }
            return c;
        }

        /// The kit as worn in this context, then the clearance (fitted on it) and the truth model.
        static void ArmContext(Ctx c, float grow)
        {
            if (grow > 0)
            {
                var top = c.look.kit.FirstOrDefault(k => k && k.name == "Kit_Top");
                if (top) { top.sharedMesh = Grown(top.sharedMesh, c.look, top, grow); Debug.Log($"[Sweep] NEW_GARMENT: {top.name} pushed out {grow * 1000:0} mm ({top.sharedMesh.name})"); }
            }
            c.legacy = new LegacyHeroPoseSafety(c.look);
            c.safety = new HeroPoseSafety(c.look);
            // the game fits on a worker thread; the tool waits for it (and so also checks that path)
            var wait = System.Diagnostics.Stopwatch.StartNew();
            while (!c.safety.clearance.Ready && wait.ElapsedMilliseconds < 60000) System.Threading.Thread.Sleep(5);
            if (!c.safety.clearance.Ready) throw new Exception("clearance proxy not ready after 60 s");
            Debug.Log($"[Sweep] background fit ready after {wait.ElapsedMilliseconds} ms (fit {c.safety.clearance.proxy.FitMs:0} ms)");
            c.safety.clearance.Diagnostics = Env("SWEEP_DIAG", "0") == "1"; c.safety.clearance.Trace = Env("SWEEP_TRACE", "0") == "1"; c.safety.clearance.TraceAll = Env("SWEEP_TRACE", "0") == "all"; if (c.safety.clearance.TraceAll) c.safety.clearance.Trace = true;
            c.truth = PrepareTruth(c.look, c.safety.clearance);
            // bake-first: AFTER = the baked correction track + the residual solve, as the game runs it
            string tm = TrackMode(c);
            if (tm == "bake") c.lib = new HeroClearanceTracks();
            else if (tm == "use") { c.lib = HeroClearanceTracks.For(c.female, c.look.golfKit); if (c.lib == null) Debug.LogWarning($"[Sweep] {c.name}: no baked tracks in Resources/HeroClearance"); }
            if (c.lib != null)
            {
                c.player = new HeroClearanceTracks.Player(HeroClearanceTracks.RootOf(c.look), c.lib); c.safety.clearance.Residual = true;
                var L = c.look; c.player.SetArms(L.Bone(HumanBodyBones.LeftUpperArm), L.Bone(HumanBodyBones.LeftLowerArm), L.Bone(HumanBodyBones.LeftHand), L.Bone(HumanBodyBones.RightUpperArm), L.Bone(HumanBodyBones.RightLowerArm), L.Bone(HumanBodyBones.RightHand));
            }
            if (c.driver)
            {
                var contact = (float[])typeof(HeroTennisDriver).GetField("contact", BindingFlags.NonPublic | BindingFlags.Instance).GetValue(c.driver);
                foreach (var s in c.driver.slots) if (s.clip) contact[(int)s.id] = s.contact;
                c.openForehand = typeof(HeroTennisDriver).GetMethod("ApplyOpenForehandClearance", BindingFlags.NonPublic | BindingFlags.Instance);
                c.serveWrist = typeof(HeroTennisDriver).GetMethod("ApplyServeWrist", BindingFlags.NonPublic | BindingFlags.Instance);
            }
            Debug.Log($"[Sweep] {c.name}: proxy {c.safety.VolumeCount} capsules fit {c.safety.clearance.proxy.FitMs:0} ms cached={c.safety.clearance.proxy.Cached} garments {c.safety.clearance.proxy.GarmentCount}: {c.safety.clearance.proxy.Report}");
        }

        /// A garment pushed `d` metres away from the body everywhere (both walls), for the NEW_GARMENT gate.
        static Mesh Grown(Mesh m, MatchHeroLook look, SkinnedMeshRenderer r, float d)
        {
            var g = Object.Instantiate(m); g.name = m.name + " grown" + (d * 1000).ToString("0") + "mm";
            var rel = look.body.transform.worldToLocalMatrix * r.transform.localToWorldMatrix; var inv = rel.inverse;
            var body = look.body.sharedMesh.vertices; var v = g.vertices; const float hc = .03f;
            var hash = new Dictionary<long, List<int>>();
            long HK(Vector3 p) => ((long)Mathf.FloorToInt(p.x / hc) + 1000) * 4000000L + ((long)Mathf.FloorToInt(p.y / hc) + 1000) * 2000L + (Mathf.FloorToInt(p.z / hc) + 1000);
            for (int i = 0; i < body.Length; i++) { long k = HK(body[i]); if (!hash.TryGetValue(k, out var l)) hash[k] = l = new List<int>(); l.Add(i); }
            for (int i = 0; i < v.Length; i++)
            {
                var p = rel.MultiplyPoint3x4(v[i]); int best = -1; float bd = float.MaxValue;
                for (int dx = -1; dx <= 1; dx++) for (int dy = -1; dy <= 1; dy++) for (int dz = -1; dz <= 1; dz++)
                        if (hash.TryGetValue(HK(p + new Vector3(dx, dy, dz) * hc), out var l)) foreach (int j in l) { float q = (body[j] - p).sqrMagnitude; if (q < bd) { bd = q; best = j; } }
                if (best < 0) continue;
                var dir = (p - body[best]); if (dir.sqrMagnitude < 1e-10f) continue;
                v[i] = inv.MultiplyPoint3x4(p + dir.normalized * d);
            }
            g.vertices = v; g.RecalculateBounds(); return g;
        }

        static List<ClipJob> Jobs(Ctx c)
        {
            var list = new List<ClipJob>();
            var free = Resources.LoadAll<AnimationClip>("HeroMoves/" + (c.female ? "Female" : "Male")).Where(x => !x.name.StartsWith("__preview__")).OrderBy(x => x.name);
            if (!c.golf)
                foreach (var g in c.driver.slots.Where(s => s.clip).GroupBy(s => s.clip))
                {
                    var s = g.First();
                    list.Add(new ClipJob { name = s.id + ":" + s.clip.name, clip = s.clip, id = s.id, contact = TennisStroke(s.id) ? s.contact : -1, racket = true });
                }
            else
                foreach (var clip in Resources.LoadAll<AnimationClip>(HeroGolfer.PathFor(c.female)).Where(x => !x.name.StartsWith("__preview__")).OrderBy(x => x.name))
                {
                    string club = GolfClub.TryGetValue(clip.name, out var cl) ? cl : null;
                    list.Add(new ClipJob { name = "golf:" + clip.name, clip = clip, club = club, golfLocked = club != null });
                }
            if (Env("SWEEP_FREE", "1") == "1") foreach (var clip in free) list.Add(new ClipJob { name = "free:" + clip.name, clip = clip });
            string filter = Env("SWEEP_CLIPS", "");
            if (filter.Length > 0) list = list.Where(j => filter.Split(',').Any(f => j.name.IndexOf(f, StringComparison.OrdinalIgnoreCase) >= 0)).ToList();
            return list;
        }

        static void Props(Ctx c, ClipJob j)
        {
            if (c.look.racketGrip) foreach (var r in c.look.racketGrip.GetComponentsInChildren<Renderer>(true)) r.enabled = j.racket;
            foreach (var (t, n) in c.clubs) t.gameObject.SetActive(j.club != null && n == j.club);
        }

        enum Mode { Raw, Before, After }
        static Action<Ctx, HeroClearance.Request> preSolve, postSolve;
        /// SWEEP_TRACKS=bake bakes every context, unless SWEEP_BAKE_ONLY lists some: the others then play their installed tracks
        /// ("use"), so one launch can re-bake a few contexts and gate-measure all of them.
        static string TrackMode(Ctx c)
        {
            string tm = Env("SWEEP_TRACKS", ""), only = Env("SWEEP_BAKE_ONLY", "");
            return tm == "bake" && only.Length > 0 && !only.Split(',').Contains(c.name) ? "use" : tm;
        }
        const float PopFloor = 60;   // deg/s
        static readonly System.Diagnostics.Stopwatch afterTimer = new System.Diagnostics.Stopwatch(); static double lastAfterMs;   // track + residual, as the game
        static float golfBakeFreedom;   // the track bake's hooks round the solve

        // ================================================================ bake-first: the correction track of one clip
        /// Pass 1: the solver plays the clip forward as the game would, recording each arm bone's local rotation before and after
        /// the solve. The difference is smoothed over time (zero phase, SWEEP_TRACK_SIGMA frames), so the correction has no
        /// onset pops and cannot change side between keys. Pass 2: the smoothed correction is applied, locked hands are put
        /// back exactly where the solver had them (contact unchanged), and the residual solve clears what smoothing re-opened.
        /// The track = pass 2's result relative to the game's pose; at runtime the same residual solve then has nothing left.
        static void BakeTrack(Ctx c, ClipJob j, float hz)
        {
            var look = c.look; var root = HeroClearanceTracks.RootOf(look);
            // 0-7 arms (clavicle, upper, lower, hand; L then R), 8-10 spine / chest / upper chest, 11-16 legs (upper, lower, foot; L then R)
            var ids = new[] { HumanBodyBones.LeftShoulder, HumanBodyBones.LeftUpperArm, HumanBodyBones.LeftLowerArm, HumanBodyBones.LeftHand,
                              HumanBodyBones.RightShoulder, HumanBodyBones.RightUpperArm, HumanBodyBones.RightLowerArm, HumanBodyBones.RightHand,
                              HumanBodyBones.Spine, HumanBodyBones.Chest, HumanBodyBones.UpperChest,
                              HumanBodyBones.LeftUpperLeg, HumanBodyBones.LeftLowerLeg, HumanBodyBones.LeftFoot, HumanBodyBones.RightUpperLeg, HumanBodyBones.RightLowerLeg, HumanBodyBones.RightFoot };
            var bones = ids.Select(look.Bone).ToArray(); int B = bones.Length;
            int n = Mathf.Max(1, Mathf.CeilToInt(j.clip.length * hz)), F = n + 1;
            var pre = new Quaternion[F, B]; var post = new Quaternion[F, B]; var pre2 = new Quaternion[F, B]; var post2 = new Quaternion[F, B];
            var handPos = new Vector3[F, 2]; var handRot = new Quaternion[F, 2]; var locked = new bool[F, 2]; var handPre = new Vector3[F, 2]; var handPost = new Vector3[F, 2];
            float sigma = float.Parse(Env("SWEEP_TRACK_SIGMA", "0.042"), CultureInfo.InvariantCulture) * hz;   // seconds -> frames (2.5 frames at 60 Hz)
            var savedPlayer = c.player; c.player = null; var clr = c.safety.clearance; bool savedResidual = clr.Residual;
            int k = 0;
            void Play(bool settle)
            {
                clr.Reset();
                for (k = 0; k <= n; k++)
                {
                    float t = Mathf.Min(j.clip.length, k / hz);
                    if (k == 0 && settle) for (int s = 0; s < 30; s++) Pose(c, j, t, Mode.After, s == 0 ? 0 : 1 / hz);   // settled as if the pose had been held
                    else Pose(c, j, t, Mode.After, k == 0 ? 0 : 1 / hz);
                }
            }
            // pass 1: the full solver (with its look-ahead), as played; where a locked hand or the held prop is still inside, the
            // body step moves the body instead (chest twist, knee swivel) with the hands and feet held exactly
            clr.Residual = false;
            if (c.golf && j.golfLocked) { j.impact = GolfImpact(c, j, hz); golfBakeFreedom = .01f / HeroClearance.MaxGroupTravel; }
            int bodyFrames = 0, truthMoves = 0, flipFixes = 0, slides = 0; bool bodyOn = Env("SWEEP_BODY_STEP", "1") == "1", truthOn = Env("SWEEP_TRUTH_PUSH", "1") == "1";
            preSolve = (cc, q) => { for (int b = 0; b < B; b++) if (bones[b]) pre[k, b] = bones[b].localRotation; locked[k, 0] = q.travelLeft < .1f; locked[k, 1] = q.travelRight < .1f; };
            postSolve = (cc, q) =>
            {
                if (bodyOn && (locked[k, 0] || locked[k, 1]) && BodyStep(cc, bones)) bodyFrames++;
                if (truthOn) truthMoves += TruthPush(cc, bones, locked[k, 0], locked[k, 1]);
                if (truthOn && (locked[k, 0] || locked[k, 1])) slides += GripSlide(cc, bones, Mathf.Min(j.clip.length, k / hz), j.contact >= 0 ? j.contact : j.impact);
                for (int b = 0; b < B; b++) if (bones[b]) post[k, b] = bones[b].localRotation;
                for (int s = 0; s < 2; s++) { var h = bones[s * 4 + 3]; if (h) { handPos[k, s] = h.position; handRot[k, s] = h.rotation; } }
            };
            Play(true);
            golfBakeFreedom = 0;
            // a looping clip is smoothed round its seam; a near-still clip (Ready, Idle: arm speeds under 90 deg/s) gets a wide
            // window (0.2 s), so the correction there is as still as the clip
            bool loop = j.clip.isLooping; float peak = 0;
            for (int f = 1; f < F; f++) foreach (int b in new[] { 1, 2, 5, 6 }) if (bones[b]) peak = Mathf.Max(peak, Quaternion.Angle(pre[f - 1, b], pre[f, b]) * hz);
            if (peak < 90) sigma = Mathf.Max(sigma, (peak < 30 ? .6f : .2f) * hz);   // a still clip's correction is as still as the clip
            // the correction, then smooth -> apply -> residual solve -> truth push, three times with a shrinking kernel: every push
            // comes after a smoothing, and every smoothing is followed by a push, so the result is both smooth and clear
            var D = new Quaternion[F, B];
            for (int f = 0; f < F; f++) for (int b = 0; b < B; b++) D[f, b] = bones[b] ? Quaternion.Inverse(pre[f, b]) * post[f, b] : Quaternion.identity;
            Quaternion[,] Ds = null;
            clr.Residual = true;
            var feet = new (Transform u, Transform l, Transform f)[] { (bones[11], bones[12], bones[13]), (bones[14], bones[15], bones[16]) };
            preSolve = (cc, q) =>
            {
                var fp = new (Vector3 p, Quaternion r)[2]; for (int s = 0; s < 2; s++) if (feet[s].f) fp[s] = (feet[s].f.position, feet[s].f.rotation);
                var hingePre = new Vector3[2];
                for (int s = 0; s < 2; s++) { var u0 = bones[s * 4 + 1]; var l0 = bones[s * 4 + 2]; var h0 = bones[s * 4 + 3]; if (u0 && l0 && h0) hingePre[s] = Vector3.Cross(l0.position - u0.position, h0.position - l0.position); }
                for (int s = 0; s < 2; s++) if (bones[s * 4 + 3]) handPre[k, s] = root.InverseTransformPoint(bones[s * 4 + 3].position);
                for (int b = 0; b < B; b++) if (bones[b]) { pre2[k, b] = bones[b].localRotation; bones[b].localRotation = bones[b].localRotation * Ds[k, b]; }
                // planted feet stay exactly where the game put them
                for (int s = 0; s < 2; s++) if (feet[s].u && feet[s].l && feet[s].f) { HeroPoseSafety.Solve(feet[s].u, feet[s].l, feet[s].f, fp[s].p); feet[s].f.rotation = fp[s].r; }
                for (int s = 0; s < 2; s++)
                {
                    var u = bones[s * 4 + 1]; var l = bones[s * 4 + 2]; var h = bones[s * 4 + 3]; if (!u || !l || !h) continue;
                    var goal = locked[k, s] ? handPos[k, s] : h.position; var turn = locked[k, s] ? handRot[k, s] : h.rotation;
                    if (locked[k, s]) { HeroPoseSafety.Solve(u, l, h, goal, hingePre[s]); h.rotation = turn; }
                    // the elbow stays within 80 deg of the game's own elbow plane: a continuous clamp, never a side switch
                    if (HeroPoseSafety.ClampSwivel(u, l, h, hingePre[s])) flipFixes++;
                }
            };
            int bakeFails = 0; var tp = new List<(Vector3, bool)>();
            float[] sigmas = Env("SWEEP_ROUNDS", "3") == "2" ? new[] { sigma, sigma * .45f } : new[] { sigma, sigma * .6f, sigma * .32f };
            bool diag = Env("SWEEP_BAKE_DIAG", "1") == "1";
            for (int round = 0; round < sigmas.Length; round++)
            {
                Ds = Smooth(D, sigmas[round], loop); bool last = round == sigmas.Length - 1;
                postSolve = (cc, q) =>
                {
                    if (truthOn) truthMoves += TruthPush(cc, bones, locked[k, 0], locked[k, 1]);
                    for (int b = 0; b < B; b++) if (bones[b]) post2[k, b] = bones[b].localRotation;
                    for (int s = 0; s < 2; s++) if (bones[s * 4 + 3]) handPost[k, s] = root.InverseTransformPoint(bones[s * 4 + 3].position);
                    if (last && diag) { AfterSolve(cc); if (MeasureTruth(cc.truth, clr, PropPoints(cc, tp)).Worst > .003f) bakeFails++; }   // diagnostics: the bake's own result
                };
                Play(true);
                for (int f = 0; f < F; f++) for (int b = 0; b < B; b++) D[f, b] = bones[b] ? Quaternion.Inverse(pre2[f, b]) * post2[f, b] : Quaternion.identity;
            }
            preSolve = postSolve = null; c.player = savedPlayer; clr.Residual = savedResidual; clr.Reset();
            // the track: only bones the correction actually moves
            var keep = Enumerable.Range(0, B).Where(b => bones[b] && Enumerable.Range(0, F).Any(f => Quaternion.Angle(pre2[f, b], post2[f, b]) > .05f)).ToArray();
            if (keep.Length == 0) { Debug.Log($"[SweepTrack] {c.name} {j.name}: nothing to correct"); return; }
            var final = new Quaternion[F, keep.Length];
            for (int f = 0; f < F; f++) for (int i = 0; i < keep.Length; i++) final[f, i] = Quaternion.Inverse(pre2[f, keep[i]]) * post2[f, keep[i]];
            if (loop) for (int i = 0; i < keep.Length; i++) final[F - 1, i] = final[0, i];
            if (peak < 90) final = Smooth(final, (peak < 30 ? .3f : .1f) * hz, loop);   // a still clip: the last push's jitter smoothed out too (re-checked by the sweep)
            var track = new HeroClearanceTracks.Track
            {
                key = HeroClearanceTracks.Key(j.clip), length = j.clip.length, hz = hz, frames = F,
                paths = keep.Select(b => HeroClearanceTracks.PathOf(bones[b], root)).ToArray(), q = HeroClearanceTracks.Pack(final),
                source = HeroClearanceTracks.Fingerprint(j.clip),
            };
            // where each LOCKED hand ends up relative to the game's own hand (0 at contact; a grip slide up to 1 cm), so the
            // game's re-lock keeps the slide and nothing else (between keys too)
            bool anySlip = false; var slip = new short[F * 6];
            for (int f = 0; f < F; f++)
                for (int s = 0; s < 2; s++)
                {
                    if (!locked[f, s]) continue;
                    // never at the contact instant: the slide fades out between 0.10 and 0.04 s from it
                    float tc = j.contact >= 0 ? j.contact : j.impact, near = tc < 0 ? 1 : Mathf.SmoothStep(0, 1, Mathf.InverseLerp(.04f, .10f, Mathf.Abs(f / hz - tc)));
                    var d = Vector3.ClampMagnitude(handPost[f, s] - handPre[f, s], .015f) * 1e4f * near;
                    int i = (f * 2 + s) * 3; slip[i] = (short)Mathf.RoundToInt(d.x); slip[i + 1] = (short)Mathf.RoundToInt(d.y); slip[i + 2] = (short)Mathf.RoundToInt(d.z);
                    if (d.sqrMagnitude > 1) anySlip = true;
                }
            if (loop) for (int i = 0; i < 6; i++) slip[(F - 1) * 6 + i] = slip[i];
            if (anySlip) track.slip = slip;
            c.lib.tracks[track.key] = track;
            float maxDeg = 0; for (int f = 0; f < F; f++) for (int i = 0; i < keep.Length; i++) maxDeg = Mathf.Max(maxDeg, Quaternion.Angle(Quaternion.identity, final[f, i]));
            Debug.Log($"[SweepTrack] {c.name} {j.name}: {keep.Length} bones x {F} frames, max {maxDeg:0.0} deg, loop {loop}, clip arm peak {peak:0} deg/s, sigma {sigma / hz:0.000} s, body step on {bodyFrames} frames, truth pushes {truthMoves}, grip slides {slides}, elbow clamps {flipFixes}, bake frames still > 3 mm {bakeFails} ({string.Join(",", keep.Select(b => ids[b]))})");
        }

        /// The truth push (offline only): the proxy is an approximation (a flared hem, a skirt's pleats can stand further off than
        /// it models), so after the solve the real meshes are measured and a free hand or forearm still inside the body or under
        /// a garment's outer wall is moved out along the surface normal there by its depth + 4 mm (wrist IK, the hand's
        /// rotation kept), up to three times. A held prop still inside moves its holding hand the same way when that hand is free.
        /// Locked hands are never moved (the body step handles those).
        static readonly bool armSwivel = Env("SWEEP_ARM_SWIVEL", "0") == "1";   // tried 10-18: no gain on the two-hand grip, more flips
        static int TruthPush(Ctx c, Transform[] bones, bool lockL, bool lockR)
        {
            var clr = c.safety.clearance; int moves = 0; var pts = new List<(Vector3, bool)>();
            // a forearm point between elbow and wrist moves only that fraction of the wrist's move: scale up so the point itself clears
            float Lever(int s, Hit h)
            {
                if (h.where == null || !h.where.Contains("fore>")) return 1;
                var l = bones[s * 4 + 2]; var hand = bones[s * 4 + 3]; if (!l || !hand) return 1;
                var ew = hand.position - l.position; float u = Vector3.Dot(h.p - l.position, ew) / Mathf.Max(1e-6f, ew.sqrMagnitude);
                return Mathf.Clamp(u, .35f, 1);
            }
            void Move(int s, Vector3 by)
            {
                var u = bones[s * 4 + 1]; var l = bones[s * 4 + 2]; var hand = bones[s * 4 + 3]; if (!u || !l || !hand) return;
                var rot = hand.rotation; HeroPoseSafety.Solve(u, l, hand, hand.position + by); hand.rotation = rot;
            }
            for (int it = 0; it < 3; it++)
            {
                AfterSolve(c);   // the meshes as drawn
                var ft = MeasureTruth(c.truth, clr, PropPoints(c, pts));
                clr.DetectGrip(); int holder = clr.HeldProp != null ? (clr.HolderSide < 0 ? 0 : 1) : -1;
                // something inside the OTHER arm (a two-hand grip: the lower hand in the upper forearm, the racket against the
                // upper arm): that arm swivels its elbow about its shoulder-wrist line, its hand staying exactly put (allowed at contact)
                var armHit = ft.body.Append(ft.propBody).Where(x => x.depth > .002f && x.where != null).OrderByDescending(x => x.depth).FirstOrDefault(x => ArmSide(x.where) >= 0);
                if (armSwivel && armHit.depth > .002f && SwivelOut(c, bones, ArmSide(armHit.where), pts)) { moves++; clr.proxy.Refresh(); AfterSolve(c); ft = MeasureTruth(c.truth, clr, PropPoints(c, pts)); }
                Hit Deepest(int s) { var l = new List<Hit> { ft.body[s], ft.cloth[s], ft.body[2 + s], ft.cloth[2 + s] }; if (s == holder) { l.Add(ft.propBody); l.Add(ft.propCloth); } return l.OrderByDescending(x => x.depth).First(); }
                bool any = false;
                if (clr.TwoHandGrip)
                {
                    // both hands on the prop: they move together, or not at all
                    if (lockL || lockR) break;
                    var a = Deepest(0); var b = Deepest(1); var h = a.depth >= b.depth ? a : b;
                    if (h.depth > .002f && h.normal.sqrMagnitude > .5f) { var by = h.normal.normalized * (h.depth + .004f) / Lever(a.depth >= b.depth ? 0 : 1, h); Move(0, by); Move(1, by); any = true; moves++; }
                }
                else
                    for (int s = 0; s < 2; s++)
                    {
                        if (s == 0 ? lockL : lockR) continue;
                        var h = Deepest(s);
                        if (h.depth <= .002f || h.normal.sqrMagnitude < .5f) continue;
                        Move(s, h.normal.normalized * (h.depth + .004f) / Lever(s, h)); any = true; moves++;
                    }
                if (!any) break;
                clr.proxy.Refresh();
            }
            return moves;
        }

        /// The grip parting (offline only): in a two-hand grip with the wrists locked (a golf swing, a two-hand backhand), when one
        /// hand lies inside the other arm or under the other hand's glove on the real meshes, both hands part along the contact
        /// normal, half the overlap + 2 mm each, each at most 1 cm (the allowed hand-path deviation), and not at all at the
        /// contact instant (eased in from 0.06 to 0.14 s away from it). (Sliding along the shaft was tried first: the overlap
        /// runs across the shaft, so it barely helped.) Elbows kept on the game's side. Returns the moves made.
        static int GripSlide(Ctx c, Transform[] bones, float t, float contact)
        {
            var clr = c.safety.clearance; clr.DetectGrip(); if (!clr.TwoHandGrip || clr.HeldProp == null) return 0;
            float allow = .01f * (contact < 0 ? 1 : Mathf.SmoothStep(0, 1, Mathf.InverseLerp(.06f, .14f, Mathf.Abs(t - contact))));
            if (allow < .001f) return 0;
            var hinge = new Vector3[2]; var moved = new float[2];
            for (int s = 0; s < 2; s++) { var u0 = bones[s * 4 + 1]; var l0 = bones[s * 4 + 2]; var h0 = bones[s * 4 + 3]; if (u0 && l0 && h0) hinge[s] = Vector3.Cross(l0.position - u0.position, h0.position - l0.position); }
            int n = 0; var pts = new List<(Vector3, bool)>();
            for (int it = 0; it < 3; it++)
            {
                AfterSolve(c); var ft = MeasureTruth(c.truth, clr, PropPoints(c, pts));
                // the deepest hand/forearm-into-the-other-arm (or under the other hand's glove) contact, and who is who
                Hit h = default; int intruder = -1, obstacle = -1;
                for (int k = 0; k < 4; k++)
                    foreach (var x in new[] { ft.body[k], ft.cloth[k] })
                    {
                        if (x.depth <= h.depth || x.where == null) continue;
                        int o = ArmSide(x.where); if (o < 0 && x.where.Contains("Glove")) o = x.where.Contains("GloveL") ? 0 : x.where.Contains("GloveR") ? 1 : -1;
                        if (o < 0 || o == k % 2) continue;
                        h = x; intruder = k % 2; obstacle = o;
                    }
                if (intruder < 0 || h.depth <= .002f || h.normal.sqrMagnitude < .5f) break;
                // both hands part along the contact normal, half each, each within the 1 cm hand-path allowance
                float half = (h.depth + .002f) * .5f; bool any = false;
                foreach (var (s, sign) in new[] { (intruder, 1f), (obstacle, -1f) })
                {
                    float step = Mathf.Min(half, allow - moved[s]); if (step < .0003f) continue;
                    var u = bones[s * 4 + 1]; var l = bones[s * 4 + 2]; var hd = bones[s * 4 + 3]; if (!u || !l || !hd) continue;
                    var rot = hd.rotation; HeroPoseSafety.Solve(u, l, hd, hd.position + h.normal.normalized * sign * step, hinge[s]); hd.rotation = rot;
                    moved[s] += step; any = true;
                }
                if (!any) break;
                n++; clr.proxy.Refresh();
            }
            return n;
        }

        /// The arm (0 left, 1 right) a truth hit's obstacle belongs to ("Rhand>LeftLowerArm" -> 0), or -1 (body, garment).
        static int ArmSide(string where)
        {
            int i = where.IndexOf('>'); if (i < 0) return -1; var o = where.Substring(i + 1);
            bool arm = o.Contains("Arm") || o.Contains("Shoulder") || o.Contains("Hand") || o.Contains("ArmBlend");
            if (!arm) return -1;
            return o.StartsWith("Left") || o.Contains("_Left") ? 0 : o.StartsWith("Right") || o.Contains("_Right") ? 1 : -1;
        }
        /// Swivels arm `s` about its shoulder-wrist line (the hand's position and rotation kept) to the angle where the real meshes
        /// are deepest-clearest (+-50 deg in 10 deg steps, then 5); keeps the elbow on the game's side. True when it moved.
        static bool SwivelOut(Ctx c, Transform[] bones, int s, List<(Vector3, bool)> pts)
        {
            var u = bones[s * 4 + 1]; var l = bones[s * 4 + 2]; var h = bones[s * 4 + 3]; if (!u || !l || !h) return false;
            var u0 = u.rotation; var hr = h.rotation; var S = u.position; var W = h.position; var axis = (W - S).normalized;
            var hinge0 = Vector3.Cross(l.position - S, W - l.position);
            float Eval(float deg)
            {
                u.rotation = Quaternion.AngleAxis(deg, axis) * u0; h.rotation = hr;
                var hinge = Vector3.Cross(l.position - S, h.position - l.position);
                if (hinge0.sqrMagnitude > 1e-8f && Vector3.Angle(hinge0, hinge) > 80) return float.MaxValue;
                c.safety.clearance.proxy.Refresh(); AfterSolve(c);
                return MeasureTruth(c.truth, c.safety.clearance, PropPoints(c, pts)).Worst + Mathf.Abs(deg) * 2e-5f;
            }
            float best = Eval(0), at = 0;
            for (float d = -50; d <= 50; d += 10) { if (d == 0) continue; float v = Eval(d); if (v < best - .0005f) { best = v; at = d; } }
            foreach (float d in new[] { at - 5, at + 5 }) { if (Mathf.Abs(d) > 50) continue; float v = Eval(d); if (v < best - .0005f) { best = v; at = d; } }
            u.rotation = Quaternion.AngleAxis(at, axis) * u0; h.rotation = hr;
            return Mathf.Abs(at) > .01f;
        }

        /// The body step (offline only): a locked hand or the held prop is still inside after the arm solve, so the body moves
        /// out of the way instead: the chest turns (about the hero's up / right / forward, up to 12 / 8 / 8 deg) and each knee
        /// swivels about its hip-ankle line (up to 25 deg; the foot does not move). Both arms are re-solved by IK so the hands
        /// keep their exact pose (the racket / club with them). Pattern search on the summed proxy violation + a small cost per
        /// degree. Returns true when it changed the pose.
        static bool BodyStep(Ctx c, Transform[] bones)
        {
            var clr = c.safety.clearance; const float m = .002f;
            float w0 = clr.MeasureAll(out float s0, m); if (w0 <= m + .001f) return false;
            var root = c.root.transform; var chest = bones[10] ? bones[10] : bones[9] ? bones[9] : bones[8]; if (!chest) return false;
            var chest0 = chest.rotation;
            var arm = new (Transform u, Transform l, Transform h, Quaternion ul, Quaternion ll, Vector3 p, Quaternion r)[2];
            for (int s = 0; s < 2; s++) { var u = bones[s * 4 + 1]; var l = bones[s * 4 + 2]; var h = bones[s * 4 + 3]; if (u && l && h) arm[s] = (u, l, h, u.localRotation, l.localRotation, h.position, h.rotation); }
            var leg = new (Transform u, Transform f, Quaternion u0, Quaternion f0, Vector3 axis)[2];
            for (int s = 0; s < 2; s++) { var u = bones[11 + s * 3]; var f = bones[13 + s * 3]; if (u && f) leg[s] = (u, f, u.rotation, f.rotation, (f.position - u.position).normalized); }
            float[] lim = { 12, 8, 8, 25, 25 }, x = new float[5];
            var hinge0 = new Vector3[2]; for (int s = 0; s < 2; s++) if (arm[s].u) hinge0[s] = Vector3.Cross(arm[s].l.position - arm[s].u.position, arm[s].h.position - arm[s].l.position);
            float Cost(float[] v)
            {
                chest.rotation = Quaternion.AngleAxis(v[0], root.up) * Quaternion.AngleAxis(v[1], root.right) * Quaternion.AngleAxis(v[2], root.forward) * chest0;
                float reach = 0;
                for (int s = 0; s < 2; s++)
                {
                    if (!arm[s].u) continue;
                    arm[s].u.localRotation = arm[s].ul; arm[s].l.localRotation = arm[s].ll;
                    HeroPoseSafety.Solve(arm[s].u, arm[s].l, arm[s].h, arm[s].p, hinge0[s]); arm[s].h.rotation = arm[s].r;
                    reach = Mathf.Max(reach, Vector3.Distance(arm[s].h.position, arm[s].p));
                    var hg = Vector3.Cross(arm[s].l.position - arm[s].u.position, arm[s].h.position - arm[s].l.position);
                    if (hinge0[s].sqrMagnitude > 1e-8f && hg.sqrMagnitude > 1e-8f && Vector3.Angle(hinge0[s], hg) > 80) reach = 1;   // a flipped elbow: rejected
                }
                for (int s = 0; s < 2; s++)
                {
                    if (!leg[s].u) continue;
                    leg[s].u.rotation = Quaternion.AngleAxis(v[3 + s], leg[s].axis) * leg[s].u0; leg[s].f.rotation = leg[s].f0;
                }
                clr.MeasureAll(out float sum, m);
                float reg = 0; for (int i = 0; i < 5; i++) reg += v[i] * v[i] * (i < 3 ? 2e-4f : 5e-5f);   // a posture change is expensive (10-18: a 6 deg chest turn at golf address read as 'angled weird')
                return sum + reg + (reach > .003f ? 1 : 0);
            }
            // the real meshes before: the move is kept only if they clear measurably (the proxy alone can reward a turn that clears nothing)
            var pts = new List<(Vector3, bool)>();
            AfterSolve(c); float truth0 = MeasureTruth(c.truth, clr, PropPoints(c, pts)).Worst;
            float best = Cost(x);
            foreach (float scale in new[] { 1 / 3f, 1 / 6f, 1 / 12f })
                for (int pass = 0; pass < 3; pass++)
                {
                    bool moved = false;
                    for (int i = 0; i < 5; i++)
                        foreach (int sign in new[] { 1, -1 })
                        {
                            var y = (float[])x.Clone(); y[i] = Mathf.Clamp(y[i] + sign * lim[i] * scale, -lim[i], lim[i]);
                            float cy = Cost(y); if (cy < best - 1e-6f) { best = cy; x = y; moved = true; break; }
                        }
                    if (!moved) break;
                }
            Cost(x);
            if (!x.Any(v => Mathf.Abs(v) > .01f)) return false;
            AfterSolve(c); float truth1 = MeasureTruth(c.truth, clr, PropPoints(c, pts)).Worst;
            if (truth1 <= truth0 - .002f) return true;
            // no real gain: the pose goes back exactly as it was
            chest.rotation = chest0;
            for (int s = 0; s < 2; s++) if (arm[s].u) { arm[s].u.localRotation = arm[s].ul; arm[s].l.localRotation = arm[s].ll; arm[s].h.rotation = arm[s].r; }
            for (int s = 0; s < 2; s++) if (leg[s].u) { leg[s].u.rotation = leg[s].u0; leg[s].f.rotation = leg[s].f0; }
            clr.proxy.Refresh();
            return false;
        }

        /// Envelope before smoothing: per bone group (each arm, the spine, each leg), every frame takes the group's largest
        /// correction within +-r frames, so smoothing afterwards cannot shave the correction below what a frame needed.
        static Quaternion[,] Dilate(Quaternion[,] D, int r)
        {
            int F = D.GetLength(0), B = D.GetLength(1); var o = (Quaternion[,])D.Clone();
            if (r <= 0) return o;
            var groups = new List<int[]>();
            if (B >= 8) { groups.Add(new[] { 0, 1, 2, 3 }); groups.Add(new[] { 4, 5, 6, 7 }); }
            if (B >= 11) groups.Add(new[] { 8, 9, 10 });
            if (B >= 17) { groups.Add(new[] { 11, 12, 13 }); groups.Add(new[] { 14, 15, 16 }); }
            if (groups.Count == 0) groups.Add(Enumerable.Range(0, B).ToArray());
            foreach (var g in groups)
            {
                var size = new float[F]; for (int f = 0; f < F; f++) foreach (int b in g) size[f] += Quaternion.Angle(Quaternion.identity, D[f, b]);
                for (int f = 0; f < F; f++)
                {
                    int best = f;
                    for (int i = Mathf.Max(0, f - r); i <= Mathf.Min(F - 1, f + r); i++) if (size[i] > size[best]) best = i;
                    foreach (int b in g) o[f, b] = D[best, b];
                }
            }
            return o;
        }

        /// Zero-phase Gaussian smoothing of per-frame rotations (sign-aligned weighted mean). sigma in frames; 0 = none.
        static Quaternion[,] Smooth(Quaternion[,] D, float sigma, bool loop = false)
        {
            int F = D.GetLength(0), B = D.GetLength(1); var o = new Quaternion[F, B];
            if (sigma <= 0) { Array.Copy(D, o, D.Length); if (loop) for (int b = 0; b < B; b++) o[F - 1, b] = o[0, b]; return o; }
            int P = F - 1;   // a looping clip's last frame is its first again (t = length wraps to 0)
            int r = Mathf.CeilToInt(sigma * 3); var w = new float[2 * r + 1]; for (int i = -r; i <= r; i++) w[i + r] = Mathf.Exp(-.5f * i * i / (sigma * sigma));
            for (int b = 0; b < B; b++)
                for (int f = 0; f < F; f++)
                {
                    Vector4 sum = Vector4.zero; var refQ = D[f, b];
                    for (int i = -r; i <= r; i++)
                    {
                        int at = loop && P > 0 ? ((f + i) % P + P) % P : Mathf.Clamp(f + i, 0, F - 1);
                        var q = D[at, b]; if (Quaternion.Dot(q, refQ) < 0) q = new Quaternion(-q.x, -q.y, -q.z, -q.w);
                        sum += new Vector4(q.x, q.y, q.z, q.w) * w[i + r];
                    }
                    o[f, b] = sum.sqrMagnitude > 1e-12f ? Quaternion.Normalize(new Quaternion(sum.x, sum.y, sum.z, sum.w)) : Quaternion.identity;
                }
            if (loop) for (int b = 0; b < B; b++) o[F - 1, b] = o[0, b];
            return o;
        }
        static void WriteTracks(Ctx c, string outDir)
        {
            if (TrackMode(c) != "bake" || c.lib == null) return;
            string file = HeroClearanceTracks.File(c.female, c.look.golfKit) + ".bytes";
            // merge with what an earlier context baked for the same hero and kit (the plaza set on a kit, a subset re-bake)
            string res = Path.Combine(Application.dataPath, "Resources/HeroClearance"); Directory.CreateDirectory(res);
            string target = Path.Combine(res, file);
            var lib = File.Exists(target) && Env("SWEEP_TRACKS_FRESH", "0") != "1" ? HeroClearanceTracks.Read(File.ReadAllBytes(target)) : new HeroClearanceTracks();
            foreach (var kv in c.lib.tracks) lib.tracks[kv.Key] = kv.Value;
            var bytes = lib.Write();
            File.WriteAllBytes(Path.Combine(outDir, file), bytes);
            if (Env("SWEEP_TRACKS_INSTALL", "1") == "1") { File.WriteAllBytes(target, bytes); HeroClearanceTracks.Install(c.female, c.look.golfKit, lib); }
            Debug.Log($"[SweepTrack] wrote {file}: {lib.tracks.Count} tracks, {bytes.Length / 1024} KB" + (Env("SWEEP_TRACKS_INSTALL", "1") == "1" ? " (installed in Resources/HeroClearance)" : ""));
        }
        static float lastTravel = 1;   // the AFTER pose's smaller hand travel (0 = wrists locked at contact)
        static void Pose(Ctx c, ClipJob j, float t, Mode mode, float dt)
        {
            if (j.graph.IsValid()) { j.play.SetTime(t); j.graph.Evaluate(0); }
            else j.clip.SampleAnimation(c.root, t);
            var look = c.look;
            bool locked = false, freeLeft = false, two = false; float freedom = 0;
            if (!c.golf && j.id is HeroTennisDriver.Clip id)
            {
                c.openForehand?.Invoke(c.driver, new object[] { id, t, 1f });
                c.serveWrist?.Invoke(c.driver, new object[] { id, t });
                bool stroke = TennisStroke(id);
                // as the live driver (PostProcess): only a stroke locks the wrists; Ready / idles / emotes / reactions are free
                locked = stroke; freeLeft = id == HeroTennisDriver.Clip.Serve;
                freedom = stroke ? Mathf.SmoothStep(0, 1, Mathf.InverseLerp(.12f, .28f, Mathf.Abs(t - j.contact))) : 0;
                two = id == HeroTennisDriver.Clip.Backhand || id == HeroTennisDriver.Clip.BackhandWide || id == HeroTennisDriver.Clip.Return || id == HeroTennisDriver.Clip.VolleyBackhand;
            }
            if (c.golf)
            {
                look.body?.GetComponent<HeroArmSkinning>()?.Apply();
                if (j.golfLocked) { if (j.clip.name == "Drive") c.golfClear.ApplyDriveFollowThrough(t); c.golfClear.Apply(); }
                HeroGripPolish.ApplyGrip(look);
                if (j.golfLocked) c.golfClear.SeparateHands();
                locked = j.golfLocked;
                // the track bake may move golf hands up to 1 cm away from impact (coordinator rule 2026-10-18); the game stays locked
                if (locked && golfBakeFreedom > 0 && j.impact >= 0) freedom = golfBakeFreedom * Mathf.SmoothStep(0, 1, Mathf.InverseLerp(.06f, .14f, Mathf.Abs(t - j.impact)));
            }
            if (mode == Mode.Before) c.legacy.Apply(locked, freeLeft, freedom, two);
            if (mode == Mode.After)
            {
                var q = new HeroClearance.Request { travelRight = locked ? freedom : 1, travelLeft = !locked || freeLeft ? 1 : freedom, twoHanded = two };
                lastTravel = Mathf.Min(q.travelLeft, q.travelRight);
                afterTimer.Restart();
                if (preSolve != null) preSolve(c, q);
                else if (c.player != null) { if (j.graph.IsValid()) { c.player.graph = j.graph; c.player.Apply(q.travelLeft, q.travelRight); } else c.player.ApplyClip(j.clip, t, q.travelLeft, q.travelRight); }
                // as HeroPoseSafety: a pure baked clip skips the residual solve
                if (preSolve == null && c.player != null && c.player.Coverage > .999f) c.safety.clearance.Reset();
                else c.safety.clearance.Solve(q, dt);
                afterTimer.Stop(); lastAfterMs = afterTimer.Elapsed.TotalMilliseconds;
                postSolve?.Invoke(c, q);
            }
            AfterSolve(c);
        }
        /// The game's passes after the clearance (grip polish, arm twist skinning, shoulder and garment correctives): the meshes
        /// as drawn depend on them, so the truth is measured after them.
        static void AfterSolve(Ctx c)
        {
            var look = c.look;
            if (!c.golf) HeroGripPolish.ApplyGrip(look);
            look.body?.GetComponent<HeroArmSkinning>()?.Apply();
            if (look.GetComponent<FemaleShoulderFit>()) { look.GetComponent<HeroShoulderDeformation>()?.Apply(); look.GetComponent<FemaleShoulderFit>().Apply(); }
            else look.GetComponent<HeroShoulderDeformation>()?.Apply();
            look.GetComponent<FemaleGarmentFinish>()?.Apply();
            look.GetComponent<GolfGarmentCorrectives>()?.Apply();
            look.GetComponent<HeroGarmentPoseCorrectives>()?.Apply();
            look.GetComponent<TailoredPoloDeformation>()?.Apply();
            look.GetComponent<KitV2PoseCorrectives>()?.Apply();
        }

        static List<(Vector3, bool)> PropPoints(Ctx c, List<(Vector3, bool)> into)
        {
            into.Clear();
            var clr = c.safety.clearance; clr.DetectGrip(); var prop = clr.HeldProp; if (prop == null) return into;
            var m = prop.grip.localToWorldMatrix;
            foreach (var (local, handle) in TruthPropPoints(prop)) into.Add((m.MultiplyPoint3x4(local), handle));
            return into;
        }
        static readonly Dictionary<HeroClearance.Prop, List<(Vector3, bool)>> propCache = new Dictionary<HeroClearance.Prop, List<(Vector3, bool)>>();
        /// ~300 surface points of the prop in its grip space (denser than the solver's samples)
        static List<(Vector3, bool)> TruthPropPoints(HeroClearance.Prop p)
        {
            if (propCache.TryGetValue(p, out var l)) return l;
            l = new List<(Vector3, bool)>(); var all = new List<Vector3>();
            foreach (var r in p.renderers)
            {
                Mesh mesh = r is SkinnedMeshRenderer s ? s.sharedMesh : r.GetComponent<MeshFilter>()?.sharedMesh; if (!mesh || !mesh.isReadable) continue;
                Matrix4x4 m;
                if (r is SkinnedMeshRenderer sk) { int bi = Array.IndexOf(sk.bones, p.grip); m = bi >= 0 ? mesh.bindposes[bi] : p.grip.worldToLocalMatrix * r.transform.localToWorldMatrix; }
                else m = p.grip.worldToLocalMatrix * r.transform.localToWorldMatrix;
                foreach (var v in mesh.vertices) all.Add(m.MultiplyPoint3x4(v));
            }
            var seen = new HashSet<long>(); const float vox = .008f;
            foreach (var v in all)
            {
                long k = ((long)Mathf.FloorToInt(v.x / vox) + 10000) * 40000L * 40000L + ((long)Mathf.FloorToInt(v.y / vox) + 10000) * 40000L + (Mathf.FloorToInt(v.z / vox) + 10000);
                if (seen.Add(k)) l.Add((v, Vector3.Dot(v, p.axisLocal) < p.handleLength));
            }
            propCache[p] = l; return l;
        }

        // ================================================================ the sweep
        sealed class Row { public string ctx, clip; public int frame; public float t; public FrameTruth before, after; public float ms; public float residual; }
        sealed class ClipStat
        {
            public string ctx, clip; public int frames; public float bodyBefore, bodyAfter, clothBefore, clothAfter; public string whereBefore, whereAfter;
            public int bodyFailBefore, bodyFailAfter, clothFailBefore, clothFailAfter;
            public float contactDrift = -1, rawPeakShoulder, rawPeakElbow, afterPeakShoulder, afterPeakElbow; public int popFrames, flips; public float popRatio; public string popAt = "", flipAt = "";
        }

        static IEnumerator SweepMain()
        {
            string outDir = Env("SWEEP_OUT", "/private/tmp/hand-clearance-sweep"); Directory.CreateDirectory(outDir);
            float hz = float.Parse(Env("SWEEP_HZ", "60"), CultureInfo.InvariantCulture), grow = float.Parse(Env("SWEEP_GROW", "0"), CultureInfo.InvariantCulture);
            int worstN = int.Parse(Env("SWEEP_WORST", "20")); bool render = Env("SWEEP_RENDER", "1") == "1";
            const float FailMm = 3f; bool withBefore = Env("SWEEP_BEFORE", "1") == "1";
            var csv = new StringWriter(); csv.WriteLine("ctx,clip,frame,t,bodyBefore,whereBodyBefore,clothBefore,whereClothBefore,bodyAfter,whereBodyAfter,clothAfter,whereClothAfter,solverMs,proxyBefore,proxyAfter,proxyWhere,msRefresh,msTranslate,msSwivel,msProp,msDiag,lookups,travel,headMm");
            var stats = new List<ClipStat>(); var costs = new List<float>(); var worstAll = new List<(Row r, string img)>();
            var cam = new GameObject("Sweep camera").AddComponent<Camera>(); cam.enabled = false; cam.clearFlags = CameraClearFlags.SolidColor; cam.backgroundColor = new Color(.22f, .25f, .28f); cam.nearClipPlane = .02f;
            var key = new GameObject("Key").AddComponent<Light>(); key.type = LightType.Directional; key.intensity = 1.25f; key.transform.rotation = Quaternion.Euler(40, -30, 0);
            RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Flat; RenderSettings.ambientLight = new Color(.55f, .55f, .58f);
            var propPts = new List<(Vector3, bool)>();
            foreach (var cname in Env("SWEEP_CONTEXTS", "tennis_male,tennis_female,golf_male,golf_female").Split(','))
            {
                var c = MakeContext(cname);
                for (int i = 0; i < 4; i++) yield return null;   // Awake / Start: materials, arm skinning, kit binding and cover
                ArmContext(c, grow);
                yield return null;
                var rows = new List<Row>();
                foreach (var j in Jobs(c))
                {
                    Props(c, j); j.Open(c.look.animator);
                    if (TrackMode(c) == "bake") BakeTrack(c, j, float.Parse(Env("SWEEP_TRACK_HZ", F(hz)), CultureInfo.InvariantCulture));
                    var st = new ClipStat { ctx = c.name, clip = j.name };
                    int n = Mathf.Max(1, Mathf.CeilToInt(j.clip.length * hz));
                    var upL = c.look.Bone(HumanBodyBones.LeftUpperArm); var upR = c.look.Bone(HumanBodyBones.RightUpperArm);
                    var loL = c.look.Bone(HumanBodyBones.LeftLowerArm); var loR = c.look.Bone(HumanBodyBones.RightLowerArm);
                    var hdL = c.look.Bone(HumanBodyBones.LeftHand); var hdR = c.look.Bone(HumanBodyBones.RightHand);
                    var rawQ = new Quaternion[n + 1, 4]; var aftQ = new Quaternion[n + 1, 4]; var rawHinge = new Vector3[n + 1, 2]; var aftHinge = new Vector3[n + 1, 2]; var bend = new float[n + 1, 2];
                    c.safety.clearance.Reset();
                    for (int k = 0; k <= n; k++)
                    {
                        float t = Mathf.Min(j.clip.length, k / hz);
                        // RAW
                        Pose(c, j, t, Mode.Raw, 0); var headRaw = HeadPoint(c);
                        rawQ[k, 0] = upL.localRotation; rawQ[k, 1] = upR.localRotation; rawQ[k, 2] = loL.localRotation; rawQ[k, 3] = loR.localRotation;
                        rawHinge[k, 0] = Vector3.Cross(loL.position - upL.position, hdL.position - loL.position); rawHinge[k, 1] = Vector3.Cross(loR.position - upR.position, hdR.position - loR.position);
                        bend[k, 0] = Vector3.Angle(loL.position - upL.position, hdL.position - loL.position); bend[k, 1] = Vector3.Angle(loR.position - upR.position, hdR.position - loR.position);
                        // BEFORE
                        FrameTruth fb;
                        if (withBefore) { Pose(c, j, t, Mode.Before, 0); fb = MeasureTruth(c.truth, c.safety.clearance, PropPoints(c, propPts)); }
                        else fb = new FrameTruth();
                        // AFTER (continuous playback at hz)
                        // frame 0: the solver settles on the first pose as if the clip had been entered from itself (the sweep starts
                        // every clip from a reset solver; the game blends in from a running one)
                        if (k == 0) for (int settle = 0; settle < 4; settle++) Pose(c, j, t, Mode.After, settle == 0 ? 0 : 1 / hz);
                        else Pose(c, j, t, Mode.After, 1 / hz);
                        float ms = (float)lastAfterMs; if (k > 0) costs.Add(ms);
                        aftQ[k, 0] = upL.localRotation; aftQ[k, 1] = upR.localRotation; aftQ[k, 2] = loL.localRotation; aftQ[k, 3] = loR.localRotation;
                        aftHinge[k, 0] = Vector3.Cross(loL.position - upL.position, hdL.position - loL.position); aftHinge[k, 1] = Vector3.Cross(loR.position - upR.position, hdR.position - loR.position);
                        var fa = MeasureTruth(c.truth, c.safety.clearance, PropPoints(c, propPts));
                        var headAfter = HeadPoint(c); float headMm = headRaw.HasValue && headAfter.HasValue ? Vector3.Distance(headRaw.Value, headAfter.Value) * 1000 : -1;
                        if (Env("SWEEP_DEBUG", "0") == "1" && k == int.Parse(Env("SWEEP_DEBUG_FRAME", "0"))) DebugHit(c, fb.WorstHit());
                        var row = new Row { ctx = c.name, clip = j.name, frame = k, t = t, before = fb, after = fa, ms = ms, residual = c.safety.clearance.ResidualDepth };
                        rows.Add(row);
                        var wb = fb.body.Concat(new[] { fb.propBody }).OrderByDescending(h => h.depth).First(); var wcb = fb.cloth.Concat(new[] { fb.propCloth }).OrderByDescending(h => h.depth).First();
                        var wa = fa.body.Concat(new[] { fa.propBody }).OrderByDescending(h => h.depth).First(); var wca = fa.cloth.Concat(new[] { fa.propCloth }).OrderByDescending(h => h.depth).First();
                        csv.WriteLine($"{c.name},{j.name},{k},{F(t)},{F(wb.depth * 1000)},{wb.where},{F(wcb.depth * 1000)},{wcb.where},{F(wa.depth * 1000)},{wa.where},{F(wca.depth * 1000)},{wca.where},{ms.ToString("0.####", CultureInfo.InvariantCulture)},{F(c.safety.clearance.BeforeDepth * 1000)},{F(c.safety.clearance.ResidualDepth * 1000)},{c.safety.clearance.ResidualWhere},{c.safety.clearance.Phase.refresh:0.###},{c.safety.clearance.Phase.translate:0.###},{c.safety.clearance.Phase.swivel:0.###},{c.safety.clearance.Phase.prop:0.###},{c.safety.clearance.Phase.diag:0.###},{c.safety.clearance.Phase.lookups},{F(lastTravel)},{F(headMm)}");
                        st.frames++;
                        if (wb.depth * 1000 > st.bodyBefore) { st.bodyBefore = wb.depth * 1000; st.whereBefore = wb.where + "@" + k; }
                        if (wa.depth * 1000 > st.bodyAfter) { st.bodyAfter = wa.depth * 1000; st.whereAfter = wa.where + "@" + k; }
                        st.clothBefore = Mathf.Max(st.clothBefore, wcb.depth * 1000); st.clothAfter = Mathf.Max(st.clothAfter, wca.depth * 1000);
                        if (wb.depth * 1000 > FailMm) st.bodyFailBefore++; if (wa.depth * 1000 > FailMm) st.bodyFailAfter++;
                        if (wcb.depth * 1000 > FailMm) st.clothFailBefore++; if (wca.depth * 1000 > FailMm) st.clothFailAfter++;
                        if (k % 40 == 39) yield return null;
                    }
                    // contact drift: the strings / club head at the clip's contact time, BEFORE vs AFTER (single exact samples)
                    if (j.contact >= 0 || j.club != null)
                    {
                        float tc = j.contact >= 0 ? j.contact : GolfImpact(c, j, hz);
                        Pose(c, j, tc, Mode.Before, 0); var pb = HeadPoint(c);
                        c.safety.clearance.Reset(); Pose(c, j, tc, Mode.After, 0); var pa = HeadPoint(c);
                        st.contactDrift = pb.HasValue && pa.HasValue ? Vector3.Distance(pb.Value, pa.Value) * 1000 : -1;
                    }
                    // pops and flips against RAW
                    for (int k = 1; k <= n; k++)
                        for (int a = 0; a < 4; a++)
                        {
                            float raw = Quaternion.Angle(rawQ[k - 1, a], rawQ[k, a]) * hz, aft = Quaternion.Angle(aftQ[k - 1, a], aftQ[k, a]) * hz;
                            if (a < 2) { st.rawPeakShoulder = Mathf.Max(st.rawPeakShoulder, raw); st.afterPeakShoulder = Mathf.Max(st.afterPeakShoulder, aft); }
                            else { st.rawPeakElbow = Mathf.Max(st.rawPeakElbow, raw); st.afterPeakElbow = Mathf.Max(st.afterPeakElbow, aft); }
                        }
                    for (int k = 1; k <= n; k++)
                        for (int a = 0; a < 4; a++)
                        {
                            float aft = Quaternion.Angle(aftQ[k - 1, a], aftQ[k, a]) * hz, raw = Quaternion.Angle(rawQ[k - 1, a], rawQ[k, a]) * hz;
                            float peak = a < 2 ? st.rawPeakShoulder : st.rawPeakElbow;
                            // NO_POP (coordinator rule, 2026-10-18): a spike is a speed over max(2 x the clip's own peak, 60 deg/s), so a
                            // near-still clip (Ready, Idle: peaks of a few deg/s) is not failed by any visible correction at all
                            if (aft > Mathf.Max(2 * peak, PopFloor) && aft > raw + 1) st.popFrames++;
                            float ratio = aft / Mathf.Max(PopFloor / 2, peak);
                            if (ratio > st.popRatio) { st.popRatio = ratio; st.popAt = $"{(a % 2 == 0 ? "L" : "R")}{(a < 2 ? "shoulder" : "elbow")}@{k} {aft:0}deg/s raw {raw:0} peak {peak:0}"; }
                        }
                    for (int k = 0; k <= n; k++)
                        for (int a = 0; a < 2; a++)
                            if (bend[k, a] > 20 && rawHinge[k, a].sqrMagnitude > 1e-8f && aftHinge[k, a].sqrMagnitude > 1e-8f && Vector3.Angle(rawHinge[k, a], aftHinge[k, a]) > 90) { st.flips++; if (st.flips <= 6) st.flipAt += (a == 0 ? "L" : "R") + k + " "; }
                    stats.Add(st); j.Close();
                    Debug.Log($"[SweepProf] per frame ms: bake {prof[0] / (n + 1):0.0} grid {prof[1] / (n + 1):0.0} armq {prof[2] / (n + 1):0.0} propq {prof[3] / (n + 1):0.0}"); Array.Clear(prof, 0, prof.Length);
                    Debug.Log($"[Sweep] {c.name} {j.name}: {n + 1} frames BODY {st.bodyBefore:0.0}->{st.bodyAfter:0.0} mm ({st.whereBefore} -> {st.whereAfter}) CLOTH {st.clothBefore:0.0}->{st.clothAfter:0.0} fail frames {st.bodyFailBefore + st.clothFailBefore}->{st.bodyFailAfter + st.clothFailAfter} drift {st.contactDrift:0.00} pop x{st.popRatio:0.00} flips {st.flips}");
                    yield return null;
                }
                // worst frames of this context (BEFORE), rendered BEFORE / AFTER from one camera at the deepest point
                var worst = rows.OrderByDescending(r => withBefore ? r.before.Worst : r.after.Worst).GroupBy(r => r.clip).Select(g => g.First()).Take(worstN).ToList();
                if (render)
                    foreach (var r in worst)
                    {
                        var j = Jobs(c).First(x => x.name == r.clip); Props(c, j);
                        var h = r.before.WorstHit(); string tag = $"{c.name}_{San(r.clip)}_{r.frame:000}";
                        var focus = h.p; var outward = h.normal.sqrMagnitude > .5f ? h.normal : Vector3.forward;
                        var from = focus + (outward * .9f + Vector3.up * .25f).normalized * .9f;
                        if (from.y < .15f) from.y = .15f;
                        Pose(c, j, r.t, Mode.Before, 0); string pb = Path.Combine(outDir, tag + "_before.png"); Shot(cam, from, focus, pb);
                        c.safety.clearance.Reset();
                        // AFTER as played: re-run the clip up to this frame so the smoothing state is the played one
                        for (int k = 0; k <= r.frame; k++) Pose(c, j, Mathf.Min(j.clip.length, k / hz), Mode.After, k == 0 ? 0 : 1 / hz);
                        Shot(cam, from, focus, Path.Combine(outDir, tag + "_after.png"));
                        if (Env("SWEEP_PROXYVIS", "0") == "1")
                        {
                            Pose(c, j, r.t, Mode.Before, 0);
                            var vis = ProxyMesh(c.safety.clearance); Shot(cam, from, focus, Path.Combine(outDir, tag + "_proxy.png")); Object.DestroyImmediate(vis);
                        }
                        worstAll.Add((r, tag));
                        yield return null;
                    }
                WriteTracks(c, outDir);
                Object.Destroy(c.root); yield return null;
            }
            File.WriteAllText(Path.Combine(outDir, "sweep.csv"), csv.ToString());
            var js = new StringBuilder("[\n");
            foreach (var s in stats)
                js.Append($"{{\"ctx\":\"{s.ctx}\",\"clip\":\"{s.clip}\",\"frames\":{s.frames},\"bodyBefore\":{F(s.bodyBefore)},\"bodyAfter\":{F(s.bodyAfter)},\"clothBefore\":{F(s.clothBefore)},\"clothAfter\":{F(s.clothAfter)},\"whereBefore\":\"{s.whereBefore}\",\"whereAfter\":\"{s.whereAfter}\",\"bodyFailBefore\":{s.bodyFailBefore},\"bodyFailAfter\":{s.bodyFailAfter},\"clothFailBefore\":{s.clothFailBefore},\"clothFailAfter\":{s.clothFailAfter},\"contactDrift\":{F(s.contactDrift)},\"rawPeakShoulder\":{F(s.rawPeakShoulder)},\"afterPeakShoulder\":{F(s.afterPeakShoulder)},\"rawPeakElbow\":{F(s.rawPeakElbow)},\"afterPeakElbow\":{F(s.afterPeakElbow)},\"popFrames\":{s.popFrames},\"popRatio\":{F(s.popRatio)},\"popAt\":\"{s.popAt}\",\"flips\":{s.flips},\"flipAt\":\"{s.flipAt.Trim()}\"}},\n");
            File.WriteAllText(Path.Combine(outDir, "clips.json"), js.ToString().TrimEnd(',', '\n') + "\n]\n");
            costs.Sort();
            float P(float q) => costs.Count == 0 ? 0 : costs[Mathf.Clamp((int)(q * (costs.Count - 1)), 0, costs.Count - 1)];
            var sum = $"{{\"grow\":{F(grow)},\"hz\":{F(hz)},\"clips\":{stats.Count},\"frames\":{stats.Sum(s => s.frames)},\"bodyFailFramesBefore\":{stats.Sum(s => s.bodyFailBefore)},\"bodyFailFramesAfter\":{stats.Sum(s => s.bodyFailAfter)},\"clothFailFramesBefore\":{stats.Sum(s => s.clothFailBefore)},\"clothFailFramesAfter\":{stats.Sum(s => s.clothFailAfter)},\"maxContactDrift\":{F(stats.Count == 0 ? 0 : stats.Max(s => s.contactDrift))},\"popFrames\":{stats.Sum(s => s.popFrames)},\"flips\":{stats.Sum(s => s.flips)},\"solverMsMean\":{(costs.Count == 0 ? 0 : costs.Average()).ToString("0.####", CultureInfo.InvariantCulture)},\"solverMsP50\":{P(.5f).ToString("0.####", CultureInfo.InvariantCulture)},\"solverMsP95\":{P(.95f).ToString("0.####", CultureInfo.InvariantCulture)},\"solverMsP99\":{P(.99f).ToString("0.####", CultureInfo.InvariantCulture)},\"solverMsMax\":{P(1).ToString("0.####", CultureInfo.InvariantCulture)},\"worst\":[{string.Join(",", worstAll.OrderByDescending(w => w.r.before.Worst).Select(w => $"{{\"tag\":\"{w.img}\",\"ctx\":\"{w.r.ctx}\",\"clip\":\"{w.r.clip}\",\"frame\":{w.r.frame},\"before\":{F(w.r.before.Worst * 1000)},\"beforeWhere\":\"{w.r.before.WorstHit().where}\",\"after\":{F(w.r.after.Worst * 1000)},\"afterWhere\":\"{w.r.after.WorstHit().where}\"}}"))}]}}";
            File.WriteAllText(Path.Combine(outDir, "summary.json"), sum);
            if (Env("SWEEP_BAKE", "0") == "1") { HeroClearanceBake.Check(Path.Combine(outDir, "bake"), true); Debug.Log("[Sweep] bake check written to " + Path.Combine(outDir, "bake")); }
            Debug.Log("[Sweep] done " + outDir + " " + sum.Substring(0, Mathf.Min(600, sum.Length)));
        }

        static void DebugHit(Ctx c, Hit h)
        {
            if (h.depth <= 0) return;
            var T = c.truth; c.safety.clearance.proxy.Refresh();
            float pd = c.safety.Depth(h.p, 0, out var push); string which = "";
            foreach (var cap in c.safety.clearance.proxy.capsules) if (cap != null && Mathf.Abs(HeroClearanceProxy.Depth(cap, h.p, true, out _) - pd) < 1e-5f) which = cap.name;
            var sb = new StringBuilder($"[SweepDebug] {h.where} depth {h.depth * 1000:0.0} p {h.p:F3} q {h.q:F3} n {h.normal:F2} cloth {h.cloth} | proxy depth {pd * 1000:0.0} mm in {which}\n");
            if (!h.cloth)
            {
                var bw = T.body.sharedMesh.boneWeights; var bones = T.body.bones;
                for (int e = 0; e < 3; e++)
                {
                    int v = T.fullTris[h.tri * 3 + e]; var w = bw[v];
                    string N(int i) => i >= 0 && i < bones.Length && bones[i] ? bones[i].name : "null" + i;
                    sb.Append($"  v{v} dom {T.vDom[v]} {N(w.boneIndex0)}:{w.weight0:0.00} {N(w.boneIndex1)}:{w.weight1:0.00} {N(w.boneIndex2)}:{w.weight2:0.00} {N(w.boneIndex3)}:{w.weight3:0.00} bv {T.bv[v]:F3} bn {T.bn[v]:F2}\n");
                }
            }
            Debug.Log(sb.ToString());
        }
        /// The fitted proxy (garment table) as an opaque lattice, arms excluded: a hand drawn inside it is cut by it.
        static GameObject ProxyMesh(HeroClearance clr)
        {
            var go = new GameObject("Proxy vis"); clr.proxy.Refresh();
            var mat = new Material(Shader.Find("Universal Render Pipeline/Unlit")); mat.SetColor("_BaseColor", new Color(.2f, .85f, .9f));
            foreach (var cap in clr.proxy.capsules)
            {
                if (cap == null || cap.part == HeroClearanceProxy.Part.UpperArm || cap.part == HeroClearanceProxy.Part.Forearm || cap.part == HeroClearanceProxy.Part.Hand || cap.part == HeroClearanceProxy.Part.Finger) continue;
                var pts = clr.proxy.SurfacePoints(cap, true).ToArray(); var tris = new List<int>();
                for (int r = 0; r + 1 < cap.Rows; r++) for (int q = 0; q < cap.M; q++)
                    {
                        int a = r * cap.M + q, b = r * cap.M + (q + 1) % cap.M, c2 = (r + 1) * cap.M + q, d = (r + 1) * cap.M + (q + 1) % cap.M;
                        tris.AddRange(new[] { a, c2, b, b, c2, d, a, b, c2, b, d, c2 });   // both sides
                    }
                var m = new Mesh { vertices = pts, triangles = tris.ToArray() };
                var o = new GameObject(cap.name); o.transform.SetParent(go.transform, false);
                o.AddComponent<MeshFilter>().sharedMesh = m; o.AddComponent<MeshRenderer>().sharedMaterial = mat;
            }
            return go;
        }
        static string San(string s) => new string(s.Select(ch => char.IsLetterOrDigit(ch) ? ch : '_').ToArray());
        static Vector3? HeadPoint(Ctx c)
        {
            if (!c.golf && c.look.racketGrip) return c.look.racketGrip.TransformPoint(c.look.stringCentreLocal);
            var p = c.safety.clearance.HeldPropAny(); if (p == null) return null;
            Vector3 far = p.local[0]; foreach (var l in p.local) if (Vector3.Dot(l, p.axisLocal) > Vector3.Dot(far, p.axisLocal)) far = l;
            return p.grip.TransformPoint(far);
        }
        /// Golf has no authored contact time in the clip: the club head's fastest frame.
        static float GolfImpact(Ctx c, ClipJob j, float hz)
        {
            float best = 0, bestT = 0; Vector3? prev = null; int n = Mathf.CeilToInt(j.clip.length * hz);
            for (int k = 0; k <= n; k++)
            {
                float t = Mathf.Min(j.clip.length, k / hz); Pose(c, j, t, Mode.Raw, 0); var p = HeadPoint(c);
                if (prev.HasValue && p.HasValue) { float v = (p.Value - prev.Value).magnitude; if (v > best) { best = v; bestT = t; } }
                prev = p;
            }
            return bestT;
        }
        static void Shot(Camera cam, Vector3 from, Vector3 at, string path, int w = 1920, int h = 1080)
        {
            cam.transform.SetPositionAndRotation(from, Quaternion.LookRotation(at - from)); cam.fieldOfView = 34; cam.aspect = w / (float)h;
            var skins = Object.FindObjectsByType<SkinnedMeshRenderer>(FindObjectsSortMode.None).Where(s => s.enabled && s.gameObject.activeInHierarchy).ToArray();
            var copies = new GameObject[skins.Length]; var meshes = new Mesh[skins.Length];
            for (int i = 0; i < skins.Length; i++)
            {
                var skin = skins[i]; var mesh = new Mesh(); skin.BakeMesh(mesh); meshes[i] = mesh;
                var copy = new GameObject("Baked proof"); copies[i] = copy; copy.transform.SetParent(skin.transform, false);
                copy.AddComponent<MeshFilter>().sharedMesh = mesh; copy.AddComponent<MeshRenderer>().sharedMaterials = skin.sharedMaterials; skin.enabled = false;
            }
            var rt = RenderTexture.GetTemporary(w, h, 24, RenderTextureFormat.ARGB32, RenderTextureReadWrite.Default, 4);
            cam.targetTexture = rt; cam.Render(); var prev = RenderTexture.active; RenderTexture.active = rt;
            var tex = new Texture2D(w, h, TextureFormat.RGB24, false); tex.ReadPixels(new Rect(0, 0, w, h), 0, 0); tex.Apply();
            File.WriteAllBytes(path, tex.EncodeToPNG()); Object.DestroyImmediate(tex);
            RenderTexture.active = prev; cam.targetTexture = null; RenderTexture.ReleaseTemporary(rt);
            for (int i = 0; i < skins.Length; i++) { skins[i].enabled = true; Object.DestroyImmediate(copies[i]); Object.DestroyImmediate(meshes[i]); }
        }
    }
}
