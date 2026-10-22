#if UNITY_EDITOR
using System.IO; using System.Linq; using UnityEngine; using UnityEditor;
namespace GolfArcade.EditorTools {
 /// Logs vertex/triangle counts of the meshes in the installed male head FBX (topology guard for the 2026-10-17 face pass).
 public static class MaleFaceMeshCount {
  public static void Run() {
   var path="Assets/Resources/Tennis/OriginalSeamBlinkFinish/Male.fbx";
   var s=string.Join("\n",AssetDatabase.LoadAllAssetsAtPath(path).OfType<Mesh>().Select(m=>$"{m.name} v={m.vertexCount} t={m.triangles.Length/3} shapes={m.blendShapeCount}"));
   File.WriteAllText(System.Environment.GetEnvironmentVariable("MESH_COUNT_OUT"),s+"\n");
  }
 }
}
#endif
