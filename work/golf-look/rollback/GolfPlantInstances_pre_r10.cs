using System;
using System.Collections.Generic;
using System.IO;
using System.Security.Cryptography;
using UnityEngine;
using UnityEngine.Rendering;
namespace GolfArcade.Course
{
    /// Draw identical plant geometry as instances, preserving each world matrix
    /// (including the unchanged plant shader's per-pivot wind phase).
    public sealed class GolfPlantInstances:MonoBehaviour
    {
        sealed class Group {public Mesh mesh;public Material material;public int sub,layer;public ShadowCastingMode shadows;public bool receive;public readonly List<Matrix4x4> matrices=new();public readonly List<Matrix4x4[]> batches=new();}
        readonly List<Group> groups=new();
        public static bool ProofMask;static Material proofMaterial;
        static readonly Dictionary<int,string> hashes=new();
        static string MeshHash(Mesh mesh)
        {
            if(hashes.TryGetValue(mesh.GetInstanceID(),out var hash))return hash;
            using var bytes=new MemoryStream();using var writer=new BinaryWriter(bytes);
            foreach(var p in mesh.vertices){writer.Write(p.x);writer.Write(p.y);writer.Write(p.z);}
            foreach(var p in mesh.normals){writer.Write(p.x);writer.Write(p.y);writer.Write(p.z);}
            foreach(var p in mesh.tangents){writer.Write(p.x);writer.Write(p.y);writer.Write(p.z);writer.Write(p.w);}
            foreach(var p in mesh.uv){writer.Write(p.x);writer.Write(p.y);}
            foreach(var p in mesh.colors){writer.Write(p.r);writer.Write(p.g);writer.Write(p.b);writer.Write(p.a);}
            for(int i=0;i<mesh.subMeshCount;i++)foreach(int j in mesh.GetIndices(i))writer.Write(j);
            hash=Convert.ToBase64String(SHA256.Create().ComputeHash(bytes.ToArray()));hashes[mesh.GetInstanceID()]=hash;return hash;
        }
        public static void Apply(GameObject model)
        {
            if(!GolfLook.UseSurfaceShaders||!SystemInfo.supportsInstancing||model.GetComponent<GolfPlantInstances>())return;
            var component=model.AddComponent<GolfPlantInstances>();var map=new Dictionary<string,Group>();int source=0;
            foreach(var r in model.GetComponentsInChildren<MeshRenderer>(true))
            {
                if(!r.enabled||!r.gameObject.activeInHierarchy)continue;
                var mf=r.GetComponent<MeshFilter>();if(!mf||!mf.sharedMesh||!mf.sharedMesh.isReadable)continue;
                var mats=r.sharedMaterials;bool plants=mats.Length>0;
                foreach(var m in mats)if(!m||m.shader.name!="GolfArcade/GolfPlants")plants=false;
                if(!plants)continue;
                var p=r.bounds.center;string mesh=MeshHash(mf.sharedMesh);
                for(int sub=0;sub<mf.sharedMesh.subMeshCount;sub++)
                {
                    var material=mats[Mathf.Min(sub,mats.Length-1)];material.enableInstancing=true;
                    string key=$"{mesh}/{sub}/{material.GetInstanceID()}/{Mathf.FloorToInt(p.x/256)}/{Mathf.FloorToInt(p.z/256)}/{(int)r.shadowCastingMode}/{r.receiveShadows}/{r.gameObject.layer}";
                    if(!map.TryGetValue(key,out var g)){g=new Group{mesh=mf.sharedMesh,material=material,sub=sub,layer=r.gameObject.layer,shadows=r.shadowCastingMode,receive=r.receiveShadows};map.Add(key,g);}
                    g.matrices.Add(r.transform.localToWorldMatrix);
                }
                r.enabled=false;source++;
            }
            component.groups.AddRange(map.Values);
            foreach(var g in component.groups)for(int start=0;start<g.matrices.Count;start+=1023)
                g.batches.Add(g.matrices.GetRange(start,Mathf.Min(1023,g.matrices.Count-start)).ToArray());
            Debug.Log($"[GolfPlantInstances] {source} original plant renderers in {map.Count} instance groups; original meshes, colours, world matrices and wind shader unchanged");
        }
        void LateUpdate()
        {
            if(ProofMask&&!proofMaterial){proofMaterial=new Material(Shader.Find("Hidden/ClothProofMask"));proofMaterial.SetColor("_ClassColour",Color.black);proofMaterial.enableInstancing=true;}
            foreach(var g in groups)foreach(var batch in g.batches)
                Graphics.DrawMeshInstanced(g.mesh,g.sub,ProofMask?proofMaterial:g.material,batch,batch.Length,null,g.shadows,g.receive,g.layer,null,LightProbeUsage.BlendProbes,null);
        }
    }
}
