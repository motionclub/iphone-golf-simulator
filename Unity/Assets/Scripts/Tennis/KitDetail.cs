using System;
using System.Linq;
using UnityEngine;

namespace GolfArcade.Tennis
{
    /// KIT DETAIL (2026-11-19, work/clothing-tex-1119): per-garment fabric scale and finish for the baked construction maps
    /// (seams, topstitching, hems, rib bands, pleats, pockets) on the tennis and bowling heroes' tops and bottoms.
    /// Reads Resources/KitDetail/<Sport>_<Sex>_<Top|Bottom>.json (written by bake_detail.py / install_tex.py) and sets the
    /// garment material's floats. Colour stays the player's pick. Off: KIT_DETAIL=0.
    public static class KitDetail
    {
        [Serializable] class Entry { public string name; public float value; }
        [Serializable] class Params { public string garment; public Entry[] floats; }

        public static void Apply(MatchHeroLook look)
        {
            if (!look || look.kit == null || Environment.GetEnvironmentVariable("KIT_DETAIL") == "0") return;
            string sport = look.golfKit ? "Golf" : string.IsNullOrEmpty(look.kitSport) ? "Tennis" : look.kitSport;
            string sex = look.female ? "Female" : "Male";
            foreach (var r in look.kit)
            {
                if (!r || (r.name != "Kit_Top" && r.name != "Kit_Bottom")) continue;
                var asset = Resources.Load<TextAsset>($"KitDetail/{sport}_{sex}_{r.name.Substring(4)}");
                if (!asset) continue;
                var p = JsonUtility.FromJson<Params>(asset.text);
                if (p?.floats == null) continue;
                foreach (var m in r.sharedMaterials.Where(m => m && m.HasProperty("_WeaveTile")))
                    foreach (var e in p.floats) m.SetFloat(e.name, e.value);
                Debug.Log($"[KitDetail] {sport}_{sex}_{r.name}: {p.floats.Length} floats");
            }
        }
    }
}
