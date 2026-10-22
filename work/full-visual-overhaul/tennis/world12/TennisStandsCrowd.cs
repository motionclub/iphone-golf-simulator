using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;

namespace GolfArcade.Tennis
{
    /// Authored seated sporting spectators with clean opaque rigid art joints.
    /// Replaces the damaged legacy crowd skin binding; the hero rigs are independent.
    public sealed class TennisStandsCrowd : MonoBehaviour
    {
        static readonly float[] TierX={-13.8f,-15f,-16.2f},TierY={.63f,1.28f,1.93f};
        static readonly float[] SeatZ={-9,-7,-5,-3,.7f,2.7f,4.7f,6.7f,10.5f,12.5f,14.5f,16.5f};const int PerRow=12;
        sealed class Fan
        {
            public Transform body,head,left,right;
            public Quaternion headRest,leftRest,rightRest;
            public float phase,cheerAt=-9,style;
        }
        readonly List<Fan> fans=new();
        sealed class InstanceBatch
        {
            public Mesh mesh;public readonly List<MeshRenderer> renderers=new();public Matrix4x4[] matrices;
        }
        readonly List<InstanceBatch> batches=new();
        Material spectatorMaterial;
        bool instancedSubmission=true;
        void Awake(){instancedSubmission=SystemInfo.supportsInstancing;}
        public bool InstancedSubmission=>instancedSubmission;
        public bool SuppressRendering {get;set;}
        public int FanCount=>fans.Count;
        public int InstanceGroupCount=>batches.Count;
        public void SetInstancedSubmission(bool enabled)
        {
            instancedSubmission=enabled&&SystemInfo.supportsInstancing;
            foreach(var batch in batches)foreach(var renderer in batch.renderers)if(renderer)renderer.enabled=!instancedSubmission;
        }
        TennisGame game;
        static Transform Part(Transform root,string name){foreach(Transform t in root)if(t.name.StartsWith(name))return t;return null;}
        public void Build(Transform parent)
        {
            game=GetComponent<TennisGame>();
            BuildStands(parent);
            var prefab=Resources.Load<GameObject>("Tennis/Premium/TennisSpectators");
            var shader=Resources.Load<Shader>("Tennis/Shaders/TennisSpectator");
            if(!prefab||!shader){Debug.LogWarning("[Crowd] authored seated spectators missing");return;}
            var material=new Material(shader){name="Sporting spectator vertex palette",enableInstancing=true};spectatorMaterial=material;
            int i=0;
            for(int tier=0;tier<TierX.Length;tier++)for(int s=0;s<PerRow;s++,i++)
            {
                var instance=Instantiate(prefab,parent);instance.name="Seated sporting fan "+i;
                int variant=(s*5+tier*3+(s/3))%6;Transform selected=null;
                foreach(var t in instance.GetComponentsInChildren<Transform>(true))
                    if(t.name.StartsWith("FAN_")){bool use=t.name=="FAN_"+variant;t.gameObject.SetActive(use);if(use)selected=t;}
                if(!selected){Destroy(instance);continue;}
                selected.localPosition=Vector3.zero;
                instance.transform.SetPositionAndRotation(new Vector3(TierX[tier],TierY[tier],SeatZ[s]),Quaternion.Euler(0,90,0)*prefab.transform.rotation);
                if(i==0)
                {
                    var head=Part(selected,"HEAD");var mf=head?head.GetComponent<MeshFilter>():null;
                    if(mf&&mf.sharedMesh)
                    {
                        var expected=new Color(.76f,.44f,.27f);var gamma=expected.gamma;float linearDistance=10,gammaDistance=10;Color found=Color.white;
                        foreach(var c in mf.sharedMesh.colors)
                        {
                            float dl=Mathf.Pow(c.r-expected.r,2)+Mathf.Pow(c.g-expected.g,2)+Mathf.Pow(c.b-expected.b,2);
                            float dg=Mathf.Pow(c.r-gamma.r,2)+Mathf.Pow(c.g-gamma.g,2)+Mathf.Pow(c.b-gamma.b,2);
                            linearDistance=Mathf.Min(linearDistance,dl);if(dg<gammaDistance){gammaDistance=dg;found=c;}
                        }
                        material.SetFloat("_ColorsAreSRGB",gammaDistance<linearDistance?1:0);
                        Debug.Log($"[CrowdColours] vertex skin {found} linearDistance={linearDistance:F6} gammaDistance={gammaDistance:F6} decodeSRGB={gammaDistance<linearDistance}");
                    }
                }
                foreach(var r in selected.GetComponentsInChildren<MeshRenderer>(true))
                {
                    r.sharedMaterial=material;r.shadowCastingMode=ShadowCastingMode.On;r.receiveShadows=true;
                    var filter=r.GetComponent<MeshFilter>();if(!filter||!filter.sharedMesh)continue;
                    var batch=batches.Find(b=>b.mesh==filter.sharedMesh);
                    if(batch==null){batch=new InstanceBatch{mesh=filter.sharedMesh};batches.Add(batch);}batch.renderers.Add(r);
                }
                var f=new Fan{body=Part(selected,"BODY"),head=Part(selected,"HEAD"),left=Part(selected,"ARM_L"),right=Part(selected,"ARM_R"),phase=i*1.618f,style=(i*17%9)/8f};
                if(!f.head||!f.left||!f.right){Destroy(instance);continue;}
                f.headRest=f.head.rotation;f.leftRest=f.left.rotation;f.rightRest=f.right.rotation;fans.Add(f);
            }
            foreach(var batch in batches)batch.matrices=new Matrix4x4[batch.renderers.Count];
            SetInstancedSubmission(instancedSubmission);
            Debug.Log("[Crowd] Clean authored seated spectators: "+fans.Count+"; rigid meshes, no skinning");
        }
        static void BuildStands(Transform parent)
        {
            foreach(var r in Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None))
            {
                if(r.name.StartsWith("Crowd_")){r.enabled=false;continue;}
                foreach(var m in r.sharedMaterials)if(m&&m.name.StartsWith("TropicalV3_022")){r.enabled=false;break;}
            }
            var root=new GameObject("Crafted sporting bleachers").transform;root.SetParent(parent,true);
            var stone=new TennisVenueBuilder.MB();var seats=new TennisVenueBuilder.MB();var bronze=new TennisVenueBuilder.MB();
            foreach(var interval in new[]{new Vector2(-10.4f,-1.8f),new Vector2(-.2f,8.3f),new Vector2(9.8f,18.4f)})
                for(int tier=0;tier<3;tier++)
                {
                    float floor=TierY[tier]-.46f;
                    TennisVenueArt.BevelBox(stone,new Vector3(TierX[tier],floor*.5f,(interval.x+interval.y)*.5f),new Vector3(1.2f,Mathf.Max(.12f,floor),interval.y-interval.x),.025f);
                }
            foreach(float z in new[]{-1f,9f})for(int step=0;step<8;step++)
            {
                float h=(step+1)*.185f;
                TennisVenueArt.BevelBox(stone,new Vector3(-12.65f-step*.53f,h*.5f,z),new Vector3(.54f,h,1.55f),.02f);
            }
            for(int tier=0;tier<3;tier++)foreach(float z in SeatZ)
            {
                var p=new Vector3(TierX[tier],TierY[tier],z);
                TennisVenueArt.BevelBox(seats,p+new Vector3(.03f,-.045f,0),new Vector3(.53f,.09f,.62f),.045f);
                TennisVenueArt.BevelBox(seats,p+new Vector3(-.255f,.25f,0),new Vector3(.075f,.52f,.59f),.035f);
                foreach(int side in new[]{-1,1})
                {
                    bronze.Cyl(p+new Vector3(-.15f,-.46f,side*.24f),.025f,.025f,.45f,8,Vector2.zero,Vector2.zero);
                    bronze.Cyl(p+new Vector3(.23f,-.46f,side*.24f),.025f,.025f,.45f,8,Vector2.zero,Vector2.zero);
                }
            }
            TennisVenueBuilder.MeshObject(root,"Cut limestone bleachers",stone.ToMesh("Cut limestone bleachers"),TennisVenueArt.Surface("Bleacher limestone",new Color(.72f,.69f,.60f),.18f,0,.035f,.012f),true);
            TennisVenueBuilder.MeshObject(root,"Teal sporting seats",seats.ToMesh("Teal sporting seats"),TennisVenueArt.Surface("Teal molded seats",new Color(.025f,.16f,.18f),.25f),true);
            TennisVenueBuilder.MeshObject(root,"Bronze seat supports",bronze.ToMesh("Bronze seat supports"),TennisVenueArt.Surface("Bronze seat supports",new Color(.18f,.22f,.20f),.3f,.25f),true);
        }
        void LateUpdate()
        {
            if(!instancedSubmission||SuppressRendering||!spectatorMaterial)return;
            // Explicit instance submissions bypass the SRP Batcher priority that
            // otherwise kept 144 individual part draws despite enableInstancing.
            var parameters=new RenderParams(spectatorMaterial){shadowCastingMode=ShadowCastingMode.On,receiveShadows=true,layer=gameObject.layer,lightProbeUsage=LightProbeUsage.BlendProbes};
            foreach(var batch in batches)
            {
                for(int i=0;i<batch.renderers.Count;i++)batch.matrices[i]=batch.renderers[i].localToWorldMatrix;
                for(int sub=0;sub<batch.mesh.subMeshCount;sub++)Graphics.RenderMeshInstanced(parameters,batch.mesh,sub,batch.matrices);
            }
        }
        void OnDestroy(){if(spectatorMaterial)Destroy(spectatorMaterial);}
        public void Cheer(float strength)
        {
            for(int i=0;i<fans.Count;i++)
                if(((i*7919)%100)/100f<=.25f+.7f*strength)fans[i].cheerAt=Time.time+((i*13)%7)*.06f;
        }
        void Update()
        {
            foreach(var f in fans)
            {
                float t=Time.time-f.cheerAt;
                float w=t<0||t>2.7f?0:Mathf.SmoothStep(0,1,Mathf.Clamp01(Mathf.Min(t/.35f,(2.7f-t)/.55f)));
                float pulse=.91f+.09f*Mathf.Sin(t*8+f.phase);
                // Court is +world X from the western stands. Shoulder flex raises
                // the authored bent arms into a seated cheer; legs stay planted.
                f.left.rotation=Quaternion.AngleAxis(w*(84+f.style*18)*pulse,Vector3.forward)*f.leftRest;
                f.right.rotation=Quaternion.AngleAxis(w*(94-f.style*16)*pulse,Vector3.forward)*f.rightRest;
                float yaw=Mathf.Sin(Time.time*.35f+f.phase)*4;
                if(game){var d=game.BallPosition-f.head.position;yaw=Mathf.Clamp(Mathf.Atan2(d.z,d.x)*Mathf.Rad2Deg,-22,22);}
                f.head.rotation=Quaternion.AngleAxis(-yaw,Vector3.up)*Quaternion.AngleAxis(Mathf.Sin(Time.time*.7f+f.phase)*1.2f-w*5,Vector3.forward)*f.headRest;
            }
        }
    }
}
