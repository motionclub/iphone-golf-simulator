using UnityEditor;

namespace GolfArcade.EditorTools
{
    /// CHARACTER QUALITY 10-24: the baked hero skin set (Resources/Tennis/SkinMaps) is data, not colour: linear, clamped, mipmapped,
    /// 2048 max; ASTC on iOS (4x4 for the pigment, whose small steps matter, 6x6 for the smooth occlusion / curvature / thinness / oil mask).
    public sealed class SkinMapImport : AssetPostprocessor
    {
        void OnPreprocessTexture()
        {
            if (!assetPath.Contains("/Resources/Tennis/SkinMaps/")) return;
            var t = (TextureImporter)assetImporter;
            t.textureType = TextureImporterType.Default; t.sRGBTexture = false; t.alphaSource = TextureImporterAlphaSource.FromInput;
            t.alphaIsTransparency = false; t.mipmapEnabled = true; t.wrapMode = UnityEngine.TextureWrapMode.Clamp; t.maxTextureSize = 2048;
            t.textureCompression = TextureImporterCompression.CompressedHQ;
            var ios = t.GetPlatformTextureSettings("iPhone");
            ios.overridden = true; ios.maxTextureSize = 2048;
            ios.format = assetPath.Contains("_pigment") ? TextureImporterFormat.ASTC_4x4 : TextureImporterFormat.ASTC_6x6;
            t.SetPlatformTextureSettings(ios);
        }
    }
}
