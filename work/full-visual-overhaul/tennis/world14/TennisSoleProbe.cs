#if UNITY_EDITOR
using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using GolfArcade.Tennis;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Object=UnityEngine.Object;

namespace GolfArcade.EditorTools
{
    /// Measures the evaluated shoe soles, not ankle joints or their shadow image.
    /// Live controller phases are followed by explicitly labelled source-only samples.
    [InitializeOnLoad] public static class TennisSoleProbe
    {
        const string Flag="TennisSoleProbe";static IEnumerator routine;static int lastFrame=-1;
        [Serializable] sealed class Row
        {
            public string sex,phase,state,clip,shoe,floorRenderer,collider;
            public int frame,vertices,soleVertices;public float time,speed,groundLift,sinkBefore,heelRest,toeRest;
            public float actorY,heroY,hipsY,footY,toeY,minShoeY,minSoleY,soleP02Y,visualFloorY,rayFloorY,visualGap,rayGap,maxSkinOracleError;
            public bool visualFloorHit,colliderHit;public Vector3 minSolePoint,actorPosition,heroLocalPosition,rendererLocalPosition;
        }
        [Serializable] sealed class Result{public string tool="TennisSoleProbe",scope="Real game Ready/idle/walk/settle evaluated shoe meshes; direct vertical intersection of the rendered court/apron mesh and independent collider rays. Source-only samples are explicitly labelled and do not certify runtime. No floor is normalized to the Ready pose.";public string venue;public Row[] rows;}
        static readonly List<Row> rows=new();static Renderer[] floors;static string output;
        static TennisSoleProbe(){EditorApplication.update+=Tick;}
        public static void Run(){output=Path.GetFullPath(Environment.GetEnvironmentVariable("TSOLE_OUT")??"../proof/full-visual-overhaul/tennis-sole-probe");Directory.CreateDirectory(output);SessionState.SetString(Flag+"out",output);SessionState.SetBool(Flag,true);EditorSceneManager.OpenScene("Assets/Scenes/Tennis.unity");EditorApplication.isPlaying=true;}
        static void Tick()
        {
            if(!SessionState.GetBool(Flag,false)||!EditorApplication.isPlaying||lastFrame==Time.frameCount)return;
            var game=Object.FindFirstObjectByType<TennisGame>();if(!game||!game.Initialized)return;lastFrame=Time.frameCount;
            try{if(routine==null){output=SessionState.GetString(Flag+"out",output);routine=Go(game);}if(!routine.MoveNext())Finish(0);}catch(Exception e){Debug.LogException(e);Finish(1);}
        }
        static void Finish(int code){SessionState.SetBool(Flag,false);Time.captureFramerate=0;if(Application.isBatchMode)EditorApplication.Exit(code);else EditorApplication.isPlaying=false;}
        static float Field(HeroTennisDriver d,string n)=>(float)typeof(HeroTennisDriver).GetField(n,BindingFlags.NonPublic|BindingFlags.Instance).GetValue(d);
        static IEnumerator Go(TennisGame game)
        {
            Time.captureFramerate=60;HeroGarmentLOD.ForceFullDetail=true;
            foreach(bool female in new[]{false,true})
            {
                game.SelectCharacter(female);string rival=female?"Viktor":"Nadia";game.ConfigureMatch(TennisGame.Mode.Campaign,rival,rival,"SOLE GEOMETRY");var p=game.GetComponent<TennisPresentation>();if(p)p.Finish();game.AutoPlay=false;game.NativeControlled=true;game.SetControllerSetup(false);
                for(int k=0;k<40;k++)yield return null;game.PrepareLesson();for(int k=0;k<12;k++)yield return null;
                floors=Object.FindObjectsByType<MeshRenderer>(FindObjectsSortMode.None).Where(r=>r.enabled&&r.sharedMaterials.Any(m=>m&&(m.name.StartsWith("TropicalV3_002")||m.name.StartsWith("TropicalV3_011")))).Cast<Renderer>().ToArray();
                var d=game.Player.GetComponentInChildren<HeroTennisDriver>();foreach(var skin in d.GetComponentsInChildren<SkinnedMeshRenderer>(true))skin.updateWhenOffscreen=true;
                for(int f=0;f<240;f++)
                {
                    if(f%30==0)game.InjectBall(new Vector3(0,40,2),Vector3.zero);
                    string phase=f<60?"live_idle":f<160?"live_walk_start_right":"live_stop_settle";
                    game.SetLateralInput(f>=60&&f<160?.34f:0,false);yield return null;
                    if(f%6==0)Measure(d,phase,f);
                    if(f==54||f==114||f==234)Photo(game.GameplayCamera,d,Path.Combine(output,(female?"female":"male")+"_"+phase+".png"));
                }
                game.SetLateralInput(0,false);game.enabled=false;d.enabled=false;
                foreach(var c in new[]{HeroTennisDriver.Clip.Ready,HeroTennisDriver.Clip.Idle,HeroTennisDriver.Clip.Walk})
                    for(int k=0;k<8;k++){d.Sample(c,d.LengthOf(c)*k/8f);Measure(d,"source_sample_"+c,k);}
                d.Sample(HeroTennisDriver.Clip.Ready,0);for(int k=0;k<3;k++)yield return null;
                Photo(game.GameplayCamera,d,Path.Combine(output,(female?"female":"male")+"_evaluated_skin_ready.png"));
                var staticShoes=new List<GameObject>();
                foreach(var shoe in d.matchLook.kit.Where(r=>r&&r.name.StartsWith("Kit_Shoe")))
                {
                    var baked=new Mesh();shoe.BakeMesh(baked,false);baked.vertices=baked.vertices.Select(shoe.transform.TransformPoint).ToArray();baked.normals=baked.normals.Select(shoe.transform.TransformDirection).ToArray();baked.RecalculateBounds();
                    var replica=new GameObject("Sole probe evaluated static "+shoe.name);replica.AddComponent<MeshFilter>().sharedMesh=baked;replica.AddComponent<MeshRenderer>().sharedMaterials=shoe.sharedMaterials;shoe.enabled=false;staticShoes.Add(replica);
                }
                for(int k=0;k<3;k++)yield return null;Photo(game.GameplayCamera,d,Path.Combine(output,(female?"female":"male")+"_evaluated_static_ready.png"));
                foreach(var replica in staticShoes){Object.DestroyImmediate(replica.GetComponent<MeshFilter>().sharedMesh);Object.DestroyImmediate(replica);}foreach(var shoe in d.matchLook.kit.Where(r=>r&&r.name.StartsWith("Kit_Shoe")))shoe.enabled=true;
                var sun=RenderSettings.sun;
                if(sun)
                {
                    float bias=sun.shadowBias,normal=sun.shadowNormalBias;
                    Photo(game.GameplayCamera,d,Path.Combine(output,(female?"female":"male")+"_contact_shadow_original_bias.png"));
                    sun.shadowBias=.015f;sun.shadowNormalBias=.05f;for(int k=0;k<3;k++)yield return null;
                    Photo(game.GameplayCamera,d,Path.Combine(output,(female?"female":"male")+"_contact_shadow_reduced_bias.png"));
                    sun.shadowBias=bias;sun.shadowNormalBias=normal;
                }
                d.enabled=true;game.enabled=true;
            }
            File.WriteAllText(Path.Combine(output,"soles.json"),JsonUtility.ToJson(new Result{venue=TennisVenue.Current.ToString(),rows=rows.ToArray()},true)+"\n");Debug.Log("[TennisSoleProbe] evaluated rows="+rows.Count+" output="+output);
        }
        static void Measure(HeroTennisDriver d,string phase,int frame)
        {
            foreach(var shoe in d.matchLook.kit.Where(r=>r&&r.name.StartsWith("Kit_Shoe")))
            {
                var baked=new Mesh();shoe.BakeMesh(baked,false);var points=baked.vertices.Select(shoe.transform.TransformPoint).ToArray();var materials=shoe.sharedMaterials;var ids=new HashSet<int>();
                for(int sub=0;sub<baked.subMeshCount&&sub<materials.Length;sub++)if(materials[sub]&&materials[sub].name.StartsWith(MatchHeroLook.RoleSole))foreach(int id in baked.GetIndices(sub))ids.Add(id);
                if(ids.Count==0)throw new InvalidOperationException("No explicit Kit_Sole vertices on "+shoe.name);
                var sole=ids.Select(i=>points[i]).OrderBy(v=>v.y).ToArray();bool left=shoe.name.EndsWith("_L");var floor=Floor(sole[0],out string floorName);var ray=Physics.RaycastAll(sole[0]+Vector3.up*.75f,Vector3.down,1.6f,~0,QueryTriggerInteraction.Ignore).Where(h=>!h.collider.transform.IsChildOf(d.actor.transform)&&!h.collider.GetComponentInParent<TennisActor>()&&h.normal.y>.8f).OrderByDescending(h=>h.point.y).ToArray();
                var row=new Row{sex=d.matchLook.female?"female":"male",phase=phase,frame=frame,time=Time.time,state=d.State,clip=d.PlayingClip,shoe=shoe.name,vertices=points.Length,soleVertices=sole.Length,speed=d.actor.Speed,groundLift=d.LastGroundLift,sinkBefore=d.SinkBeforeGround,heelRest=Field(d,"heelRest"),toeRest=Field(d,"toeRest"),actorY=d.actor.transform.position.y,heroY=d.transform.position.y,hipsY=d.matchLook.Bone(HumanBodyBones.Hips).position.y,footY=d.matchLook.Bone(left?HumanBodyBones.LeftFoot:HumanBodyBones.RightFoot).position.y,toeY=d.matchLook.Bone(left?HumanBodyBones.LeftToes:HumanBodyBones.RightToes).position.y,minShoeY=points.Min(v=>v.y),minSoleY=sole[0].y,soleP02Y=sole[Mathf.Min(sole.Length-1,Mathf.FloorToInt(sole.Length*.02f))].y,minSolePoint=sole[0],visualFloorHit=floor.HasValue,visualFloorY=floor??0,floorRenderer=floorName,visualGap=floor.HasValue?sole[0].y-floor.Value:0,actorPosition=d.actor.transform.position,heroLocalPosition=d.transform.localPosition,rendererLocalPosition=shoe.transform.localPosition,colliderHit=ray.Length>0};
                // Independent linear-blend oracle uses the original vertices/binds
                // and actual current bone matrices, without BakeMesh transforms.
                var source=shoe.sharedMesh;var sourceVertices=source.vertices;var binds=source.bindposes;var weights=source.boneWeights;var bones=shoe.bones;
                foreach(int id in ids)
                {
                    var bw=weights[id];Vector3 oracle=Vector3.zero;
                    void Add(int bone,float w){if(w>0)oracle+=(bones[bone].localToWorldMatrix*binds[bone]).MultiplyPoint3x4(sourceVertices[id])*w;}
                    Add(bw.boneIndex0,bw.weight0);Add(bw.boneIndex1,bw.weight1);Add(bw.boneIndex2,bw.weight2);Add(bw.boneIndex3,bw.weight3);
                    row.maxSkinOracleError=Mathf.Max(row.maxSkinOracleError,Vector3.Distance(oracle,points[id]));
                }
                if(ray.Length>0){row.rayFloorY=ray[0].point.y;row.collider=ray[0].collider.name;row.rayGap=sole[0].y-ray[0].point.y;}rows.Add(row);Object.DestroyImmediate(baked);
            }
        }
        static float? Floor(Vector3 point,out string name)
        {
            float best=float.NegativeInfinity;name="";
            foreach(var r in floors)
            {
                var mf=r.GetComponent<MeshFilter>();if(!mf||!mf.sharedMesh)continue;var mesh=mf.sharedMesh;var v=mesh.vertices;var indices=mesh.triangles;
                for(int i=0;i<indices.Length;i+=3)
                {
                    var a=r.transform.TransformPoint(v[indices[i]]);var b=r.transform.TransformPoint(v[indices[i+1]]);var c=r.transform.TransformPoint(v[indices[i+2]]);
                    float det=(b.z-c.z)*(a.x-c.x)+(c.x-b.x)*(a.z-c.z);if(Mathf.Abs(det)<1e-8f)continue;
                    float wa=((b.z-c.z)*(point.x-c.x)+(c.x-b.x)*(point.z-c.z))/det,wb=((c.z-a.z)*(point.x-c.x)+(a.x-c.x)*(point.z-c.z))/det,wc=1-wa-wb;if(wa<-.0001f||wb<-.0001f||wc<-.0001f)continue;
                    float y=wa*a.y+wb*b.y+wc*c.y;if(y>point.y+.2f||y<point.y-.8f||y<=best)continue;best=y;name=r.name;
                }
            }
            return float.IsNegativeInfinity(best)?(float?)null:best;
        }
        static void Photo(Camera camera,HeroTennisDriver d,string path)
        {
            var before=camera.transform.position;var rot=camera.transform.rotation;float fov=camera.fieldOfView;var from=d.actor.transform.TransformPoint(1.8f,.52f,1.9f);var to=d.actor.transform.TransformPoint(0,.18f,0);camera.transform.SetPositionAndRotation(from,Quaternion.LookRotation(to-from));camera.fieldOfView=38;
            var rt=RenderTexture.GetTemporary(960,640,24,RenderTextureFormat.ARGB32,RenderTextureReadWrite.Default,4);var old=camera.targetTexture;var active=RenderTexture.active;camera.targetTexture=rt;camera.Render();camera.targetTexture=old;RenderTexture.active=rt;var tex=new Texture2D(960,640,TextureFormat.RGB24,false);tex.ReadPixels(new Rect(0,0,960,640),0,0);tex.Apply();File.WriteAllBytes(path,tex.EncodeToPNG());Object.DestroyImmediate(tex);RenderTexture.active=active;RenderTexture.ReleaseTemporary(rt);camera.transform.SetPositionAndRotation(before,rot);camera.fieldOfView=fov;
        }
    }
}
#endif
