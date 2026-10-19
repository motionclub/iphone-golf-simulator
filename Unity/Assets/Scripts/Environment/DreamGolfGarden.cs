using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;

namespace GolfArcade.EnvironmentArt
{
    /// The second golf art pass: actual geometry registered to the unchanged course.
    /// No colliders, physics materials, scoring regions or camera transforms are added.
    public sealed class DreamGolfGarden : MonoBehaviour
    {
        readonly List<Material> materials=new();
        public static bool Enabled => LuminousCoastPilot.Enabled && System.Environment.GetEnvironmentVariable("LUMINOUS_DREAM")!="0";
        public static void Build(Transform course)
        {
            if(!Enabled || course.GetComponentInChildren<DreamGolfGarden>())return;
            var prefab=Resources.Load<GameObject>("Environment/LuminousCoast/DreamGarden");
            var shader=Resources.Load<Shader>("Environment/LuminousCoast/DreamSurface");
            if(!prefab || !shader){Debug.LogError("[DreamGarden] missing scene kit/shader");return;}
            var root=Instantiate(prefab,course,false);root.name="Dream Coast garden";
            var owner=root.AddComponent<DreamGolfGarden>();
            Transform Find(Transform parent,string name){foreach(var t in parent.GetComponentsInChildren<Transform>(true))if(t.name==name)return t;return null;}
            var a=Find(root.transform,"DREAM_ANCHOR_TEE");var b=Find(root.transform,"DREAM_ANCHOR_PIN");var c=Find(root.transform,"DREAM_ANCHOR_UP");
            var x=Find(course,"MARKER_TEE");var y=Find(course,"MARKER_PIN");var z=Find(course,"MARKER_UP");
            if(!a||!b||!c||!x||!y||!z){Debug.LogError("[DreamGarden] missing course anchors");Destroy(root);return;}
            var fromUp=(c.position-a.position).normalized;var toUp=(z.position-x.position).normalized;
            var from=Vector3.ProjectOnPlane(b.position-a.position,fromUp);var to=Vector3.ProjectOnPlane(y.position-x.position,toUp);
            float scale=to.magnitude/from.magnitude;
            var rotation=Quaternion.LookRotation(to,toUp)*Quaternion.Inverse(Quaternion.LookRotation(from,fromUp));
            var offset=a.position-root.transform.position;
            root.transform.localScale*=scale;root.transform.rotation=rotation*root.transform.rotation;root.transform.position=x.position-rotation*offset*scale;
            float error=Mathf.Max(Vector3.Distance(a.position,x.position),Mathf.Max(Vector3.Distance(b.position,y.position),Vector3.Distance(c.position,z.position)));
            if(error>.003f){Debug.LogError($"[DreamGarden] registration failed: {error}");Destroy(root);return;}
            var cache=new Dictionary<string,Material>();int triangles=0;
            foreach(var r in root.GetComponentsInChildren<MeshRenderer>()) {
                string role=r.name.Replace("DREAM_","").Split('.')[0];
                if(!cache.TryGetValue(role,out var m)) {
                    m=new Material(role=="Waterfall"?Resources.Load<Shader>("Environment/LuminousCoast/DreamWaterfall"):shader){name="Dream Coast "+role,enableInstancing=true};
                    materialsAdd(m);cache[role]=m;
                    if(role!="Waterfall") {
                        m.SetFloat("_Metallic",role=="Gold"?.72f:role=="Teal"?.35f:0);
                        m.SetFloat("_Smoothness",role=="Gold"?.58f:role=="Teal"?.65f:role=="Plaster"?.32f:.16f);
                        m.SetFloat("_Detail",role=="Stone"?1:role=="Wood"?.65f:.08f);
                        m.SetFloat("_Leaf",role=="Leaf"||role=="Bloom"?1:0);
                        m.SetFloat("_Cull",role=="Leaf"||role=="Bloom"?0:2);
                        m.SetTexture("_RockMap",Resources.Load<Texture2D>("Course/Resort/CoastalCliffScan_C"));
                        m.SetTexture("_RockNormal",Resources.Load<Texture2D>("Course/Resort/CoastalCliffScan_N"));
                    }
                }
                var slots=new Material[r.sharedMaterials.Length];for(int i=0;i<slots.Length;i++)slots[i]=m;r.sharedMaterials=slots;
                r.shadowCastingMode=role=="Waterfall"||role=="Leaf"||role=="Bloom"?ShadowCastingMode.Off:ShadowCastingMode.On;r.receiveShadows=true;
                var mesh=r.GetComponent<MeshFilter>().sharedMesh;triangles+=mesh.triangles.Length/3;

            }
            void materialsAdd(Material m)=>owner.materials.Add(m);
            foreach(var r in course.GetComponentsInChildren<MeshRenderer>(true)) {
                if(r.transform.IsChildOf(root.transform))continue;
                if(r.name=="LIGHTHOUSE"||r.name=="RESORT_LANDMARK_LIGHTHOUSE"||r.name=="BRIDGE_RAILS"||r.name=="RESORT_LANDMARK_BRIDGE_RAILS")r.enabled=false;
            }
            Debug.Log($"[DreamGarden] registered {triangles} triangles, {cache.Count} materials, anchor error {error:F6}; no colliders added");
        }
        void OnDestroy(){foreach(var m in materials)if(m)Destroy(m);}
    }
}
