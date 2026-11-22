using UnityEngine;

namespace GolfArcade.Tennis
{
    /// The tennis venues' worlds, lent to the bowling lanes (2026-11-21, Adnan: "re-use ... the skyscraper map we use for tennis
    /// as a bowling alley"). Bowling builds its own deck furniture (lanes, lounge, crowd); these calls build everything the tennis
    /// court sits in -- the slab, what holds it up and the world round it -- sized to the alley's footprint instead of the court's,
    /// and the venue's sky, ambient and fog. No lights are created: bowling's per-object light slots belong to the pins.
    public static partial class TennisVenueBuilder
    {
        /// The rooftop slab (half extents hx, hz about `root`), the tower under it, the cloud sea and the skyline.
        public static void SkyscraperForBowling(Transform root, float hx, float hz) => Skyscraper.ForBowling(root, hx, hz);

        /// The obsidian slab (half extents hx, hz about `root`), its keel, the terraced crater, the lava lake and its islands,
        /// the pylons, the eruption plume and the embers.
        public static void VolcanoForBowling(Transform root, float hx, float hz) => Volcano.ForBowling(root, hx, hz);

        /// The venue's sky, ambient and fog, as its tennis match has them. `key` is aimed and coloured as the tennis sun.
        /// Any extra light the tennis rig adds (the crater's lava up-lights) is removed again.
        public static void SkyForBowling(TennisVenueKind kind, Light key, Camera camera)
        {
            var was = TennisVenue.Selected; TennisVenue.Selected = kind;   // the rendered backdrop reads the tennis venue
            try
            {
                var before = Object.FindObjectsByType<Light>(FindObjectsSortMode.None);
                RenderSettings.sun = key;
                switch (kind)
                {
                    case TennisVenueKind.Skyscraper: Skyscraper.Light(key, camera); break;
                    case TennisVenueKind.Volcano: Volcano.Light(key, camera); break;
                    default:
                        TennisLookSun(key);
                        GolfArcade.EnvironmentArt.RenderedBackdrop.TennisEarly();
                        break;
                }
                var keep = new System.Collections.Generic.HashSet<Light>(before) { key };
                foreach (var l in Object.FindObjectsByType<Light>(FindObjectsSortMode.None))
                    if (!keep.Contains(l)) Object.Destroy(l.gameObject);
                camera.farClipPlane = Mathf.Max(camera.farClipPlane, TennisVenue.FarClipFor(kind));
                if (RenderSettings.skybox) camera.clearFlags = CameraClearFlags.Skybox;
                Debug.Log("[Bowling] " + kind + " sky: " + (RenderSettings.skybox ? RenderSettings.skybox.name + " (" + RenderSettings.skybox.shader.name + ")" : "none") + ", far clip " + camera.farClipPlane);
            }
            finally { TennisVenue.Selected = was; }
        }

        static void TennisLookSun(Light key)
        {
            key.transform.rotation = Quaternion.LookRotation(-TennisLook.SunDirection);
            key.color = TennisLook.SunColor; key.intensity = TennisLook.SunIntensity;
        }
    }
}
