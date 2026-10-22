using UnityEditor;

namespace GolfArcade.EditorTools
{
    /// Chat 10 (work/majestic-all-maps): the caldera walls are recoloured at runtime (MajesticKit.Darken: the kit's grey
    /// basalt reads pale under the Magma dusk), which needs their mesh colours readable. Only these small FBX (caldera
    /// walls ~1.8 k vertices each, basalt spire, obsidian arch, caldera volcano) keep a CPU copy; the rest of the kit stays non-readable.
    sealed class MajesticKitImport : AssetPostprocessor
    {
        void OnPreprocessModel()
        {
            if (!(assetPath.Contains("Resources/Majestic/Kit/CalderaWall_") || assetPath.EndsWith("Kit/BasaltSpire.fbx") || assetPath.EndsWith("Kit/ObsidianArch.fbx") || assetPath.EndsWith("Kit/CalderaVolcano.fbx"))) return;
            if (assetImporter is ModelImporter m) m.isReadable = true;
        }
    }
}
