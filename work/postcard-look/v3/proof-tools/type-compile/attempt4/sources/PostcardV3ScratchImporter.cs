// DRAFT: applies baseline course importer settings to NEW scratch assets only.
using UnityEditor;
namespace GolfArcade.EditorTools
{
    public sealed class PostcardV3ScratchImporter:AssetPostprocessor
    {
        void OnPreprocessModel()
        {
            if(!assetPath.StartsWith("Assets/Editor/PostcardV3Scratch/",System.StringComparison.Ordinal))return;
            var i=(ModelImporter)assetImporter;
            i.isReadable=true;i.importCameras=false;i.importLights=false;i.importAnimation=false;
            i.importBlendShapes=false;i.importVisibility=false;i.animationType=ModelImporterAnimationType.None;
            i.meshCompression=ModelImporterMeshCompression.Off;i.importNormals=ModelImporterNormals.Import;
            i.materialImportMode=ModelImporterMaterialImportMode.ImportStandard;i.materialLocation=ModelImporterMaterialLocation.InPrefab;
            i.useFileScale=true;i.globalScale=1f;
        }
    }
}
