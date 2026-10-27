using MotionSports.Brand;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace GolfArcade.Bowling
{
    /// Club Lanes, the bowling venue (PLAN_Bowling.md §7.1), lit the way the best modern alleys are
    /// (boutique lanes, cosmic/night bowling, TV bowling sets), in the MotionSports brand palette:
    ///   * a dark navy room, so the light lives on the lanes: the pin deck is the brightest thing
    ///     in view, the lanes glow and reflect, everything else falls off into navy;
    ///   * glossy maple lanes that mirror the lights, pins and masking (reflection probe);
    ///   * lane-guard LED strips (Glow Blue) running the length of every capping: leading lines
    ///     straight to the pins;
    ///   * masking units as big lit brand panels with the swing-arc motif, score monitors above;
    ///   * a spotlit pin deck in a black shadow box, so the polished pins pop;
    ///   * a neon swing arc over the lanes, warm pendant lights over the settee, a cosmic carpet;
    ///   * bloom, ACES tonemapping and a bottom-corner vignette (brand guide §4).
    /// Everything sits on the BowlingLane dimensions; only the dressing changed from the P0 greybox.
    public static class BowlingClubLanes
    {
        public const float LanePitch = BowlingAlley.LanePitch;
        /// The settee behind the approach, where the players who are not bowling sit.
        public const float LoungeZ = -11.2f;
        const int LanesEachSide = 2;

        static readonly Color Maple = new Color(.93f, .74f, .50f), Pine = new Color(.98f, .82f, .58f);

        // ------------------------------------------------------------------ materials

        internal static Shader Lit => Shader.Find("Universal Render Pipeline/Lit");

        internal static Material Surface(Color c, float smooth, Texture tex = null, Vector2? tiling = null, float metallic = 0)
        {
            var m = new Material(Lit);
            m.SetColor("_BaseColor", c);
            if (tex) { m.SetTexture("_BaseMap", tex); if (tiling.HasValue) m.SetTextureScale("_BaseMap", tiling.Value); }
            m.SetFloat("_Smoothness", smooth); m.SetFloat("_Metallic", metallic);
            m.enableInstancing = true;
            return m;
        }

        /// A glowing surface: `intensity` > 1 is HDR, so bloom picks it up.
        public static Material Glow(Color c, float intensity, Texture tex = null)
        {
            var m = Surface(Color.black, .5f);
            m.SetColor("_EmissionColor", c * intensity);
            if (tex) { m.SetTexture("_EmissionMap", tex); m.SetColor("_BaseColor", Color.white * .05f); }
            m.EnableKeyword("_EMISSION");
            m.globalIlluminationFlags = MaterialGlobalIlluminationFlags.None;
            return m;
        }

        // ------------------------------------------------------------------ textures

        /// The swing arc (brand guide §7): part of a 4:3 ellipse, tapering from 15 % at the tail to
        /// full width at the head, white core with an Arc Warm fringe and a soft glow, alpha 0 → 1.
        /// Drawn into an RGBA texture on a background (alpha 0 when `background` is clear).
        public static Texture2D ArcTexture(int w, int h, Color background, float sweepFrom = 200, float sweepTo = 340, float width = .05f, bool echoes = true)
        {
            var tex = new Texture2D(w, h, TextureFormat.RGBA32, true) { wrapMode = TextureWrapMode.Clamp, name = "SwingArc" };
            var px = new Color[w * h];
            for (int i = 0; i < px.Length; i++) px[i] = background;
            void Arc(float rx, float ry, float a0, float a1, float wid, Color core, Color fringe, float alpha, bool taper)
            {
                int steps = 900;
                for (int s = 0; s <= steps; s++)
                {
                    float t = s / (float)steps, a = Mathf.Lerp(a0, a1, t) * Mathf.Deg2Rad;
                    float cx = .5f + Mathf.Cos(a) * rx, cy = .18f - Mathf.Sin(a) * ry;   // centre low, arc over the top
                    float half = wid * (taper ? Mathf.Lerp(.15f, 1f, t) : 1) * .5f;
                    float al = alpha * (taper ? t : 1);
                    int r = Mathf.CeilToInt(half * 2.2f * w);
                    int px0 = Mathf.RoundToInt(cx * w), py0 = Mathf.RoundToInt(cy * h);
                    for (int dy = -r; dy <= r; dy++)
                        for (int dx = -r; dx <= r; dx++)
                        {
                            int x = px0 + dx, y = py0 + dy;
                            if (x < 0 || y < 0 || x >= w || y >= h) continue;
                            float d = Mathf.Sqrt(dx * dx + dy * dy) / (half * w + 1e-4f);
                            if (d > 2.2f) continue;
                            // core (42 % of the width), warm fringe, then soft glow
                            Color c; float k;
                            if (d < .42f) { c = core; k = 1; }
                            else if (d < 1) { c = Color.Lerp(core, fringe, (d - .42f) / .58f); k = 1; }
                            else { c = fringe; k = Mathf.Pow(1 - (d - 1) / 1.2f, 2) * .5f; }
                            k *= al;
                            var o = px[y * w + x];
                            px[y * w + x] = new Color(Mathf.Max(o.r, c.r * k + o.r * (1 - k)), Mathf.Max(o.g, c.g * k + o.g * (1 - k)), Mathf.Max(o.b, c.b * k + o.b * (1 - k)), Mathf.Max(o.a, k));
                        }
                }
            }
            if (echoes)
            {
                // three faint concentric arcs behind (white 8 %, gold 10 %, white 5 %), 198–342°
                Arc(.43f, .60f, 198, 342, .010f, Color.white, Color.white, .08f, false);
                Arc(.40f, .55f, 198, 342, .006f, BrandColors.Gold, BrandColors.Gold, .10f, false);
                Arc(.46f, .66f, 198, 342, .016f, Color.white, Color.white, .05f, false);
            }
            Arc(.36f, .48f, sweepFrom, sweepTo, width, Color.white, BrandColors.ArcWarm, 1, true);
            tex.SetPixels(px); tex.Apply(true);
            return tex;
        }

        /// Masking-unit art: the brand background gradient (Deep Navy → Royal) with a swing arc.
        internal static Texture2D MaskingArt()
        {
            const int w = 512, h = 256;
            var tex = ArcTexture(w, h, Color.clear, 205, 335, .045f);
            var px = tex.GetPixels();
            var g = BrandColors.Background();
            for (int y = 0; y < h; y++)
                for (int x = 0; x < w; x++)
                {
                    // vertical brand gradient (top = navy), with the Lift spotlight behind the centre
                    float v = 1 - y / (float)h;
                    var bg = g.Evaluate(Mathf.SmoothStep(0, 1, v));
                    float dx = (x / (float)w - .5f) * 1.6f, dy = (y / (float)h - .45f);
                    float spot = Mathf.Pow(Mathf.Clamp01(1 - Mathf.Sqrt(dx * dx + dy * dy) / .48f), 1.6f) * .55f;
                    bg = Color.Lerp(bg, BrandColors.Lift, spot);
                    var a = px[y * w + x];
                    px[y * w + x] = bg * (1 - a.a) + new Color(a.r, a.g, a.b);   // the arc is premultiplied
                }
            tex.SetPixels(px); tex.Apply(true);
            return tex;
        }

        /// Cosmic bowling-alley carpet: navy with scattered brand arcs and dots.
        internal static Texture2D Carpet()
        {
            const int n = 256;
            var tex = new Texture2D(n, n, TextureFormat.RGBA32, true) { wrapMode = TextureWrapMode.Repeat, name = "ClubCarpet" };
            var px = new Color[n * n];
            var rng = new System.Random(11);
            for (int i = 0; i < px.Length; i++) px[i] = Color.Lerp(BrandColors.N900, BrandColors.NavyInk, (float)rng.NextDouble() * .5f);
            Color[] inks = { BrandColors.Royal, BrandColors.Glow, BrandColors.Gold, BrandColors.Bright };
            for (int k = 0; k < 70; k++)
            {
                var c = inks[rng.Next(inks.Length)];
                int cx = rng.Next(n), cy = rng.Next(n), r = 4 + rng.Next(14);
                float a0 = (float)rng.NextDouble() * Mathf.PI * 2, span = 1.2f + (float)rng.NextDouble() * 1.5f;
                bool dot = rng.NextDouble() < .45;
                for (int s = 0; s < 60; s++)
                {
                    float a = a0 + span * s / 60f;
                    int x = dot ? cx : (cx + Mathf.RoundToInt(Mathf.Cos(a) * r) + n) % n, y = dot ? cy : (cy + Mathf.RoundToInt(Mathf.Sin(a) * r) + n) % n;
                    for (int dy = -1; dy <= 1; dy++) for (int dx = -1; dx <= 1; dx++) px[((y + dy + n) % n) * n + (x + dx + n) % n] = c * .8f;
                    if (dot) break;
                }
            }
            tex.SetPixels(px); tex.Apply(true);
            return tex;
        }

        // ------------------------------------------------------------------ geometry helpers

        internal static GameObject Box(Transform p, string name, Vector3 c, Vector3 s, Material m) => BowlingAlley.Box(p, name, c, s, m);

        /// A Unity quad faces -z, i.e. the bowler and the TV camera, with its texture upright.
        internal static GameObject Quad(Transform p, string name, Vector3 c, Vector3 s, Material m)
        {
            var go = GameObject.CreatePrimitive(PrimitiveType.Quad);
            Object.Destroy(go.GetComponent<Collider>());
            go.name = name; go.transform.SetParent(p, false);
            go.transform.localPosition = c; go.transform.localScale = s;
            go.GetComponent<MeshRenderer>().sharedMaterial = m;
            return go;
        }

        internal static void Light(Transform parent, string name, LightType type, Vector3 pos, Vector3 euler, Color color, float intensity, float range, float angle = 0, LightShadows shadows = LightShadows.None)
        {
            var l = new GameObject(name).AddComponent<Light>();
            l.transform.SetParent(parent, false);
            l.transform.localPosition = pos; l.transform.localRotation = Quaternion.Euler(euler);
            l.type = type; l.color = color; l.intensity = intensity; l.range = range; l.shadows = shadows;
            if (type == LightType.Spot) { l.spotAngle = angle; l.innerSpotAngle = angle * .55f; }
        }

        // ------------------------------------------------------------------ build

        public sealed class Venue
        {
            public Transform Root;
            public ReflectionProbe Probe, PinProbe;
            public Volume Post;
            public Majestic.MajesticCrowd Crowd;
            public BowlingVenueFx Fx;
            public readonly System.Collections.Generic.List<(Vector3 pos, float yaw)> Seats = new System.Collections.Generic.List<(Vector3 pos, float yaw)>();
        }

        /// Tiered seating: `rows` tiers stepping up and away along `back`, `seats` per tier spaced along
        /// the gallery; each seat is queued for the instanced crowd (filled at the end of Build).
        internal static void Gallery(Transform root, Vector3 front, Vector3 back, int seats, int rows, float yaw, Material step, Material trim, Venue venue, bool alongX = false)
        {
            const float Depth = .8f, Rise = .42f, Spacing = .62f;
            var along = alongX ? Vector3.right : Vector3.forward;
            float length = seats * Spacing;
            for (int r = 0; r < rows; r++)
            {
                float top = (r + 1) * Rise;
                var c = front + back * (Depth * (r + .5f)) + along * (length / 2) + Vector3.up * (top / 2);
                var size = alongX ? new Vector3(length, top, Depth) : new Vector3(Depth, top, length);
                Box(root, "GalleryTier", c, size, step);
                var lip = front + back * (Depth * r + .02f) + along * (length / 2) + Vector3.up * (top - .01f);
                Box(root, "GalleryTrim", lip, alongX ? new Vector3(length, .03f, .04f) : new Vector3(.04f, .03f, length), trim);
                for (int k = 0; k < seats; k++)
                {
                    // leave a few empty seats so it reads as a real night out, not a wall of fans
                    if ((k * 7 + r * 3) % 5 == 0) continue;
                    var at = front + back * (Depth * r + .45f) + along * (Spacing * (k + .5f)) + Vector3.up * top;
                    venue.Seats.Add((at, yaw));
                }
            }
        }

        /// Smoked glass for the windows: barely there, with a faint reflection.
        internal static Material Glass()
        {
            var m = new Material(Lit);
            m.SetFloat("_Surface", 1); m.SetFloat("_Blend", 0);
            m.SetOverrideTag("RenderType", "Transparent");
            m.SetInt("_SrcBlend", (int)BlendMode.SrcAlpha); m.SetInt("_DstBlend", (int)BlendMode.OneMinusSrcAlpha); m.SetInt("_ZWrite", 0);
            m.EnableKeyword("_SURFACE_TYPE_TRANSPARENT");
            m.renderQueue = (int)RenderQueue.Transparent;
            m.SetColor("_BaseColor", new Color(BrandColors.NavyDeep.r, BrandColors.NavyDeep.g, BrandColors.NavyDeep.b, .12f));
            m.SetFloat("_Smoothness", .95f);
            return m;
        }

        /// The view out of the windows: the sunset above the clouds (the tennis rooftop sky), on a big
        /// inward-facing cylinder round the building, horizon at about eye height.
        internal static void SkyDome(Transform root, string panorama = "Tennis/Premium/SkyRooftop", float bottom = -42, float top = 46, float brightness = .95f)
        {
            var tex = Resources.Load<Texture2D>(panorama);
            if (!tex) return;
            const int seg = 64; const float radius = 80;   // by default the panorama's horizon lands near eye height
            var v = new System.Collections.Generic.List<Vector3>(); var uv = new System.Collections.Generic.List<Vector2>(); var tri = new System.Collections.Generic.List<int>();
            for (int i = 0; i <= seg; i++)
            {
                float a = i / (float)seg * Mathf.PI * 2;
                var d = new Vector3(Mathf.Sin(a), 0, Mathf.Cos(a)) * radius;
                v.Add(d + Vector3.up * bottom); uv.Add(new Vector2(i / (float)seg * 2, 0));   // the panorama twice round
                v.Add(d + Vector3.up * top); uv.Add(new Vector2(i / (float)seg * 2, 1));
            }
            for (int i = 0; i < seg; i++)
            {
                int a = i * 2;
                tri.Add(a); tri.Add(a + 1); tri.Add(a + 2);   // wound to face inward
                tri.Add(a + 2); tri.Add(a + 1); tri.Add(a + 3);
            }
            var mesh = new Mesh { name = "SkyDome" }; mesh.SetVertices(v); mesh.SetUVs(0, uv); mesh.SetTriangles(tri, 0); mesh.RecalculateBounds();
            var go = new GameObject("SkyDome");
            go.transform.SetParent(root, false); go.transform.localPosition = new Vector3(0, 0, 5);
            go.AddComponent<MeshFilter>().sharedMesh = mesh;
            var mat = new Material(Shader.Find("Universal Render Pipeline/Unlit"));
            mat.SetTexture("_BaseMap", tex); mat.SetColor("_BaseColor", Color.white * brightness);
            var r = go.AddComponent<MeshRenderer>(); r.sharedMaterial = mat; r.shadowCastingMode = ShadowCastingMode.Off; r.receiveShadows = false;
        }


        /// What the five lanes are made of and how their pin decks are lit; every venue fills one in.
        internal sealed class LaneTheme
        {
            public Material Bed, Deck, Approach, Gutter, Capping, Led, Kickback, KickbackLed, ShadowBox, MaskingArt, MaskingFrame, MaskingLip, Monitor, MonitorFrame, Ink;
            /// Lane-guard LED per lane (lane index -2..2, side -1/+1); null = `Led` everywhere.
            public System.Func<int, float, Material> LedPattern;
            public Color PinSpot = new Color(1, .95f, .86f);
            public float PinSpotIntensity = 5, PinFace = 1.5f;
            /// The venue uses BowlingAlleyKit's geometry: Lanes() only lights the pin decks.
            public bool Kit;
            /// Emissive pin-deck light bar (kit venues light it from the kit's PinLight slot instead).
            public Material LedFor(int lane, float side) => LedPattern != null ? LedPattern(lane, side) : Led;
        }

        /// The shared lane kit: five regulation lanes (bed, deck, approach, foul line, gutters, capping
        /// with lane-guard LEDs, kickbacks, the black shadow box, masking unit, optional monitors) and
        /// the pin-deck light rig every venue uses (spot + face light = each pin's 2 light slots).
        internal static void Lanes(Transform root, LaneTheme t)
        {
            float w = BowlingLane.HalfWidth, g = BowlingLane.GutterWidth, end = BowlingLane.LaneEnd;
            float deckFrom = BowlingLane.FoulToHeadPin - .6f;
            for (int i = -LanesEachSide; i <= LanesEachSide; i++)
            {
                bool main = i == 0;
                var lane = new GameObject(main ? "Lane" : "NeighbourLane").transform;
                lane.SetParent(root, false); lane.localPosition = new Vector3(i * LanePitch, 0, 0);
                if (!t.Kit) LaneGeometry(lane, t, i, main, w, g, end, deckFrom);
                // The pinsetter spotlight: warm white straight down onto the deck, the hottest light in the room.
                Light(lane, "PinDeckSpot", LightType.Spot, new Vector3(0, .97f, BowlingLane.FoulToHeadPin - .55f), new Vector3(66, 0, 0),
                    t.PinSpot, main ? t.PinSpotIntensity : t.PinSpotIntensity * .9f, 4.5f, 84, main ? LightShadows.Soft : LightShadows.None);
                // from near the viewing direction, so every pin carries a long vertical highlight down its belly
                Light(lane, "PinFaceLight", LightType.Point, new Vector3(0, 1.05f, BowlingLane.FoulToHeadPin - 2.4f), Vector3.zero, t.PinSpot, main ? t.PinFace : t.PinFace * .75f, 5.5f);
            }
        }

        /// The greybox lane (pre-kit venues): boxes and quads on the BowlingLane dimensions.
        static void LaneGeometry(Transform lane, LaneTheme t, int i, bool main, float w, float g, float end, float deckFrom)
        {
            {
                Box(lane, "Bed", new Vector3(0, -.03f, deckFrom / 2), new Vector3(2 * w, .06f, deckFrom), t.Bed);
                Box(lane, "PinDeck", new Vector3(0, -.03f, (deckFrom + end) / 2), new Vector3(2 * w, .06f, end - deckFrom), t.Deck);
                Box(lane, "Approach", new Vector3(0, -.03f, -BowlingLane.ApproachLength / 2 - .4f), new Vector3(2 * (w + g + .14f), .06f, BowlingLane.ApproachLength + .8f), t.Approach);
                Box(lane, "FoulLine", new Vector3(0, .001f, .005f), new Vector3(2 * (w + g), .002f, .012f), t.Ink);
                foreach (float s in new[] { -1f, 1f })
                {
                    Box(lane, "Gutter", new Vector3(s * (w + g / 2), -BowlingLane.GutterDepth - .02f, end / 2), new Vector3(g, .04f, end), t.Gutter);
                    // the capping between lanes, with a lane-guard LED strip on its inner edge
                    Box(lane, "Capping", new Vector3(s * (w + g + .07f), .02f, deckFrom / 2), new Vector3(.14f, .1f, deckFrom), t.Capping);
                    Box(lane, "LaneGuardLED", new Vector3(s * (w + g + .005f), .072f, deckFrom / 2), new Vector3(.012f, .012f, deckFrom - .2f), t.LedFor(i, s));
                    // kickbacks: navy plates with a vertical LED edge where the pin deck starts
                    Box(lane, "Kickback", new Vector3(s * (BowlingLane.KickbackX + .05f), .45f, (deckFrom + end + 1.2f) / 2), new Vector3(.1f, .95f, end + 1.2f - deckFrom), t.Kickback);
                    Box(lane, "KickbackLED", new Vector3(s * (BowlingLane.KickbackX - .002f), .45f, deckFrom + .02f), new Vector3(.012f, .9f, .02f), t.KickbackLed);
                }
                // The shadow box around the pins: black, so the spotlit pins pop out of it.
                Box(lane, "Pit", new Vector3(0, -.32f, end + .55f), new Vector3(2 * (BowlingLane.KickbackX + .1f), .05f, 1.1f), t.ShadowBox);
                Box(lane, "Cushion", new Vector3(0, .4f, end + 1.15f), new Vector3(2 * (BowlingLane.KickbackX + .1f), 1.5f, .1f), t.ShadowBox);
                Box(lane, "ShadowBoxRoof", new Vector3(0, 1.0f, (deckFrom + end + 1.2f) / 2), new Vector3(2 * (BowlingLane.KickbackX + .1f), .05f, end + 1.2f - deckFrom), t.ShadowBox);
                // Masking unit: a big lit brand panel with the swing arc, a gold trim lip, a score monitor above.
                Quad(lane, "MaskingArt", new Vector3(0, 1.62f, deckFrom - .16f), new Vector3(2 * (BowlingLane.KickbackX + .15f), 1.15f, 1), t.MaskingArt);
                Box(lane, "MaskingFrame", new Vector3(0, 1.62f, deckFrom - .12f), new Vector3(2 * (BowlingLane.KickbackX + .2f), 1.25f, .06f), t.MaskingFrame);
                Box(lane, "MaskingLip", new Vector3(0, 1.02f, deckFrom - .2f), new Vector3(2 * (BowlingLane.KickbackX + .2f), .05f, .1f), t.MaskingLip);
                if (t.Monitor) Box(lane, "MonitorFrame", new Vector3(0, 2.62f, deckFrom - .25f), new Vector3(1.25f, .66f, .06f), t.MonitorFrame);
                if (t.Monitor) Box(lane, "Monitor", new Vector3(0, 2.62f, deckFrom - .29f), new Vector3(1.15f, .57f, .01f), t.Monitor);

                // the pinsetter light bar: a bright strip across the front of the shadow box. It is what
                // the lacquered pins mirror (long vertical highlights), and it lights their faces.
                Box(lane, "PinLightBar", new Vector3(0, .93f, deckFrom + .05f), new Vector3(2 * BowlingLane.HalfWidth, .03f, .05f), Glow(t.PinSpot, 4));
                // tall light strips on the inside of the kickbacks, beside the rack: what the lacquered
                // pins mirror as long vertical highlights (reflection probe; they cost no light slots)
                foreach (float s in new[] { -1f, 1f })
                {
                    Box(lane, "PinDeckStrip", new Vector3(s * (BowlingLane.KickbackX - .005f), .5f, BowlingLane.FoulToHeadPin + .45f), new Vector3(.01f, .8f, .06f), Glow(Color.white, 3.5f));
                }

                if (main) BowlingAlley.Markings(lane);
            }
        }

        public static Venue Build(Transform parent, Camera camera)
        {
            var root = new GameObject("ClubLanes").transform;
            root.SetParent(parent, false);
            var venue = new Venue { Root = root };
            venue.Fx = root.gameObject.AddComponent<BowlingVenueFx>();

            // The alley itself: the shared kit (12 lanes, returns, consoles, monitors, settees) in Club Lanes'
            // navy, brass and walnut, on lacquered maple (work/bowling-look/PLAN_BowlingLook.md).
            var gold = BowlingAlleyKit.Plain(BrandColors.Gold * .9f, .82f, 1);
            var navyGloss = BowlingAlleyKit.Plain(BrandColors.NavyDeep * .95f, .86f);
            var navyMatte = BowlingAlleyKit.Plain(BrandColors.NavyDeep * .7f, .45f);
            var black = BowlingAlleyKit.Plain(new Color(.01f, .012f, .02f), .1f);
            var screen = BowlingAlleyKit.Emissive(Color.white, 1.1f, BowlingAlleyKit.Tex("ScoreScreen_Emission"));
            var masking = BowlingAlleyKit.Emissive(Color.white, 1.25f, BowlingAlleyKit.Tex("MaskingClub_Emission"));
            var slots = new System.Collections.Generic.Dictionary<string, Material>
            {
                ["LaneMaple"] = BowlingAlleyKit.Lane("LaneMaple", Color.white, .97f),
                ["LanePine"] = BowlingAlleyKit.Lane("LanePine", Color.white, .97f),
                ["Approach"] = BowlingAlleyKit.Lane("Approach", Color.white * .95f, .8f, .5f, .25f),
                ["Ink"] = BowlingAlleyKit.Plain(new Color(.07f, .045f, .03f), .7f),
                ["Gutter"] = BowlingAlleyKit.Plain(new Color(.42f, .44f, .5f), .9f, .92f),   // brushed steel: mirrors the lanes and lights
                ["Capping"] = navyGloss, ["CappingTrim"] = gold, ["Kickback"] = navyGloss, ["Pit"] = black,
                ["PinLight"] = BowlingAlleyKit.Emissive(new Color(1, .95f, .86f), 4),
                ["MaskingFrame"] = navyMatte, ["MaskingPanel"] = masking,
                ["Numbers"] = BowlingAlleyKit.Emissive(new Color(1, .84f, .5f), 2.2f),
                ["Step"] = gold, ["Divider"] = BowlingAlleyKit.Lane("Approach", new Color(.62f, .48f, .36f), .85f, .5f, .3f),   // a darker maple inlay between lane pairs
                ["ReturnBody"] = navyGloss, ["ReturnTrim"] = gold, ["ReturnDark"] = black,
                ["ReturnAccent"] = BowlingAlleyKit.Emissive(BrandColors.Glow, 3f),
                ["ConsoleBody"] = navyGloss, ["ConsoleTrim"] = gold, ["Screen"] = screen,
                ["MonitorFrame"] = BowlingAlleyKit.Plain(new Color(.02f, .022f, .03f), .75f), ["MonitorMount"] = gold,
                ["Upholstery"] = BowlingAlleyKit.Pbr("LeatherNavy", Color.white, .9f, new Vector2(2, 2)),
                ["SofaBase"] = gold,
                ["TableTop"] = BowlingAlleyKit.Pbr("MarbleDark", Color.white, .95f, new Vector2(1.5f, 1.5f)), ["TableBase"] = gold,
            };
            var balls = new[]
            {
                BowlingAlleyKit.Plain(BrandColors.Royal, .92f), BowlingAlleyKit.Plain(new Color(.75f, .1f, .35f), .92f),
                BowlingAlleyKit.Plain(new Color(.05f, .5f, .55f), .92f), BowlingAlleyKit.Plain(BrandColors.Gold * .85f, .92f),
            };
            BowlingAlleyKit.Place(root, slots, balls);
            var theme = new LaneTheme { Kit = true };
            Lanes(root, theme);
            venue.Fx.AddFlash(masking);
            float end = BowlingLane.LaneEnd, deckFrom = BowlingLane.FoulToHeadPin - .6f;

            // The room: a sky lounge at the top of the club tower. Floor-to-ceiling windows down both sides
            // and above the masking look out on a sunset above the clouds; a walnut-slat ceiling with brass
            // light coves and downlights; an art-deco carpet in the settee and lounge; a bar at the back.
            const float halfRoom = 12.6f, back = -15.8f, ceil = 4.5f;
            var carpet = BowlingAlleyKit.Pbr("CarpetClub", Color.white, .9f, Vector2.one, .6f);
            BowlingAlleyKit.Floor(root, "Carpet", new Vector3(0, BowlingAlleyKit.SetteeFloor, (BowlingAlleyKit.ApproachBack + back) / 2),
                new Vector2(2 * halfRoom, BowlingAlleyKit.ApproachBack - back), carpet, .9f);
            // the aisles beside the bank, lane level, as far as the windows
            foreach (float s in new[] { -1f, 1f })
            {
                float edge = s < 0 ? -BowlingAlleyKit.BankLeft : BowlingAlleyKit.BankRight, w = halfRoom - edge;
                BowlingAlleyKit.Floor(root, "AisleCarpet", new Vector3(s * (edge + w / 2), 0, (BowlingAlleyKit.ApproachBack + end + 2) / 2),
                    new Vector2(w, end + 2 - BowlingAlleyKit.ApproachBack), carpet, .9f);
                Box(root, "AisleEdge", new Vector3(s * (edge + w / 2), -.105f, (BowlingAlleyKit.ApproachBack + end + 2) / 2), new Vector3(w, .19f, end + 2 - BowlingAlleyKit.ApproachBack), navyMatte);   // 10-27: top 1 cm under the aisle carpet (was in its plane: z-fight)
            }
            var walnut = BowlingAlleyKit.Pbr("Walnut", Color.white, .7f, Vector2.one, .8f);
            var ceiling = BowlingAlleyKit.Floor(root, "WalnutCeiling", new Vector3(0, ceil, (back + end + 2) / 2), new Vector2(2 * halfRoom, end + 2 - back), walnut, 1.1f);
            ceiling.transform.localRotation = Quaternion.Euler(-90, 0, 0);
            // brass-edged coves dividing the ceiling into bays over each lane pair, with warm cove light
            var cove = BowlingAlleyKit.Emissive(new Color(1, .78f, .45f), 2.6f);
            foreach (float x in BowlingAlleyKit.PairX)
                foreach (float s in new[] { -1f, 1f })
                {
                    Box(root, "CoveBeam", new Vector3(x + s * LanePitch, ceil - .12f, (back + end) / 2), new Vector3(.22f, .24f, end - back), navyMatte);
                    Box(root, "CoveBrass", new Vector3(x + s * LanePitch, ceil - .245f, (back + end) / 2), new Vector3(.24f, .012f, end - back), gold);
                    Box(root, "CoveLight", new Vector3(x + s * LanePitch + s * -.13f, ceil - .2f, (back + end) / 2), new Vector3(.025f, .05f, end - back - .4f), cove);
                }
            // downlights: small warm discs in rows down every lane pair
            var downlight = BowlingAlleyKit.Emissive(new Color(1, .9f, .72f), 5);
            foreach (float x in BowlingAlleyKit.PairX)
                for (float z = back + 1.5f; z < end - 1; z += 2.4f)
                    foreach (float s in new[] { -.42f, .42f })
                    {
                        var d = GameObject.CreatePrimitive(PrimitiveType.Cylinder); Object.Destroy(d.GetComponent<Collider>());
                        d.name = "Downlight"; d.transform.SetParent(root, false);
                        d.transform.localPosition = new Vector3(x + s * LanePitch, ceil - .01f, z); d.transform.localScale = new Vector3(.16f, .01f, .16f);
                        d.GetComponent<MeshRenderer>().sharedMaterial = downlight;
                        d.GetComponent<MeshRenderer>().shadowCastingMode = ShadowCastingMode.Off;
                    }
            // window walls down both sides: sill, header, columns with brass sconces, tinted glass, the sky beyond
            var mullion = BowlingAlleyKit.Plain(new Color(.03f, .04f, .08f), .6f, .4f);
            var glass = Glass();
            var sconce = BowlingAlleyKit.Emissive(new Color(1, .8f, .55f), 3);
            foreach (float s in new[] { -1f, 1f })
            {
                Box(root, "WindowSill", new Vector3(s * (halfRoom + .1f), .3f, (back + end) / 2), new Vector3(.2f, .6f, end - back + 2), navyMatte);
                Box(root, "WindowSillBrass", new Vector3(s * (halfRoom - .005f), .6f, (back + end) / 2), new Vector3(.03f, .03f, end - back + 2), gold);
                Box(root, "WindowHeader", new Vector3(s * (halfRoom + .1f), ceil - .2f, (back + end) / 2), new Vector3(.2f, .4f, end - back + 2), navyMatte);
                for (float z = back + 1; z <= end + 1; z += 2.4f) Box(root, "Mullion", new Vector3(s * (halfRoom + .05f), 2.2f, z), new Vector3(.06f, 3.6f, .06f), mullion);
                for (float z = back + 2.2f; z <= end; z += 7.2f)
                {
                    Box(root, "Column", new Vector3(s * (halfRoom - .3f), ceil / 2, z), new Vector3(.6f, ceil, .6f), navyMatte);
                    Box(root, "ColumnBrass", new Vector3(s * (halfRoom - .3f), .15f, z), new Vector3(.64f, .3f, .64f), gold);
                    Box(root, "Sconce", new Vector3(s * (halfRoom - .61f), 2.3f, z), new Vector3(.04f, .34f, .12f), sconce);
                }
                Quad(root, "WindowGlass", new Vector3(s * (halfRoom + .05f), 2.2f, (back + end) / 2), new Vector3(end - back + 2, 3.6f, 1), glass).transform.localRotation = Quaternion.Euler(0, s * 90, 0);
            }
            // above the masking: the glass band onto the sunset, a navy fascia, and the club crest sign
            Quad(root, "BackGlass", new Vector3(0, 3.4f, deckFrom + .6f), new Vector3(2 * halfRoom, 2.2f, 1), glass);
            for (float x = -halfRoom; x <= halfRoom + .01f; x += 2.4f) Box(root, "BackMullion", new Vector3(x, 3.4f, deckFrom + .6f), new Vector3(.06f, 2.2f, .06f), mullion);
            Box(root, "DeckWallBelow", new Vector3(0, 1.1f, end + 1.7f), new Vector3(2 * halfRoom, 2.2f, .2f), black);
            // the club's sign over the masking: a navy plaque with the gold crown and name
            BowlingAlleyKit.Sign(root, "ClubSign", "SignClub_Emission", new Vector3(0, 3.05f, deckFrom - .32f), new Vector2(5.6f, 1.4f), 1.5f);
            SkyDome(root);
            // the lounge behind the settees: a raised back gallery for the house and a brass-and-marble bar
            Box(root, "BackWall", new Vector3(0, ceil / 2, back - .1f), new Vector3(2 * halfRoom, ceil, .2f), walnut);
            Gallery(root, new Vector3(-6.5f, BowlingAlleyKit.SetteeFloor, -11.6f), new Vector3(0, 0, -1), 21, 3, 0, navyMatte, gold, venue, alongX: true);
            var marble = BowlingAlleyKit.Pbr("MarbleDark", Color.white, .95f, new Vector2(4, 1));
            foreach (float s in new[] { -1f, 1f })
            {
                Box(root, "BarCounter", new Vector3(s * 9.6f, .35f, -12.2f), new Vector3(3.2f, 1.06f, .7f), navyGloss);
                Box(root, "BarTop", new Vector3(s * 9.6f, .9f, -12.2f), new Vector3(3.4f, .05f, .85f), marble);
                Box(root, "BarFoot", new Vector3(s * 9.6f, -.1f, -11.84f), new Vector3(3.2f, .04f, .05f), gold);
            }
            // the players' own settee (BowlingVenue seats the waiting players at LoungeZ)
            BowlingVenue.Settee(root, BowlingAlleyKit.Pbr("LeatherNavy", Color.white, .9f, new Vector2(2, 2)), gold);
            BowlingAlleyKit.SetteeSeats(venue.Seats);
            // the room is evenly lit like a real centre: nothing in it throws the key's shadow across the lanes
            foreach (var r in root.GetComponentsInChildren<MeshRenderer>(true)) r.shadowCastingMode = ShadowCastingMode.Off;

            // Light. TennisURP gives each object only 2 additional lights, so the key is the main
            // directional light (no slot): from behind and above the bowler, raking down the lanes,
            // it lights the wood and puts a front highlight on every pin. Each pin's two slots go to
            // its deck spot and face light; nothing else is placed near the pins.
            // a warm, high-key room (the target is a bright sky lounge, not a dark arena)
            BowlingVenue.Ambient(new Color(.66f, .62f, .66f), new Color(.58f, .48f, .40f), new Color(.30f, .22f, .18f));
            RenderSettings.fog = true; RenderSettings.fogMode = FogMode.Linear;
            RenderSettings.fogColor = BrandColors.N900; RenderSettings.fogStartDistance = 30; RenderSettings.fogEndDistance = 160;
            Key(root, new Color(1, .95f, .88f), 1.45f, new Vector3(18, 4, 0));
            BowlerLights(root, new Color(1, .95f, .88f));

            Probes(root, venue, 2 * halfRoom, BrandColors.N900);
            venue.Post = Post(root, camera);
            // the fans: GPU-instanced seated spectators (the tennis stands' art), one draw per part
            venue.Crowd = Majestic.MajesticCrowd.Build(root, venue.Seats, lod: true);
            return venue;
        }

        /// A venue's grade. The defaults are Club Lanes'.
        internal sealed class PostLook
        {
            public float BloomThreshold = 1.0f, BloomIntensity = .9f, BloomScatter = .68f;
            public Color BloomTint = Color.white;
            public float Exposure = .45f, Contrast = 14, Saturation = 10;
            public float Temperature, Tint;               // white balance (0 = neutral)
            public Color Filter = Color.white;            // colour filter (ColorAdjustments)
            public Color Shadows = Color.grey, Highlights = Color.grey;     // split toning (grey = off)
            public float Vignette = .25f, VignetteSmooth = .6f;
            public Color VignetteColor = BrandColors.ShadowInk;
        }

        /// Bloom (the LEDs, masking art and neon glow), ACES tonemapping, a little contrast and the
        /// brand vignette (≈0.25 intensity, 0.6 smoothness), or the venue's own look.
        internal static Volume Post(Transform root, Camera camera, PostLook look = null)
        {
            look ??= new PostLook();
            if (camera)
            {
                var data = camera.GetUniversalAdditionalCameraData();
                data.renderPostProcessing = true;
                data.antialiasing = AntialiasingMode.SubpixelMorphologicalAntiAliasing;
                camera.allowHDR = true;
            }
            var go = new GameObject("VenuePost");
            go.transform.SetParent(root, false);
            var v = go.AddComponent<Volume>();
            v.isGlobal = true; v.priority = 10;
            var p = ScriptableObject.CreateInstance<VolumeProfile>();
            var bloom = p.Add<Bloom>(true); bloom.threshold.Override(look.BloomThreshold); bloom.intensity.Override(look.BloomIntensity); bloom.scatter.Override(look.BloomScatter); bloom.tint.Override(look.BloomTint);
            var tone = p.Add<Tonemapping>(true); tone.mode.Override(TonemappingMode.ACES);
            var color = p.Add<ColorAdjustments>(true); color.postExposure.Override(look.Exposure); color.contrast.Override(look.Contrast); color.saturation.Override(look.Saturation);
            if (look.Filter != Color.white) color.colorFilter.Override(look.Filter);
            if (look.Temperature != 0 || look.Tint != 0) { var wb = p.Add<WhiteBalance>(true); wb.temperature.Override(look.Temperature); wb.tint.Override(look.Tint); }
            if (look.Shadows != Color.grey || look.Highlights != Color.grey)
            {
                var split = p.Add<SplitToning>(true); split.shadows.Override(look.Shadows); split.highlights.Override(look.Highlights); split.balance.Override(0);
            }
            var vig = p.Add<Vignette>(true); vig.intensity.Override(look.Vignette); vig.smoothness.Override(look.VignetteSmooth); vig.color.Override(look.VignetteColor);
            v.sharedProfile = p;
            return v;
        }

        /// The two box-projected reflection probes every venue has (rendered once the room is built):
        /// one over the lanes, and a small one at the pin deck so the pins mirror their own surroundings
        /// (the light bar, the kickback strips, the black shadow box: the dark edges sell the gloss).
        internal static void Probes(Transform root, Venue venue, float span, Color background, float intensity = 1.15f)
        {
            var probe = new GameObject("LaneReflections").AddComponent<ReflectionProbe>();
            probe.transform.SetParent(root, false);
            probe.transform.localPosition = new Vector3(0, .6f, 9);
            probe.mode = ReflectionProbeMode.Realtime;
            probe.refreshMode = ReflectionProbeRefreshMode.ViaScripting;
            probe.timeSlicingMode = ReflectionProbeTimeSlicingMode.NoTimeSlicing;
            probe.boxProjection = true;
            probe.size = new Vector3(span, 5, 34);
            probe.resolution = 256; probe.hdr = true; probe.intensity = intensity;
            probe.clearFlags = ReflectionProbeClearFlags.SolidColor; probe.backgroundColor = background;
            venue.Probe = probe;

            var pinProbe = new GameObject("PinDeckReflections").AddComponent<ReflectionProbe>();
            pinProbe.transform.SetParent(root, false);
            pinProbe.transform.localPosition = new Vector3(0, .3f, BowlingLane.FoulToHeadPin + .3f);
            pinProbe.mode = ReflectionProbeMode.Realtime; pinProbe.refreshMode = ReflectionProbeRefreshMode.ViaScripting;
            pinProbe.timeSlicingMode = ReflectionProbeTimeSlicingMode.NoTimeSlicing;
            pinProbe.boxProjection = true; pinProbe.size = new Vector3(2 * BowlingLane.KickbackX, 1.6f, 3f);
            pinProbe.resolution = 128; pinProbe.hdr = true; pinProbe.importance = 2; pinProbe.blendDistance = .3f;
            pinProbe.clearFlags = ReflectionProbeClearFlags.SolidColor; pinProbe.backgroundColor = Color.black;
            venue.PinProbe = pinProbe;
        }

        /// The key: the main directional light (it takes no per-object light slot).
        internal static Light Key(Transform root, Color color, float intensity, Vector3 euler, float shadowStrength = .6f)
        {
            var key = new GameObject("Key").AddComponent<Light>();
            key.transform.SetParent(root, false);
            key.type = LightType.Directional; key.intensity = intensity; key.color = color;
            key.shadows = LightShadows.Soft; key.shadowStrength = shadowStrength; key.transform.rotation = Quaternion.Euler(euler);
            return key;
        }

        /// The bowler's lights, shared by every venue: a spot over the approach and a stage light from
        /// down the lane onto the foul line (the bowler's face in the reaction shot).
        internal static void BowlerLights(Transform root, Color color, float approach = 6, float front = 5)
        {
            Light(root, "ApproachKey", LightType.Spot, new Vector3(0, 4.2f, -6.5f), new Vector3(58, 0, 0), color, approach, 12, 55, LightShadows.Soft);
            Light(root, "BowlerFront", LightType.Spot, new Vector3(0, 2.8f, 3.2f), new Vector3(28, 180, 0), color, front, 9, 50);
        }
    }
}
