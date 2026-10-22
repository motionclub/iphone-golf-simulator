using System.Collections.Generic;
using GolfArcade.Course;
using GolfArcade.Game;
using GolfArcade.Tennis;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace GolfArcade.Majestic
{
    /// What the weather layer draws on its own (everything else is inside the world materials):
    /// - the fall layer: one sphere round the camera; rain streaks / snow / ash in three depth layers, computed from the
    ///   view direction in its shader (MajesticWeatherFall), masked out of the ball corridor on screen;
    /// - near drops: one particle system, at most 400, spawned only outside the ball corridor (MajesticWeatherDrop);
    /// - the sky: a storm wall on the horizon, sunbeams and a rainbow when rain clears, lava bombs in an eruption
    ///   (MajesticWeatherSky). All on the overlay layer, no shadows, no depth reads.
    public sealed class MajesticWeatherFx
    {
        public const int MaxDrops = 400;
        readonly GameObject root;
        readonly Renderer fall; readonly Material fallMat;
        readonly ParticleSystem drops; readonly ParticleSystemRenderer dropRenderer; readonly Material dropMat;
        readonly Renderer wall, rainbow, beams; readonly Material wallMat, rainbowMat, beamsMat;
        readonly List<(Transform t, TrailRenderer trail, Vector3 v)> bombs = new();
        readonly Material bombMat;
        readonly Renderer mirror; readonly Material mirrorMat;   // tennis: the wet court's screen-space mirror
        UniversalAdditionalCameraData mirrorCam; bool mirrorCamHadColor;
        readonly System.Random rng = new(7177);   // never UnityEngine.Random: gameplay's random sequences stay untouched
        float bombsUntil; Vector3 bombVent;
        float spawnDebt, clearRTennis = 2.2f;
        public int Rejected { get; private set; }
        public ParticleSystem Drops => drops;
        public Renderer Fall => fall;
        public Renderer Wall => wall;
        public Renderer RainbowRenderer => rainbow;

        public MajesticWeatherFx(Transform parent)
        {
            root = new GameObject("Majestic weather") { layer = BallLook.OverlayLayer };
            root.transform.SetParent(parent, false);
            var fallShader = Resources.Load<Shader>("Majestic/MajesticWeatherFall");
            var dropShader = Resources.Load<Shader>("Majestic/MajesticWeatherDrop");
            var skyShader = Resources.Load<Shader>("Majestic/MajesticWeatherSky");

            fallMat = new Material(fallShader) { name = "Majestic weather fall" };
            fall = Piece("Fall layer", Sphere(), fallMat);

            var go = new GameObject("Near drops") { layer = BallLook.OverlayLayer };
            go.transform.SetParent(root.transform, false);
            drops = go.AddComponent<ParticleSystem>();
            drops.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);
            var main = drops.main; main.loop = true; main.playOnAwake = false; main.maxParticles = MaxDrops;
            main.simulationSpace = ParticleSystemSimulationSpace.World; main.startSpeed = 0; main.gravityModifier = 0;
            var emission = drops.emission; emission.enabled = false;
            var shape = drops.shape; shape.enabled = false;
            dropRenderer = go.GetComponent<ParticleSystemRenderer>();
            dropMat = new Material(dropShader) { name = "Majestic weather drops" };
            dropRenderer.sharedMaterial = dropMat; dropRenderer.shadowCastingMode = ShadowCastingMode.Off; dropRenderer.receiveShadows = false;

            wallMat = SkyMat(skyShader, "Storm wall", 2, false, 2620);
            wall = Piece("Storm wall", Band(), wallMat);
            rainbowMat = SkyMat(skyShader, "Rainbow", 0, true, 2630);
            rainbow = Piece("Rainbow", Ring(), rainbowMat);
            beamsMat = SkyMat(skyShader, "Sunbeams", 1, true, 2640);
            beams = Piece("Sunbeams", Fan(), beamsMat);
            bombMat = SkyMat(skyShader, "Lava bomb", 3, true, 3010);
            mirrorMat = new Material(Resources.Load<Shader>("Majestic/MajesticWeatherReflect")) { name = "Majestic weather wet court mirror" };
            mirror = Piece("Wet court mirror", Quad(), mirrorMat);
            var sphere = Sphere(6, 4);
            for (int i = 0; i < 8; i++)
            {
                var b = Piece("Lava bomb " + i, sphere, bombMat);
                var tail = new GameObject("Trail") { layer = BallLook.OverlayLayer };   // (one Renderer per GameObject)
                tail.transform.SetParent(b.transform, false);
                var trail = tail.AddComponent<TrailRenderer>();
                trail.sharedMaterial = bombMat; trail.time = .9f; trail.minVertexDistance = 2f; trail.time = 1.2f;
                trail.widthCurve = new AnimationCurve(new Keyframe(0, 7f), new Keyframe(1, 0));
                trail.shadowCastingMode = ShadowCastingMode.Off; trail.receiveShadows = false; trail.emitting = false;
                b.gameObject.SetActive(false);
                bombs.Add((b.transform, trail, Vector3.zero));
            }
            Hide();
        }

        Renderer Piece(string name, Mesh mesh, Material m)
        {
            var go = new GameObject(name) { layer = BallLook.OverlayLayer };
            go.transform.SetParent(root.transform, false);
            go.AddComponent<MeshFilter>().sharedMesh = mesh;
            var r = go.AddComponent<MeshRenderer>();
            r.sharedMaterial = m; r.shadowCastingMode = ShadowCastingMode.Off; r.receiveShadows = false;
            r.lightProbeUsage = LightProbeUsage.Off; r.reflectionProbeUsage = ReflectionProbeUsage.Off;
            return r;
        }

        static Material SkyMat(Shader s, string name, int mode, bool additive, int queue)
        {
            var m = new Material(s) { name = "Majestic weather " + name, renderQueue = queue };
            m.SetFloat("_Mode", mode);
            m.SetFloat("_SrcBlend", additive ? (float)BlendMode.One : (float)BlendMode.SrcAlpha);
            m.SetFloat("_DstBlend", additive ? (float)BlendMode.One : (float)BlendMode.OneMinusSrcAlpha);
            return m;
        }

        public void Hide()
        {
            fall.enabled = false; wall.enabled = false; rainbow.enabled = false; beams.enabled = false;
            Mirror(null, false);
            if (drops) { drops.Clear(); drops.Stop(); }
            foreach (var b in bombs) if (b.t) b.t.gameObject.SetActive(false);
        }

        public void Destroy() { if (root) Object.Destroy(root); }

        float R(float a, float b) => a + (float)rng.NextDouble() * (b - a);

        // ------------------------------------------------------------------ per frame
        static readonly int AmountId = Shader.PropertyToID("_Amount"), KindId = Shader.PropertyToID("_Kind"), ColorId = Shader.PropertyToID("_Color"),
            WindId = Shader.PropertyToID("_Slant"), CorridorId = Shader.PropertyToID("_CorridorSS"), CorridorRId = Shader.PropertyToID("_CorridorR"),
            FlashId = Shader.PropertyToID("_Flash"), GlowId = Shader.PropertyToID("_Glow"), GlowId2 = Shader.PropertyToID("_Glow"), SpeedId = Shader.PropertyToID("_Speed");

        public void Update(MajesticWeather w, Camera cam, float now, float dt)
        {
            if (!w.Active) { Hide(); return; }
            var look = w.Now;
            var at = cam.transform.position;
            root.layer = BallLook.OverlayLayer;
            float far = Mathf.Min(cam.farClipPlane * .62f, w.Tennis ? 700 : 1300);

            // the fall layer: around the lens, drawn over everything at low alpha, never over the ball's line
            int kind = (int)look.Fall;
            bool falling = look.Precip > .01f && kind > 0;
            fall.enabled = falling;
            Vector4 corridor = Vector4.zero; float corridorR = 0;
            if (falling || look.Precip > 0)
            {
                var a = cam.WorldToViewportPoint(w.CorridorA); var b = cam.WorldToViewportPoint(Vector3.Lerp(w.CorridorA, w.CorridorB, .35f));
                if (a.z > 0)
                {
                    if (b.z <= 0) b = a;
                    corridor = new Vector4(a.x, a.y, b.x, b.y); corridorR = w.Tennis ? 0 : .07f;
                }
            }
            if (falling)
            {
                fall.transform.position = at; fall.transform.localScale = Vector3.one * Mathf.Max(cam.nearClipPlane * 4, 2f);
                var lit = Color.Lerp(w.FogColour * 1.25f, Color.white, look.Fall == WeatherFall.Snow ? .6f : .15f);
                if (look.Fall == WeatherFall.Ash) lit = new Color(.42f, .4f, .4f);
                fallMat.SetFloat(AmountId, look.Precip);
                fallMat.SetFloat(KindId, kind);
                fallMat.SetColor(ColorId, lit + new Color(.3f, .32f, .4f) * w.Flash);
                fallMat.SetFloat(WindId, Vector2.Dot(w.WindDir, new Vector2(cam.transform.right.x, cam.transform.right.z)) * (look.Wind * .5f + w.GustNow * .4f) * (kind == 1 ? .25f : 1f));
                fallMat.SetFloat(SpeedId, kind == 1 ? 1 : kind == 2 ? .16f + .3f * look.Wind : .11f);
                fallMat.SetFloat(GlowId, look.Embers);
                fallMat.SetVector(CorridorId, corridor); fallMat.SetFloat(CorridorRId, corridorR);
            }
            NearDrops(w, cam, look, dt);

            // the sky
            var fwd = cam.transform.forward; fwd.y = 0; if (fwd.sqrMagnitude < 1e-4f) fwd = Vector3.forward; fwd.Normalize();
            float storm = look.StormWall;
            wall.enabled = storm > .02f;
            if (wall.enabled)
            {
                var toward = Quaternion.Euler(0, 32, 0) * fwd;
                wall.transform.SetPositionAndRotation(at, Quaternion.LookRotation(toward));
                wall.transform.localScale = Vector3.one * far;
                wallMat.SetFloat(AmountId, storm * Mathf.Lerp(.55f, 1, look.Cloud));
                bool ash = w.Family == Sky.Ash;
                var deck = ash ? new Color(.16f, .1f, .09f) : Color.Lerp(new Color(.1f, .115f, .15f), new Color(.24f, .26f, .31f), 1 - storm);
                wallMat.SetColor(ColorId, deck * Mathf.Clamp(RenderSettings.ambientSkyColor.maxColorComponent * 1.4f, .45f, 1.1f));
                wallMat.SetColor(GlowId2, ash ? new Color(1f, .38f, .12f) * (.35f + .65f * w.Flash) : Color.black);
                wallMat.SetFloat(FlashId, w.Flash);
            }
            rainbow.enabled = w.Rainbow > .01f;
            if (rainbow.enabled)
            {
                var toward = w.Tennis ? Vector3.forward : TowardPin(at, fwd);
                var centre = (toward - Vector3.up * .32f).normalized;
                rainbow.transform.SetPositionAndRotation(at + centre * far, Quaternion.LookRotation(centre));
                rainbow.transform.localScale = Vector3.one * far;
                rainbowMat.SetFloat(AmountId, w.Rainbow * .55f);
            }
            beams.enabled = w.Beams > .01f;
            if (beams.enabled)
            {
                var sun = RenderSettings.sun; var toSun = sun ? -sun.transform.forward : Vector3.up;
                var beamColor = sun ? sun.color : Color.white;
                if (w.Now.Shafts > .01f && w.Phase != WeatherPhase.Clearing)
                {
                    // storm: the sun breaking through on the far side from the storm wall, low and golden (W03), in view
                    toSun = (Quaternion.Euler(0, -38, 0) * fwd * Mathf.Cos(14 * Mathf.Deg2Rad) + Vector3.up * Mathf.Sin(14 * Mathf.Deg2Rad)).normalized;
                    beamColor = new Color(1f, .78f, .45f);
                }
                // storm shafts hang in the air in front of the near hills (w.Tennis: the stands); the clearing's sit far off
                float beamDist = w.Now.Shafts > .01f && w.Phase != WeatherPhase.Clearing ? (w.Tennis ? 45 : 85) : far;
                beams.transform.SetPositionAndRotation(at + toSun * beamDist, Quaternion.LookRotation(toSun) * Quaternion.Euler(0, 0, now * 1.5f));
                beams.transform.localScale = Vector3.one * beamDist;
                beamsMat.SetFloat(AmountId, w.Beams * .32f);
                // storm shafts are light in the air between camera and hills: drawn over them (clearing beams stay behind the scene)
                beamsMat.SetFloat("_ZTest", w.Now.Shafts > .01f && w.Phase != WeatherPhase.Clearing ? (float)CompareFunction.Always : (float)CompareFunction.LessEqual);
                beamsMat.SetColor(ColorId, beamColor);
            }
            Bombs(dt);
            Mirror(cam, w.Tennis && look.Wet > .03f);
        }

        /// The wet court's mirror needs the opaque colour copy on the gameplay camera while (only while) it shows.
        void Mirror(Camera cam, bool on)
        {
            if (!mirror) return;
            if (on && cam)
            {
                mirror.enabled = true;
                mirror.transform.SetPositionAndRotation(new Vector3(0, .004f, 0), Quaternion.identity);
                mirror.transform.localScale = new Vector3(TennisVenue.DeckHalfX * 2 + 4, 1, TennisVenue.DeckHalfZ * 2 + 4);
                var data = cam.GetUniversalAdditionalCameraData();
                if (data != mirrorCam) { Mirror(null, false); mirrorCam = data; mirrorCamHadColor = data.requiresColorTexture; }
                data.requiresColorTexture = true;
                return;
            }
            mirror.enabled = false;
            if (mirrorCam) { mirrorCam.requiresColorTexture = mirrorCamHadColor; mirrorCam = null; }
        }

        static Mesh Quad()
        {
            var m = new Mesh { name = "Majestic weather mirror" };
            m.SetVertices(new List<Vector3> { new(-.5f, 0, -.5f), new(.5f, 0, -.5f), new(-.5f, 0, .5f), new(.5f, 0, .5f) });
            m.SetTriangles(new[] { 0, 2, 1, 1, 2, 3 }, 0); m.RecalculateBounds();
            return m;
        }

        static Vector3 TowardPin(Vector3 at, Vector3 fallback)
        {
            var golf = Object.FindFirstObjectByType<GolfGame>();
            if (golf && golf.CurrentHole != null)
            {
                var d = HoleView.ToWorld(golf.CurrentHole.Pin) - at; d.y = 0;
                if (d.sqrMagnitude > 400) return d.normalized;
            }
            return fallback;
        }

        // ------------------------------------------------------------------ near drops (<= 400, never in the corridor)
        void NearDrops(MajesticWeather w, Camera cam, WeatherLook look, float dt)
        {
            int kind = (int)look.Fall;
            // gusts with nothing falling: petals and leaves racing past (Sky.Rain biomes), embers in the ash biome
            bool debris = kind == 0 && look.Gust > .3f && w.PlayShare > .5f;
            float amount = debris ? look.Gust * (.7f + .5f * w.GustNow) : look.Precip * (kind == 3 ? .55f : 1);   // ash: fewer, larger flakes
            if (amount < .01f || (kind == 0 && !debris)) { if (drops.isPlaying || drops.particleCount > 0) { drops.Clear(); drops.Stop(); } return; }
            if (!drops.isPlaying) drops.Play();
            if (debris) kind = w.Family == Sky.Ash ? 3 : 4;
            bool rain = kind == 1;
            float life = rain ? .55f : kind == 4 ? 1.6f : 3.2f;
            dropRenderer.renderMode = rain ? ParticleSystemRenderMode.Stretch : ParticleSystemRenderMode.Billboard;
            dropRenderer.velocityScale = rain ? .045f : 0; dropRenderer.lengthScale = rain ? 1 : 1;
            dropMat.SetFloat(KindId, kind);
            if (kind == 4 && w.Tennis) clearRTennis = 7f; else clearRTennis = 2.2f;
            var lit = rain ? Color.Lerp(w.FogColour * 1.4f, Color.white, .3f) : kind == 2 ? new Color(.97f, .98f, 1f) : new Color(.36f, .34f, .34f);
            int cap = Mathf.RoundToInt(MaxDrops * Mathf.Clamp01(amount));
            spawnDebt += cap / life * dt;
            int n = Mathf.Min((int)spawnDebt, Mathf.Max(0, cap - drops.particleCount)); spawnDebt -= (int)spawnDebt;
            if (n <= 0) return;
            var t = cam.transform; var at = t.position;
            var wind = new Vector3(w.WindDir.x, 0, w.WindDir.y) * (look.Wind * 4 + w.GustNow * 5) * (w.Tennis ? 1f : 1.09f);
            var fall = rain ? Vector3.down * 22f + wind * .5f : kind == 4 ? Vector3.down * .4f + wind * 1.6f : Vector3.down * (kind == 2 ? 1.6f : 1.1f) + wind * (kind == 2 ? .9f : .5f);
            float tanH = Mathf.Tan(cam.fieldOfView * .5f * Mathf.Deg2Rad);
            float clearR = w.Tennis ? clearRTennis : 3.2f;   // tennis debris keeps off the whole court's width
            for (int i = 0; i < n; i++)
            {
                for (int attempt = 0; attempt < 4; attempt++)
                {
                    float z = Mathf.Lerp(rain ? 1.6f : 3.5f, 16f, Mathf.Pow(R(0, 1), 1.6f));
                    float x = R(-1, 1) * z * tanH * cam.aspect * 1.15f, y = R(-1, 1.2f) * z * tanH * 1.15f;
                    var p = at + t.forward * z + t.right * x + t.up * y;
                    var end = p + fall * life * 1.15f;   // (the longest life a drop can get)
                    bool hit = false;
                    float margin = kind == 4 ? 1.2f : kind == 1 ? .2f : .5f;   // room for each drop's own jitter (petals drift most)
                    for (int k = 0; k <= 8 && !hit; k++) hit = InCorridor(Vector3.Lerp(p, end, k / 8f), w, clearR + margin);   // the whole path, not its ends
                    if (hit) { Rejected++; continue; }
                    float size = rain ? R(.012f, .022f) : kind == 2 ? R(.03f, .06f) : R(.035f, .07f);
                    var c = lit; c.a = rain ? R(.35f, .6f) : R(.7f, .95f);
                    if (kind == 3 && R(0, 1) < (debris ? .8f : .12f * look.Embers)) { c = new Color(1f, R(.35f, .6f), .12f, 1f); size *= .7f; }
                    if (kind == 4) { c = Petals[rng.Next(Petals.Length)]; size = R(.12f, .26f); }
                    var v = fall + new Vector3(R(-.3f, .3f), R(-.5f, .5f), R(-.3f, .3f)) * (rain ? 1 : .6f);
                    drops.Emit(new ParticleSystem.EmitParams { position = p, velocity = v, startSize = size, startColor = c, startLifetime = life * R(.8f, 1.1f) }, 1);
                    break;
                }
            }
        }

        static readonly Color[] Petals = { new(1f, .55f, .7f), new(1f, .8f, .3f), new(.95f, .3f, .3f), new(.45f, .72f, .28f), new(1f, .95f, .9f), new(.35f, .6f, .25f) };

        /// Inside the ball corridor: within `r` of the line from the ball to its target, or of the camera's sight line to the ball.
        public static bool InCorridor(Vector3 p, MajesticWeather w, float r)
        {
            if (w.Tennis) return Seg(p, w.CorridorA, w.CorridorB) < r;
            return Seg(p, w.CorridorA, w.CorridorB) < r || (w.Cam && Seg(p, w.Cam.transform.position, w.CorridorA) < r * .5f);
        }

        static float Seg(Vector3 p, Vector3 a, Vector3 b)
        {
            var ab = b - a; float t = Mathf.Clamp01(Vector3.Dot(p - a, ab) / Mathf.Max(ab.sqrMagnitude, 1e-4f));
            return Vector3.Distance(p, a + ab * t);
        }

        // ------------------------------------------------------------------ eruption
        public void Erupt(MajesticWeather w, Camera cam)
        {
            var at = cam.transform.position;
            var fwd = cam.transform.forward; fwd.y = 0; fwd = fwd.sqrMagnitude > 1e-4f ? fwd.normalized : Vector3.forward;
            if (w.Tennis) bombVent = new Vector3(4, 28, 168);
            else bombVent = at + Quaternion.Euler(0, 14, 0) * TowardPin(at, fwd) * 210 + Vector3.up * 45;
            for (int i = 0; i < bombs.Count; i++)
            {
                var (t, trail, _) = bombs[i];
                t.gameObject.SetActive(true); t.position = bombVent + new Vector3(R(-4, 4), 0, R(-4, 4)); t.localScale = Vector3.one * R(8f, 14f);
                trail.Clear(); trail.emitting = true; trail.time = .9f;
                var side = Quaternion.Euler(0, R(0, 360), 0) * Vector3.forward;
                bombs[i] = (t, trail, side * R(10, 26) + Vector3.up * R(34, 52));
            }
            bombsUntil = Time.time + 5.5f;
        }

        void Bombs(float dt)
        {
            bool live = Time.time < bombsUntil;
            for (int i = 0; i < bombs.Count; i++)
            {
                var (t, trail, v) = bombs[i];
                if (!t || !t.gameObject.activeSelf) continue;
                if (!live) { trail.emitting = false; t.gameObject.SetActive(false); continue; }
                v += Vector3.down * 16f * dt; t.position += v * dt;
                bombs[i] = (t, trail, v);
            }
            bombMat.SetFloat(AmountId, 1);
        }

        // ------------------------------------------------------------------ meshes
        static Mesh Sphere(int seg = 24, int rings = 12)
        {
            var m = new Mesh { name = "Majestic weather sphere" };
            var v = new List<Vector3>(); var idx = new List<int>();
            for (int j = 0; j <= rings; j++)
                for (int i = 0; i <= seg; i++)
                {
                    float th = Mathf.PI * j / rings, ph = 2 * Mathf.PI * i / seg;
                    v.Add(new Vector3(Mathf.Sin(th) * Mathf.Cos(ph), Mathf.Cos(th), Mathf.Sin(th) * Mathf.Sin(ph)));
                }
            for (int j = 0; j < rings; j++)
                for (int i = 0; i < seg; i++)
                {
                    int a = j * (seg + 1) + i, b = a + seg + 1;
                    idx.AddRange(new[] { a, a + 1, b, a + 1, b + 1, b });
                }
            m.SetVertices(v); m.SetTriangles(idx, 0); m.RecalculateBounds();
            return m;
        }

        /// Storm wall: a band of the horizon, 150° wide, -3°..30° up, unit radius; uv = (azimuth 0..1, elevation 0..1).
        static Mesh Band()
        {
            var m = new Mesh { name = "Majestic storm wall" };
            const int seg = 40; var v = new List<Vector3>(); var uv = new List<Vector2>(); var idx = new List<int>();
            for (int i = 0; i <= seg; i++)
            {
                float u = i / (float)seg, az = (u - .5f) * 150 * Mathf.Deg2Rad;
                for (int j = 0; j <= 1; j++)
                {
                    float el = (j == 0 ? -3 : 30) * Mathf.Deg2Rad;
                    v.Add(new Vector3(Mathf.Sin(az) * Mathf.Cos(el), Mathf.Sin(el), Mathf.Cos(az) * Mathf.Cos(el)));
                    uv.Add(new Vector2(u, j));
                }
            }
            for (int i = 0; i < seg; i++) { int a = i * 2; idx.AddRange(new[] { a, a + 1, a + 2, a + 1, a + 3, a + 2 }); }
            m.SetVertices(v); m.SetUVs(0, uv); m.SetTriangles(idx, 0); m.RecalculateBounds();
            return m;
        }

        /// Rainbow: a ring of angular radius 42° (and the faint secondary at 51°) seen from the origin, centred on +Z at
        /// unit distance; uv.x = across the band (0 inner .. 1 outer), uv.y = along it; uv2.x = 1 for the secondary bow.
        static Mesh Ring()
        {
            var m = new Mesh { name = "Majestic rainbow" };
            var v = new List<Vector3>(); var uv = new List<Vector2>(); var uv2 = new List<Vector2>(); var idx = new List<int>();
            void Bow(float deg, float width, float secondary)
            {
                int start = v.Count; const int seg = 64;
                float r0 = Mathf.Tan((deg - width) * Mathf.Deg2Rad), r1 = Mathf.Tan((deg + width) * Mathf.Deg2Rad);
                for (int i = 0; i <= seg; i++)
                {
                    float a = Mathf.PI * i / seg;   // upper half only (the lower half is under the ground)
                    var dir = new Vector3(Mathf.Cos(a), Mathf.Sin(a), 0);
                    v.Add(dir * r0); v.Add(dir * r1);
                    uv.Add(new Vector2(0, i / (float)seg)); uv.Add(new Vector2(1, i / (float)seg));
                    uv2.Add(new Vector2(secondary, 0)); uv2.Add(new Vector2(secondary, 0));
                }
                for (int i = 0; i < seg; i++) { int a = start + i * 2; idx.AddRange(new[] { a, a + 1, a + 2, a + 1, a + 3, a + 2 }); }
            }
            Bow(42, 1.6f, 0); Bow(51, 1.9f, 1);
            m.SetVertices(v); m.SetUVs(0, uv); m.SetUVs(1, uv2); m.SetTriangles(idx, 0); m.RecalculateBounds();
            return m;
        }

        /// Sunbeams: nine rays fanning out from the sun's point (origin) in its plane; uv.x = along (0 at the sun), uv.y = across -1..1.
        static Mesh Fan()
        {
            var m = new Mesh { name = "Majestic sunbeams" };
            var v = new List<Vector3>(); var uv = new List<Vector2>(); var idx = new List<int>();
            var rng = new System.Random(31);
            for (int i = 0; i < 9; i++)
            {
                float a = (i / 9f + (float)rng.NextDouble() * .06f) * Mathf.PI * 2, len = .45f + (float)rng.NextDouble() * .35f, w0 = .01f, w1 = .05f + (float)rng.NextDouble() * .05f;
                var d = new Vector3(Mathf.Cos(a), Mathf.Sin(a), 0); var s = new Vector3(-d.y, d.x, 0);
                int b = v.Count;
                v.Add(-s * w0); v.Add(s * w0); v.Add(d * len - s * w1); v.Add(d * len + s * w1);
                uv.Add(new Vector2(0, -1)); uv.Add(new Vector2(0, 1)); uv.Add(new Vector2(1, -1)); uv.Add(new Vector2(1, 1));
                idx.AddRange(new[] { b, b + 2, b + 1, b + 1, b + 2, b + 3 });
            }
            m.SetVertices(v); m.SetUVs(0, uv); m.SetTriangles(idx, 0); m.RecalculateBounds();
            return m;
        }
    }
}
