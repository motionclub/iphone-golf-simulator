#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using UnityEngine;
using GolfArcade.EnvironmentArt;
namespace GolfArcade.EditorTools {
 public static class LuminousCoastAudit {
  [Serializable] sealed class Evidence {public string scene,venue,skyShader,colliderHash,courtGeometryHash;public int pilotRoots,colliders;public float courtHeight;public string[] pilotMaterials;public bool courtColorOverride;}
  public static void Write() {
   string path=Environment.GetEnvironmentVariable("LUMINOUS_AUDIT_OUT");if(string.IsNullOrWhiteSpace(path))return;
   var colliders=UnityEngine.Object.FindObjectsByType<MeshCollider>(FindObjectsSortMode.None).OrderBy(c=>c.name).ToArray();
   var text=new StringBuilder();
   foreach(var c in colliders){text.Append(c.name).Append(c.enabled).Append(c.transform.localToWorldMatrix.ToString("R"));var m=c.sharedMesh;if(!m)continue;text.Append(m.name).Append(m.vertexCount);if(m.isReadable){foreach(var v in m.vertices)text.Append(v.ToString("R"));foreach(var i in m.triangles)text.Append(i).Append(',');}}
   var court=new StringBuilder();
   foreach(var r in UnityEngine.Object.FindObjectsByType<MeshRenderer>(FindObjectsSortMode.None).Where(r=>r.sharedMaterials.Any(m=>m&&m.name.StartsWith("TropicalV3_002"))).OrderBy(r=>r.name)) {
    var mesh=r.GetComponent<MeshFilter>()?.sharedMesh;if(!mesh)continue;
    court.Append(r.name).Append(r.transform.localToWorldMatrix.ToString("R")).Append(mesh.vertexCount);
    if(mesh.isReadable){foreach(var v in mesh.vertices)court.Append(v.ToString("R"));foreach(var i in mesh.triangles)court.Append(i).Append(',');}
   }
   using var sha=SHA256.Create();
   var e=new Evidence {scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene().name,venue=GolfArcade.Tennis.TennisVenue.Current.ToString(),skyShader=RenderSettings.skybox?RenderSettings.skybox.shader.name:"none",courtHeight=GolfArcade.Tennis.TennisVenue.RenderedCourtHeight,courtGeometryHash=BitConverter.ToString(sha.ComputeHash(Encoding.UTF8.GetBytes(court.ToString()))).Replace("-","").ToLowerInvariant(),colliders=colliders.Length,colliderHash=BitConverter.ToString(sha.ComputeHash(Encoding.UTF8.GetBytes(text.ToString()))).Replace("-","").ToLowerInvariant(),pilotRoots=UnityEngine.Object.FindObjectsByType<LuminousCoastPilot>(FindObjectsSortMode.None).Length,courtColorOverride=GolfArcade.Tennis.TennisVenue.CourtColorOverride.HasValue,pilotMaterials=UnityEngine.Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None).SelectMany(r=>r.sharedMaterials).Where(m=>m&&m.name.Contains("Luminous")).Select(m=>m.name).Distinct().OrderBy(n=>n).ToArray()};
   var golf=UnityEngine.Object.FindFirstObjectByType<GolfArcade.Game.GolfGame>();if(golf)e.venue="Golf hole "+golf.CurrentHole.Number;
   Directory.CreateDirectory(Path.GetDirectoryName(path));File.WriteAllText(path,JsonUtility.ToJson(e,true));
  }
 }
}
#endif
