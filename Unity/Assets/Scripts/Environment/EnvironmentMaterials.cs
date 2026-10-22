using System.Collections.Generic;
using UnityEngine;

namespace GolfArcade.EnvironmentArt
{
    /// Six authoring masters, with existing specialist shaders retained as variants.
    /// Builders still supply their textures, vertex-channel roles and local settings.
    /// The masters introduce no shader switches, keywords, passes or draw submissions.
    public static class EnvironmentMaterials
    {
        static readonly Dictionary<string,Material> masters=new();
        public static string Family(string shaderName)=>shaderName switch {
            "GolfArcade/TennisWorldSurface"=>"M_Ground",
            "GolfArcade/TennisBotanical"=>"M_Foliage",
            "GolfArcade/HubSurface"=>"M_Prop",
            "GolfArcade/GolfOcean"=>"M_Water",
            "GolfArcade/GolfLava"=>"M_Emissive",
            "GolfArcade/TennisCoastalSky"=>"M_Sky",
            _=>null
        };
        public static Material Create(Shader shader,string name=null,bool instancing=false)
        {
            Material source=null;
            string family=EnvironmentLook.Stage>=3 && shader ? Family(shader.name):null;
            if(family!=null && !masters.TryGetValue(family,out source)) {
                source=Resources.Load<Material>("Environment/Materials/"+family);masters[family]=source;
            }
            // A mismatched or missing master must not substitute a different shader.
            var result=source && source.shader==shader?new Material(source):new Material(shader);
            if(name!=null)result.name=name;
            result.enableInstancing=instancing;
            return result;
        }
    }
}
