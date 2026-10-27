#if UNITY_EDITOR
// HEROLOD COVER FIX (2026-10-26): why the HeroLod copies of "(kit v2 cover)" bodies drew dark streaks / black faces, and proof of the fix.
// Clone only:  HLF_OUT=<dir> [HLF_LEVELS=1,2] GOLF_MUTE=1 Unity -projectPath <clone> -executeMethod GolfArcade.EditorTools.HeroLodCoverProbe.Run
// Opens Bowling.unity, spawns the bowling-kit heroes (HeroLodExempt removed) and the tennis heroes beside the venue, waits for their LODs,
// then writes report.txt (per part and level: vertex attributes, flipped triangles, border length, proxy state) and stills
// <hero>_<view>_off.jpg (CHARACTER_LOD=0) / _L1.jpg / _L2.jpg (CHARACTER_LOD_FORCE=1 / 2).
using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text;
using GolfArcade.CharacterLod;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using Object = UnityEngine.Object;

namespace GolfArcade.EditorTools
{
    [InitializeOnLoad]
    public static class HeroLodCoverProbe
    {
        const string Key = "HeroLodCoverProbe";
        static IEnumerator job; static int lastFrame = -1, started = -1;
        static HeroLodCoverProbe() { EditorApplication.update += Tick; }

        public static void Run()
        {
            var o = Environment.GetEnvironmentVariable("HLF_OUT"); if (string.IsNullOrEmpty(o)) throw new ArgumentException("HLF_OUT");
            Directory.CreateDirectory(o); SessionState.SetString(Key + "out", Path.GetFullPath(o)); SessionState.SetBool(Key, true);
            EditorUtility.audioMasterMute = true;
            EditorSceneManager.OpenScene("Assets/Scenes/Bowling.unity"); EditorApplication.isPlaying = true;
        }

        static string Out => SessionState.GetString(Key + "out", "/tmp/hlf");
        static readonly StringBuilder report = new();
        static void Log(string s) { Debug.Log("[HeroLodCover] " + s); report.AppendLine(s); File.WriteAllText(Path.Combine(Out, "report.txt"), report.ToString()); }

        static void Tick()
        {
            if (!SessionState.GetBool(Key, false)) return;
            if (!EditorUtility.audioMasterMute) EditorUtility.audioMasterMute = true;
            if (!EditorApplication.isPlaying) return;
            if (AudioListener.volume != 0) AudioListener.volume = 0;
            if (Time.frameCount == lastFrame) return; lastFrame = Time.frameCount;
            if (started < 0) started = Time.frameCount;
            var game = Object.FindFirstObjectByType<Bowling.BowlingGame>();
            if ((!game || !game.Initialized) && Time.frameCount - started < 600) return;
            try { job ??= Main(); if (!job.MoveNext()) { SessionState.SetBool(Key, false); EditorApplication.Exit(0); } }
            catch (Exception e) { Debug.LogException(e); Log("EXCEPTION " + e); SessionState.SetBool(Key, false); EditorApplication.Exit(1); }
        }

        sealed class Hero { public string name; public GameObject go; public HeroLod lod; }

        static IEnumerator Main()
        {
            Log($"HeroLod.Enabled={HeroLod.Enabled} ForceLevel={HeroLod.ForceLevel} Version={HeroLod.Version}");
            // our own heroes beside the venue, away from the game's own bowlers
            var heroes = new List<Hero>();
            var cam0 = Camera.main; var basePos = cam0 ? cam0.transform.position : Vector3.zero;
            for (int i = 0; i < 4; i++)
            {
                bool female = (i & 1) == 1, bowling = i < 2;
                var at = new Vector3(basePos.x - 6 + i * 4f, 0, basePos.z - 6);
                GameObject go;
                if (bowling)
                {
                    var bh = Bowling.BowlingHero.Spawn(null, female, at, 180);
                    foreach (var ex in bh.GetComponentsInChildren<HeroLodExempt>(true)) Object.DestroyImmediate(ex);
                    go = bh.gameObject;
                }
                else
                {
                    // like BowlingHero.Spawn: a root placed in the world, the prefab at its origin (the hero's own systems keep the prefab's local pose)
                    go = new GameObject(); go.transform.SetPositionAndRotation(at, Quaternion.Euler(0, 180, 0));
                    var hero = Object.Instantiate(Tennis.TennisCustomization.HeroBase(female), go.transform, false);
                    hero.transform.localPosition = Vector3.zero; hero.transform.localRotation = Quaternion.identity;
                    Hub.HubHeroAnimator.Attach(hero);
                }
                go.name = (bowling ? "Bowling" : "Tennis") + (female ? "F" : "M");
                heroes.Add(new Hero { name = go.name, go = go });
            }
            // wait for HeroLodBoot to attach and every part's LODs to exist
            float t0 = Time.realtimeSinceStartup;
            while (Time.realtimeSinceStartup - t0 < 120)
            {
                foreach (var h in heroes) if (!h.lod) h.lod = h.go.GetComponentInChildren<HeroLod>();
                if (heroes.All(h => h.lod && h.lod.Ready)) break;
                yield return null;
            }
            for (int i = 0; i < 30; i++) yield return null;
            Log($"ready after {Time.realtimeSinceStartup - t0:0.0}s cacheHits={HeroLodLibrary.CacheHits} misses={HeroLodLibrary.CacheMisses}");
            var levels = (Environment.GetEnvironmentVariable("HLF_LEVELS") ?? "1,2").Split(',').Select(int.Parse).ToArray();
            Time.timeScale = 0;   // freeze the pose for the stills
            foreach (var h in heroes)
            {
                if (!h.lod) { Log(h.name + ": NO HeroLod"); continue; }
                Log($"== {h.name} ready={h.lod.Ready}");
                foreach (var lv in levels)
                {
                    HeroLod.ForceLevel = lv; yield return null; yield return null;
                    Inspect(h, lv);
                }
            }
            HeroLod.ForceLevel = -1;
            if (Environment.GetEnvironmentVariable("HLF_SEQ") == "1") { var sq = Seq(heroes); while (sq.MoveNext()) yield return sq.Current; }
            if (Environment.GetEnvironmentVariable("HLF_AB") == "1") { var ab = AB(heroes); while (ab.MoveNext()) yield return ab.Current; }
            // stills
            var camGo = new GameObject("HLF cam"); var cam = camGo.AddComponent<Camera>(); cam.enabled = false; cam.fieldOfView = 26; cam.nearClipPlane = .05f; cam.farClipPlane = 300;
            var rt = new RenderTexture(1200, 1200, 24, RenderTextureFormat.ARGB32) { antiAliasing = 4 };
            foreach (var h in Environment.GetEnvironmentVariable("HLF_STILLS") == "0" ? new List<Hero>() : heroes)
            {
                var look = h.go.GetComponentInChildren<Tennis.MatchHeroLook>();
                var head = look.Bone(HumanBodyBones.Head); var chest = look.Bone(HumanBodyBones.Chest) ? look.Bone(HumanBodyBones.Chest) : look.Bone(HumanBodyBones.Spine);
                var fwd = h.go.transform.forward; var right = h.go.transform.right;
                var views = new (string name, Vector3 pos, Vector3 target)[]
                {
                    ("face", head.position + fwd * .75f + Vector3.up * .05f, head.position + Vector3.up * .05f),
                    ("body", chest.position + fwd * 3.6f + Vector3.up * .1f - right * .6f, chest.position - Vector3.up * .3f),
                    ("side", chest.position + right * 2.8f + fwd * .9f, chest.position - Vector3.up * .3f),
                };
                foreach (var v in views)
                {
                    cam.transform.SetPositionAndRotation(v.pos, Quaternion.LookRotation(v.target - v.pos));
                    foreach (var mode in new[] { -1 }.Concat(levels))
                    {
                        HeroLod.Enabled = mode >= 0; HeroLod.ForceLevel = Math.Max(0, mode);
                        yield return null; yield return null;
                        var tag = mode < 0 ? "off" : "L" + mode;
                        Save(Grab(cam, rt), $"{h.name}_{v.name}_{tag}.jpg");
                        Log($"still {h.name}_{v.name}_{tag} level={h.lod.Level} originalsOnly={h.lod.OriginalsOnly}");
                    }
                }
            }
            HeroLod.Enabled = true; HeroLod.ForceLevel = -1; Time.timeScale = 1;
            Log("done");
        }

        /// Body LOD2 rebuilt with Compact variants (blendshape normal/tangent deltas, bone weights), face still per variant.
        static IEnumerator AB(List<Hero> heroes)
        {
            var camGo = new GameObject("HLF ab cam"); var cam = camGo.AddComponent<Camera>(); cam.enabled = false; cam.fieldOfView = 26; cam.nearClipPlane = .05f;
            var rt = new RenderTexture(800, 800, 24, RenderTextureFormat.ARGB32) { antiAliasing = 4 };
            HeroLod.ForceLevel = 2;
            foreach (var h in heroes)
            {
                var list = (IList)partsField.GetValue(h.lod); object body = null;
                foreach (var p in list) { var r = (Renderer)p.GetType().GetField("renderer").GetValue(p); if (r && r.name.StartsWith("Body")) body = p; }
                if (body == null) continue;
                var t = body.GetType(); var lod0 = (Mesh)t.GetField("lod0").GetValue(body); var lods = (Mesh[])t.GetField("lods").GetValue(body);
                var orig = lods[2]; var sk = (SkinnedMeshRenderer)t.GetField("renderer").GetValue(body);
                // the triangle lists of LOD2 in source indices: map lod vertices back by their (position, uv0, normal)
                Dump(lod0, Path.Combine(Out, $"mesh_{h.name}_src.bin")); Dump(orig, Path.Combine(Out, $"mesh_{h.name}_lod2.bin"));
                if (lods[1]) Dump(lods[1], Path.Combine(Out, $"mesh_{h.name}_lod1.bin"));
                var tris = SourceTris(lod0, orig);
                ShapeStats(lod0);
                WeightExample(lod0, orig);
                var look = h.go.GetComponentInChildren<Tennis.MatchHeroLook>(); var head = look.Bone(HumanBodyBones.Head); var fwd = h.go.transform.forward;
                cam.transform.SetPositionAndRotation(head.position + fwd * .75f + Vector3.up * .05f, Quaternion.LookRotation(-fwd));
                Save(Grab(cam, rt), $"AB_{h.name}_orig.jpg");
                { var fresh = Variant(lod0, tris, 0, true); Log($"AB {h.name} orig vs fresh: {MeshDiff(orig, fresh)}"); Object.Destroy(fresh); }
                foreach (var (name, shapes, weights) in new[] { ("asis", 0, true), ("shapesNullNT", 1, true), ("shapesNone", 2, true) })
                {
                    var m = Variant(lod0, tris, shapes, weights);
                    lods[2] = m; yield return null; yield return null; yield return null;
                    Save(Grab(cam, rt), $"AB_{h.name}_{name}.jpg"); Log($"AB {h.name} {name} attrs={string.Join(",", m.GetVertexAttributes().Select(Desc))}");
                }
                lods[2] = orig; yield return null; yield return null; yield return null;
                Save(Grab(cam, rt), $"AB_{h.name}_origAgain.jpg");
            }
            HeroLod.ForceLevel = -1;
        }
        /// Level toggles as the stills step and the game do them: which transition turns the proxy skin black?
        static IEnumerator Seq(List<Hero> heroes)
        {
            var camGo = new GameObject("HLF seq cam"); var cam = camGo.AddComponent<Camera>(); cam.enabled = false; cam.fieldOfView = 26; cam.nearClipPlane = .05f;
            var rt = new RenderTexture(600, 600, 24, RenderTextureFormat.ARGB32) { antiAliasing = 4 };
            var steps = new List<(string name, Action set, int frames)>
            {
                ("L2steady", () => { HeroLod.Enabled = true; HeroLod.ForceLevel = 2; }, 20),
                ("off", () => { HeroLod.Enabled = false; }, 3),
                ("L2afterOff", () => { HeroLod.Enabled = true; HeroLod.ForceLevel = 2; }, 3),
                ("L2afterOff+30", () => { }, 30),
                ("L1", () => { HeroLod.ForceLevel = 1; }, 3),
                ("L2afterL1", () => { HeroLod.ForceLevel = 2; }, 3),
                ("L0", () => { HeroLod.ForceLevel = 0; }, 3),
                ("L2afterL0", () => { HeroLod.ForceLevel = 2; }, 3),
                ("L1afterL2", () => { HeroLod.ForceLevel = 1; }, 3),
                ("L1+60", () => { }, 60),
                ("heroInactive", () => { foreach (var hh in heroes) hh.go.SetActive(false); }, 3),
                ("L1reactivated", () => { foreach (var hh in heroes) hh.go.SetActive(true); }, 3),
                ("L2reactivated", () => { HeroLod.ForceLevel = 2; }, 3),
            };
            foreach (var ts in new[] { 0f, 1f })
            {
                Time.timeScale = ts;
                foreach (var h in heroes)
                {
                    var look = h.go.GetComponentInChildren<Tennis.MatchHeroLook>(); var head = look.Bone(HumanBodyBones.Head); var fwd = h.go.transform.forward;
                    int k = 0;
                    foreach (var st in steps)
                    {
                        st.set(); for (int i = 0; i < st.frames; i++) yield return null;
                        if (!h.go.activeSelf) { Log($"SEQ {h.name} {st.name} (inactive)"); k++; continue; }
                        cam.transform.SetPositionAndRotation(head.position + fwd * .75f + Vector3.up * .05f, Quaternion.LookRotation(-fwd));
                        Save(Grab(cam, rt), $"SEQ_t{ts}_{h.name}_{k++:00}_{st.name}.jpg");
                        Log($"SEQ t{ts} {h.name} {st.name} level={h.lod.Level} {ProxyState(h)}");
                    }
                }
            }
            HeroLod.Enabled = true; HeroLod.ForceLevel = -1; Time.timeScale = 0;
        }
        static string ProxyState(Hero h)
        {
            var sb = new StringBuilder();
            foreach (var p in (IList)partsField.GetValue(h.lod))
            {
                var t = p.GetType(); var r = (Renderer)t.GetField("renderer").GetValue(p); if (!r || !r.name.StartsWith("Body")) continue;
                var x = (SkinnedMeshRenderer)t.GetField("proxySkin").GetValue(p); var o = (SkinnedMeshRenderer)r;
                sb.Append($"orig off={o.forceRenderingOff} upd={o.updateWhenOffscreen} w=[");
                for (int i = 0; i < o.sharedMesh.blendShapeCount; i++) sb.Append($"{o.GetBlendShapeWeight(i):0.#},");
                if (x) { sb.Append($"] proxy en={x.enabled} mesh={(x.sharedMesh ? x.sharedMesh.vertexCount : -1)} w=["); for (int i = 0; i < x.sharedMesh.blendShapeCount; i++) sb.Append($"{x.GetBlendShapeWeight(i):0.#},"); sb.Append($"] vis={x.isVisible} bounds={x.bounds.size}"); }
            }
            return sb.ToString();
        }

        /// Where two meshes differ: vertex streams, indices, bind poses, skin weights, blendshape frames.
        static string MeshDiff(Mesh a, Mesh b)
        {
            var sb = new StringBuilder();
            if (a.vertexCount != b.vertexCount) return $"vertexCount {a.vertexCount}/{b.vertexCount}";
            using (var da = Mesh.AcquireReadOnlyMeshData(a)) using (var db = Mesh.AcquireReadOnlyMeshData(b))
            {
                for (int s = 0; s < da[0].vertexBufferCount; s++)
                {
                    var x = da[0].GetVertexData<byte>(s); var y = db[0].GetVertexData<byte>(s); int diff = 0;
                    if (x.Length != y.Length) { sb.Append($" stream{s} len {x.Length}/{y.Length}"); continue; }
                    for (int i = 0; i < x.Length; i++) if (x[i] != y[i]) diff++;
                    sb.Append($" stream{s} bytesDiff={diff}");
                }
            }
            int idiff = 0; for (int s = 0; s < a.subMeshCount; s++) { var x = a.GetTriangles(s); var y = b.GetTriangles(s); if (x.Length != y.Length) idiff += 1000000; else for (int i = 0; i < x.Length; i++) if (x[i] != y[i]) idiff++; }
            sb.Append($" indexDiff={idiff}");
            var ba = a.bindposes; var bb = b.bindposes; int bpd = 0; for (int i = 0; i < Math.Min(ba.Length, bb.Length); i++) if (ba[i] != bb[i]) bpd++; sb.Append($" bindposeDiff={bpd}");
            var wa = a.GetAllBoneWeights(); var wb = b.GetAllBoneWeights(); int wd = 0; if (wa.Length != wb.Length) wd = -1; else for (int i = 0; i < wa.Length; i++) if (wa[i].boneIndex != wb[i].boneIndex || wa[i].weight != wb[i].weight) wd++; sb.Append($" weightDiff={wd}");
            int n = a.vertexCount; var v1 = new Vector3[n]; var n1 = new Vector3[n]; var t1 = new Vector3[n]; var v2 = new Vector3[n]; var n2 = new Vector3[n]; var t2 = new Vector3[n];
            for (int s = 0; s < Math.Min(a.blendShapeCount, b.blendShapeCount); s++)
            {
                a.GetBlendShapeFrameVertices(s, 0, v1, n1, t1); b.GetBlendShapeFrameVertices(s, 0, v2, n2, t2); int dv = 0, dn = 0, dt = 0;
                for (int i = 0; i < n; i++) { if (v1[i] != v2[i]) dv++; if (n1[i] != n2[i]) dn++; if (t1[i] != t2[i]) dt++; }
                sb.Append($" shape{s}:{a.GetBlendShapeName(s)}/{b.GetBlendShapeName(s)} dv={dv} dn={dn} dt={dt}");
            }
            sb.Append($" bounds {a.bounds}/{b.bounds}");
            return sb.ToString();
        }
        /// Raw dump for tools/analyse.py: counts, then positions, normals, colors32, uv0..uv4 (as vec4), bone weights (4 idx + 4 w), triangles.
        static void Dump(Mesh m, string path)
        {
            using var w = new BinaryWriter(File.Create(path));
            int n = m.vertexCount; w.Write(n);
            foreach (var v in m.vertices) { w.Write(v.x); w.Write(v.y); w.Write(v.z); }
            var nr = m.normals; for (int i = 0; i < n; i++) { var v = nr.Length == n ? nr[i] : Vector3.zero; w.Write(v.x); w.Write(v.y); w.Write(v.z); }
            var c = m.colors32; for (int i = 0; i < n; i++) { var v = c.Length == n ? c[i] : new Color32(); w.Write(v.r); w.Write(v.g); w.Write(v.b); w.Write(v.a); }
            for (int ch = 0; ch < 5; ch++) { var l = new List<Vector4>(); m.GetUVs(ch, l); for (int i = 0; i < n; i++) { var v = l.Count == n ? l[i] : Vector4.zero; w.Write(v.x); w.Write(v.y); w.Write(v.z); w.Write(v.w); } }
            var bw = m.boneWeights; for (int i = 0; i < n; i++) { var b = bw.Length == n ? bw[i] : new BoneWeight(); w.Write(b.boneIndex0); w.Write(b.boneIndex1); w.Write(b.boneIndex2); w.Write(b.boneIndex3); w.Write(b.weight0); w.Write(b.weight1); w.Write(b.weight2); w.Write(b.weight3); }
            w.Write(m.subMeshCount); for (int s = 0; s < m.subMeshCount; s++) { var t = m.GetTriangles(s); w.Write(t.Length); foreach (var i in t) w.Write(i); }
        }
        static int[][] SourceTris(Mesh src, Mesh lod)
        {
            var sp = src.vertices; var sn = src.normals; var lp = lod.vertices; var ln = lod.normals;
            var map = new Dictionary<(Vector3, Vector3), int>(); for (int i = sp.Length - 1; i >= 0; i--) map[(sp[i], sn[i])] = i;
            var res = new int[lod.subMeshCount][];
            for (int s = 0; s < res.Length; s++) res[s] = lod.GetTriangles(s).Select(i => map[(lp[i], ln[i])]).ToArray();
            return res;
        }
        static void ShapeStats(Mesh m)
        {
            int n = m.vertexCount; var dv = new Vector3[n]; var dn = new Vector3[n]; var dt = new Vector3[n];
            for (int s = 0; s < m.blendShapeCount; s++)
                for (int f = 0; f < m.GetBlendShapeFrameCount(s); f++)
                {
                    m.GetBlendShapeFrameVertices(s, f, dv, dn, dt);
                    Log($"  shape {m.name.Substring(0, 4)} {s} '{m.GetBlendShapeName(s)}' f{f} w={m.GetBlendShapeFrameWeight(s, f)} |dv|max={dv.Max(v => v.magnitude):0.0000} |dn|max={dn.Max(v => v.magnitude):0.000} |dt|max={dt.Max(v => v.magnitude):0.000}");
                }
            Log($"  hasTangent={m.HasVertexAttribute(VertexAttribute.Tangent)} maxBonesPerVertex={m.GetBonesPerVertex().Max()}");
        }
        static void WeightExample(Mesh src, Mesh lod)
        {
            var sp = src.vertices; var lp = lod.vertices; var bw0 = src.boneWeights; var bw1 = lod.boneWeights; var per = src.GetBonesPerVertex(); var all = src.GetAllBoneWeights();
            var start = new int[sp.Length + 1]; for (int i = 0; i < sp.Length; i++) start[i + 1] = start[i] + per[i];
            var byPos = new Dictionary<Vector3, int>(); for (int i = 0; i < sp.Length; i++) byPos[sp[i]] = i;
            int shown = 0; double worst = 0;
            for (int j = 0; j < lp.Length && shown < 3; j++)
            {
                int i = byPos[lp[j]]; if (bw0[i].Equals(bw1[j])) continue;
                string A(BoneWeight b) => $"{b.boneIndex0}:{b.weight0:0.0000} {b.boneIndex1}:{b.weight1:0.0000} {b.boneIndex2}:{b.weight2:0.0000} {b.boneIndex3}:{b.weight3:0.0000}";
                var sb = new StringBuilder(); for (int k = start[i]; k < start[i + 1]; k++) sb.Append($"{all[k].boneIndex}:{all[k].weight:0.0000} ");
                Log($"  weights v{i}: legacy src {A(bw0[i])} | all src {sb}| lod {A(bw1[j])}"); shown++;
            }
        }
        static Mesh Variant(Mesh source, int[][] tris, int shapesMode, bool setWeights)
        {
            var m = HeroLodLibrary.Compact(source, tris);
            if (shapesMode == 0 && setWeights) return m;
            int n = source.vertexCount; var map = new int[n]; for (int i = 0; i < n; i++) map[i] = -1; var keep = new List<int>();
            foreach (var sub in tris) foreach (var i in sub) if (map[i] < 0) { map[i] = keep.Count; keep.Add(i); }
            if (!setWeights)
            {
                // rebuild without SetBoneWeights: the copied BlendWeight/BlendIndices stream only
                var src = Mesh.AcquireReadOnlyMeshData(source); var d = src[0]; var od = Mesh.AllocateWritableMeshData(1); var o = od[0];
                o.SetVertexBufferParams(keep.Count, source.GetVertexAttributes());
                for (int s = 0; s < d.vertexBufferCount; s++) { int stride = d.GetVertexBufferStride(s); if (stride == 0) continue; var f = d.GetVertexData<byte>(s); var to = o.GetVertexData<byte>(s); for (int i = 0; i < keep.Count; i++) Unity.Collections.NativeArray<byte>.Copy(f, keep[i] * stride, to, i * stride, stride); }
                int total = tris.Sum(x => x.Length); o.SetIndexBufferParams(total, IndexFormat.UInt32); var ix = o.GetIndexData<int>(); int k = 0; foreach (var sub in tris) foreach (var i in sub) ix[k++] = map[i];
                o.subMeshCount = tris.Length; int st = 0; for (int s = 0; s < tris.Length; s++) { o.SetSubMesh(s, new SubMeshDescriptor(st, tris[s].Length), MeshUpdateFlags.DontRecalculateBounds); st += tris[s].Length; }
                var nm = new Mesh { name = source.name }; Mesh.ApplyAndDisposeWritableMeshData(od, nm, MeshUpdateFlags.DontRecalculateBounds); src.Dispose();
                nm.bindposes = source.bindposes; Object.Destroy(m); m = nm;
            }
            else m.ClearBlendShapes();
            if (shapesMode != 2)
            {
                if (!setWeights || shapesMode == 1) m.ClearBlendShapes();
                var dv = new Vector3[n]; var dn = new Vector3[n]; var dt = new Vector3[n]; var sv = new Vector3[keep.Count]; var sn = new Vector3[keep.Count]; var stt = new Vector3[keep.Count];
                for (int s = 0; s < source.blendShapeCount; s++)
                    for (int f = 0; f < source.GetBlendShapeFrameCount(s); f++)
                    {
                        source.GetBlendShapeFrameVertices(s, f, dv, dn, dt);
                        for (int q = 0; q < keep.Count; q++) { sv[q] = dv[keep[q]]; sn[q] = dn[keep[q]]; stt[q] = dt[keep[q]]; }
                        m.AddBlendShapeFrame(source.GetBlendShapeName(s), source.GetBlendShapeFrameWeight(s, f), sv, shapesMode == 1 ? null : sn, shapesMode == 1 ? null : stt);
                    }
            }
            m.bounds = source.bounds; m.UploadMeshData(false);
            return m;
        }

        static Texture2D Grab(Camera cam, RenderTexture rt)
        {
            cam.targetTexture = rt; cam.Render();
            var a = RenderTexture.active; RenderTexture.active = rt;
            var t = new Texture2D(rt.width, rt.height, TextureFormat.RGB24, false); t.ReadPixels(new Rect(0, 0, rt.width, rt.height), 0, 0); t.Apply();
            RenderTexture.active = a; return t;
        }
        static void Save(Texture2D t, string name) { File.WriteAllBytes(Path.Combine(Out, name), t.EncodeToJPG(90)); Object.Destroy(t); }

        // ---------- diagnostics ----------
        static readonly FieldInfo partsField = typeof(HeroLod).GetField("parts", BindingFlags.NonPublic | BindingFlags.Instance);
        static void Inspect(Hero h, int level)
        {
            var list = (IList)partsField.GetValue(h.lod);
            foreach (var p in list)
            {
                var t = p.GetType();
                var r = (Renderer)t.GetField("renderer").GetValue(p);
                var lod0 = (Mesh)t.GetField("lod0").GetValue(p);
                var lods = (Mesh[])t.GetField("lods").GetValue(p);
                var proxy = (Renderer)t.GetField("proxy").GetValue(p);
                bool ready = (bool)t.GetField("ready").GetValue(p), failed = (bool)t.GetField("failed").GetValue(p);
                var lm = lods != null && level < lods.Length ? lods[level] : null;
                var sb = new StringBuilder($"  L{level} {(r ? r.name : "null")} [{(lod0 ? lod0.name : "null")}] ready={ready} failed={failed} hidden={(r && r.forceRenderingOff)}");
                Mesh pm = proxy is SkinnedMeshRenderer ps ? ps.sharedMesh : proxy && proxy.TryGetComponent<MeshFilter>(out var pf) ? pf.sharedMesh : null;
                sb.Append($" proxy={(proxy ? (proxy.enabled ? "on" : "off") : "none")} proxyMesh={(pm ? (pm == lm ? "lod" : pm.name) : "null")}");
                if (!lm || !lod0) { Log(sb + " (no lod mesh)"); continue; }
                sb.Append($" v {lod0.vertexCount}->{lm.vertexCount} tris {Tris(lod0)}->{Tris(lm)}");
                var a0 = lod0.GetVertexAttributes(); var a1 = lm.GetVertexAttributes();
                if (!a0.SequenceEqual(a1)) sb.Append(" ATTRS DIFFER: " + string.Join(",", a0.Select(Desc)) + " vs " + string.Join(",", a1.Select(Desc)));
                else sb.Append(" attrs=" + string.Join(",", a0.Select(Desc)));
                sb.Append(" | " + AttributeMismatch(lod0, lm));
                sb.Append($" | flipped {Flipped(lod0)}->{Flipped(lm)} border m {Border(lod0):0.000}->{Border(lm):0.000}");
                sb.Append($" | bindposes {lod0.bindposes.Length}/{lm.bindposes.Length} shapes {lod0.blendShapeCount}/{lm.blendShapeCount}");
                if (r is SkinnedMeshRenderer s0 && proxy is SkinnedMeshRenderer s1)
                    sb.Append($" bones {s0.bones.Length}/{s1.bones.Length} same={s0.bones.SequenceEqual(s1.bones)} root={(s0.rootBone == s1.rootBone)}");
                if (proxy) { var m0 = r.sharedMaterials; var m1 = proxy.sharedMaterials; sb.Append($" mats same={m0.SequenceEqual(m1)} shader={(m0.Length > 0 && m0[0] ? m0[0].shader.name : "-")}"); }
                Log(sb.ToString());
            }
        }
        static string Desc(VertexAttributeDescriptor d) => $"{d.attribute}:{d.format}x{d.dimension}@{d.stream}";
        static long Tris(Mesh m) { long t = 0; for (int s = 0; s < m.subMeshCount; s++) t += m.GetIndexCount(s) / 3; return t; }

        /// For each LOD vertex, is there a source vertex at the same position with identical attributes? Mismatch count per attribute.
        static string AttributeMismatch(Mesh src, Mesh lod)
        {
            var sp = src.vertices; var lp = lod.vertices;
            var byPos = new Dictionary<Vector3, List<int>>();
            for (int i = 0; i < sp.Length; i++) { if (!byPos.TryGetValue(sp[i], out var l)) byPos[sp[i]] = l = new List<int>(1); l.Add(i); }
            var checks = new List<(string name, Func<int, int, bool> eq)>();
            { var a = src.normals; var b = lod.normals; if (a.Length == sp.Length && b.Length == lp.Length) checks.Add(("normal", (i, j) => a[i] == b[j])); else checks.Add(($"normal(len {a.Length}/{b.Length})", (i, j) => false)); }
            { var a = src.tangents; var b = lod.tangents; if (a.Length == sp.Length && b.Length == lp.Length) checks.Add(("tangent", (i, j) => a[i] == b[j])); }
            { var a = src.colors32; var b = lod.colors32; if (a.Length == sp.Length && b.Length == lp.Length) checks.Add(("color", (i, j) => a[i].r == b[j].r && a[i].g == b[j].g && a[i].b == b[j].b && a[i].a == b[j].a)); }
            for (int ch = 0; ch < 8; ch++)
            {
                if (!src.HasVertexAttribute(VertexAttribute.TexCoord0 + ch)) continue;
                var a = new List<Vector4>(); var b = new List<Vector4>(); src.GetUVs(ch, a); lod.GetUVs(ch, b);
                if (b.Count != lp.Length) { checks.Add(("uv" + ch + "(missing)", (i, j) => false)); continue; }
                checks.Add(("uv" + ch, (i, j) => a[i] == b[j]));
            }
            var bw0 = src.boneWeights; var bw1 = lod.boneWeights;
            if (bw0.Length == sp.Length && bw1.Length == lp.Length) checks.Add(("weights", (i, j) => bw0[i].Equals(bw1[j])));
            var bad = new int[checks.Count]; int unmatchedPos = 0;
            for (int j = 0; j < lp.Length; j++)
            {
                if (!byPos.TryGetValue(lp[j], out var cand)) { unmatchedPos++; continue; }
                for (int c = 0; c < checks.Count; c++) { bool any = false; foreach (var i in cand) if (checks[c].eq(i, j)) { any = true; break; } if (!any) bad[c]++; }
            }
            var sb = new StringBuilder($"posMiss {unmatchedPos}");
            for (int c = 0; c < checks.Count; c++) sb.Append($" {checks[c].name}:{bad[c]}");
            return sb.ToString();
        }

        /// Triangles whose winding disagrees with their vertex normals (render as dark backfaces / holes).
        static int Flipped(Mesh m)
        {
            var v = m.vertices; var n = m.normals; if (n.Length != v.Length) return -1; int bad = 0;
            for (int s = 0; s < m.subMeshCount; s++)
            {
                var t = m.GetTriangles(s);
                for (int i = 0; i < t.Length; i += 3)
                {
                    var f = Vector3.Cross(v[t[i + 1]] - v[t[i]], v[t[i + 2]] - v[t[i]]);
                    if (Vector3.Dot(f, n[t[i]] + n[t[i + 1]] + n[t[i + 2]]) < 0) bad++;
                }
            }
            return bad;
        }

        /// Total length of edges used by one triangle only (position-welded): holes add border.
        static double Border(Mesh m)
        {
            var v = m.vertices; var id = new Dictionary<Vector3, int>(); var pid = new int[v.Length];
            for (int i = 0; i < v.Length; i++) { if (!id.TryGetValue(v[i], out var k)) id[v[i]] = k = id.Count; pid[i] = k; }
            var count = new Dictionary<long, int>(); var ends = new Dictionary<long, (int, int)>();
            for (int s = 0; s < m.subMeshCount; s++)
            {
                var t = m.GetTriangles(s);
                for (int i = 0; i < t.Length; i += 3)
                    for (int c = 0; c < 3; c++)
                    {
                        int a = t[i + c], b = t[i + (c + 1) % 3]; int pa = pid[a], pb = pid[b]; if (pa == pb) continue;
                        long key = pa < pb ? ((long)pa << 32) | (uint)pb : ((long)pb << 32) | (uint)pa;
                        count[key] = count.TryGetValue(key, out var n) ? n + 1 : 1; ends[key] = (a, b);
                    }
            }
            double len = 0; foreach (var kv in count) if (kv.Value == 1) { var (a, b) = ends[kv.Key]; len += (v[a] - v[b]).magnitude; }
            return len;
        }
    }
}
#endif
