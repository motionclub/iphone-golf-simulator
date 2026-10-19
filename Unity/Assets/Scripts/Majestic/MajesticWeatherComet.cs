using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;
using Object = UnityEngine.Object;

namespace GolfArcade.Majestic
{
    /// The ball's comet outline (Adnan 10-18: "an extremely subtle outlining, maybe more so a happy outlining ... like a
    /// heat seeking missile outline / asteroid outline like flames"). Additive warm light only, never dark:
    /// a hair-thin hot line round the ball's silhouette with a soft flickering flame glow outside it, streaming away from
    /// the motion (gently upward at rest), plus a short flame trail that appears only while the ball flies or rolls fast.
    /// Barely there in clear sun; a little stronger as the weather takes light away (MajesticWeatherGlow.Darkness).
    /// Two small meshes per ball (a 16x10 shell and a 4-vertex ribbon), one material each: ships on the phone.
    public sealed class MajesticWeatherComet
    {
        /// The look, chosen by Adnan from three proofs. Env MAJESTIC_BALL_RIM=A|B|C picks one (proof runs).
        public struct Style
        {
            public string Name; public float Width, Flame, Speed, TrailSeconds, TrailMaxRadii, Clear, Max; public Color Hot, Warm;
        }
        public static readonly Style[] Styles =
        {
            new() { Name = "A ember",  Width = .10f, Flame = .6f,  Speed = 3, TrailSeconds = .05f,  TrailMaxRadii = 7,  Clear = .16f, Max = .85f, Hot = new Color(1f, .93f, .72f), Warm = new Color(1f, .5f, .14f) },
            new() { Name = "B comet",  Width = .15f, Flame = 1.0f, Speed = 4, TrailSeconds = .09f,  TrailMaxRadii = 14, Clear = .2f,  Max = 1f,   Hot = new Color(1f, .95f, .8f),  Warm = new Color(1f, .42f, .1f) },
            new() { Name = "C spark",  Width = .07f, Flame = .25f, Speed = 2, TrailSeconds = .035f, TrailMaxRadii = 4,  Clear = .14f, Max = .75f, Hot = new Color(1f, .97f, .88f), Warm = new Color(1f, .72f, .38f) },
        };
        public static int Variant = Pick(Environment.GetEnvironmentVariable("MAJESTIC_BALL_RIM"));
        /// Tennis only (Adnan 10-18: "strengthen the tennis ball's warm outline for rain"): the yellow ball on a bright wet
        /// court and sea needs more than the golf ember. A strength floor and a deeper gold, crisp ring
        /// (warm light over its rim, never dark). Env MAJESTIC_TENNIS_EMBER=0 turns it off (proof A/B).
        public static bool TennisBoost = Environment.GetEnvironmentVariable("MAJESTIC_TENNIS_EMBER") != "0";
        // ring 3 from the 10-18 proof (proof/tennis_boost3): a crisp, stronger gold ring (filling the ball white instead washed the ring out)
        public static float TennisFloor = 2.2f, TennisWidth = .08f, TennisInner = .8f;
        public static Color TennisHot = new(1f, .82f, .45f);
        static int Pick(string v) => v == "B" ? 1 : v == "C" ? 2 : 0;

        readonly Material rimMat, trailMat;
        GameObject rim, trail; Mesh trailMesh;
        Vector3 lastPos, vel; bool havePos;
        readonly Vector3[] tv = new Vector3[4];

        public MajesticWeatherComet()
        {
            var s = Resources.Load<Shader>("Majestic/MajesticWeatherComet");
            rimMat = new Material(s) { name = "Majestic weather ball comet rim" }; rimMat.SetFloat("_Mode", 0); rimMat.SetFloat("_Cull", (float)CullMode.Back);
            trailMat = new Material(s) { name = "Majestic weather ball comet trail" }; trailMat.SetFloat("_Mode", 1); trailMat.SetFloat("_Cull", (float)CullMode.Off);
        }

        /// d = how much light the weather takes (0 clear .. 1); metres = world units to metres.
        public void Update(MajesticWeather w, Transform ballRoot, float d, float metres)
        {
            Renderer src = null;
            if (ballRoot) foreach (var r in ballRoot.GetComponentsInChildren<MeshRenderer>()) if (r.enabled && r.gameObject.activeInHierarchy && !r.name.StartsWith("Majestic weather")) { src = r; break; }
            Make();
            bool on = src && w.Cam;
            if (rim.activeSelf != on) rim.SetActive(on);
            if (!on) { trail.SetActive(false); havePos = false; return; }
            var st = Styles[Mathf.Clamp(Variant, 0, Styles.Length - 1)];
            var b = src.bounds; float rad = Mathf.Max(b.extents.x, Mathf.Max(b.extents.y, b.extents.z));
            var c = b.center;

            // the ball's speed, smoothed; a jump (new hole, re-drop) is not motion
            float dt = Mathf.Max(Time.deltaTime, 1e-4f);
            if (havePos)
            {
                var step = (c - lastPos) / dt;
                vel = step.magnitude * metres > 120 ? Vector3.zero : Vector3.Lerp(vel, step, Mathf.Clamp01(dt * 18));
            }
            lastPos = c; havePos = true;
            float speed = vel.magnitude * metres;                        // m/s
            float moving = Mathf.SmoothStep(0, 1, Mathf.InverseLerp(5, 14, speed));

            float amount = Mathf.Lerp(st.Clear, st.Max, Mathf.Clamp01(d));
            bool boost = w.Tennis && TennisBoost;
            if (boost) amount = Mathf.Max(amount, Mathf.Lerp(.45f, TennisFloor, Mathf.Clamp01(d * 1.6f)));   // clear sun stays modest
            rim.layer = trail.layer = src.gameObject.layer;
            rim.transform.SetPositionAndRotation(c, Quaternion.identity);
            rim.transform.localScale = Vector3.one * rad * 4.2f;         // shell radius 2.1 ball radii: room for the flame
            var away = moving > .01f ? -vel.normalized : Vector3.up;
            rimMat.SetVector("_Center", new Vector4(c.x, c.y, c.z, rad));
            rimMat.SetVector("_Bias", new Vector4(away.x, away.y, away.z, moving > .01f ? .4f + .6f * moving : .35f));
            rimMat.SetFloat("_Amount", amount);
            rimMat.SetFloat("_Width", boost ? TennisWidth : st.Width); rimMat.SetFloat("_Inner", boost ? TennisInner : .88f); rimMat.SetFloat("_Flame", st.Flame); rimMat.SetFloat("_Speed", st.Speed);
            rimMat.SetColor("_Hot", boost ? TennisHot : st.Hot); rimMat.SetColor("_Warm", st.Warm);

            bool tail = moving > .01f;
            if (trail.activeSelf != tail) trail.SetActive(tail);
            if (!tail) return;
            float len = Mathf.Min(vel.magnitude * st.TrailSeconds, rad * st.TrailMaxRadii);
            var dir = -vel.normalized; var tip = c + dir * len;
            var view = (c - w.Cam.transform.position).normalized;
            var side = Vector3.Cross(dir, view); side = side.sqrMagnitude > 1e-6f ? side.normalized * rad * .9f : w.Cam.transform.right * rad * .9f;
            tv[0] = c - side; tv[1] = c + side; tv[2] = tip - side * .15f; tv[3] = tip + side * .15f;
            trailMesh.vertices = tv; trailMesh.RecalculateBounds();
            trail.transform.SetPositionAndRotation(Vector3.zero, Quaternion.identity); trail.transform.localScale = Vector3.one;
            trailMat.SetFloat("_Amount", amount * moving * 1.1f);
            trailMat.SetFloat("_Speed", st.Speed); trailMat.SetColor("_Hot", st.Hot); trailMat.SetColor("_Warm", st.Warm);
        }

        void Make()
        {
            if (!rim)
            {
                rim = new GameObject("Majestic weather ball comet");
                rim.AddComponent<MeshFilter>().sharedMesh = Shell();
                Quiet(rim.AddComponent<MeshRenderer>(), rimMat);
            }
            if (!trail)
            {
                trail = new GameObject("Majestic weather ball comet trail");
                trailMesh = new Mesh { name = "Majestic weather comet trail" }; trailMesh.MarkDynamic();
                trailMesh.vertices = new Vector3[4];
                trailMesh.uv = new[] { new Vector2(0, -1), new Vector2(0, 1), new Vector2(1, -1), new Vector2(1, 1) };
                trailMesh.triangles = new[] { 0, 2, 1, 1, 2, 3 };
                trail.AddComponent<MeshFilter>().sharedMesh = trailMesh;
                Quiet(trail.AddComponent<MeshRenderer>(), trailMat);
                trail.SetActive(false);
            }
        }

        static void Quiet(MeshRenderer r, Material m)
        {
            r.sharedMaterial = m; r.shadowCastingMode = ShadowCastingMode.Off; r.receiveShadows = false;
            r.lightProbeUsage = LightProbeUsage.Off; r.reflectionProbeUsage = ReflectionProbeUsage.Off; r.allowOcclusionWhenDynamic = false;
        }

        /// A unit-diameter UV sphere, 16 x 10.
        static Mesh shell;
        static Mesh Shell()
        {
            if (shell) return shell;
            const int seg = 16, rings = 10;
            var v = new List<Vector3>(); var t = new List<int>();
            for (int y = 0; y <= rings; y++)
            {
                float th = Mathf.PI * y / rings;
                for (int x = 0; x <= seg; x++) { float ph = 2 * Mathf.PI * x / seg; v.Add(new Vector3(Mathf.Sin(th) * Mathf.Cos(ph), Mathf.Cos(th), Mathf.Sin(th) * Mathf.Sin(ph)) * .5f); }
            }
            for (int y = 0; y < rings; y++) for (int x = 0; x < seg; x++)
            {
                int a = y * (seg + 1) + x, b = a + seg + 1;
                t.Add(a); t.Add(a + 1); t.Add(b); t.Add(a + 1); t.Add(b + 1); t.Add(b);
            }
            shell = new Mesh { name = "Majestic weather comet shell" }; shell.SetVertices(v); shell.SetTriangles(t, 0); shell.RecalculateBounds();
            return shell;
        }

        public void Hide() { if (rim) rim.SetActive(false); if (trail) trail.SetActive(false); havePos = false; }
        public void Destroy() { if (rim) Object.Destroy(rim); if (trail) Object.Destroy(trail); if (trailMesh) Object.Destroy(trailMesh); }
    }
}
