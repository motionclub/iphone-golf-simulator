using System;
using System.Linq;
using UnityEditor;

namespace GolfArcade.EditorTools
{
    /// 2026-11-22 size pass: Unity's Low mesh compression on the scenery models (stored at 20-bit positions, 8-bit normals and tangents,
    /// 16-bit UVs over each mesh's own range; meshes are full floats again once loaded). 146 MB of vertex data ships as about 63 MB.
    /// Left out on purpose:
    /// - characters (every hero, kit and golfer stays uncompressed);
    /// - the golf course models in Resources/Course: their ground becomes the ball's MeshColliders, so its surface stays exact
    ///   (only the gallery crowd and the botanical kit there are scenery);
    /// - models whose UVs tile far past 0..1 (16 bits over a range of 50 would move texture detail by pixels) and models with blend
    ///   shapes (the animated sea): `Excluded`.
    /// The vertex layout of every shipped mesh is in work/perf-size-audit-1122/runs/mesh/mesh_audit.csv (tools/unity/MeshSizeAudit.cs).
    public sealed class MeshCompressionRules : AssetPostprocessor
    {
        static readonly string[] Folders = {
            "Assets/Resources/Tennis/TropicalV3/", "Assets/Resources/Tennis/Premium/", "Assets/Resources/Environment/",
            "Assets/Resources/Bowling/",
            "Assets/Resources/Course/Resort/GolfGallerySpectators.fbx", "Assets/Resources/Course/Resort/BotanicalKit.fbx" };
        static readonly string[] Excluded = {
            "Assets/Resources/Environment/LuminousCoast/DreamGarden.fbx",   // UVs to 57
            "Assets/Resources/Majestic/Kit/CalderaWall_A.fbx",              // UVs to 5
            "Assets/Resources/Tennis/Premium/TennisCoast.fbx",              // UVs to 48
            "Assets/Resources/Tennis/Premium/TennisHorizon2.fbx" };         // UVs to 8
        /// (Not Resources/Majestic: its landmark kit carries data in its extra UV channels, glow for lit windows and more, read by
        /// MajesticDressing; compressed, the skyscraper venue's towers went dark, 11-22 before/after stills in runs/mesh/shots.)
        /// Physics reads these: the bowling pin deck builds its colliders from the pin models (BowlingArt.PinHulls: Pin_Colliders; a
        /// compressed hull changed the pinfall, BowlingPhysicsTests.PinDeckSmoke), and the ball's.
        static readonly string[] PhysicsModels = { "Assets/Resources/Bowling/Pin", "Assets/Resources/Bowling/Ball" };
        public static bool Compressed(string path) =>
            Folders.Any(f => path.StartsWith(f, StringComparison.Ordinal)) && !Excluded.Contains(path)
            && !PhysicsModels.Any(f => path.StartsWith(f, StringComparison.Ordinal));

        public override uint GetVersion() => 3;
        public override int GetPostprocessOrder() => 1000;   // after the folder importers, which set the rest of each model's rules

        void OnPreprocessModel()
        {
            if (!Compressed(assetPath) || !(assetImporter is ModelImporter m)) return;
            m.meshCompression = ModelImporterMeshCompression.Low;
        }
    }
}
