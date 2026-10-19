#if UNITY_EDITOR
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Reflection;
using UnityEditor;
using UnityEngine;
using GolfArcade.Game;
using GolfArcade.Tennis;
using GolfArcade.Shot;
using Object = UnityEngine.Object;

namespace GolfArcade.EditorTools
{
    /// Bounded diagnostic coverage, never animation-specific garment repairs.
    /// Run in the existing Editor with GARMENT_STRESS_OUT set to an explicit
    /// task proof directory. GARMENT_STRESS_MODE=golf|tennis|both (default both).
    /// GARMENT_STRESS_IMAGES is clamped to 0..30 (default24). No asset writes.
    public static class FemaleGarmentStressReview
    {
        const BindingFlags Instance = BindingFlags.Instance|BindingFlags.NonPublic|BindingFlags.Public;
        const BindingFlags Static = BindingFlags.Static|BindingFlags.NonPublic|BindingFlags.Public;
        static readonly CultureInfo Inv = CultureInfo.InvariantCulture;
        static readonly string[] JointNames = { "Hips", "Chest", "UpperChest", "LeftShoulder", "LeftUpperArm", "LeftLowerArm", "LeftHand", "RightShoulder", "RightUpperArm", "RightLowerArm", "RightHand" };
        [Serializable] sealed class Row
        {
            public string sport, category, name, path, actualRenderer, image, error;
            public float normalizedTime, elevation, yaw, axialTwist, torsoTwist;
            public int finiteFailures, collapsedTriangles, inversionIndicators, severeStrainEdges, weldGroups;
            public float maximumWeldGapMetres, maximumEdgeRatio, minimumEdgeRatio, p95AbsoluteEdgeStrain, minimumAreaRatio;
            public float[] joints;
        }
        [Serializable] sealed class Report
        {
            public string conclusion = "DIAGNOSTIC_REVIEW_REQUIRED";
            public string limitations = "Finite/weld/strain/orientation diagnostics do not establish cloth-body clearance, realistic drape or an all-motion visual PASS. Synthetic sweeps bypass gameplay IK. Bone-blended transitions exercise interpolation, not the complete gameplay transition state machine. Actual game proof and native parity remain separate.";
            public string inversionDefinition = "Triangle cross product opposed to rest normal transported by current bone matrices; indicator can include strong legitimate local bending. Collapse threshold: current area below5% rest; severe edge ratio outside0.5..1.5.";
            public string startedUtc, finishedUtc, sleeveSweepFlag, clothPrototypeFlag, topDqFlag;
            public string[] jointNames = JointNames;
            public int samples, images, exceptions, finiteFailureSamples, weldFailureSamples, collapseSamples, orientationIndicatorSamples;
            public bool visualReviewRequired = true, devicePerformanceTested = false, nativeParityTested = false;
            public List<Row> rows = new List<Row>();
        }
        sealed class Pose
        {
            public Transform[] transforms; public Vector3[] p, s; public Quaternion[] q;
            public static Pose Save(Transform root)
            {
                var ts = root.GetComponentsInChildren<Transform>(true).Where(t => !t.name.StartsWith("ArmBlend_", StringComparison.Ordinal)).ToArray();
                return new Pose { transforms=ts, p=ts.Select(t=>t.localPosition).ToArray(), q=ts.Select(t=>t.localRotation).ToArray(), s=ts.Select(t=>t.localScale).ToArray() };
            }
            public void Restore() { for(int i=0;i<transforms.Length;i++) if(transforms[i]) { transforms[i].localPosition=p[i]; transforms[i].localRotation=q[i]; transforms[i].localScale=s[i]; } }
            public void Blend(Pose other, float t)
            {
                var lookup = new Dictionary<Transform,int>(); for(int i=0;i<other.transforms.Length;i++) lookup[other.transforms[i]]=i;
                for(int i=0;i<transforms.Length;i++) if(transforms[i] && lookup.TryGetValue(transforms[i], out int j))
                { transforms[i].localPosition=Vector3.Lerp(p[i],other.p[j],t); transforms[i].localRotation=Quaternion.Slerp(q[i],other.q[j],t); transforms[i].localScale=Vector3.Lerp(s[i],other.s[j],t); }
            }
        }
        sealed class Geometry
        {
            public SkinnedMeshRenderer top; public Vector3[] rest; public int[] triangles, edgeA, edgeB;
            public float[] edgeLengths, doubleAreas; public Vector3[] restNormals;
            public BoneWeight[] weights; public Matrix4x4[] binds; public int[][] welds;
            public Geometry(SkinnedMeshRenderer renderer)
            {
                top=renderer;var mesh=top.sharedMesh;rest=mesh.vertices;triangles=mesh.triangles;weights=mesh.boneWeights;binds=mesh.bindposes;
                var edges=new HashSet<long>(); var aa=new List<int>();var bb=new List<int>();
                for(int t=0;t<triangles.Length;t+=3)for(int k=0;k<3;k++) { int a=triangles[t+k],b=triangles[t+(k+1)%3];if(a>b)(a,b)=(b,a);if(edges.Add(((long)a<<32)|(uint)b)){aa.Add(a);bb.Add(b);} }
                edgeA=aa.ToArray();edgeB=bb.ToArray();edgeLengths=new float[edgeA.Length];
                for(int i=0;i<edgeLengths.Length;i++)edgeLengths[i]=Vector3.Distance(rest[edgeA[i]],rest[edgeB[i]]);
                doubleAreas=new float[triangles.Length/3];restNormals=new Vector3[doubleAreas.Length];
                for(int t=0;t<doubleAreas.Length;t++){int k=t*3;var n=Vector3.Cross(rest[triangles[k+1]]-rest[triangles[k]],rest[triangles[k+2]]-rest[triangles[k]]);doubleAreas[t]=n.magnitude;restNormals[t]=n.normalized;}
                welds=Enumerable.Range(0,rest.Length).GroupBy(i=>(Mathf.RoundToInt(rest[i].x*100000),Mathf.RoundToInt(rest[i].y*100000),Mathf.RoundToInt(rest[i].z*100000))).Where(g=>g.Count()>1).Select(g=>g.ToArray()).ToArray();
            }
            public Renderer Actual(out Mesh mesh)
            {
                // A generated sleeve surface is the rendered garment. Measuring
                // the hidden original skinned top would give false evidence.
                foreach(var r in top.GetComponentsInChildren<MeshRenderer>(true))
                    if(r.enabled && !r.forceRenderingOff && r.gameObject.activeInHierarchy && r.TryGetComponent<MeshFilter>(out var f) && f.sharedMesh && f.sharedMesh.vertexCount==rest.Length)
                    {mesh=f.sharedMesh;return r;}
                if(top.enabled && !top.forceRenderingOff && top.gameObject.activeInHierarchy){mesh=top.sharedMesh;return top;}
                throw new InvalidOperationException("No visible top surface with matching source topology");
            }
            public void Measure(Row row)
            {
                var actual=Actual(out var mesh);row.actualRenderer=actual.name;
                Vector3[] points;
                if(actual is SkinnedMeshRenderer skin)points=ManualWorld(skin, false);
                else {points=mesh.vertices;var matrix=actual.transform.localToWorldMatrix;for(int i=0;i<points.Length;i++)points[i]=matrix.MultiplyPoint3x4(points[i]);}
                for(int i=0;i<points.Length;i++)if(!Finite(points[i]))row.finiteFailures++;
                row.weldGroups=welds.Length;
                foreach(var group in welds)for(int i=1;i<group.Length;i++)row.maximumWeldGapMetres=Mathf.Max(row.maximumWeldGapMetres,Vector3.Distance(points[group[0]],points[group[i]]));
                var boneMatrices=top.bones.Select((b,i)=>b.localToWorldMatrix*binds[i]).ToArray();
                float scale=Mathf.Abs(top.transform.lossyScale.x),areaScale=scale*scale;
                var strains=new float[edgeLengths.Length];row.minimumEdgeRatio=float.MaxValue;row.minimumAreaRatio=float.MaxValue;
                for(int e=0;e<edgeLengths.Length;e++)
                {float ratio=Vector3.Distance(points[edgeA[e]],points[edgeB[e]])/Mathf.Max(edgeLengths[e]*scale,1e-9f);strains[e]=Mathf.Abs(ratio-1);row.maximumEdgeRatio=Mathf.Max(row.maximumEdgeRatio,ratio);row.minimumEdgeRatio=Mathf.Min(row.minimumEdgeRatio,ratio);if(ratio<.5f||ratio>1.5f)row.severeStrainEdges++;}
                Array.Sort(strains);row.p95AbsoluteEdgeStrain=strains[Mathf.Clamp((int)(strains.Length*.95f),0,strains.Length-1)];
                for(int t=0;t<doubleAreas.Length;t++)
                {
                    int k=t*3;var cross=Vector3.Cross(points[triangles[k+1]]-points[triangles[k]],points[triangles[k+2]]-points[triangles[k]]);
                    float areaRatio=cross.magnitude/Mathf.Max(doubleAreas[t]*areaScale,1e-12f);row.minimumAreaRatio=Mathf.Min(row.minimumAreaRatio,areaRatio);if(areaRatio<.05f)row.collapsedTriangles++;
                    Vector3 expected=Vector3.zero;
                    for(int v=0;v<3;v++){var w=weights[triangles[k+v]];var n=restNormals[t];expected+=boneMatrices[w.boneIndex0].MultiplyVector(n)*w.weight0+boneMatrices[w.boneIndex1].MultiplyVector(n)*w.weight1+boneMatrices[w.boneIndex2].MultiplyVector(n)*w.weight2+boneMatrices[w.boneIndex3].MultiplyVector(n)*w.weight3;}
                    if(Vector3.Dot(cross,expected)<0)row.inversionIndicators++;
                }
            }
        }
        sealed class Context
        {
            public string sport;public GameObject root;public MatchHeroLook look;public GolferView golfer;public HeroTennisDriver driver;public Camera camera;public Geometry geometry;public List<AnimationClip> clips;
            public Action<AnimationClip,float> sample;
        }
        static Report report;static string output;static int maxImages,clipImages,sweepImages,transitionImages,clipQuota,sweepQuota,transitionQuota;
        static object Call(object o,string method,params object[] args)=>o.GetType().GetMethod(method,Instance).Invoke(o,args);
        static object Turn(string method,params object[] args)=>typeof(HeroTurnaround).GetMethod(method,Static).Invoke(null,args);
        static void Set(object o,string field,object value)=>o.GetType().GetField(field,Instance).SetValue(o,value);
        static bool Finite(Vector3 p)=>!(float.IsNaN(p.x)||float.IsNaN(p.y)||float.IsNaN(p.z)||float.IsInfinity(p.x)||float.IsInfinity(p.y)||float.IsInfinity(p.z));
        static string Safe(string s)=>string.Concat(s.Select(c=>char.IsLetterOrDigit(c)||c=='-'||c=='_'?c:'_'));
        static string F(float f)=>f.ToString("R",Inv);

        public static void Run()
        {
            output=Environment.GetEnvironmentVariable("GARMENT_STRESS_OUT");
            if(string.IsNullOrWhiteSpace(output))throw new InvalidOperationException("Set GARMENT_STRESS_OUT to an explicit proof directory");
            Directory.CreateDirectory(output);maxImages=24;if(int.TryParse(Environment.GetEnvironmentVariable("GARMENT_STRESS_IMAGES"),out var n))maxImages=Mathf.Clamp(n,0,30);
            clipImages=sweepImages=transitionImages=0;
            EditorUtility.audioMasterMute=true;AudioListener.volume=0;
            report=new Report{startedUtc=DateTime.UtcNow.ToString("O"),sleeveSweepFlag=Environment.GetEnvironmentVariable("GARMENT_SLEEVE_SWEEP"),clothPrototypeFlag=Environment.GetEnvironmentVariable("GARMENT_CLOTH_PROTOTYPE"),topDqFlag=Environment.GetEnvironmentVariable("GARMENT_TOP_DQ")};
            string mode=Environment.GetEnvironmentVariable("GARMENT_STRESS_MODE")??"both";
            int budget=mode=="both"?maxImages/2:maxImages;
            clipQuota=Mathf.Min(8,budget/3);transitionQuota=Mathf.Min(4,budget/6);sweepQuota=Mathf.Max(0,budget-clipQuota-transitionQuota);
            try {if(mode=="both"||mode=="golf")RunSport(true);if(mode=="both"||mode=="tennis")RunSport(false);}
            finally {report.finishedUtc=DateTime.UtcNow.ToString("O");WriteReport();}
            Debug.Log($"[FemaleGarmentStressReview] {report.samples} samples, {report.images} images. DIAGNOSTIC_REVIEW_REQUIRED: {output}");
        }

        static Context Build(bool golf)
        {
            Turn("PurgeDeadCaches");Turn("Studio",golf);
            var c=new Context{sport=golf?"golf":"tennis"};
            if(golf)
            {
                c.golfer=GolferView.CreatePlayer(null,new GolferView.Look{Hero=new HeroLook{Female=true,Haircut=0,Skin=new Color(.953f,.855f,.788f),HairColor=Color.black}});
                c.root=c.golfer.gameObject;c.look=c.root.GetComponentInChildren<MatchHeroLook>();Call(c.look,"OwnMaterials");
                Set(c.golfer,"poseSafety",new HeroPoseSafety(c.look));
                c.clips=Resources.LoadAll<AnimationClip>(HeroGolfer.PathFor(true)).Where(x=>!x.name.StartsWith("__preview__")).OrderBy(x=>x.name).ToList();
                AnimationClip prepared=null;
                c.sample=(clip,t)=>
                {
                    if(prepared!=clip)
                    {
                        bool swing=new[]{"Drive","IronSwing","HalfSwing","Chip","Putt"}.Contains(clip.name);
                        if(swing)c.golfer.SetClub(clip.name=="Drive"?GolfClub.Driver:clip.name=="IronSwing"?GolfClub.Iron:clip.name=="Putt"?GolfClub.Putter:GolfClub.Wedge,clip.name=="Chip");
                        Set(c.golfer,"clipName",clip.name);Set(c.golfer,"EndTime",clip.length);Call(c.golfer,"Play",clip,0f);Set(c.golfer,"phase",swing?0:4);Call(c.golfer,"TickFade",1f);prepared=clip;
                    }
                    Call(c.golfer,"Show",Mathf.Clamp(t,0,clip.length));Correct(c.look);
                };
            }
            else
            {
                object[] args={"MatchHero_Female",null,null};c.root=(GameObject)Turn("BuildHero",args);c.look=c.root.GetComponentInChildren<MatchHeroLook>();c.driver=c.root.GetComponent<HeroTennisDriver>();
                if(!c.driver.matchLook)c.driver.matchLook=c.look;c.driver.Build();
                var slots=c.driver.slots.Where(s=>s.clip).ToArray();c.clips=slots.Select(s=>s.clip).Distinct().OrderBy(x=>x.name).ToList();
                c.sample=(clip,t)=>{var slot=slots.First(s=>s.clip==clip);c.driver.Sample(slot.id,t);Correct(c.look);};
            }
            c.look.SetKit(golf?"E87B65":"C5D64B",golf?"23304B":"EEEAE3","FFFFFF");
            c.camera=Object.FindObjectsByType<Camera>(FindObjectsSortMode.None).First(x=>x.name=="TurnaroundCamera");c.camera.aspect=1;c.camera.fieldOfView=30;c.camera.nearClipPlane=.01f;
            var top=c.look.kit.First(x=>x&&x.name=="Kit_Top");c.geometry=new Geometry(top);return c;
        }

        static void Correct(MatchHeroLook look)
        {
            foreach(var skin in look.GetComponentsInChildren<HeroArmSkinning>(true))skin.Apply();
            look.GetComponent<HeroShoulderDeformation>()?.Apply();look.GetComponent<FemaleShoulderFit>()?.Apply();look.GetComponent<FemaleGarmentFinish>()?.Apply();
            look.GetComponent<GolfGarmentCorrectives>()?.Apply();look.GetComponent<HeroGarmentPoseCorrectives>()?.Apply();look.GetComponent<TailoredPoloDeformation>()?.Apply();
            if(look.kitV2){KitV2PoseCorrectives.Attach(look);look.GetComponent<KitV2PoseCorrectives>()?.Apply();}
            foreach(var sleeve in look.GetComponentsInChildren<FemaleSleeveSweep>(true))sleeve.Apply();
        }

        /// Close diagnostic shots of one clip: GARMENT_SHOT_SPORT=golf|tennis, GARMENT_SHOT_CLIP=<name>, GARMENT_SHOT_TIMES=s1,s2 (seconds), GARMENT_STRESS_OUT.
        public static void ShotClip()
        {
            output=Environment.GetEnvironmentVariable("GARMENT_STRESS_OUT");Directory.CreateDirectory(output);maxImages=30;
            EditorUtility.audioMasterMute=true;AudioListener.volume=0;report=new Report();
            bool golf=Environment.GetEnvironmentVariable("GARMENT_SHOT_SPORT")=="golf";Context c=null;
            try
            {
                c=Build(golf);var clip=c.clips.First(x=>x.name==Environment.GetEnvironmentVariable("GARMENT_SHOT_CLIP"));
                File.WriteAllLines(Path.Combine(output,"renderers.txt"),c.root.GetComponentsInChildren<Renderer>(true).Select(r=>r.GetType().Name+" "+r.name+" enabled="+r.enabled+" active="+r.gameObject.activeInHierarchy));
                foreach(var t in Environment.GetEnvironmentVariable("GARMENT_SHOT_TIMES").Split(',').Select(x=>float.Parse(x,Inv)))
                {
                    c.sample(clip,t);var row=new Row{sport=c.sport,category="shot",name=clip.name+"_"+t.ToString("F2",Inv)};Record(c,row,true);
                }
            }
            finally {if(c!=null&&c.root)Object.DestroyImmediate(c.root);Turn("Release");}
        }
        static void RunSport(bool golf)
        {
            Context c=null;
            try
            {
                c=Build(golf);
                clipImages=sweepImages=transitionImages=0;var picturedClipGroups=new HashSet<string>();
                foreach(var clip in c.clips)for(int i=0;i<12;i++)
                {
                    float normalized=i/11f;var row=new Row{sport=c.sport,category="clip",name=clip.name,normalizedTime=normalized,path=golf?"GolferView.Show":"HeroTennisDriver.Sample"};
                    try {c.sample(clip,clip.length*normalized);string group=ClipImageGroup(clip.name);bool image=i==6&&clipImages<clipQuota&&group!=null&&!picturedClipGroups.Contains(group);Record(c,row,image);if(image){clipImages++;picturedClipGroups.Add(group);}}
                    catch(Exception error){RecordError(row,error);}
                }
                // Use a temporary full bind pose as the synthetic sweep origin.
                // It changes only this disposable instance, never rig assets.
                Turn("RestPose",c.look.gameObject);var neutral=Pose.Save(c.look.transform);
                foreach(int side in new[]{0,1})
                {
                    for(int elevation=0;elevation<=170;elevation+=10)Anatomy(c,neutral,side,elevation,0,0,0,"elevation",elevation==0||elevation==90||elevation==170);
                    for(int yaw=-75;yaw<=75;yaw+=15)Anatomy(c,neutral,side,80,yaw,0,0,"crossbody",Math.Abs(yaw)==75);
                    for(int twist=-80;twist<=80;twist+=10)Anatomy(c,neutral,side,100,0,twist,0,"axial",Math.Abs(twist)==80);
                }
                for(int twist=-40;twist<=40;twist+=5)Anatomy(c,neutral,0,75,30,0,twist,"torso",Math.Abs(twist)==40);
                for(int i=0;i<=48;i++)
                {float phase=i/48f*Mathf.PI*2;Anatomy(c,neutral,i%2,85+80*Mathf.Sin(phase),75*Mathf.Cos(phase),80*Mathf.Sin(phase*2),40*Mathf.Cos(phase*2),"combined",false);}
                var transitions=c.clips.Where(x=>Representative(x.name)).Take(6).ToArray();
                for(int pair=0;pair+1<transitions.Length;pair++)
                {
                    c.sample(transitions[pair],transitions[pair].length*.8f);var a=Pose.Save(c.look.transform);
                    c.sample(transitions[pair+1],transitions[pair+1].length*.2f);var b=Pose.Save(c.look.transform);
                    for(int i=0;i<12;i++)
                    {
                        var row=new Row{sport=c.sport,category="transition",name=transitions[pair].name+"_to_"+transitions[pair+1].name,normalizedTime=i/11f,path="synthetic local-bone blend + accepted safety"};
                        try{a.Blend(b,row.normalizedTime);var safety=new HeroPoseSafety(c.look);safety.Apply(false);Correct(c.look);bool image=i==6&&transitionImages<transitionQuota;Record(c,row,image);if(image)transitionImages++;}catch(Exception error){RecordError(row,error);}
                    }
                }
            }
            catch(Exception error){RecordError(new Row{sport=golf?"golf":"tennis",category="setup",name="setup"},error);}
            finally {if(c!=null&&c.root)Object.DestroyImmediate(c.root);Turn("Release");WriteReport();}
        }

        static bool Representative(string name)=>new[]{"Drive","IronSwing","Serve","Smash","Wave","Jump","Emote","RunForward","Walk","Cheer"}.Any(x=>name.IndexOf(x,StringComparison.OrdinalIgnoreCase)>=0);
        static string ClipImageGroup(string name)
        {
            bool Has(params string[] values)=>values.Any(x=>name.IndexOf(x,StringComparison.OrdinalIgnoreCase)>=0);
            if(Has("Run","Walk"))return "locomotion";
            if(Has("Overhead","Smash"))return "overhead";
            if(Has("Drive","IronSwing","Serve","Forehand"))return "stroke";
            if(Has("Wave","Emote","Jump","Cheer","FistPump"))return "emote";
            return null;
        }
        static void Anatomy(Context c,Pose neutral,int side,float elevation,float yaw,float twist,float torso,string category,bool image)
        {
            var row=new Row{sport=c.sport,category="anatomy_"+category,name=(side==0?"left":"right"),elevation=elevation,yaw=yaw,axialTwist=twist,torsoTwist=torso,path="synthetic direct joints, no gameplay IK"};
            try
            {
                neutral.Restore();var upper=c.look.Bone(side==0?HumanBodyBones.LeftUpperArm:HumanBodyBones.RightUpperArm);var lower=c.look.Bone(side==0?HumanBodyBones.LeftLowerArm:HumanBodyBones.RightLowerArm);
                var up=c.look.transform.up;var right=c.look.transform.right;float rad=elevation*Mathf.Deg2Rad;
                Vector3 direction=Quaternion.AngleAxis(yaw,up)*(right*(side==0?-1:1)*Mathf.Sin(rad)-up*Mathf.Cos(rad));
                upper.rotation=Quaternion.AngleAxis(twist,direction)*Quaternion.FromToRotation(lower.position-upper.position,direction)*upper.rotation;
                var chest=c.look.Bone(HumanBodyBones.Chest);chest.rotation=Quaternion.AngleAxis(torso,up)*chest.rotation;Correct(c.look);
                image=image&&sweepImages<sweepQuota;Record(c,row,image);if(image)sweepImages++;
            }
            catch(Exception error){RecordError(row,error);}
        }

        static void Record(Context c,Row row,bool image)
        {
            c.geometry.Measure(row);var joints=new List<float>();
            foreach(var name in JointNames)
            {
                var t=c.look.body.bones.FirstOrDefault(x=>x&&x.name==name);
                if(!t){joints.AddRange(new float[7]);continue;}
                var p=c.look.transform.InverseTransformPoint(t.position);var q=Quaternion.Inverse(c.look.transform.rotation)*t.rotation;
                joints.AddRange(new[]{p.x,p.y,p.z,q.x,q.y,q.z,q.w});
            }
            row.joints=joints.ToArray();
            if(image&&report.images<maxImages)
            {
                var center=c.look.transform.TransformPoint(new Vector3(0,1.22f,0));c.camera.transform.position=center+c.look.transform.TransformDirection(new Vector3(.75f,.10f,2.8f));c.camera.transform.LookAt(center,c.look.transform.up);
                string file=$"{report.images:D2}-{Safe(row.sport)}-{Safe(row.category)}-{Safe(row.name)}.jpg";Shot(c,c.camera,Path.Combine(output,file));row.image=file;report.images++;
            }
            report.rows.Add(row);report.samples++;
            if(row.finiteFailures>0)report.finiteFailureSamples++;if(row.maximumWeldGapMetres>.001f)report.weldFailureSamples++;if(row.collapsedTriangles>0)report.collapseSamples++;if(row.inversionIndicators>0)report.orientationIndicatorSamples++;
        }
        static void RecordError(Row row,Exception error){row.error=(error is TargetInvocationException&&error.InnerException!=null?error.InnerException:error).ToString();report.rows.Add(row);report.exceptions++;}

        static Vector3[] ManualWorld(SkinnedMeshRenderer skin,bool normal)
        {
            var mesh=skin.sharedMesh;var points=normal?mesh.normals:mesh.vertices;var dp=new Vector3[points.Length];var dn=new Vector3[points.Length];var dt=new Vector3[points.Length];
            for(int shape=0;shape<mesh.blendShapeCount;shape++)
            {
                float weight=skin.GetBlendShapeWeight(shape)/100;if(Mathf.Abs(weight)<1e-7f)continue;mesh.GetBlendShapeFrameVertices(shape,mesh.GetBlendShapeFrameCount(shape)-1,dp,dn,dt);var delta=normal?dn:dp;for(int i=0;i<points.Length;i++)points[i]+=delta[i]*weight;
            }
            var matrices=skin.bones.Select((b,i)=>b.localToWorldMatrix*mesh.bindposes[i]).ToArray();var weights=mesh.boneWeights;
            for(int i=0;i<points.Length;i++)
            {
                var w=weights[i];var p=points[i];
                points[i]=normal?(matrices[w.boneIndex0].MultiplyVector(p)*w.weight0+matrices[w.boneIndex1].MultiplyVector(p)*w.weight1+matrices[w.boneIndex2].MultiplyVector(p)*w.weight2+matrices[w.boneIndex3].MultiplyVector(p)*w.weight3).normalized
                    :matrices[w.boneIndex0].MultiplyPoint3x4(p)*w.weight0+matrices[w.boneIndex1].MultiplyPoint3x4(p)*w.weight1+matrices[w.boneIndex2].MultiplyPoint3x4(p)*w.weight2+matrices[w.boneIndex3].MultiplyPoint3x4(p)*w.weight3;
            }
            return points;
        }

        static void Shot(Context context,Camera camera,string path)
        {
            var temporary=new List<GameObject>();var hidden=new List<SkinnedMeshRenderer>();RenderTexture rt=null;Texture2D tex=null;var active=RenderTexture.active;var priorTarget=camera.targetTexture;
            try
            {
                var hideNames=new HashSet<string>((Environment.GetEnvironmentVariable("GARMENT_SHOT_HIDE")??"").Split(',').Where(x=>x.Length>0));
                foreach(var skin in context.root.GetComponentsInChildren<SkinnedMeshRenderer>(true).Where(r=>r.enabled&&!r.forceRenderingOff&&r.gameObject.activeInHierarchy))
                {
                    if(hideNames.Contains(skin.name)){hidden.Add(skin);skin.enabled=false;continue;}   // diagnostic identification shots
                    var mesh=Object.Instantiate(skin.sharedMesh);mesh.ClearBlendShapes();mesh.vertices=ManualWorld(skin,false);mesh.normals=ManualWorld(skin,true);mesh.RecalculateBounds();
                    var go=new GameObject("Stress CPU posed "+skin.name);temporary.Add(go);go.layer=skin.gameObject.layer;go.AddComponent<MeshFilter>().sharedMesh=mesh;
                    var renderer=go.AddComponent<MeshRenderer>();renderer.sharedMaterials=skin.sharedMaterials;renderer.renderingLayerMask=skin.renderingLayerMask;renderer.shadowCastingMode=skin.shadowCastingMode;renderer.receiveShadows=skin.receiveShadows;
                    var block=new MaterialPropertyBlock();skin.GetPropertyBlock(block);renderer.SetPropertyBlock(block);hidden.Add(skin);skin.enabled=false;
                }
                rt=RenderTexture.GetTemporary(720,720,24,RenderTextureFormat.ARGB32,RenderTextureReadWrite.sRGB,2);camera.targetTexture=rt;camera.Render();RenderTexture.active=rt;
                tex=new Texture2D(720,720,TextureFormat.RGB24,false);tex.ReadPixels(new Rect(0,0,720,720),0,0);tex.Apply();File.WriteAllBytes(path,tex.EncodeToJPG(90));
            }
            finally
            {
                foreach(var skin in hidden)if(skin)skin.enabled=true;foreach(var go in temporary){if(go){Object.DestroyImmediate(go.GetComponent<MeshFilter>().sharedMesh);Object.DestroyImmediate(go);}}
                camera.targetTexture=priorTarget;RenderTexture.active=active;if(rt)RenderTexture.ReleaseTemporary(rt);if(tex)Object.DestroyImmediate(tex);
            }
        }

        static void WriteReport()
        {
            File.WriteAllText(Path.Combine(output,"report.json"),JsonUtility.ToJson(report,true));
            using var writer=new StreamWriter(Path.Combine(output,"samples.csv"));
            writer.WriteLine("sport,category,name,path,normalizedTime,elevation,yaw,axialTwist,torsoTwist,renderer,finiteFailures,weldGroups,maxWeldGapMetres,collapsedTriangles,inversionIndicators,minAreaRatio,maxEdgeRatio,minEdgeRatio,p95AbsEdgeStrain,severeStrainEdges,image,error");
            foreach(var r in report.rows)
            {
                string Q(string s)=>"\""+(s??"").Replace("\"","\"\"").Replace("\r"," ").Replace("\n"," ")+"\"";
                writer.WriteLine(string.Join(",",Q(r.sport),Q(r.category),Q(r.name),Q(r.path),F(r.normalizedTime),F(r.elevation),F(r.yaw),F(r.axialTwist),F(r.torsoTwist),Q(r.actualRenderer),r.finiteFailures,r.weldGroups,F(r.maximumWeldGapMetres),r.collapsedTriangles,r.inversionIndicators,F(r.minimumAreaRatio),F(r.maximumEdgeRatio),F(r.minimumEdgeRatio),F(r.p95AbsoluteEdgeStrain),r.severeStrainEdges,Q(r.image),Q(r.error)));
            }
        }
    }
}
#endif
