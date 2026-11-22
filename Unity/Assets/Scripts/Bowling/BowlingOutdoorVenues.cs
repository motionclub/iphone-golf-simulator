using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;
using GolfArcade.Tennis;

namespace GolfArcade.Bowling
{
    /// Three open-air bowling venues on the tennis courts' worlds (2026-11-21, Adnan: "re-use ... the skyscraper map we use for
    /// tennis as a bowling alley, the tennis beach court ... proceed with all 3 ... make sure they are set outside, not inside"):
    ///
    ///   RooftopLanes     the Sky Open rooftop: the alley on the tower's open deck above the cloud sea, the skyline all round
    ///   BeachCourtLanes  the Tropical Open resort: the alley where the court was, the beach house, palms, island and lagoon
    ///   CraterLanes      the Magma Open slab: the alley on the obsidian slab hovering over the crater's lava lake
    ///
    /// Each is the shared lane kit (same lanes, cameras, pin lights as every venue) dressed in the venue's palette, with no roof
    /// and no walls: the sky is the ceiling. The tennis world is built by the tennis venue code (TennisVenueBuilder.*ForBowling,
    /// the resort arena prefab) under its own root beside the alley, so the alley's static batching never touches it.
    public static class BowlingOutdoorVenues
    {
        /// The alley's footprint (BowlingAlleyKit bank + lounge + pin decks), with a little margin.
        static readonly float CentreX = (BowlingAlleyKit.BankLeft + BowlingAlleyKit.BankRight) / 2;
        const float Back = -15.8f;
        static float Front => BowlingLane.LaneEnd + 2;
        static float CentreZ => (Back + Front) / 2;
        /// Half extents of the borrowed slab: room for the bank, a promenade down each side and the lounge.
        const float SlabHalfX = 13.6f, SlabHalfZ = 20.0f;

        sealed class Palette
        {
            public Material Capping, CappingTrim, Kickback, Gutter, MaskingFrame, Step, ReturnBody, ReturnTrim, ReturnDark, ReturnAccent,
                ConsoleBody, ConsoleTrim, MonitorFrame, MonitorMount, Upholstery, SofaBase, TableTop, TableBase;
            public string MaskingArt, ScreenArt;
            public float MaskingGlow = 1.15f;
            public Color LaneTint = Color.white, PinSpot = new Color(1f, .93f, .82f), Numbers = new Color(1f, .88f, .62f);
            public Material[] Balls;
        }

        /// The kit in the venue's dress, the pin-deck lights and the strike flash on the masking art.
        static void Alley(Transform root, BowlingClubLanes.Venue venue, Palette p)
        {
            var masking = BowlingAlleyKit.Emissive(Color.white, p.MaskingGlow, BowlingAlleyKit.Tex(p.MaskingArt));
            var slots = new Dictionary<string, Material>
            {
                ["LaneMaple"] = BowlingAlleyKit.Lane("LaneMaple", p.LaneTint, .96f),
                ["LanePine"] = BowlingAlleyKit.Lane("LanePine", p.LaneTint, .96f),
                ["Approach"] = BowlingAlleyKit.Lane("Approach", p.LaneTint * .96f, .8f, .5f, .25f),
                ["Ink"] = BowlingAlleyKit.Plain(new Color(.18f, .11f, .07f), .6f),
                ["Gutter"] = p.Gutter, ["Capping"] = p.Capping, ["CappingTrim"] = p.CappingTrim, ["Kickback"] = p.Kickback,
                ["Pit"] = BowlingAlleyKit.Plain(new Color(.02f, .018f, .02f), .1f),
                ["PinLight"] = BowlingAlleyKit.Emissive(p.PinSpot, 4),
                ["MaskingFrame"] = p.MaskingFrame, ["MaskingPanel"] = masking, ["Numbers"] = BowlingAlleyKit.Emissive(p.Numbers, 2.1f),
                ["Step"] = p.Step, ["Divider"] = BowlingAlleyKit.Lane("Approach", new Color(.62f, .48f, .36f), .82f, .5f, .28f),
                ["ReturnBody"] = p.ReturnBody, ["ReturnTrim"] = p.ReturnTrim, ["ReturnDark"] = p.ReturnDark, ["ReturnAccent"] = p.ReturnAccent,
                ["ConsoleBody"] = p.ConsoleBody, ["ConsoleTrim"] = p.ConsoleTrim,
                ["Screen"] = BowlingAlleyKit.Emissive(Color.white, 1.1f, BowlingAlleyKit.Tex(p.ScreenArt)),
                ["MonitorFrame"] = p.MonitorFrame, ["MonitorMount"] = p.MonitorMount,
                ["Upholstery"] = p.Upholstery, ["SofaBase"] = p.SofaBase, ["TableTop"] = p.TableTop, ["TableBase"] = p.TableBase,
            };
            BowlingAlleyKit.Place(root, slots, p.Balls);
            BowlingClubLanes.Lanes(root, new BowlingClubLanes.LaneTheme { Kit = true, PinSpot = p.PinSpot, PinSpotIntensity = 4.6f, PinFace = 1.4f });
            venue.Fx.AddFlash(masking);
        }

        /// The open-air lounge every outdoor venue shares: the players' settee, the bleachers behind it for the crowd, two bars.
        static void Lounge(Transform root, BowlingClubLanes.Venue venue, Material seat, Material trim, Material step, Material bar, Material barTop)
        {
            BowlingClubLanes.Gallery(root, new Vector3(-6.5f, BowlingAlleyKit.SetteeFloor, -11.6f), new Vector3(0, 0, -1), 21, 3, 0, step, trim, venue, alongX: true);
            BowlingVenue.Settee(root, seat, trim);
            foreach (float s in new[] { -1f, 1f })
            {
                BowlingClubLanes.Box(root, "Bar", new Vector3(s * 9.9f, .37f, -12.4f), new Vector3(3.2f, 1.1f, .8f), bar);
                BowlingClubLanes.Box(root, "BarTop", new Vector3(s * 9.9f, .94f, -12.3f), new Vector3(3.4f, .06f, 1), barTop);
            }
            BowlingAlleyKit.SetteeSeats(venue.Seats);
        }

        /// The borrowed world's root: beside the alley (not under it, so the alley's static batching leaves it alone),
        /// centred on the alley, its slab top level with the lounge floor.
        static Transform World(Transform parent, string name)
        {
            var w = new GameObject(name).transform;
            w.SetParent(parent, false);
            w.localPosition = new Vector3(CentreX, BowlingAlleyKit.SetteeFloor - .002f, CentreZ);
            return w;
        }

        /// Promenade floor round the bank (lounge level, the slab's own colour shows only past it).
        static void Promenade(Transform root, Material m, float metresPerTile)
        {
            BowlingAlleyKit.Floor(root, "Promenade", new Vector3(CentreX, BowlingAlleyKit.SetteeFloor + .004f, CentreZ),
                new Vector2(2 * SlabHalfX - 1.4f, Front - Back + 2.2f), m, metresPerTile);
        }

        /// A row of short posts strung with warm bulbs along both sides: the open-air alley's evening light (emission only).
        static void StringLights(Transform root, BowlingVenueFx fx, Material pole, Color bulb, float x0, float x1)
        {
            var poles = new List<CombineInstance>(); var bulbs = new List<CombineInstance>();
            var cyl = BowlingVenue.Primitive(PrimitiveType.Cylinder); var sphere = BowlingVenue.Primitive(PrimitiveType.Sphere);
            foreach (float x in new[] { x0, x1 })
            {
                for (float z = -13.5f; z <= 20.5f; z += 4.25f)
                    poles.Add(BowlingVenue.Part(cyl, new Vector3(x, BowlingAlleyKit.SetteeFloor + 1.6f, z), Quaternion.identity, new Vector3(.08f, 1.6f, .08f)));
                for (int k = 0; k < 64; k++)
                {
                    float z = -13.5f + k * (34f / 64f), span = Mathf.Repeat(z + 13.5f, 4.25f) / 4.25f;
                    bulbs.Add(BowlingVenue.Part(sphere, new Vector3(x, BowlingAlleyKit.SetteeFloor + 3.1f - .32f * Mathf.Sin(span * Mathf.PI), z), Quaternion.identity, Vector3.one * .1f));
                }
            }
            BowlingVenue.Combine(root, "StringLightPoles", poles, pole);
            var glow = BowlingClubLanes.Glow(bulb, 3.2f);
            BowlingVenue.Combine(root, "StringLightBulbs", bulbs, glow, false);
            fx.AddPulse(glow, .6f, .05f);
        }

        static BowlingClubLanes.Venue Begin(Transform parent, string name, out Transform root)
        {
            root = new GameObject(name).transform;
            root.SetParent(parent, false);
            var venue = new BowlingClubLanes.Venue { Root = root };
            venue.Fx = root.gameObject.AddComponent<BowlingVenueFx>();
            return venue;
        }

        // =====================================================================================================================
        // ROOFTOP LANES: Sky Open's tower top. Dusk, lavender and coral, the cloud sea 58 m below.
        // =====================================================================================================================

        public static BowlingClubLanes.Venue Rooftop(Transform parent, Camera camera)
        {
            var venue = Begin(parent, "RooftopLanes", out var root);
            var world = World(parent, "Rooftop world (Sky Open)");
            TennisVenueBuilder.SkyscraperForBowling(world, SlabHalfX, SlabHalfZ);

            var coral = BowlingClubLanes.Surface(new Color(.95f, .45f, .40f), .5f);
            var lavender = BowlingAlleyKit.Plain(new Color(.42f, .38f, .66f), .82f);
            var lavenderDeep = BowlingAlleyKit.Plain(new Color(.20f, .18f, .36f), .7f);
            var gold = BowlingAlleyKit.Plain(new Color(.92f, .72f, .28f), .8f, .6f);
            var teal = BowlingAlleyKit.Plain(new Color(.03f, .40f, .36f), .6f);
            Alley(root, venue, new Palette
            {
                Capping = lavender, CappingTrim = gold, Kickback = lavender, Gutter = BowlingAlleyKit.Plain(new Color(.52f, .56f, .62f), .9f, .9f),
                MaskingFrame = lavenderDeep, Step = gold, ReturnBody = lavender, ReturnTrim = gold, ReturnDark = lavenderDeep,
                ReturnAccent = BowlingAlleyKit.Emissive(new Color(1f, .55f, .45f), 2.6f), ConsoleBody = lavender, ConsoleTrim = gold,
                MonitorFrame = BowlingAlleyKit.Plain(new Color(.04f, .04f, .07f), .75f), MonitorMount = gold,
                Upholstery = BowlingAlleyKit.Pbr("LeatherNavy", new Color(1f, .62f, .58f), .85f, new Vector2(2, 2)), SofaBase = gold,
                TableTop = BowlingAlleyKit.Pbr("MarbleDark", Color.white, .95f, new Vector2(1.5f, 1.5f)), TableBase = gold,
                MaskingArt = "MaskingClub_Emission", ScreenArt = "ScoreScreen_Emission",
                LaneTint = new Color(1f, .95f, .9f), PinSpot = new Color(1f, .9f, .8f),
                Balls = new[] { BowlingAlleyKit.Plain(new Color(.55f, .45f, .95f), .93f), BowlingAlleyKit.Plain(new Color(.95f, .42f, .38f), .93f),
                                BowlingAlleyKit.Plain(new Color(.05f, .5f, .55f), .93f), BowlingAlleyKit.Plain(new Color(.92f, .72f, .28f), .93f) },
            });

            // the deck: pale pavers round the bank (the slab's stone and coral band past them, then the drop to the clouds)
            Promenade(root, BowlingClubLanes.Surface(new Color(.66f, .66f, .70f), .3f, BowlingAlley.Boards(), new Vector2(1, 1)), 1.2f);
            var concrete = BowlingClubLanes.Surface(new Color(.58f, .58f, .64f), .3f);
            Lounge(root, venue, BowlingAlleyKit.Pbr("LeatherNavy", new Color(1f, .62f, .58f), .85f, new Vector2(2, 2)), gold, concrete, lavender, gold);
            StringLights(root, venue.Fx, BowlingClubLanes.Surface(new Color(.82f, .84f, .88f), .5f, null, null, .5f), new Color(1f, .78f, .5f),
                BowlingAlleyKit.BankLeft - .9f, BowlingAlleyKit.BankRight + .9f);
            // coral planters with low shrubs down the promenades
            var leaf = BowlingClubLanes.Surface(new Color(.20f, .42f, .30f), .3f);
            foreach (float x in new[] { BowlingAlleyKit.BankLeft - 2.1f, BowlingAlleyKit.BankRight + 2.1f })
                for (float z = -4f; z <= 19f; z += 7.5f)
                {
                    BowlingClubLanes.Box(root, "Planter", new Vector3(x, BowlingAlleyKit.SetteeFloor + .3f, z), new Vector3(.9f, .6f, 2.4f), coral);
                    BowlingClubLanes.Box(root, "PlanterShrub", new Vector3(x, BowlingAlleyKit.SetteeFloor + .78f, z), new Vector3(.72f, .4f, 2.2f), leaf);
                }
            foreach (var r in root.GetComponentsInChildren<MeshRenderer>(true)) if (r.name == "Promenade") r.shadowCastingMode = ShadowCastingMode.Off;

            var key = BowlingClubLanes.Key(root, Color.white, 1.7f, new Vector3(30, -40, 0), .72f);
            TennisVenueBuilder.SkyForBowling(TennisVenueKind.Skyscraper, key, camera);
            BowlingClubLanes.BowlerLights(root, new Color(1f, .86f, .74f), 4.6f, 4.4f);
            BowlingClubLanes.Probes(root, venue, 2 * SlabHalfX, new Color(.55f, .48f, .72f), 1.05f);
            venue.Post = BowlingClubLanes.Post(root, camera, new BowlingClubLanes.PostLook
            {
                BloomThreshold = 1.1f, BloomIntensity = .6f, BloomScatter = .65f, BloomTint = new Color(1f, .86f, .9f),
                Exposure = .2f, Contrast = 12, Saturation = 12, Temperature = 4, Vignette = .2f, VignetteColor = new Color(.12f, .08f, .2f),
            });
            venue.Crowd = Majestic.MajesticCrowd.Build(root, venue.Seats, lod: true);
            return venue;
        }

        // =====================================================================================================================
        // BEACH COURT LANES: the Tropical Open resort. The lanes are laid where the court was; the beach house, the pergola
        // stands, the palms, the island and the lagoon stay. Midday sun.
        // =====================================================================================================================

        /// Tennis court kit materials (TennisVenueBuilder.CourtKit): the court, its lines, posts, net and umpire chair go.
        static readonly string[] CourtPieces = { "TropicalV3_002", "TropicalV3_003", "TropicalV3_008", "TropicalV3_012", "TropicalV3_023" };

        public static BowlingClubLanes.Venue BeachCourt(Transform parent, Camera camera)
        {
            var venue = Begin(parent, "BeachCourtLanes", out var root);
            var world = new GameObject("Beach court world (Tropical Open)").transform; world.SetParent(parent, false);
            var arenaPrefab = Resources.Load<GameObject>("Tennis/TropicalV3/TropicalTennisResort");
            if (arenaPrefab)
            {
                var arena = Object.Instantiate(arenaPrefab, world);
                arena.name = "Tropical tennis resort v3 (bowling)";
                arena.transform.rotation = Quaternion.Euler(0, 180, 0);
                TennisLook.StyleArena(arena);
                // the court's top sits at the lounge floor: the alley stands on it as the players did
                float courtTop = TennisVenue.HasRenderedCourtHeight ? TennisVenue.RenderedCourtHeight : .03f;
                float drop = BowlingAlleyKit.SetteeFloor - .004f - courtTop;
                arena.transform.position += Vector3.up * drop;
                GameObject island = null;
                var islandPrefab = Resources.Load<GameObject>("Tennis/Island/TennisIsland");
                if (islandPrefab)
                {
                    island = Object.Instantiate(islandPrefab, world); island.name = "Tropical island";
                    island.transform.rotation = arena.transform.rotation * islandPrefab.transform.rotation;
                    island.transform.position += Vector3.up * drop;
                    TennisLook.StyleIsland(island);
                }
                var was = TennisVenue.Selected; TennisVenue.Selected = TennisVenueKind.Resort;
                try { TennisEnvironmentV4.Apply(arena, island); } finally { TennisVenue.Selected = was; }
                ClearFootprint(world);
            }

            var whiteWood = BowlingAlleyKit.Plain(new Color(.93f, .92f, .88f), .7f);
            var ocean = BowlingAlleyKit.Plain(new Color(.07f, .42f, .46f), .8f);
            var terracotta = BowlingAlleyKit.Plain(new Color(.80f, .38f, .22f), .6f);
            var teak = BowlingAlleyKit.Pbr("Teak", Color.white, .8f, new Vector2(.5f, .5f));
            Alley(root, venue, new Palette
            {
                Capping = whiteWood, CappingTrim = terracotta, Kickback = ocean, Gutter = BowlingAlleyKit.Plain(new Color(.16f, .1f, .06f), .85f, .2f),
                MaskingFrame = whiteWood, Step = terracotta, ReturnBody = ocean, ReturnTrim = whiteWood, ReturnDark = BowlingAlleyKit.Plain(new Color(.04f, .18f, .2f), .6f),
                ReturnAccent = BowlingAlleyKit.Emissive(new Color(.25f, .95f, .85f), 2.4f), ConsoleBody = whiteWood, ConsoleTrim = teak,
                MonitorFrame = BowlingAlleyKit.Plain(new Color(.92f, .92f, .9f), .6f), MonitorMount = teak,
                Upholstery = BowlingAlleyKit.Pbr("Rattan", Color.white, .8f, new Vector2(3, 3)), SofaBase = teak, TableTop = teak, TableBase = whiteWood,
                MaskingArt = "MaskingTiki_Emission", ScreenArt = "ScoreScreenTiki_Emission",
                LaneTint = new Color(1f, .94f, .84f), PinSpot = new Color(1f, .95f, .86f),
                Balls = new[] { BowlingAlleyKit.Plain(new Color(.1f, .6f, .65f), .93f), BowlingAlleyKit.Plain(new Color(.95f, .5f, .3f), .93f),
                                BowlingAlleyKit.Plain(new Color(.2f, .4f, .9f), .93f), BowlingAlleyKit.Plain(new Color(.98f, .85f, .3f), .93f) },
            });

            // the court's own acrylic round the bank (ocean teal) inside a white run-off line, like the tennis court it was
            var acrylic = BowlingClubLanes.Surface(new Color(.085f, .40f, .43f), .45f);
            Promenade(root, acrylic, 4);
            foreach (float s in new[] { -1f, 1f })
                BowlingClubLanes.Box(root, "CourtLine", new Vector3(CentreX + s * (SlabHalfX - .9f), BowlingAlleyKit.SetteeFloor + .006f, CentreZ), new Vector3(.08f, .004f, Front - Back + 1.8f), whiteWood);
            Lounge(root, venue, BowlingClubLanes.Surface(new Color(.10f, .52f, .56f), .45f), teak, whiteWood, whiteWood, teak);
            StringLights(root, venue.Fx, teak, new Color(1f, .84f, .6f), BowlingAlleyKit.BankLeft - .9f, BowlingAlleyKit.BankRight + .9f);
            foreach (var r in root.GetComponentsInChildren<MeshRenderer>(true)) if (r.name == "Promenade" || r.name == "CourtLine") r.shadowCastingMode = ShadowCastingMode.Off;

            var key = BowlingClubLanes.Key(root, Color.white, 1.65f, new Vector3(50, -40, 0), .72f);
            TennisVenueBuilder.SkyForBowling(TennisVenueKind.Resort, key, camera);
            key.intensity *= .78f;   // the tennis noon sun bleached the maple: the lanes need their grain
            BowlingVenue.Ambient(new Color(.46f, .58f, .78f), new Color(.62f, .60f, .54f), new Color(.40f, .37f, .30f));
            BowlingVenue.Fog(new Color(.74f, .84f, .92f), 120, 900);
            BowlingClubLanes.BowlerLights(root, new Color(1f, .94f, .86f), 2.6f, 2.6f);
            BowlingClubLanes.Probes(root, venue, 2 * SlabHalfX, new Color(.55f, .74f, .9f), 1.0f);
            venue.Post = BowlingClubLanes.Post(root, camera, new BowlingClubLanes.PostLook
            {
                BloomThreshold = 1.2f, BloomIntensity = .45f, BloomScatter = .6f, BloomTint = new Color(1f, .95f, .88f),
                Exposure = -.2f, Contrast = 14, Saturation = 14, Temperature = 4, Vignette = .15f, VignetteColor = new Color(.05f, .12f, .18f),
            });
            venue.Crowd = Majestic.MajesticCrowd.Build(root, venue.Seats, lod: true);
            return venue;
        }

        /// Hides whatever of the resort stands in the alley's footprint (benches, lamp posts, planters, the stands' front rows)
        /// and every light the arena brought (the pins own their light slots). Ground and anything bigger than a building stays.
        static void ClearFootprint(Transform world)
        {
            var area = new Bounds(new Vector3(CentreX, 2.2f, CentreZ), new Vector3(BowlingAlleyKit.BankRight - BowlingAlleyKit.BankLeft + 2.6f, 4.6f, Front - Back + 1.2f));
            int hidden = 0;
            foreach (var r in world.GetComponentsInChildren<Renderer>(true))
            {
                if (!r.enabled) continue;
                string m = r.sharedMaterial ? r.sharedMaterial.name : "";
                bool court = false; foreach (var k in CourtPieces) if (m.StartsWith(k)) { court = true; break; }
                var b = r.bounds;
                bool ground = b.size.x > 34 || b.size.z > 44 || b.max.y < BowlingAlleyKit.SetteeFloor + .05f;
                if (court || (!ground && b.Intersects(area))) { r.enabled = false; hidden++; }
            }
            foreach (var l in world.GetComponentsInChildren<Light>(true)) Object.Destroy(l.gameObject);
            Debug.Log("[Bowling] beach court: hid " + hidden + " resort pieces in the alley footprint");
        }

        // =====================================================================================================================
        // CRATER LANES: Magma Open's obsidian slab over the lava lake. Ash dusk, the eruption on the far rim.
        // =====================================================================================================================

        public static BowlingClubLanes.Venue Crater(Transform parent, Camera camera)
        {
            var venue = Begin(parent, "CraterLanes", out var root);
            var world = World(parent, "Crater world (Magma Open)");
            TennisVenueBuilder.VolcanoForBowling(world, SlabHalfX, SlabHalfZ);

            var obsidian = BowlingAlleyKit.Plain(new Color(.05f, .045f, .055f), .82f);
            var basalt = BowlingAlleyKit.Pbr("Basalt", Color.white, .5f, new Vector2(1, 1));
            var ember = BowlingAlleyKit.Emissive(new Color(1f, .36f, .08f), 2.6f);
            var copper = BowlingAlleyKit.Plain(new Color(.62f, .32f, .18f), .75f, .7f);
            Alley(root, venue, new Palette
            {
                Capping = obsidian, CappingTrim = ember, Kickback = basalt, Gutter = BowlingAlleyKit.Plain(new Color(.08f, .07f, .08f), .8f, .4f),
                MaskingFrame = obsidian, Step = copper, ReturnBody = basalt, ReturnTrim = copper, ReturnDark = obsidian, ReturnAccent = ember,
                ConsoleBody = basalt, ConsoleTrim = copper, MonitorFrame = obsidian, MonitorMount = copper,
                Upholstery = BowlingAlleyKit.Pbr("LeatherNavy", new Color(.55f, .2f, .14f), .8f, new Vector2(2, 2)), SofaBase = copper,
                TableTop = obsidian, TableBase = copper,
                MaskingArt = "MaskingMagma_Emission", ScreenArt = "ScoreScreenMagma_Emission", MaskingGlow = 1.2f,
                LaneTint = new Color(1f, .9f, .82f), PinSpot = new Color(1f, .9f, .78f), Numbers = new Color(1f, .62f, .32f),
                Balls = new[] { BowlingAlleyKit.Plain(new Color(.12f, .1f, .12f), .95f), BowlingAlleyKit.Plain(new Color(.85f, .25f, .08f), .93f),
                                BowlingAlleyKit.Plain(new Color(.45f, .12f, .1f), .93f), BowlingAlleyKit.Plain(new Color(.3f, .32f, .4f), .93f) },
            });

            Promenade(root, BowlingAlleyKit.Pbr("Basalt", new Color(.55f, .52f, .55f), .55f, Vector2.one), 2.2f);
            Lounge(root, venue, BowlingAlleyKit.Pbr("LeatherNavy", new Color(.55f, .2f, .14f), .8f, new Vector2(2, 2)), copper, basalt, obsidian, copper);
            StringLights(root, venue.Fx, obsidian, new Color(1f, .5f, .18f), BowlingAlleyKit.BankLeft - .9f, BowlingAlleyKit.BankRight + .9f);
            foreach (var r in root.GetComponentsInChildren<MeshRenderer>(true)) if (r.name == "Promenade") r.shadowCastingMode = ShadowCastingMode.Off;

            var key = BowlingClubLanes.Key(root, Color.white, 1.6f, new Vector3(30, -40, 0), .7f);
            TennisVenueBuilder.SkyForBowling(TennisVenueKind.Volcano, key, camera);
            // The tennis crater lights its walls with two lava up-lights (directional): here they would take the pins' light slots,
            // so the sun stands higher and warmer, the ambient carries the lava bounce, and a warm haze lifts the terraces out of black.
            key.transform.rotation = Quaternion.LookRotation(-new Vector3(.66f, .62f, .70f).normalized);
            key.color = new Color(1f, .84f, .72f); key.intensity = 1.6f;
            BowlingVenue.Ambient(new Color(.46f, .40f, .50f), new Color(.52f, .34f, .30f), new Color(.62f, .26f, .12f));
            BowlingVenue.Fog(new Color(.58f, .34f, .30f), 60, 900);
            if (RenderSettings.skybox && RenderSettings.skybox.HasProperty("_Exposure")) RenderSettings.skybox.SetFloat("_Exposure", 1.35f);
            BowlingClubLanes.BowlerLights(root, new Color(1f, .78f, .6f), 4.8f, 4.6f);
            BowlingClubLanes.Probes(root, venue, 2 * SlabHalfX, new Color(.45f, .22f, .16f), 1.1f);
            venue.Post = BowlingClubLanes.Post(root, camera, new BowlingClubLanes.PostLook
            {
                BloomThreshold = 1.0f, BloomIntensity = .75f, BloomScatter = .68f, BloomTint = new Color(1f, .7f, .5f),
                Exposure = .25f, Contrast = 13, Saturation = 10, Temperature = 4, Vignette = .2f, VignetteColor = new Color(.12f, .04f, .02f),
            });
            venue.Crowd = Majestic.MajesticCrowd.Build(root, venue.Seats, lod: true);
            return venue;
        }
    }
}
