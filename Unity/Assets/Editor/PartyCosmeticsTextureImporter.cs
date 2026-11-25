using UnityEditor;
using UnityEngine;
namespace GolfArcade.EditorTools {
    /// Offline colour detail only; normal maps and hero textures are outside this scope.
    public sealed class PartyCosmeticsTextureImporter : AssetPostprocessor {
        void OnPreprocessTexture() {
            if (!assetPath.StartsWith("Assets/Resources/Cosmetics/")) return;
            var t=(TextureImporter)assetImporter;t.textureType=TextureImporterType.Default;t.sRGBTexture=true;
            t.mipmapEnabled=true;t.maxTextureSize=512;t.wrapModeU=TextureWrapMode.Repeat;t.wrapModeV=TextureWrapMode.Clamp;
            t.filterMode=FilterMode.Trilinear;t.textureCompression=TextureImporterCompression.Compressed;t.crunchedCompression=false;
            var ios=t.GetPlatformTextureSettings("iPhone");ios.overridden=true;ios.maxTextureSize=512;ios.format=TextureImporterFormat.ASTC_6x6;t.SetPlatformTextureSettings(ios);
        }
    }
}
