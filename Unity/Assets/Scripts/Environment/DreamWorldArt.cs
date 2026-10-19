using System.Collections.Generic;
using GolfArcade.Course;
using UnityEngine;
using UnityEngine.Rendering;
namespace GolfArcade.EnvironmentArt
{
    /// Modular silhouettes and local light sources; existing authored foliage and legal ground remain.
    /// Every catalogue entry has its own arrangement. No landable floating surface is implied.
    public sealed class DreamWorldArt : MonoBehaviour
    {
        readonly List<Material> materials=new();readonly List<Mesh> meshes=new();readonly List<Light> accents=new();
        readonly List<Renderer> luminous=new();Material stone,edge,glow;int location;bool basalt,glacial,terraced;
        public static void Build(Transform parent,Hole hole)
        {
            if(!DreamEnvironment.Enabled || hole.Number<7 || parent.GetComponentInChildren<DreamWorldArt>())return;
            var root=new GameObject("Dream world · "+hole.Name);root.transform.SetParent(parent,false);
            var a=root.AddComponent<DreamWorldArt>();a.location=hole.Number;a.Palette(hole.Theme=="magma",hole.Number==17,hole.Number==18);
            a.Golf(hole);a.Combine();
            if(hole.Number==19||hole.Number==20)a.Pollen(hole);
        }
        public static void Tennis(Transform parent,int venue)
        {
            if(!DreamEnvironment.Enabled||parent.GetComponentInChildren<DreamWorldArt>())return;
            var root=new GameObject("Dream venue layers");root.transform.SetParent(parent,false);var a=root.AddComponent<DreamWorldArt>();a.location=100+venue;
            a.Palette(venue==2,false,false);
            for(int i=0;i<5;i++){
                float angle=(i*62+15+venue*23)*Mathf.Deg2Rad;var p=new Vector3(Mathf.Sin(angle)*(65+i*16),-12-venue*8,Mathf.Cos(angle)*(65+i*16));
                if(venue==0)a.Arch(p,14+i*1.5f,2.2f,Quaternion.Euler(0,i*37,0));
                else a.Spire(p,new Vector3(18+i*3,35+i*10,16+i*3),i+venue*90);
            }
            for(int side=-1;side<=1;side+=2)for(int end=-1;end<=1;end+=2){
                var p=new Vector3(side*12,0,end*19);a.Column(p,9,.22f,a.stone);
                a.Orb(p+Vector3.up*9,Vector3.one*.65f,a.glow);
                var l=new GameObject("Court practical").AddComponent<Light>();l.transform.SetParent(root.transform,false);l.transform.position=p+Vector3.up*8.5f;l.type=LightType.Point;l.range=28;l.shadows=LightShadows.None;l.color=new Color(1,.8f,.55f);l.intensity=0;a.accents.Add(l);
            }
            a.Combine();
        }
        void Palette(bool magma,bool ice,bool mesa)
        {
            basalt=magma;glacial=ice;terraced=mesa;
            Color rock=magma?new Color(.15f,.17f,.22f):ice?new Color(.33f,.59f,.7f):mesa?new Color(.62f,.33f,.18f):new Color(.72f,.76f,.69f);
            Color rim=magma?new Color(.28f,.23f,.29f):ice?new Color(.68f,.89f,.94f):mesa?new Color(.9f,.61f,.32f):new Color(.92f,.9f,.76f);
            stone=Mat("Sculpted stone",rock,.15f);edge=Mat("Weathered edges",rim,.27f);glow=Mat("Luminous mineral",magma?new Color(1,.24f,.04f):new Color(.1f,.7f,.75f),.35f);
            glow.EnableKeyword("_EMISSION");glow.SetColor("_EmissionColor",magma?new Color(1.5f,.2f,.01f):new Color(.1f,.65f,.7f));
        }
        Material Mat(string name,Color color,float smooth)
        {
            var m=new Material(name=="Luminous mineral"?Shader.Find("Universal Render Pipeline/Lit"):Resources.Load<Shader>("Course/Shaders/GolfRock")){name=name,enableInstancing=true};m.SetColor("_BaseColor",color);m.SetFloat("_Smoothness",smooth);
            if(name!="Luminous mineral"){m.SetTexture("_BaseMap",Resources.Load<Texture2D>("Course/Resort/CoastalCliffScan_C"));m.SetTexture("_BumpMap",Resources.Load<Texture2D>("Course/Resort/CoastalCliffScan_N"));m.EnableKeyword("_NORMALMAP");m.SetTextureScale("_BaseMap",Vector2.one*.3f);m.SetColor("_BaseColor",Color.white);m.SetFloat("_Rock",1);m.SetFloat("_PaletteMode",1);m.SetColor("_LowColor",color*.72f);m.SetColor("_HighColor",color*1.08f);m.SetFloat("_PaletteDetail",0);m.SetFloat("_DetailContrast",1.2f);m.SetFloat("_GeologicalMacro",.4f);m.SetFloat("_RockScale",.055f);m.SetFloat("_NormalEnabled",1);m.SetFloat("_TriplanarNormals",1);m.SetFloat("_BumpScale",.35f);m.SetFloat("_Wrap",.35f);}
            materials.Add(m);return m;
        }
        void Golf(Hole h)
        {
            bool magma=h.Theme=="magma";var tee=h.Tee;var pin=h.Pin;
            float length=(float)tee.DistanceTo(pin),heading=(float)tee.HeadingTo(pin);var rot=Quaternion.Euler(0,heading,0);
            var centre=new Vector3((float)(tee.X+pin.X)*.5f,0,(float)(tee.D+pin.D)*.5f);
            // The accepted hole12 garden remains its primary landmark. Other holes use smaller individual compositions.
            int count=h.Number==12?2:2+h.Number%3;
            for(int i=0;i<count;i++){
                float side=((i+h.Number)%2==0?1:-1),along=(i-.8f)*length*.30f;
                var p=centre+rot*new Vector3(side*(100+18*i+ h.Number%3*10),0,along);
                p.y=(float)(h.Ground?.Invoke(new CoursePoint(p.x,p.z))??0)-25;
                if(!magma&&h.Number!=17&&h.Number!=18 && (i+h.Number)%2==0)Arch(p,35+5*i,5+i,rot*Quaternion.Euler(0,i*23,0));
                else Spire(p,new Vector3(24+5*i,65+12*i,24+4*i),h.Number*17+i);
            }
            // Local accents are placed beyond the conservative corridor, never over legal landing surfaces.
            for(int i=0;i<6;i++){
                var c=DreamCourseLayout.Along(h,.15+i*.12);var n=DreamCourseLayout.Along(h,.16+i*.12);float angle=(float)c.HeadingTo(n)*Mathf.Deg2Rad;
                float offset=(float)(h.FairwayWidth*.5+h.RoughWidth+6);var p=new Vector3((float)c.X+Mathf.Cos(angle)*offset,0,(float)c.D-Mathf.Sin(angle)*offset);
                p.y=(float)(h.Ground?.Invoke(new CoursePoint(p.x,p.z))??0);
                if(magma){Spire(p,new Vector3(2.5f,5+i%3,3),h.Number+i);Orb(p+Vector3.up*.4f,new Vector3(3,.18f,1),glow);}
                else if(h.Number==17){Spire(p,new Vector3(2,6,2),h.Number+i);Orb(p+Vector3.up*3,new Vector3(.4f,4,.4f),glow);}
                else if(h.Number==19||h.Number==20){
                    Column(p,1.6f,.08f,stone);
                    for(int petal=0;petal<5;petal++){
                        float turn=petal*Mathf.PI*2/5;
                        Orb(p+new Vector3(Mathf.Cos(turn)*.48f,1.6f,Mathf.Sin(turn)*.48f),new Vector3(.65f,.18f,.38f),glow);
                    }
                    for(int leaf=0;leaf<3;leaf++){
                        var foliage=Primitive(PrimitiveType.Sphere,"Luminous grove leaf",edge);
                        foliage.transform.position=p+new Vector3((leaf%2==0?1:-1)*.4f,.35f+leaf*.3f,0);
                        foliage.transform.localScale=new Vector3(1.25f,.12f,.4f);foliage.transform.rotation=Quaternion.Euler(0,leaf*47,25);
                    }
                }
                else{Column(p,2.8f,.22f,stone);Orb(p+Vector3.up*2.9f,Vector3.one*.55f,glow);}
            }
        }
        void Pollen(Hole hole)
        {
            // Four small patches, each hard-capped at 24 motes. Independent decorative seed.
            var material=new Material(Shader.Find("GolfArcade/ParticleAdd")){name="Grove pollen",mainTexture=GolfArcade.Game.ShotEffects.Soft()};materials.Add(material);
            for(int i=0;i<4;i++){
                var point=DreamCourseLayout.Along(hole,.12+i*.22);
                var go=new GameObject("Drifting grove pollen");go.transform.SetParent(transform,false);
                go.transform.position=new Vector3((float)point.X,(float)(hole.Ground?.Invoke(point)??0)+2,(float)point.D);
                var ps=go.AddComponent<ParticleSystem>();ps.Stop(true,ParticleSystemStopBehavior.StopEmittingAndClear);ps.useAutoRandomSeed=false;ps.randomSeed=(uint)(hole.Number*137+i);
                var main=ps.main;main.maxParticles=24;main.startLifetime=8;main.startSpeed=.12f;main.startSize=new ParticleSystem.MinMaxCurve(.035f,.08f);main.startColor=new Color(1,.83f,.4f,.3f);main.simulationSpace=ParticleSystemSimulationSpace.World;
                var emission=ps.emission;emission.rateOverTime=3;var shape=ps.shape;shape.shapeType=ParticleSystemShapeType.Box;shape.scale=new Vector3(18,3,24);
                var velocity=ps.velocityOverLifetime;velocity.enabled=true;velocity.space=ParticleSystemSimulationSpace.World;velocity.x=.35f;velocity.y=.08f;velocity.z=.12f;
                var renderer=ps.GetComponent<ParticleSystemRenderer>();renderer.sharedMaterial=material;renderer.shadowCastingMode=ShadowCastingMode.Off;ps.Play();
            }
        }
        void Column(Vector3 p,float height,float radius,Material m)
        {
            var go=Primitive(PrimitiveType.Cylinder,"Local accent",m);go.transform.position=p+Vector3.up*height*.5f;go.transform.localScale=new Vector3(radius*2,height*.5f,radius*2);
        }
        void Orb(Vector3 p,Vector3 scale,Material m){var go=Primitive(PrimitiveType.Sphere,"Light pool source",m);go.transform.position=p;go.transform.localScale=scale;luminous.Add(go.GetComponent<Renderer>());}
        GameObject Primitive(PrimitiveType type,string name,Material m)
        {
            var go=GameObject.CreatePrimitive(type);go.name=name;go.transform.SetParent(transform,false);Destroy(go.GetComponent<Collider>());go.GetComponent<Renderer>().sharedMaterial=m;return go;
        }
        void Spire(Vector3 p,Vector3 scale,int seed)
        {
            const int sides=20,rings=14;var vertices=new List<Vector3>();var triangles=new List<int>();
            for(int j=0;j<rings;j++)for(int i=0;i<sides;i++){
                float a=i*Mathf.PI*2/sides;float y=j/(float)(rings-1);float profile=terraced?(1-y*.4f)*(1+.04f*Mathf.Sin(Mathf.Floor(y*6)*2.1f)):Mathf.Pow(1-y,glacial?.85f:basalt?.42f:.6f)+.025f;
                float r=profile*(1+.065f*Mathf.Sin(seed+i*.91f)+.035f*Mathf.Sin(y*19+seed));
                float bend=Mathf.Sin(seed*.3f)*y*y*.24f;
                vertices.Add(p+Vector3.Scale(new Vector3(Mathf.Cos(a)*r+bend,y,Mathf.Sin(a)*r),scale));
            }
            for(int j=0;j<rings-1;j++)for(int i=0;i<sides;i++){int a=j*sides+i,b=j*sides+(i+1)%sides,c=a+sides,d=b+sides;triangles.AddRange(new[]{a,c,b,b,c,d});}
            int cap=vertices.Count;vertices.Add(p+new Vector3(Mathf.Sin(seed*.3f)*.24f*scale.x,scale.y,0));
            for(int i=0;i<sides;i++)triangles.AddRange(new[]{cap,(rings-1)*sides+(i+1)%sides,(rings-1)*sides+i});
            Make("Layered landform",vertices,triangles,stone);
        }
        void Arch(Vector3 p,float radius,float thickness,Quaternion rot)
        {
            const int steps=36,sides=8;var v=new List<Vector3>();var tris=new List<int>();
            for(int j=0;j<=steps;j++){
                float a=j*Mathf.PI/steps;var c=new Vector3(Mathf.Cos(a)*radius,Mathf.Sin(a)*radius,0);
                for(int i=0;i<sides;i++){float b=i*Mathf.PI*2/sides;var local=c+new Vector3(Mathf.Cos(a)*Mathf.Cos(b),Mathf.Sin(a)*Mathf.Cos(b),Mathf.Sin(b))*thickness*(1+.08f*Mathf.Sin(j*2+i));v.Add(p+rot*local);}
            }
            for(int j=0;j<steps;j++)for(int i=0;i<sides;i++){int a=j*sides+i,b=j*sides+(i+1)%sides,c=a+sides,d=b+sides;tris.AddRange(new[]{a,c,b,b,c,d});}
            Make("Sculpted horizon arch",v,tris,edge);
        }
        void Make(string name,List<Vector3> vertices,List<int> tris,Material material)
        {
            var mesh=new Mesh{name=name};mesh.SetVertices(vertices);mesh.SetTriangles(tris,0);var uv=new List<Vector2>();foreach(var v in vertices)uv.Add(new Vector2(v.x+v.z*.3f,v.y+v.z*.2f));mesh.SetUVs(0,uv);mesh.RecalculateNormals();mesh.RecalculateBounds();meshes.Add(mesh);
            var go=new GameObject(name,typeof(MeshFilter),typeof(MeshRenderer));go.transform.SetParent(transform,false);go.GetComponent<MeshFilter>().sharedMesh=mesh;go.GetComponent<MeshRenderer>().sharedMaterial=material;
        }
        void Combine()
        {
            foreach(var material in materials){var parts=new List<CombineInstance>();var remove=new List<GameObject>();foreach(var mf in GetComponentsInChildren<MeshFilter>())if(mf.GetComponent<Renderer>().sharedMaterial==material){parts.Add(new CombineInstance{mesh=mf.sharedMesh,transform=transform.worldToLocalMatrix*mf.transform.localToWorldMatrix});remove.Add(mf.gameObject);}
                if(parts.Count==0)continue;var combined=new Mesh{name="Dream catalogue "+location+" "+material.name,indexFormat=IndexFormat.UInt32};combined.CombineMeshes(parts.ToArray());meshes.Add(combined);
                foreach(var go in remove){go.SetActive(false);Destroy(go);}var root=new GameObject(combined.name,typeof(MeshFilter),typeof(MeshRenderer));root.transform.SetParent(transform,false);root.GetComponent<MeshFilter>().sharedMesh=combined;var renderer=root.GetComponent<MeshRenderer>();renderer.sharedMaterial=material;renderer.shadowCastingMode=ShadowCastingMode.Off;
            }
        }
        void LateUpdate(){float night=1-(float)DreamConditions.Daylight(DreamEnvironment.Utc);foreach(var l in accents)l.intensity=night*90;}
        void OnDestroy(){foreach(var m in materials)if(m)Destroy(m);foreach(var m in meshes)if(m)Destroy(m);}
    }
}
