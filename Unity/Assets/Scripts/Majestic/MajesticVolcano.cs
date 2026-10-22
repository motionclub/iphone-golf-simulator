using System.Collections.Generic;
using UnityEngine;

namespace GolfArcade.Majestic
{
    /// Volcano dressing toward concepts/after/tennis_volcano_storm.jpg: an erupting cone straight down the
    /// court (rising out of the lava lake ~180 m away, peak ~11° above the gameplay eye line), glowing lava
    /// rivers, a lit ash plume, distant lightning, and a dark glossy court that reflects the lava glow
    /// (a generated reflection panorama on TennisWorldSurface's existing _ReflectionMap slot — no SSR).
    public static class MajesticVolcano
    {
        static Transform plume;
        static readonly List<GameObject> bolts = new();
        static float nextStrike = 3, strikeEnd, flashUntil;
        static int strikes;
        static readonly List<(Material m, string prop, object value)> saved = new();
        static readonly HashSet<Material> styled = new();
        static Texture2D reflection;
        public static float Flash => Time.time < flashUntil ? 1 : 0;

        public static void Build(Transform root, MajesticLook look)
        {
            bolts.Clear(); nextStrike = Time.time + 3; strikes = 0;
            var mat = MajesticMesh.Dressing();
            var rng = new System.Random(102);
            var centre = new Vector3(4, -46, 168);

            // ---- cone with lava rivers ----
            var cone = new MajesticMesh();
            const int seg = 220, rings = 38; const float R = 118, H = 82, crater = .9f;
            float[] riverAz = { -1.95f, -1.62f, -1.2f, -.78f, -1.40f };   // around -pi/2 = facing the court (-Z)
            Vector3 P(int k, int j)
            {
                float a = k * Mathf.PI * 2 / seg, h = Mathf.Min(j / (float)rings, crater);
                float ridge = 1 + .11f * Mathf.Sin(a * 5 + h * 4) + .07f * Mathf.Sin(a * 11 + 1.7f + h * 6) + .04f * Mathf.Sin(a * 31 + h * 17) + .025f * Mathf.Sin(a * 67 + h * 29);
                float shoulder = 1 + .18f * Mathf.Exp(-Mathf.Pow((h - .35f) / .12f, 2)) * (.5f + .5f * Mathf.Sin(a * 3 + .8f));
                float r = R * Mathf.Pow(1 - h, 1.35f) * ridge * shoulder;
                return centre + new Vector3(Mathf.Cos(a) * r, h * H, Mathf.Sin(a) * r);
            }
            float Lava(float az, float h)
            {
                float lava = 0;
                for (int i = 0; i < riverAz.Length; i++)
                {
                    float centreAz = riverAz[i] + .13f * Mathf.Sin(h * 9 + i * 2.1f) + .05f * Mathf.Sin(h * 23 + i);
                    float width = Mathf.Lerp(.055f, .02f, h) * (i == 4 ? 1.6f : 1);
                    float d = Mathf.Abs(Mathf.DeltaAngle(az * Mathf.Rad2Deg, centreAz * Mathf.Rad2Deg)) * Mathf.Deg2Rad;
                    float start = .15f + i * .04f;
                    if (h > start) lava = Mathf.Max(lava, Mathf.Clamp01(1 - d / width) * Mathf.Clamp01((h - start) / .05f));
                }
                if (h > .82f) lava = Mathf.Max(lava, Mathf.Clamp01((h - .82f) / .08f));
                return Mathf.SmoothStep(0, 1, lava);
            }
            Color Col(float az, float h, float lava)
            {
                var rock = Color.Lerp(new Color(.13f, .09f, .11f), new Color(.25f, .16f, .15f), .5f + .5f * Mathf.Sin(az * 17 + h * 13));
                return Color.Lerp(rock, new Color(1f, .30f, .05f), lava);
            }
            for (int j = 0; j < rings; j++)
                for (int k = 0; k < seg; k++)
                {
                    float a0 = k * Mathf.PI * 2 / seg, a1 = (k + 1) * Mathf.PI * 2 / seg, h0 = j / (float)rings, h1 = (j + 1) / (float)rings;
                    float l00 = Lava(a0, h0), l10 = Lava(a1, h0), l11 = Lava(a1, h1), l01 = Lava(a0, h1);
                    cone.QuadV(P(k, j), P(k + 1, j), P(k + 1, j + 1), P(k, j + 1), Col(a0, h0, l00), Col(a1, h0, l10), Col(a1, h1, l11), Col(a0, h1, l01), l00 * 3.2f, l10 * 3.2f, l11 * 3.2f, l01 * 3.2f);
                }
            cone.Glow = 4; // crater lid glow
            var top = centre + Vector3.up * (H * crater);
            for (int k = 0; k < seg; k++) cone.Tri(P(k, rings), P(k + 1, rings), top + Vector3.down * 4, new Color(1f, .32f, .06f));
            cone.Build(root, "Majestic volcano cone", mat, false);

            // ---- ash plume: lumpy lit puffs, glowing orange at the base, bruised purple above ----
            var p = new MajesticMesh();
            // the frame top is ~60 m up at the cone's distance: a dark column that leans back (+Z) out of
            // frame, glowing only right above the vent
            for (int i = 0; i < 40; i++)
            {
                float t = i / 39f, spread = Mathf.Lerp(5, 60, t);
                var c = top + new Vector3(((float)rng.NextDouble() - .5f) * spread * 1.6f + Mathf.Sin(t * 7) * 12, Mathf.Lerp(3, 150, t) + ((float)rng.NextDouble() - .5f) * 22, Mathf.Lerp(0, 110, t * t) + ((float)rng.NextDouble() - .5f) * spread * .8f);
                float r = Mathf.Lerp(6, 34, t) * (.75f + (float)rng.NextDouble() * .5f);
                var low = Color.Lerp(new Color(1f, .30f, .06f), new Color(.20f, .15f, .18f), Mathf.Clamp01(t * 7f));
                var high = Color.Lerp(new Color(.26f, .19f, .21f), new Color(.15f, .13f, .19f), Mathf.Clamp01(t * 2));
                p.Glow = i < 3 ? 1.1f * (1 - i / 3f) : 0;
                p.Blob(c, new Vector3(r, r * .62f, r * .9f), high, low, 12);
            }
            plume = p.Build(root, "Majestic ash plume", mat, false).transform;

            // ---- distant lightning (three prebuilt bolts, shown one at a time) ----
            for (int b = 0; b < 3; b++)
            {
                var m = new MajesticMesh { Glow = 9 };
                var start = new Vector3(120 + b * 45, 210 + b * 15, 330 - b * 30);
                Bolt(m, start, start + new Vector3(-20 + b * 12, -190, 10), .9f, rng, 0);
                var go = m.Build(root, "Majestic lightning " + b, mat, false); go.SetActive(false); bolts.Add(go);
            }
        }

        static void Bolt(MajesticMesh m, Vector3 a, Vector3 d, float width, System.Random rng, int depth)
        {
            var col = new Color(.88f, .80f, 1f);
            Vector3 prev = a; int steps = 9;
            for (int i = 1; i <= steps; i++)
            {
                var next = Vector3.Lerp(a, d, i / (float)steps) + (i < steps ? new Vector3(((float)rng.NextDouble() - .5f) * 22, 0, ((float)rng.NextDouble() - .5f) * 8) : Vector3.zero);
                var side = Vector3.Cross((next - prev).normalized, Vector3.forward).normalized * width;
                m.Quad(prev - side, prev + side, next + side, next - side, col);
                if (depth == 0 && i > 2 && i < steps - 1 && rng.NextDouble() < .35) Bolt(m, next, next + new Vector3(((float)rng.NextDouble() - .5f) * 60, -50, 0), width * .5f, rng, 1);
                prev = next;
            }
        }

        public static void Animate(MajesticLook look, float t)
        {
            if (plume) plume.RotateAround(new Vector3(4, 0, 168), Vector3.up, Time.deltaTime * 1.2f);
            // lightning: a strike every 5-11 s, two quick flickers (well under 3 flashes per second)
            if (bolts.Count > 0)
            {
                if (t >= nextStrike && strikeEnd < t)
                {
                    strikes++; strikeEnd = t + .32f; flashUntil = t + .09f;
                    nextStrike = t + 5 + (strikes * 7919 % 600) / 100f;
                }
                int which = strikes % bolts.Count; float since = strikeEnd - t;
                bool on = since > 0 && (since > .22f || (since < .14f && since > .06f));
                for (int i = 0; i < bolts.Count; i++) bolts[i].SetActive(on && i == which);
            }
        }

        public static void SetMaterials(bool on, MajesticLook look)
        {
            if (on)
            {
                foreach (var r in Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None))
                    foreach (var m in r.sharedMaterials)
                    {
                        if (!m || styled.Contains(m)) continue; string n = m.name;
                        if (n.StartsWith("TropicalV3_002")) Glossy(m, look.Court, .62f, .62f);
                        else if (n.StartsWith("TropicalV3_011")) Glossy(m, look.Lawn, .5f, .45f);
                        else continue;
                        styled.Add(m);
                    }
            }
            else
            {
                for (int i = saved.Count - 1; i >= 0; i--)
                {
                    var (m, prop, value) = saved[i]; if (!m) continue;
                    switch (value) { case Color c: m.SetColor(prop, c); break; case float f: m.SetFloat(prop, f); break; case Texture tex: m.SetTexture(prop, tex); break; case null: m.SetTexture(prop, null); break; }
                }
                saved.Clear(); styled.Clear();
            }
        }

        static void Set(Material m, string prop, object value)
        {
            if (!m.HasProperty(prop)) return;
            object old = value switch { Color => m.GetColor(prop), float => m.GetFloat(prop), _ => m.GetTexture(prop) };
            if (!saved.Exists(s => s.m == m && s.prop == prop)) saved.Add((m, prop, old));
            switch (value) { case Color c: m.SetColor(prop, c); break; case float f: m.SetFloat(prop, f); break; case Texture t: m.SetTexture(prop, t); break; }
        }

        static void Glossy(Material m, Color baseColor, float smooth, float reflect)
        {
            Set(m, "_BaseColor", baseColor); Set(m, "_Smoothness", smooth);
            Set(m, "_ReflectionMap", LavaReflection()); Set(m, "_ReflectionWeight", reflect); Set(m, "_ReflectionHeading", 0f);
        }

        /// Equirect panorama in TennisWorldSurface's mapping (u = atan2(z,x)/2pi + .5, v = .53 + asin(y)/pi):
        /// bruised purple sky, a hot band low on the horizon, and bright streaks toward the cone (+Z) and
        /// the two lava falls (front-left / front-right).
        static Texture2D LavaReflection()
        {
            if (reflection) return reflection;
            const int w = 256, h = 128;
            reflection = new Texture2D(w, h, TextureFormat.RGBA32, true, false) { wrapMode = TextureWrapMode.Repeat, name = "Majestic lava reflection" };
            var px = new Color[w * h];
            float[] hot = { .75f, .63f, .87f, .70f, .80f }; float[] power = { 1.3f, 1f, 1f, .55f, .55f };
            for (int y = 0; y < h; y++)
                for (int x = 0; x < w; x++)
                {
                    float u = x / (float)w, v = y / (float)h;
                    float elev = Mathf.Clamp01((v - .53f) / .45f);
                    var c = Color.Lerp(new Color(.22f, .22f, .30f), new Color(.14f, .14f, .22f), elev);
                    float band = Mathf.Exp(-elev * 9) * .9f;
                    c += new Color(1f, .32f, .08f) * band * .45f;
                    for (int i = 0; i < hot.Length; i++)
                    {
                        float du = Mathf.Abs(Mathf.Repeat(u - hot[i] + .5f, 1) - .5f);
                        c += new Color(1f, .34f, .07f) * power[i] * Mathf.Exp(-du * du / .0006f) * Mathf.Exp(-elev * 4) * 1.6f;
                    }
                    px[y * w + x] = c;
                }
            reflection.SetPixels(px); reflection.Apply(true, true);
            return reflection;
        }
    }
}
