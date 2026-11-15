#if UNITY_EDITOR
using UnityEditor;
using UnityEngine;

namespace GolfArcade.EditorTools
{
    /// CLOTH JIGGLE looseness maps (KitV2_<sport>_<sex>_Top_J.png) are data sampled in the vertex stage: linear, no mips, uncompressed, clamped,
    /// on every platform (a compressed or sRGB map would move the wrong cloth by the wrong amount).
    public sealed class ClothJiggleImport : AssetPostprocessor
    {
        void OnPreprocessTexture()
        {
            if (!assetPath.EndsWith("_Top_J.png")) return;
            var ti = (TextureImporter)assetImporter;
            ti.sRGBTexture = false; ti.mipmapEnabled = false; ti.wrapMode = TextureWrapMode.Clamp; ti.filterMode = FilterMode.Bilinear;
            ti.textureCompression = TextureImporterCompression.Uncompressed; ti.maxTextureSize = 512;
            foreach (var platform in new[] { "iPhone", "Standalone" })
            {
                var ps = ti.GetPlatformTextureSettings(platform);
                ps.overridden = true; ps.format = TextureImporterFormat.RGBA32; ps.maxTextureSize = 512; ti.SetPlatformTextureSettings(ps);
            }
        }
    }
}
#endif
