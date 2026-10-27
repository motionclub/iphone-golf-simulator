// CHARACTER LOD (2026-10-17, character-lod chat): distance LOD for every hero (tennis, golf, plaza, party spectators).
// Self-attaching: HeroLodBoot finds each MatchHeroLook and adds a HeroLod; no hero prefab, scene or shared script is edited.
//
// For each drawn renderer under the hero (body, rigid face, garments, accessories; >= MinTriangles), once its mesh has settled
// after the build, LOD1..LOD4 are compacted copies of that mesh with fewer triangles: index-only simplification
// (HeroLodSimplifier), so every kept vertex carries its original position, skin weights, bind pose, blendshape deltas, normal and
// UV. The ORIGINAL renderers are never modified (their sharedMesh, bones, materials stay what their owners set, so every system
// that reads or re-derives hero meshes keeps seeing LOD0). At LOD0 they draw as before: close-ups and the locker are untouched.
// At LOD>0 an original is hidden with forceRenderingOff (and stops skinning) while a proxy renderer next to it draws the LOD
// copy with the original's bones, materials, shadow / layer settings, property block and blendshape weights, synced every frame.
// A proxy is never disabled, only hidden with forceRenderingOff too (10-26: a body proxy SkinnedMeshRenderer switched off and on
// again drew its skin with broken vertex data, dark streaks and black faces, until its GameObject was re-activated).
// The level follows the hero's on-screen height (largest over the rendering cameras), with hysteresis, like HeroGarmentLOD.
// Triangle lists come from Resources/CharacterLOD/HeroLodCache.bytes (keyed by a hash of the final runtime mesh) or, on a
// miss, from a worker thread; until they exist the hero simply stays at LOD0.
// Env: CHARACTER_LOD=0 disables it; CHARACTER_LOD_FORCE=0..4 pins the level (proof films and A/B runs).
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using UnityEngine;
using UnityEngine.Rendering;

namespace GolfArcade.CharacterLod
{
    [DefaultExecutionOrder(32000), DisallowMultipleComponent]
    public sealed class HeroLod : MonoBehaviour
    {
        // ---- tuning: screen height of a 1.75 m hero as a fraction of the view height ----
        /// Level l is used while the hero is below Bands[l-1] and at or above Bands[l]. At or above Bands[0] it is a close-up:
        /// LOD0, the original renderers. Golf tee view ~0.39-0.40 (LOD2, clear of the 0.46 edge plus hysteresis), far tennis player / fly-overs LOD3-4.
        public static readonly float[] Bands = { .60f, .46f, .16f, .04f };
        public const int Levels = 5;
        /// Relative: leave a level only once the height is this fraction past the band edge (a fixed margin swallowed the far bands).
        public static float Hysteresis = .07f;
        /// Triangle share and largest allowed surface error (metres, bind space) per level. 1 px of a 1.75 m hero at 1080 lines
        /// is 2.7 mm at the 0.60 band, 3.5 mm at 0.46, 10 mm at 0.16 and 40 mm at 0.04: every level stays within about a pixel.
        public static readonly double[] Ratio = { 1, .50, .30, .12, .10 };
        public static readonly double[] MaxError = { 0, .0020, .0035, .0080, .0120 };
        public const int MinTriangles = 4000;
        public const int Version = 4;                                      // bump when the simplifier or the parameters change
        public const string ProxyPrefix = "HeroLod ";

        public static bool Enabled = Environment.GetEnvironmentVariable("CHARACTER_LOD") != "0";
        /// -1 = by distance; 0..4 pins every hero (proof films / A-B runs).
        public static int ForceLevel = int.TryParse(Environment.GetEnvironmentVariable("CHARACTER_LOD_FORCE"), out var f) ? f : -1;

        public int Level { get; private set; }
        /// True when every tracked original draws itself and no proxy is on: what LOD0 must be (identity check).
        public bool OriginalsOnly => parts.All(p => !p.renderer || (!p.renderer.forceRenderingOff && (!p.proxy || p.proxy.forceRenderingOff) && p.Current == p.lod0));
        public float ScreenHeight { get; private set; }
        public bool Ready => parts.Count > 0 && parts.All(p => p.ready || p.failed);
        public IEnumerable<(Renderer renderer, int[] tris, bool ready)> Parts => parts.Select(p => (p.renderer, p.tris, p.ready));

        sealed class Part
        {
            public Renderer renderer; public MeshFilter filter; public SkinnedMeshRenderer skin;
            public Mesh lod0; public Mesh[] lods = new Mesh[Levels];
            public int[] tris = new int[Levels];
            public bool ready, failed, pending, requested;   // requested: holds a HeroLodLibrary user count (released once)
            // proxy drawing LOD>0, and what the original had before we hid it
            public Renderer proxy; public SkinnedMeshRenderer proxySkin; public MeshFilter proxyFilter;
            public bool hidden, keptOffscreen;
            public Mesh Current => filter ? filter.sharedMesh : skin.sharedMesh;
        }
        readonly List<Part> parts = new();
        int stableFrames; string lastSignature; float bornAt;
        Transform head; bool headSearched;
        bool built; int nextScan;
        static readonly List<Material> mats = new(), proxyMats = new();
        MaterialPropertyBlock block;

        void Awake() { bornAt = Time.unscaledTime; Level = 0; }

        void OnDisable() => Apply(0);
        void OnDestroy()
        {
            Apply(0);
            foreach (var p in parts) { if (p.proxy) Destroy(p.proxy.gameObject); if (p.requested) HeroLodLibrary.Release(p.lod0); }
            parts.Clear();
        }

        void LateUpdate()
        {
            if (!Enabled) { Apply(0); return; }
            // wait until the hero's build (cover, footwear, faces, correctives, accessories) has stopped changing meshes;
            // afterwards re-scan once a second, or at once when an original got a new mesh from its owner
            if (!built || Time.frameCount >= nextScan)
            {
                nextScan = Time.frameCount + 60;
                var sig = Signature();
                if (sig != lastSignature) { lastSignature = sig; stableFrames = 0; Adopt(); built = false; }
            }
            if (!built && ++stableFrames >= 12 && Time.unscaledTime - bornAt > .3f) { Build(); built = true; }
            foreach (var p in parts)
            {
                if (p.pending && HeroLodLibrary.TryGet(p.lod0, out var lods)) Finish(p, lods);
                if (!p.renderer || p.Current != p.lod0) nextScan = 0;
            }
            Apply(Choose());
        }

        // ---------- renderers ----------
        string Signature()
        {
            var sb = new System.Text.StringBuilder();
            foreach (var r in GetComponentsInChildren<Renderer>(true))
            {
                if (r.name.StartsWith(ProxyPrefix, StringComparison.Ordinal)) continue;
                Mesh m = r is SkinnedMeshRenderer s ? s.sharedMesh : r.TryGetComponent<MeshFilter>(out var mf) ? mf.sharedMesh : null;
                if (!m) continue;
                // only drawn renderers get LODs; a renderer switched on later (club change, haircut) re-triggers the scan
                if (!r.enabled || !r.gameObject.activeInHierarchy) { sb.Append('-'); continue; }
                sb.Append(m.GetInstanceID()).Append(',');
            }
            return sb.ToString();
        }

        /// Track (new) renderers and notice meshes their owners replaced: the new mesh becomes LOD0.
        void Adopt()
        {
            foreach (var r in GetComponentsInChildren<Renderer>(true))
            {
                if (!(r is SkinnedMeshRenderer) && !(r is MeshRenderer)) continue;
                if (r.name.StartsWith(ProxyPrefix, StringComparison.Ordinal)) continue;
                if (!r.enabled || !r.gameObject.activeInHierarchy) continue;   // kept if already tracked: it may come back
                var part = parts.FirstOrDefault(p => p.renderer == r);
                if (part == null)
                {
                    part = new Part { renderer = r, skin = r as SkinnedMeshRenderer, filter = r is MeshRenderer ? r.GetComponent<MeshFilter>() : null };
                    if (r is MeshRenderer && !part.filter) continue;
                    part.lod0 = part.Current; if (!Eligible(part)) continue;
                    parts.Add(part); continue;
                }
                var cur = part.Current;
                if (cur == part.lod0) continue;
                // re-derived by its owner (re-dress, accessory cover, ...): show the original, start over from its new mesh
                Show(part);
                // only a part that requested LODs holds a user count: releasing one that never did took another hero's (shared garment) LODs
                if (part.requested) HeroLodLibrary.Release(part.lod0);
                part.lod0 = cur; part.lods = new Mesh[Levels]; part.ready = part.failed = part.pending = part.requested = false;
                if (!Eligible(part)) { if (part.proxy) Destroy(part.proxy.gameObject); parts.Remove(part); }
            }
            foreach (var p in parts) if (!p.renderer && p.proxy) Destroy(p.proxy.gameObject);
            parts.RemoveAll(p => !p.renderer);
        }

        bool Eligible(Part p)
        {
            var m = p.lod0; if (!m || !m.isReadable) return false;
            // the legacy tennis distance kit (HeroGarmentLOD) swaps its own non-V2 pieces: leave those to it
            if (p.renderer.name.StartsWith("Kit_", StringComparison.Ordinal) && !Tennis.MatchHeroLook.IsKitV2(m) && GetComponent<Tennis.HeroGarmentLOD>()) return false;
            long tris = 0; for (int s = 0; s < m.subMeshCount; s++) { if (m.GetTopology(s) != MeshTopology.Triangles) return false; tris += m.GetIndexCount(s) / 3; }
            if (tris < MinTriangles) return false;
            for (int l = 0; l < Levels; l++) p.tris[l] = (int)tris;
            return true;
        }

        void Build()
        {
            foreach (var p in parts)
            {
                if (p.ready || p.failed || p.pending) continue;
                if (HeroLodLibrary.Request(p.lod0, p.skin)) p.pending = p.requested = true; else p.failed = true;
            }
        }

        void Finish(Part p, Mesh[] lods)
        {
            p.pending = false;
            if (lods == null) { p.failed = true; return; }
            p.lods = (Mesh[])lods.Clone(); p.lods[0] = p.lod0;
            for (int l = 1; l < Levels; l++) { long t = 0; for (int s = 0; s < lods[l].subMeshCount; s++) t += lods[l].GetIndexCount(s) / 3; p.tris[l] = (int)t; }
            p.ready = true;
        }

        // ---------- level ----------
        int Choose()
        {
            if (ForceLevel >= 0) return Mathf.Clamp(ForceLevel, 0, Levels - 1);
            float h = 0;
            if (!head && !headSearched) { head = FindDeep(transform, "Head"); headSearched = true; }
            Vector3 centre = head ? Vector3.Lerp(transform.position, head.position, .5f) : transform.position + Vector3.up * (.9f * transform.lossyScale.y);
            float height = 1.75f * Mathf.Abs(transform.lossyScale.y);
            int n = Camera.allCamerasCount; if (cams.Length < n) cams = new Camera[n * 2];
            Camera.GetAllCameras(cams);
            for (int i = 0; i < n; i++)
            {
                var c = cams[i]; if (!c || !c.isActiveAndEnabled || (c.cullingMask & (1 << gameObject.layer)) == 0) continue;
                float frac;
                if (c.orthographic) frac = height / (2 * Mathf.Max(1e-3f, c.orthographicSize));
                else
                {
                    var toHero = centre - c.transform.position;
                    if (Vector3.Dot(toHero, c.transform.forward) < -height) continue;   // well behind this camera
                    frac = height / (2 * Mathf.Max(.05f, toHero.magnitude) * Mathf.Tan(c.fieldOfView * .5f * Mathf.Deg2Rad));
                }
                h = Mathf.Max(h, frac);
            }
            ScreenHeight = h;
            // hysteresis: leave the current level only once past a band edge by the margin
            int raw = Band(h);
            if (raw == Level) return Level;
            return raw > Level ? Band(h * (1 + Hysteresis)) : Band(h * (1 - Hysteresis));
        }
        public static int Band(float h) { int l = 0; while (l < Bands.Length && h < Bands[l]) l++; return l; }
        static Camera[] cams = new Camera[8];

        static Transform FindDeep(Transform t, string name)
        {
            foreach (var c in t.GetComponentsInChildren<Transform>(true)) if (c.name == name) return c;
            return null;
        }

        // ---------- drawing ----------
        void Apply(int level)
        {
            Level = level;
            foreach (var p in parts)
            {
                if (!p.renderer) continue;
                if (level == 0 || !p.ready || p.Current != p.lod0 || !p.lods[level]) { Show(p); continue; }
                Proxy(p, p.lods[level]);
            }
        }

        /// The original draws again; the proxy rests (hidden, never disabled: see the header).
        void Show(Part p)
        {
            if (p.proxy && !p.proxy.forceRenderingOff) p.proxy.forceRenderingOff = true;
            if (!p.hidden || !p.renderer) return;
            p.renderer.forceRenderingOff = false;
            if (p.skin) p.skin.updateWhenOffscreen = p.keptOffscreen;
            p.hidden = false;
        }

        /// Draw `mesh` through the proxy with everything the original would use this frame; hide the original.
        void Proxy(Part p, Mesh mesh)
        {
            var r = p.renderer;
            if (!p.proxy)
            {
                var go = new GameObject(ProxyPrefix + r.name) { hideFlags = HideFlags.DontSave };
                go.transform.SetParent(r.transform, false);
                if (p.skin) { p.proxySkin = go.AddComponent<SkinnedMeshRenderer>(); p.proxy = p.proxySkin; }
                else { p.proxyFilter = go.AddComponent<MeshFilter>(); p.proxy = go.AddComponent<MeshRenderer>(); }
            }
            var x = p.proxy;
            if (x.gameObject.layer != r.gameObject.layer) x.gameObject.layer = r.gameObject.layer;
            if (p.skin)
            {
                var s = p.proxySkin;
                if (s.sharedMesh != mesh) s.sharedMesh = mesh;
                if (s.rootBone != p.skin.rootBone) s.rootBone = p.skin.rootBone;
                if (!ReferenceEquals(s.bones, null) && s.bones.Length == p.skin.bones.Length) { if (Time.frameCount % 30 == 0 && !s.bones.SequenceEqual(p.skin.bones)) s.bones = p.skin.bones; }
                else s.bones = p.skin.bones;
                s.quality = p.skin.quality; s.localBounds = p.skin.localBounds; s.updateWhenOffscreen = false;
                s.skinnedMotionVectors = p.skin.skinnedMotionVectors;
                int shapes = Mathf.Min(mesh.blendShapeCount, p.lod0.blendShapeCount);
                for (int i = 0; i < shapes; i++) { float w = p.skin.GetBlendShapeWeight(i); if (s.GetBlendShapeWeight(i) != w) s.SetBlendShapeWeight(i, w); }
            }
            else if (p.proxyFilter.sharedMesh != mesh) p.proxyFilter.sharedMesh = mesh;
            // materials (same objects, so tints applied to them follow), shadows, layers, probes, property block
            r.GetSharedMaterials(mats); x.GetSharedMaterials(proxyMats);
            if (!mats.SequenceEqual(proxyMats)) x.sharedMaterials = mats.ToArray();
            x.shadowCastingMode = r.shadowCastingMode; x.receiveShadows = r.receiveShadows;
            x.renderingLayerMask = r.renderingLayerMask; x.lightProbeUsage = r.lightProbeUsage; x.reflectionProbeUsage = r.reflectionProbeUsage;
            x.probeAnchor = r.probeAnchor ? r.probeAnchor : r.transform; x.motionVectorGenerationMode = r.motionVectorGenerationMode;
            x.allowOcclusionWhenDynamic = r.allowOcclusionWhenDynamic; x.sortingOrder = r.sortingOrder;
            if (r.HasPropertyBlock()) { block ??= new MaterialPropertyBlock(); r.GetPropertyBlock(block); x.SetPropertyBlock(block); }
            else if (x.HasPropertyBlock()) x.SetPropertyBlock(null);
            bool drawn = r.enabled && r.gameObject.activeInHierarchy;
            if (x.forceRenderingOff == drawn) x.forceRenderingOff = !drawn;
            if (!p.hidden)
            {
                p.keptOffscreen = p.skin && p.skin.updateWhenOffscreen;
                r.forceRenderingOff = true;
                if (p.skin) p.skin.updateWhenOffscreen = false;   // a hidden original must not keep skinning
                p.hidden = true;
            }
        }
    }

    /// LOD meshes shared by every hero that uses the same source mesh (garment assets are shared; runtime body meshes are not).
    public static class HeroLodLibrary
    {
        sealed class Entry { public Mesh[] lods; public int users; public Task<int[][][]> job; public bool done; }
        static readonly Dictionary<Mesh, Entry> entries = new();
        /// Computed this session, keyed by mesh hash: what the bake tool writes into the cache file.
        public static readonly Dictionary<ulong, int[][][]> Computed = new();
        public static int CacheHits, CacheMisses;

        public static bool Request(Mesh source, SkinnedMeshRenderer skin)
        {
            if (!source) return false;
            if (entries.TryGetValue(source, out var e)) { e.users++; return true; }
            e = new Entry { users = 1 }; entries[source] = e;
            try
            {
                var hash = HeroLodCache.Hash(source);
                if (HeroLodCache.TryGet(hash, source, out var cached)) { CacheHits++; e.lods = Make(source, cached); e.done = true; return true; }
                CacheMisses++;
                var input = Extract(source, skin);
                e.job = Task.Run(() =>
                {
                    var levels = new int[HeroLod.Levels][][];
                    for (int l = 1; l < HeroLod.Levels; l++) levels[l] = HeroLodSimplifier.Simplify(input, HeroLod.Ratio[l], HeroLod.MaxError[l]).submeshes;
                    return levels;
                });
                pendingHash[source] = hash;
                return true;
            }
            catch (Exception ex) { Debug.LogWarning("[HeroLod] " + source.name + ": " + ex.Message); entries.Remove(source); return false; }
        }
        static readonly Dictionary<Mesh, ulong> pendingHash = new();

        public static bool TryGet(Mesh source, out Mesh[] lods)
        {
            lods = null;
            if (!source || !entries.TryGetValue(source, out var e)) return true;   // gone: report "no LODs"
            if (!e.done)
            {
                if (e.job == null || !e.job.IsCompleted) return false;
                if (e.job.IsFaulted) { Debug.LogWarning("[HeroLod] " + source.name + ": " + e.job.Exception?.GetBaseException().Message); e.done = true; return true; }
                var levels = e.job.Result; e.lods = Make(source, levels); e.done = true;
                if (pendingHash.TryGetValue(source, out var h)) { Computed[h] = levels; pendingHash.Remove(source); }
            }
            lods = e.lods; return true;
        }

        public static void Release(Mesh source)
        {
            if (!source || !entries.TryGetValue(source, out var e)) return;
            if (--e.users > 0) return;
            if (e.lods != null) for (int l = 1; l < e.lods.Length; l++) if (e.lods[l]) UnityEngine.Object.Destroy(e.lods[l]);
            entries.Remove(source); pendingHash.Remove(source);
        }

        static Mesh[] Make(Mesh source, int[][][] levels)
        {
            var lods = new Mesh[HeroLod.Levels]; lods[0] = source;
            for (int l = 1; l < HeroLod.Levels; l++) lods[l] = Compact(source, levels[l]);
            return lods;
        }

        /// A copy of `source` holding only the vertices `tris` uses, byte for byte (every vertex stream: positions, normals,
        /// tangents, colours, UVs, skin weights), plus its bind poses, skin weights and blendshape frames for those vertices.
        public static Mesh Compact(Mesh source, int[][] tris)
        {
            int n = source.vertexCount; var map = new int[n]; for (int i = 0; i < n; i++) map[i] = -1;
            var keep = new List<int>(n / 2);
            foreach (var sub in tris) foreach (var i in sub) if (map[i] < 0) { map[i] = keep.Count; keep.Add(i); }
            int m = keep.Count;
            var mesh = new Mesh { name = source.name, hideFlags = HideFlags.DontSave };   // MatchHeroLook.IsKitV2 and friends read the name
            using (var src = Mesh.AcquireReadOnlyMeshData(source))
            {
                var d = src[0]; var outData = Mesh.AllocateWritableMeshData(1); var o = outData[0];
                o.SetVertexBufferParams(m, source.GetVertexAttributes());
                for (int s = 0; s < d.vertexBufferCount; s++)
                {
                    int stride = d.GetVertexBufferStride(s); if (stride == 0) continue;
                    var from = d.GetVertexData<byte>(s); var to = o.GetVertexData<byte>(s);
                    for (int i = 0; i < m; i++) Unity.Collections.NativeArray<byte>.Copy(from, keep[i] * stride, to, i * stride, stride);
                }
                int total = 0; foreach (var sub in tris) total += sub.Length;
                bool wide = m > 65535;
                o.SetIndexBufferParams(total, wide ? UnityEngine.Rendering.IndexFormat.UInt32 : UnityEngine.Rendering.IndexFormat.UInt16);
                if (wide) { var ix = o.GetIndexData<int>(); int k = 0; foreach (var sub in tris) foreach (var i in sub) ix[k++] = map[i]; }
                else { var ix = o.GetIndexData<ushort>(); int k = 0; foreach (var sub in tris) foreach (var i in sub) ix[k++] = (ushort)map[i]; }
                o.subMeshCount = tris.Length; int start = 0;
                for (int s = 0; s < tris.Length; s++)
                {
                    o.SetSubMesh(s, new UnityEngine.Rendering.SubMeshDescriptor(start, tris[s].Length, MeshTopology.Triangles),
                        UnityEngine.Rendering.MeshUpdateFlags.DontRecalculateBounds | UnityEngine.Rendering.MeshUpdateFlags.DontValidateIndices);
                    start += tris[s].Length;
                }
                Mesh.ApplyAndDisposeWritableMeshData(outData, mesh, UnityEngine.Rendering.MeshUpdateFlags.DontRecalculateBounds);
            }
            mesh.bindposes = source.bindposes;
            var per = source.GetBonesPerVertex();
            if (per.Length == n)
            {
                var weights = source.GetAllBoneWeights(); var start = new int[n + 1];
                for (int i = 0; i < n; i++) start[i + 1] = start[i] + per[i];
                int total = 0; foreach (var i in keep) total += per[i];
                var newPer = new Unity.Collections.NativeArray<byte>(m, Unity.Collections.Allocator.Temp);
                var newW = new Unity.Collections.NativeArray<BoneWeight1>(total, Unity.Collections.Allocator.Temp);
                int w = 0;
                for (int k = 0; k < m; k++) { int i = keep[k]; newPer[k] = per[i]; for (int j = start[i]; j < start[i + 1]; j++) newW[w++] = weights[j]; }
                mesh.SetBoneWeights(newPer, newW); newPer.Dispose(); newW.Dispose();
            }
            if (source.blendShapeCount > 0)
            {
                var dv = new Vector3[n]; var dn = new Vector3[n]; var dt = new Vector3[n];
                var sv = new Vector3[m]; var sn = new Vector3[m]; var st = new Vector3[m];
                for (int s = 0; s < source.blendShapeCount; s++)
                    for (int f = 0; f < source.GetBlendShapeFrameCount(s); f++)
                    {
                        source.GetBlendShapeFrameVertices(s, f, dv, dn, dt);
                        for (int k = 0; k < m; k++) { sv[k] = dv[keep[k]]; sn[k] = dn[keep[k]]; st[k] = dt[keep[k]]; }
                        mesh.AddBlendShapeFrame(source.GetBlendShapeName(s), source.GetBlendShapeFrameWeight(s, f), sv, sn, st);
                    }
            }
            mesh.bounds = source.bounds;
            mesh.UploadMeshData(false);   // stays readable: other systems may read hero meshes
            return mesh;
        }

        /// Positions, triangle lists and the per-vertex penalty features (skin centroid, normal, blendshape deltas).
        public static HeroLodSimplifier.Input Extract(Mesh m, SkinnedMeshRenderer skin)
        {
            var v = m.vertices; int n = v.Length;
            var pos = new float[n * 3]; for (int i = 0; i < n; i++) { pos[3 * i] = v[i].x; pos[3 * i + 1] = v[i].y; pos[3 * i + 2] = v[i].z; }
            var subs = new int[m.subMeshCount][]; for (int s = 0; s < subs.Length; s++) subs[s] = m.GetTriangles(s);
            int shapes = Math.Min(8, m.blendShapeCount);
            int fd = 3 + 3 + 3 * shapes; var f = new float[n * fd];
            var normals = m.normals;
            if (normals != null && normals.Length == n)
                for (int i = 0; i < n; i++) { f[i * fd + 3] = normals[i].x * .010f; f[i * fd + 4] = normals[i].y * .010f; f[i * fd + 5] = normals[i].z * .010f; }
            var binds = m.bindposes;
            if (binds != null && binds.Length > 0)
            {
                var bonePos = binds.Select(b => (Vector3)b.inverse.GetColumn(3)).ToArray();
                var per = m.GetBonesPerVertex(); var weights = m.GetAllBoneWeights();
                if (per.Length == n)
                {
                    int w = 0;
                    for (int i = 0; i < n; i++)
                    {
                        Vector3 c = Vector3.zero;
                        for (int k = 0; k < per[i]; k++, w++) { var bw = weights[w]; if (bw.boneIndex < bonePos.Length) c += bonePos[bw.boneIndex] * bw.weight; }
                        f[i * fd] = c.x * .05f; f[i * fd + 1] = c.y * .05f; f[i * fd + 2] = c.z * .05f;
                    }
                }
            }
            if (shapes > 0)
            {
                var dv = new Vector3[n]; var dn = new Vector3[n]; var dt = new Vector3[n];
                for (int s = 0; s < shapes; s++)
                {
                    int frame = m.GetBlendShapeFrameCount(s) - 1; if (frame < 0) continue;
                    m.GetBlendShapeFrameVertices(s, frame, dv, dn, dt);
                    for (int i = 0; i < n; i++) { int o = i * fd + 6 + 3 * s; f[o] = dv[i].x; f[o + 1] = dv[i].y; f[o + 2] = dv[i].z; }
                }
            }
            return new HeroLodSimplifier.Input { positions = pos, submeshes = subs, features = f, featureDim = fd };
        }
    }

    /// Baked triangle lists (Resources/CharacterLOD/HeroLodCache.bytes), keyed by a hash of the final runtime mesh.
    public static class HeroLodCache
    {
        static Dictionary<ulong, (int offset, int length)> index; static byte[] data;

        public static ulong Hash(Mesh m)
        {
            ulong h = 1469598103934665603UL;
            void Mix(uint x) { for (int i = 0; i < 4; i++) { h ^= (x >> (8 * i)) & 0xff; h *= 1099511628211UL; } }
            Mix((uint)HeroLod.Version); Mix((uint)m.vertexCount); Mix((uint)m.subMeshCount);
            foreach (var p in m.vertices) { Mix((uint)BitConverter.SingleToInt32Bits(p.x)); Mix((uint)BitConverter.SingleToInt32Bits(p.y)); Mix((uint)BitConverter.SingleToInt32Bits(p.z)); }
            for (int s = 0; s < m.subMeshCount; s++) { var t = m.GetTriangles(s); Mix((uint)t.Length); foreach (var i in t) Mix((uint)i); }
            return h;
        }

        static void Load()
        {
            if (index != null) return;
            index = new Dictionary<ulong, (int, int)>();
            var asset = Resources.Load<TextAsset>("CharacterLOD/HeroLodCache"); if (!asset) return;
            data = asset.bytes;
            // header: "HLOD", version, count; entries: hash u64, offset i32, length i32
            if (data.Length < 12 || BitConverter.ToInt32(data, 0) != 0x444F4C48 || BitConverter.ToInt32(data, 4) != HeroLod.Version) { data = null; return; }
            int count = BitConverter.ToInt32(data, 8);
            for (int i = 0; i < count; i++) { int o = 12 + i * 16; index[BitConverter.ToUInt64(data, o)] = (BitConverter.ToInt32(data, o + 8), BitConverter.ToInt32(data, o + 12)); }
        }

        public static bool TryGet(ulong hash, Mesh source, out int[][][] levels)
        {
            levels = null; Load();
            if (data == null || !index.TryGetValue(hash, out var at)) return false;
            int o = at.offset; int subCount = BitConverter.ToInt32(data, o); o += 4;
            if (subCount != source.subMeshCount) return false;
            levels = new int[HeroLod.Levels][][];
            for (int l = 1; l < HeroLod.Levels; l++)
            {
                levels[l] = new int[subCount][];
                for (int s = 0; s < subCount; s++)
                {
                    // count > 0: int32 indices; count < 0: -count uint16 indices (meshes under 65,536 vertices)
                    int c = BitConverter.ToInt32(data, o); o += 4;
                    if (c >= 0) { var a = new int[c]; Buffer.BlockCopy(data, o, a, 0, c * 4); o += c * 4; levels[l][s] = a; }
                    else { c = -c; var a = new int[c]; for (int i = 0; i < c; i++) a[i] = BitConverter.ToUInt16(data, o + 2 * i); o += c * 2; levels[l][s] = a; }
                }
            }
            return true;
        }

        /// Decodes every entry of the shipped cache: entry count, and false if any entry is malformed (EditMode test).
        public static (int entries, bool ok) Validate()
        {
            Load(); if (data == null) return (0, true);
            foreach (var kv in index)
            {
                int o = kv.Value.offset, end = o + kv.Value.length; int subs = BitConverter.ToInt32(data, o); o += 4;
                for (int k = 0; k < subs * (HeroLod.Levels - 1); k++)
                {
                    if (o + 4 > end) return (index.Count, false);
                    int c = BitConverter.ToInt32(data, o); o += 4 + (c >= 0 ? c * 4 : -c * 2);
                    if (o > end || Math.Abs(c) % 3 != 0) return (index.Count, false);
                }
                if (o != end) return (index.Count, false);
            }
            return (index.Count, true);
        }

        /// Serialise entries (bake tool). Entries already in the shipped cache are kept unless replaced.
        public static byte[] Write(IDictionary<ulong, int[][][]> entries)
        {
            Load();
            var all = new Dictionary<ulong, byte[]>();
            if (data != null) foreach (var kv in index) { var b = new byte[kv.Value.length]; Buffer.BlockCopy(data, kv.Value.offset, b, 0, b.Length); all[kv.Key] = b; }
            foreach (var kv in entries)
            {
                using var ms = new System.IO.MemoryStream(); using var w = new System.IO.BinaryWriter(ms);
                int subs = kv.Value[1].Length; w.Write(subs);
                bool narrow = kv.Value.Skip(1).All(lv => lv.All(sub => sub.All(i => i < 65536)));
                for (int l = 1; l < HeroLod.Levels; l++) for (int s = 0; s < subs; s++)
                {
                    var ix = kv.Value[l][s];
                    if (narrow) { w.Write(-ix.Length); foreach (var i in ix) w.Write((ushort)i); }
                    else { w.Write(ix.Length); foreach (var i in ix) w.Write(i); }
                }
                all[kv.Key] = ms.ToArray();
            }
            using var o = new System.IO.MemoryStream(); using var bw = new System.IO.BinaryWriter(o);
            bw.Write(0x444F4C48); bw.Write(HeroLod.Version); bw.Write(all.Count);
            int offset = 12 + all.Count * 16; var order = all.Keys.OrderBy(k => k).ToList();
            foreach (var k in order) { bw.Write(k); bw.Write(offset); bw.Write(all[k].Length); offset += all[k].Length; }
            foreach (var k in order) bw.Write(all[k]);
            return o.ToArray();
        }
    }

    /// Adds a HeroLod to every hero (anything carrying MatchHeroLook) in every scene, a couple of times a second.
    sealed class HeroLodBoot : MonoBehaviour
    {
        float next;
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        static void Boot()
        {
            if (!HeroLod.Enabled) return;
            var go = new GameObject("Hero LOD boot") { hideFlags = HideFlags.HideAndDontSave };
            DontDestroyOnLoad(go); go.AddComponent<HeroLodBoot>();
        }
        void Update()
        {
            if (Time.unscaledTime < next) return; next = Time.unscaledTime + .5f;
            if (!HeroLod.Enabled) return;
            foreach (var look in FindObjectsByType<Tennis.MatchHeroLook>(FindObjectsInactive.Exclude, FindObjectsSortMode.None))
                if (!look.GetComponent<HeroLod>() && !look.GetComponentInParent<HeroLodExempt>()) look.gameObject.AddComponent<HeroLod>();
        }
    }

    /// A hero under this always draws its full meshes (HeroLodBoot never attaches a HeroLod): bowling's few bowlers, who are
    /// filmed close; their LOD copies of the bowling kit bodies showed holes (dark streaks, black faces) in game.
    public sealed class HeroLodExempt : MonoBehaviour { }
}
