using System.Collections.Generic;
using MotionSports.Brand;
using UnityEngine;
using UnityEngine.Rendering;

namespace GolfArcade.Bowling
{
    /// Neon Nights (PLAN_BowlingVenues.md §3.2): cosmic bowling at midnight. The room is black and
    /// everything that matters glows:
    ///   * lane-guard LEDs alternating cyan and magenta, glowing lane arrows, LED totems at the foul line;
    ///   * a synthwave LED wall over the pins (sun, grid, mountains) that blazes up on a strike;
    ///   * a ceiling lattice of neon lines leading to the pins, a blacklight carpet, a mirror-black floor;
    ///   * violet key and ambient, a near-white UV spot on the pins, heavy bloom and a cool grade.
    public static class BowlingNeonNights
    {
        public static readonly Color Cyan = new Color(.10f, .88f, 1f), Magenta = new Color(1f, .16f, .78f), Violet = new Color(.48f, .22f, 1f);
        const int LanesEachSide = 2;

        /// The LED wall: a synthwave sunset (striped sun, magenta mountains, a cyan perspective grid).
        static Texture2D LedWall()
        {
            const int w = 1024, h = 320;
            var tex = new Texture2D(w, h, TextureFormat.RGBA32, true) { wrapMode = TextureWrapMode.Clamp, name = "NeonLedWall" };
            var px = new Color[w * h];
            const float horizon = .36f;
            for (int y = 0; y < h; y++)
                for (int x = 0; x < w; x++)
                {
                    float u = x / (float)w, v = y / (float)h;
                    Color c;
                    if (v > horizon)
                    {
                        // sky: black-violet at the top to magenta haze at the horizon, a few stars
                        float k = (v - horizon) / (1 - horizon);
                        c = Color.Lerp(new Color(.55f, .08f, .45f), new Color(.03f, .0f, .08f), Mathf.Pow(k, .55f));
                        if (BowlingVenue.Noise(u * 140, v * 60, 3) > .86f && k > .3f) c += Color.white * .5f;
                        // the sun: gold at the top to magenta at the bottom, cut by stripes that thicken downward
                        float dx = (u - .5f) * (w / (float)h), dy = v - (horizon + .2f);
                        float r = Mathf.Sqrt(dx * dx + dy * dy);
                        if (r < .26f)
                        {
                            float sv = Mathf.InverseLerp(-.26f, .26f, dy);
                            var sun = Color.Lerp(new Color(1f, .15f, .55f), new Color(1f, .82f, .25f), sv);
                            float band = Mathf.Repeat((dy + .26f) * 26, 1);
                            bool cut = dy < .04f && band < Mathf.Lerp(.55f, .1f, Mathf.InverseLerp(-.26f, .04f, dy));
                            if (!cut) c = sun * 1.4f;
                        }
                        else c += new Color(1f, .3f, .6f) * Mathf.Pow(Mathf.Clamp01(1 - (r - .26f) / .25f), 2) * .35f;
                        // mountains in front of the sun's lower half, with a magenta rim
                        float m = horizon + .03f + .11f * Mathf.Abs(Mathf.Sin(u * 9.1f)) * BowlingVenue.Noise(u * 6, 0, 5) + .05f * BowlingVenue.Noise(u * 30, 1, 6);
                        if (v < m) c = v > m - .006f ? Magenta * 1.6f : new Color(.05f, .0f, .1f);
                    }
                    else
                    {
                        // the floor grid in perspective: horizontal lines bunching toward the horizon, rays to the centre
                        float d = (horizon - v) / horizon;                       // 0 at the horizon, 1 at the bottom
                        float z = 1 / Mathf.Max(d, .02f);
                        float lineZ = Mathf.Abs(Mathf.Repeat(z * .9f, 1) - .5f) * 2;
                        float ray = Mathf.Abs(Mathf.Repeat((u - .5f) / Mathf.Max(d, .03f) * 4 + .5f, 1) - .5f) * 2;
                        float g = Mathf.Max(Mathf.SmoothStep(.86f, 1, lineZ) * Mathf.Clamp01(d * 3), Mathf.SmoothStep(.9f, 1, ray));
                        c = Color.Lerp(new Color(.02f, .0f, .06f), Cyan * 1.3f, g * Mathf.Lerp(.5f, 1, d));
                        c += new Color(.5f, .05f, .4f) * Mathf.Pow(1 - d, 6) * .5f;   // horizon glow
                    }
                    px[y * w + x] = c;
                }
            tex.SetPixels(px); tex.Apply(true);
            return tex;
        }

        /// The masking units: black with a swing arc running cyan to magenta and a faint grid.
        static Texture2D Masking()
        {
            const int w = 512, h = 256;
            var tex = BowlingClubLanes.ArcTexture(w, h, Color.clear, 205, 335, .05f);
            var px = tex.GetPixels();
            for (int y = 0; y < h; y++)
                for (int x = 0; x < w; x++)
                {
                    float u = x / (float)w, v = y / (float)h;
                    var bg = new Color(.02f, .0f, .05f);
                    if (Mathf.Repeat(u * 24, 1) < .04f || Mathf.Repeat(v * 12, 1) < .06f) bg = Violet * .22f;
                    var a = px[y * w + x];
                    var tint = Color.Lerp(Cyan, Magenta, u);
                    // the arc's white core stays white; its fringe and glow take the neon tint
                    var arc = Color.Lerp(tint, Color.white, Mathf.Pow(a.a, 4)) * a.a;
                    px[y * w + x] = bg * (1 - a.a) + arc * 1.2f;
                }
            tex.SetPixels(px); tex.Apply(true);
            return tex;
        }

        /// Blacklight carpet: black with UV-reactive speckles, squiggles and stars.
        static Texture2D Carpet()
        {
            const int n = 256;
            var tex = new Texture2D(n, n, TextureFormat.RGBA32, true) { wrapMode = TextureWrapMode.Repeat, name = "NeonCarpet" };
            var px = new Color[n * n];
            var rng = new System.Random(23);
            for (int i = 0; i < px.Length; i++) px[i] = new Color(.01f, .0f, .03f);
            Color[] inks = { Cyan, Magenta, new Color(.85f, 1f, .2f), new Color(1f, .7f, .1f), Violet };
            for (int k = 0; k < 90; k++)
            {
                var c = inks[rng.Next(inks.Length)];
                int cx = rng.Next(n), cy = rng.Next(n), len = 6 + rng.Next(26);
                float a = (float)rng.NextDouble() * Mathf.PI * 2, turn = ((float)rng.NextDouble() - .5f) * .5f;
                bool star = rng.NextDouble() < .3;
                float fx = cx, fy = cy;
                for (int s = 0; s < (star ? 1 : len); s++)
                {
                    int x = ((int)fx % n + n) % n, y = ((int)fy % n + n) % n;
                    int r = star ? 2 : 1;
                    for (int dy = -r; dy <= r; dy++) for (int dx = -r; dx <= r; dx++)
                            if (!star || dx == 0 || dy == 0) px[((y + dy + n) % n) * n + (x + dx + n) % n] = c;
                    fx += Mathf.Cos(a); fy += Mathf.Sin(a); a += turn;
                }
            }
            tex.SetPixels(px); tex.Apply(true);
            return tex;
        }

        public static BowlingClubLanes.Venue Build(Transform parent, Camera camera)
        {
            var root = new GameObject("NeonNights").transform;
            root.SetParent(parent, false);
            var venue = new BowlingClubLanes.Venue { Root = root };
            var fx = venue.Fx = root.gameObject.AddComponent<BowlingVenueFx>();

            // The alley: the shared kit in blacklight dress (mirror-black fixtures, glowing returns, dividers and
            // lane numbers, an LED wall for masking) on cooled maple (work/bowling-look/PLAN_BowlingLook.md).
            var gloss = BowlingAlleyKit.Plain(new Color(.02f, .015f, .03f), .93f);
            var chrome = BowlingAlleyKit.Plain(new Color(.6f, .6f, .66f), .9f, 1);
            var matte = BowlingAlleyKit.Plain(new Color(.02f, .012f, .035f), .3f);
            var black = BowlingAlleyKit.Plain(new Color(.005f, .004f, .01f), .1f);
            var cyan = BowlingClubLanes.Glow(Cyan, 3.4f);
            var magenta = BowlingClubLanes.Glow(Magenta, 3.4f);
            var masking = BowlingAlleyKit.Emissive(Color.white, 1.8f, BowlingAlleyKit.Tex("MaskingNeon_Emission"));
            var cool = new Color(.95f, .9f, 1f);
            var slots = new Dictionary<string, Material>
            {
                ["LaneMaple"] = BowlingAlleyKit.Lane("LaneMaple", cool, .97f),
                ["LanePine"] = BowlingAlleyKit.Lane("LanePine", cool, .97f),
                ["Approach"] = BowlingAlleyKit.Lane("Approach", cool * .8f, .8f, .5f, .25f),
                ["Ink"] = BowlingClubLanes.Glow(Cyan, 1.6f),                  // blacklight: the inlaid arrows and dots glow
                ["Gutter"] = gloss, ["Capping"] = gloss, ["CappingTrim"] = cyan, ["Kickback"] = gloss, ["Pit"] = black,
                ["PinLight"] = BowlingAlleyKit.Emissive(new Color(.93f, .91f, 1f), 4),
                ["MaskingFrame"] = gloss, ["MaskingPanel"] = masking, ["Numbers"] = BowlingClubLanes.Glow(Magenta, 2.6f),
                ["Step"] = magenta, ["Divider"] = BowlingClubLanes.Glow(Cyan, .45f),
                ["ReturnBody"] = gloss, ["ReturnTrim"] = chrome, ["ReturnDark"] = black, ["ReturnAccent"] = magenta,
                ["ConsoleBody"] = gloss, ["ConsoleTrim"] = cyan,
                ["Screen"] = BowlingAlleyKit.Emissive(Color.white, 1.2f, BowlingAlleyKit.Tex("ScoreScreenNeon_Emission")),
                ["MonitorFrame"] = gloss, ["MonitorMount"] = chrome,
                ["Upholstery"] = BowlingAlleyKit.Pbr("LeatherNavy", new Color(1.6f, .5f, 1.9f), .95f, new Vector2(2, 2)),   // purple vinyl
                ["SofaBase"] = magenta,
                ["TableTop"] = gloss, ["TableBase"] = cyan,
            };
            var balls = new[]
            {
                BowlingAlleyKit.Emissive(Cyan, .9f), BowlingAlleyKit.Emissive(Magenta, .9f),
                BowlingAlleyKit.Emissive(new Color(1f, .75f, .1f), .8f), BowlingAlleyKit.Emissive(new Color(.5f, 1f, .2f), .8f),
            };
            BowlingAlleyKit.Place(root, slots, balls);
            BowlingClubLanes.Lanes(root, new BowlingClubLanes.LaneTheme { Kit = true, PinSpot = new Color(.93f, .91f, 1f), PinSpotIntensity = 5.2f, PinFace = 1.6f });
            fx.AddFlash(masking);
            fx.AddPulse(cyan, 1.2f, .2f); fx.AddPulse(magenta, 1.2f, .2f, 1.6f);

            float end = BowlingLane.LaneEnd, deckFrom = BowlingLane.FoulToHeadPin - .6f;
            const float halfRoom = 12.6f, back = -15.8f, ceil = 4.6f;
            // The room: black and glossy, so the neon doubles in the floor; the blacklight carpet in the settee
            // and lounge; black walls with neon runs; a truss ceiling with light lines over every lane edge.
            var carpet = BowlingAlleyKit.Pbr("CarpetNeon", Color.white, .5f, Vector2.one, .5f);
            carpet.EnableKeyword("_EMISSION"); carpet.SetTexture("_EmissionMap", BowlingAlleyKit.Tex("CarpetNeon_Emission")); carpet.SetColor("_EmissionColor", Color.white * 1.3f);
            BowlingAlleyKit.Floor(root, "Carpet", new Vector3(0, BowlingAlleyKit.SetteeFloor, (BowlingAlleyKit.ApproachBack + back) / 2), new Vector2(2 * halfRoom, BowlingAlleyKit.ApproachBack - back), carpet, 1.2f)
                .GetComponent<MeshRenderer>().sharedMaterial.SetTextureScale("_EmissionMap", new Vector2(2 * halfRoom / 1.2f, (BowlingAlleyKit.ApproachBack - back) / 1.2f));
            foreach (float s in new[] { -1f, 1f })
            {
                float edge = s < 0 ? -BowlingAlleyKit.BankLeft : BowlingAlleyKit.BankRight, w = halfRoom - edge;
                BowlingClubLanes.Box(root, "AisleFloor", new Vector3(s * (edge + w / 2), -.095f, (BowlingAlleyKit.ApproachBack + end + 2) / 2), new Vector3(w, .19f, end + 2 - BowlingAlleyKit.ApproachBack), gloss);
                BowlingClubLanes.Box(root, "Wall", new Vector3(s * (halfRoom + .1f), ceil / 2, (back + end) / 2), new Vector3(.2f, ceil, end - back + 4), matte);
                var tube = s < 0 ? cyan : magenta;
                BowlingClubLanes.Box(root, "WallNeonHigh", new Vector3(s * halfRoom, 3.6f, (back + end) / 2), new Vector3(.03f, .03f, end - back), tube);
                BowlingClubLanes.Box(root, "WallNeonLow", new Vector3(s * halfRoom, 1.2f, (back + end) / 2), new Vector3(.03f, .02f, end - back), tube);
                for (float z = back + 2; z < end; z += 4.2f)
                    BowlingVenue.Slab(root, "WallBolt", new Vector3(s * halfRoom, 2.4f, z), new Vector3(.02f, .025f, 2.3f), new Vector3(s * 30, 0, 0), BowlingClubLanes.Glow(Violet, 2.2f));
            }
            BowlingClubLanes.Box(root, "Ceiling", new Vector3(0, ceil + .05f, (back + end) / 2), new Vector3(2 * halfRoom, .1f, end - back + 4), matte);
            // truss chords across the room every 3 m, light lines down every lane edge, pulsing
            for (float z = back + 1.5f; z <= end; z += 3f)
            {
                BowlingClubLanes.Box(root, "TrussTop", new Vector3(0, ceil - .25f, z), new Vector3(2 * halfRoom, .05f, .05f), chrome);
                BowlingClubLanes.Box(root, "TrussLow", new Vector3(0, ceil - .6f, z), new Vector3(2 * halfRoom, .05f, .05f), chrome);
                for (float x = -halfRoom + .3f; x < halfRoom; x += .7f)
                    BowlingVenue.Slab(root, "TrussWeb", new Vector3(x, ceil - .42f, z), new Vector3(.02f, .42f, .02f), new Vector3(0, 0, ((int)(x * 10) & 1) == 0 ? 35 : -35), chrome);
            }
            for (int i = BowlingAlleyKit.FirstLane; i <= BowlingAlleyKit.LastLane + 1; i++)
            {
                var m = BowlingClubLanes.Glow((i & 1) == 0 ? Cyan : Magenta, 2.6f);
                BowlingClubLanes.Box(root, "LatticeRun", new Vector3((i - .5f) * BowlingClubLanes.LanePitch, ceil - .7f, (back + end) / 2), new Vector3(.04f, .03f, end - back), m);
                fx.AddPulse(m, 1.6f, .35f, i * 1.1f);
            }
            var bar = BowlingClubLanes.Glow(Violet, 1.8f);
            for (float z = back + 1.5f; z <= end; z += 3f) BowlingClubLanes.Box(root, "LatticeBar", new Vector3(0, ceil - .62f, z), new Vector3(2 * halfRoom, .025f, .03f), bar);
            fx.AddPulse(bar, .9f, .3f);

            // LED totems at the foul line on the divider strips, cycling through the neon colours
            Color[] cycle = { Cyan, Violet, Magenta, new Color(1f, .7f, .15f) };
            foreach (float x in new[] { -7.425f, -4.125f, -.825f, 2.475f, 5.775f })
            {
                var m = BowlingClubLanes.Glow(Cyan, 1.6f);
                BowlingClubLanes.Box(root, "Totem", new Vector3(x, .7f, -.6f), new Vector3(.07f, 1.4f, .07f), m);
                BowlingClubLanes.Box(root, "TotemBase", new Vector3(x, .04f, -.6f), new Vector3(.18f, .08f, .18f), gloss);
                fx.AddCycle(m, cycle, 1.6f, 6, x);
            }

            // Over the masking: the synthwave LED wall, the brightest picture in the room.
            var wall = BowlingClubLanes.Glow(Color.white, 1.5f, LedWall());
            BowlingClubLanes.Quad(root, "LedWall", new Vector3(-.8f, 3.5f, deckFrom + .4f), new Vector3(BowlingAlleyKit.BankRight - BowlingAlleyKit.BankLeft + 1, 2.2f, 1), wall);
            BowlingClubLanes.Box(root, "LedWallFrameLow", new Vector3(-.8f, 2.38f, deckFrom + .35f), new Vector3(BowlingAlleyKit.BankRight - BowlingAlleyKit.BankLeft + 1, .04f, .06f), magenta);
            BowlingClubLanes.Box(root, "DeckWallBelow", new Vector3(-.8f, 1.3f, end + 1.6f), new Vector3(2 * halfRoom, 2.6f, .2f), black);
            fx.AddFlash(wall);

            // Behind the settees: the players' sofa, the lounge gallery, a neon swing arc on the back wall.
            BowlingVenue.Settee(root, BowlingAlleyKit.Pbr("LeatherNavy", new Color(1.6f, .3f, 1.3f), .95f, new Vector2(2, 2)), cyan, gloss);
            BowlingClubLanes.Gallery(root, new Vector3(-6.5f, BowlingAlleyKit.SetteeFloor, -11.6f), new Vector3(0, 0, -1), 21, 3, 0, gloss, magenta, venue, alongX: true);
            BowlingClubLanes.Box(root, "LoungeWall", new Vector3(0, ceil / 2, back - .1f), new Vector3(2 * halfRoom, ceil, .2f), matte);
            var arc = BowlingClubLanes.Quad(root, "LoungeNeonArc", new Vector3(0, 3.4f, back + .05f), new Vector3(7, 2.2f, 1),
                BowlingVenue.Additive(BowlingClubLanes.ArcTexture(1024, 384, Color.clear, 200, 340, .03f), new Color(1f, .35f, .9f) * 1.6f));
            arc.transform.localRotation = Quaternion.Euler(0, 180, 0);   // facing the lanes (the reaction shot looks back at it)
            BowlingClubLanes.Light(root, "LoungeGlow", LightType.Point, new Vector3(0, 2.6f, BowlingClubLanes.LoungeZ), Vector3.zero, Magenta, 1.8f, 4);
            BowlingAlleyKit.SetteeSeats(venue.Seats);
            foreach (var r in root.GetComponentsInChildren<MeshRenderer>(true)) r.shadowCastingMode = ShadowCastingMode.Off;

            // Light: a violet room. The key is the main directional (no light slot), low and violet;
            // the pins keep a near-white UV spot so they are still the brightest thing on screen.
            RenderSettings.ambientMode = AmbientMode.Flat;
            RenderSettings.ambientLight = new Color(.13f, .07f, .24f);
            BowlingVenue.Fog(new Color(.07f, .02f, .13f), 24, 95);
            BowlingClubLanes.Key(root, new Color(.82f, .70f, 1f), 2.5f, new Vector3(22, 0, 0), .7f);
            BowlingClubLanes.BowlerLights(root, new Color(.95f, .82f, 1f), 6, 7.5f);

            BowlingClubLanes.Probes(root, venue, 2 * halfRoom, new Color(.02f, 0, .04f), 1.25f);
            venue.Post = BowlingClubLanes.Post(root, camera, new BowlingClubLanes.PostLook
            {
                BloomThreshold = .8f, BloomIntensity = 1.5f, BloomScatter = .74f, BloomTint = new Color(1f, .85f, 1f),
                Exposure = .45f, Contrast = 18, Saturation = 22, Temperature = -12, Tint = 8,
                Vignette = .32f, VignetteColor = new Color(.05f, 0, .1f),
            });
            venue.Crowd = Majestic.MajesticCrowd.Build(root, venue.Seats, lod: true);
            return venue;
        }
    }
}
