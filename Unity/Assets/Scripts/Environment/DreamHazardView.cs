using System.Collections.Generic;
using GolfArcade.Course;
using GolfArcade.Game;
using UnityEngine;
namespace GolfArcade.EnvironmentArt
{
    /// VFX consumes the same cycle as collision. Nothing spawns or retargets in flight.
    public sealed class DreamHazardView : MonoBehaviour
    {
        Hole hole;readonly List<Transform> plumes=new();readonly List<Renderer> warnings=new();readonly List<TextMesh> labels=new();
        readonly List<Material> materials=new();readonly List<Mesh> meshes=new();VentStage[] stages;EventSounds sound;float nextLabel;
        public static void Build(Transform parent,Hole hole)
        {
            if(hole.Dream==null)return;var root=new GameObject("Authored hazard windows");root.transform.SetParent(parent,false);
            var v=root.AddComponent<DreamHazardView>();v.hole=hole;v.sound=EventSounds.Create(root.transform);v.stages=new VentStage[hole.Dream.Hazards.Length];
            foreach(var h in hole.Dream.Hazards){
                var p=new Vector3((float)h.Centre.X,(float)h.Height,(float)h.Centre.D);
                var warning=HoleView.Primitive(PrimitiveType.Cylinder,h.Id+" warning",new Color(.22f,.17f,.13f),root.transform);
                warning.transform.position=p+Vector3.up*.08f;warning.transform.localScale=new Vector3((float)h.Radius*2,.08f,(float)h.Radius*2);
                if(h.Kind==DreamHazardKind.IceRunway){
                    var vertices=new List<Vector3>();var indices=new List<int>();
                    for(int z=-40;z<40;z++)for(int x=0;x<5;x++){
                        var at=new CoursePoint(h.Centre.X+x-2,h.Centre.D+z+.5);
                        if(hole.LieAt(at)!=CourseLie.Ice)continue;
                        int start=vertices.Count;
                        foreach(var delta in new[]{new Vector2(-.5f,-.5f),new Vector2(-.5f,.5f),new Vector2(.5f,.5f),new Vector2(.5f,-.5f)}){
                            var point=new CoursePoint(at.X+delta.x,at.D+delta.y);vertices.Add(new Vector3((float)point.X,(float)(hole.Ground?.Invoke(point)??0)+.025f,(float)point.D));
                        }
                        indices.AddRange(new[]{start,start+1,start+2,start,start+2,start+3});
                    }
                    var mesh=new Mesh{name="Fjord legal ice runway"};mesh.SetVertices(vertices);mesh.SetTriangles(indices,0);mesh.RecalculateNormals();v.meshes.Add(mesh);
                    warning.transform.position=Vector3.zero;warning.transform.localScale=Vector3.one;warning.GetComponent<MeshFilter>().sharedMesh=mesh;
                    warning.GetComponent<Renderer>().material.SetFloat("_Smoothness",.85f);
                }
                v.warnings.Add(warning.GetComponent<Renderer>());v.materials.Add(warning.GetComponent<Renderer>().material);
                var plume=HoleView.Primitive(PrimitiveType.Cylinder,"Bounded active plume",new Color(1,.28f,.04f),root.transform);
                var plumeRenderer=plume.GetComponent<Renderer>();var plumeShader=Resources.Load<Shader>("Environment/DreamLavaPlume");
                if(plumeShader)plumeRenderer.material.shader=plumeShader;
                plume.transform.position=p+Vector3.up*(float)h.ActiveHeight*.5f;plume.transform.localScale=new Vector3((float)h.Radius*2,(float)h.ActiveHeight*.5f,(float)h.Radius*2);plume.SetActive(false);v.plumes.Add(plume.transform);v.materials.Add(plume.GetComponent<Renderer>().material);
                var go=new GameObject("Window sign");go.transform.SetParent(root.transform,false);go.transform.position=p+new Vector3(0,5,0);
                var text=go.AddComponent<TextMesh>();text.characterSize=.75f;text.fontSize=40;text.anchor=TextAnchor.MiddleCenter;text.color=new Color(1,.87f,.55f);v.labels.Add(text);
            }
        }
        void LateUpdate()
        {
            if(hole?.Dream==null)return;double now=hole.Movers?.Now??0;
            bool updateLabel=Time.unscaledTime>=nextLabel;if(updateLabel)nextLabel=Time.unscaledTime+.1f;
            for(int i=0;i<hole.Dream.Hazards.Length;i++){
                var h=hole.Dream.Hazards[i];var state=h.Stage(now);bool vent=h.Kind==DreamHazardKind.LavaVent;
                bool visible=DreamVisibility.Visible(warnings[i].transform.position);
                plumes[i].gameObject.SetActive(vent&&state==VentStage.Active);warnings[i].enabled=visible;
                materials[i*2].color=vent?state==VentStage.Warning?new Color(1,.65f,.06f):state==VentStage.Active?new Color(1,.2f,.02f):new Color(.16f,.22f,.24f):new Color(.3f,.65f,.7f);
                labels[i].gameObject.SetActive(visible);if(updateLabel||stages[i]!=state)labels[i].text=vent?(state==VentStage.Warning?"ERUPTING IN ":state==VentStage.Active?"ACTIVE ":"COOLING ")+h.UntilChange(now).ToString("0.0")+"s":hole.Dream.RouteName;
                if(Camera.main)labels[i].transform.rotation=Camera.main.transform.rotation;
                if(vent&&state==VentStage.Warning&&stages[i]!=state)sound.Rumble();stages[i]=state;
            }
        }
        void OnDestroy(){foreach(var m in materials)if(m)Destroy(m);foreach(var m in meshes)if(m)Destroy(m);}
    }
}
