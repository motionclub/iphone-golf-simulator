using System;
using System.Collections.Generic;
using UnityEngine;

namespace GolfArcade.Tennis
{
    /// HERO STUDIO (2026-11-12, work/final-plan-1111/phase2): shapes worked out offline, on the heroes' own meshes, and stored
    /// as per-vertex offsets the game adds when it prepares a hero.
    ///   him: the whole body rebuilt as one (chest, back, stomach, neck, arms), his tennis / golf / bowling tops refitted to
    ///        it, the garments that follow it, and a rounded toe on his shoes. This REPLACES the 11-11 HeroBuild for him.
    ///   her: only her three tops, refitted on her own unchanged body, added after her own HeroBuild.
    /// Data: Resources/HeroStudio/<renderer name>_<vertex count>.bytes = "HSD1", int32 count, then int16 x,y,z per vertex in
    /// 1/50000 m (rest pose, hero frame), written by work/final-plan-1111/phase2/make_game_data.py. A mesh of his with no file
    /// of its own (a distance garment, a sock, an accessory) follows the body's own offsets underneath it, as HeroBuild's
    /// garments did. Normals and tangents turn with the surface (welded face normals before and after), so authored seams and
    /// detail normals survive. HERO_STUDIO=0 in the environment switches all of it off (he then gets the 11-11 build again).
    public static class HeroStudio
    {
        public static bool Enabled = Environment.GetEnvironmentVariable("HERO_STUDIO") != "0";
        const float Unit = 1f / 50000f;
        static readonly Dictionary<(Mesh, bool), Mesh> cache = new Dictionary<(Mesh, bool), Mesh>();
        static readonly Dictionary<string, Vector3[]> data = new Dictionary<string, Vector3[]>();

        /// The body's offsets, per hero, for the meshes that have no file of their own.
        sealed class Field
        {
            public Vector3[] p, d; public CellGrid grid;   // (flat cells, same order of points as the lists it replaced: CellGrid.cs)
            const float Cell = .03f, R = .045f;
            public Field(Vector3[] p, Vector3[] d)
            {
                this.p = p; this.d = d;
                grid = new CellGrid(p, p.Length, Cell);
            }
            public Vector3 Sample(Vector3 q)
            {
                int cx = CellGrid.Coord(q.x, Cell), cy = CellGrid.Coord(q.y, Cell), cz = CellGrid.Coord(q.z, Cell);
                Vector3 sum = Vector3.zero; float ws = 0; int r = Mathf.CeilToInt(R / Cell);
                for (int x = -r; x <= r; x++) for (int y = -r; y <= r; y++) for (int z = -r; z <= r; z++)
                    if (grid.Find(cx + x, cy + y, cz + z, out int s, out int e))
                        for (int n = s; n < e; n++) { int i = grid.Items[n]; float dist = (p[i] - q).magnitude; if (dist >= R) continue; float k = 1 - dist / R; k = k * k * k; sum += d[i] * k; ws += k; }
                // (the still skin around a moved patch is in the average too: a vertex beside the patch does not take its whole offset)
                return ws > 1e-6f ? sum / ws : Vector3.zero;
            }
        }
        static readonly Dictionary<MatchHeroLook, Field> fields = new Dictionary<MatchHeroLook, Field>();
        static Field lastMale;

        static Vector3[] Load(string name, int n)
        {
            string key = name + "_" + n;
            if (data.TryGetValue(key, out var v)) return v;
            var asset = Resources.Load<TextAsset>("HeroStudio/" + key); Vector3[] o = null;
            if (asset)
            {
                var b = asset.bytes;
                if (b.Length == 8 + n * 6 && b[0] == 'H' && b[1] == 'S' && b[2] == 'D' && b[3] == '1' && BitConverter.ToInt32(b, 4) == n)
                {
                    o = new Vector3[n];
                    for (int i = 0; i < n; i++) o[i] = new Vector3(BitConverter.ToInt16(b, 8 + i * 6), BitConverter.ToInt16(b, 10 + i * 6), BitConverter.ToInt16(b, 12 + i * 6)) * Unit;
                }
                else Debug.LogWarning($"[HeroStudio] {key}: {b.Length} bytes do not fit {n} vertices");
            }
            data[key] = o; return o;
        }

        /// `her`: the call comes after her own build (HeroBuild.Prepare), for her refitted tops; without it she is left alone.
        public static Mesh Override(MatchHeroLook look, SkinnedMeshRenderer smr, Mesh source, bool her = false)
        {
            if (!Enabled || !look || (look.female && !her) || !smr || !source || !source.isReadable) return source;
            if (source.name.Contains("(studio)")) return source;
            bool body = smr == look.body;
            if (!body && cache.TryGetValue((source, look.female), out var done) && done) return done;
            int n = source.vertexCount;
            Matrix4x4 toHero = look.transform.worldToLocalMatrix * smr.transform.localToWorldMatrix, fromHero = toHero.inverse;
            var v = source.vertices; var offsets = Load(body ? "Body_M" : smr.name, n);
            var hero = new Vector3[n]; for (int i = 0; i < n; i++) hero[i] = toHero.MultiplyPoint3x4(v[i]);
            if (offsets == null)
            {
                // no file of its own: his garments follow the body underneath (her meshes without a file stay exactly as they are)
                if (look.female || body) return source;
                if (!fields.TryGetValue(look, out var f) || f == null) f = lastMale;
                if (f == null) return source;
                offsets = new Vector3[n]; bool any = false;
                for (int i = 0; i < n; i++) { offsets[i] = f.Sample(hero[i]); if (offsets[i].sqrMagnitude > 1e-12f) any = true; }
                if (!any) { cache[(source, look.female)] = source; return source; }
            }
            else if (body) { var f = new Field(hero, offsets); fields[look] = f; lastMale = f; if (fields.Count > 16) Prune(); }
            if (body && cache.TryGetValue((source, look.female), out var bodyDone) && bodyDone) return bodyDone;
            var after = new Vector3[n]; float largest = 0; int moved = 0;
            for (int i = 0; i < n; i++)
            {
                after[i] = fromHero.MultiplyPoint3x4(hero[i] + offsets[i]);
                float d = offsets[i].magnitude; if (d > 1e-5f) moved++; if (d > largest) largest = d;
            }
            // welded face normals of the surface before and after: each stored normal and tangent turns by the same rotation
            var weld = new Dictionary<Vector3Int, int>(); var group = new int[n]; int groups = 0;
            for (int i = 0; i < n; i++) { var key = new Vector3Int(Mathf.RoundToInt(v[i].x * 20000), Mathf.RoundToInt(v[i].y * 20000), Mathf.RoundToInt(v[i].z * 20000)); if (!weld.TryGetValue(key, out int g)) weld[key] = g = groups++; group[i] = g; }
            var was = new Vector3[groups]; var now = new Vector3[groups];
            for (int sm = 0; sm < source.subMeshCount; sm++)
            {
                var tris = source.GetTriangles(sm);
                for (int t = 0; t + 2 < tris.Length; t += 3)
                {
                    int a = tris[t], b = tris[t + 1], c = tris[t + 2];
                    var f0 = Vector3.Cross(v[b] - v[a], v[c] - v[a]); var f1 = Vector3.Cross(after[b] - after[a], after[c] - after[a]);
                    was[group[a]] += f0; was[group[b]] += f0; was[group[c]] += f0; now[group[a]] += f1; now[group[b]] += f1; now[group[c]] += f1;
                }
            }
            var normals = source.normals; var tangents = source.tangents;
            var newNormals = (Vector3[])normals.Clone(); var newTangents = (Vector4[])tangents.Clone();
            for (int i = 0; i < n; i++)
            {
                Vector3 a = was[group[i]], b = now[group[i]]; if (a.sqrMagnitude < 1e-20f || b.sqrMagnitude < 1e-20f) continue;
                var q = Quaternion.FromToRotation(a, b);
                if (i < normals.Length) newNormals[i] = (q * normals[i]).normalized;
                if (i < tangents.Length) { var t3 = (q * new Vector3(tangents[i].x, tangents[i].y, tangents[i].z)).normalized; newTangents[i] = new Vector4(t3.x, t3.y, t3.z, tangents[i].w); }
            }
            var ready = UnityEngine.Object.Instantiate(source); ready.name = source.name + " (studio)"; ready.hideFlags = HideFlags.DontSave;
            ready.vertices = after;
            if (normals.Length == n) ready.normals = newNormals;
            if (tangents.Length == n) ready.tangents = newTangents;
            ready.RecalculateBounds(); cache[(source, look.female)] = ready;
            Debug.Log($"[HeroStudio] {smr.name} {source.name} v={n}: moved={moved} largest={largest * 1000:F1}mm{(Load(body ? "Body_M" : smr.name, n) == null ? " (follows the body)" : "")}");
            return ready;
        }

        static void Prune()
        {
            var dead = new List<MatchHeroLook>(); foreach (var k in fields.Keys) if (!k) dead.Add(k);
            foreach (var k in dead) fields.Remove(k);
        }
    }
}
