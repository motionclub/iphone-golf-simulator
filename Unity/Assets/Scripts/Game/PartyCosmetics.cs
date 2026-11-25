using System;
using System.Collections.Generic;
using UnityEngine;

namespace GolfArcade.Game
{
    /// Offline, cosmetic-only party gear. IDs are allowlisted before resource lookup.
    public static class PartyCosmetics
    {
        public static readonly string[] Clubs = { "party.hockey", "party.slugger", "party.balloon", "party.candy" };
        public static readonly string[] Balls = { "ball.orbit", "ball.melon", "ball.checker", "ball.sunset" };
        public static readonly string[] Extras = { "extra.mint", "extra.neon", "extra.caramel" };
        public static string ClubSkin = "standard", BallSkin = "standard", AccessorySkin = "standard";
        public static string ValidClub(string id) => Array.IndexOf(Clubs, id) >= 0 ? id : "standard";
        public static string ValidBall(string id) => Array.IndexOf(Balls, id) >= 0 ? id : "standard";
        public static string ValidExtra(string id) => Array.IndexOf(Extras, id) >= 0 ? id : "standard";
        public static Texture2D BallTexture(string id) => ValidBall(id) == "standard" ? Texture2D.whiteTexture : Resources.Load<Texture2D>("Cosmetics/" + id.Replace('.', '_'));
        public static (Color, Color)? ExtraColours(string id) => id switch {
            "extra.mint" => (Hex("23C8A5"), Hex("173247")),
            "extra.neon" => (Hex("7748CB"), Hex("EFFF62")),
            "extra.caramel" => (Hex("BA783F"), Hex("FFF0D6")),
            _ => null
        };
        public static SkinnedMeshRenderer ContactReference(bool female, string renderer) {
            var asset = Resources.Load<GameObject>("Golf/Equipment/" + (female ? "Female" : "Male"));
            if (!asset) return null;
            foreach (var r in asset.GetComponentsInChildren<SkinnedMeshRenderer>(true)) if (r.name == renderer) return r;
            return null;
        }
        static Color Hex(string s) { ColorUtility.TryParseHtmlString("#" + s, out var c); return c; }
        [Serializable] sealed class MaterialSpec { public string name,texture; public float[] color;public float metallic,roughness; }
        [Serializable] sealed class MaterialCatalog { public MaterialSpec[] materials; }
        static MaterialCatalog definitions;
        static readonly Dictionary<string, Material> materials = new();
        public static Material MaterialFor(Material source)
        {
            if (!source || !source.name.StartsWith("Party_")) return null;
            string name = source.name.Split('.')[0];
            if (materials.TryGetValue(name, out var cached) && cached) return cached;
            definitions ??= JsonUtility.FromJson<MaterialCatalog>(Resources.Load<TextAsset>("Cosmetics/materials").text);
            var spec = Array.Find(definitions.materials, d => d.name == name);
            if (spec == null) return null;
            var color = new Color(spec.color[0],spec.color[1],spec.color[2],1);
            var m = new Material(Shader.Find("Universal Render Pipeline/Lit")) { name = name, color = color };
            m.SetColor("_BaseColor", color); m.SetFloat("_Metallic", spec.metallic); m.SetFloat("_Smoothness", 1 - spec.roughness);
            if (!string.IsNullOrEmpty(spec.texture)) {
                var detail = Resources.Load<Texture2D>("Cosmetics/Cosmetic_" + spec.texture);
                if (detail) { detail.wrapModeU=TextureWrapMode.Repeat; detail.wrapModeV=TextureWrapMode.Repeat; }
                m.SetTexture("_BaseMap", detail);
            }
            materials[name] = m; return m;
        }
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        static void Reset() { ClubSkin = BallSkin = AccessorySkin = "standard"; }
    }
}
