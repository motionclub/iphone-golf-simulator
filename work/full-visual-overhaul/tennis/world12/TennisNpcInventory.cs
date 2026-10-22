#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;
using GolfArcade.Tennis;
using Object=UnityEngine.Object;
namespace GolfArcade.EditorTools
{
    /// Evaluated live hierarchy and actual enabled render-pass inventory.
    public static class TennisNpcInventory
    {
        [Serializable] public sealed class RendererRecord
        {
            public string path,source;public bool enabled,active,visibleLastFrame,skinned;
            public string[] materials;public int drawableSlots,hiddenSlots;
        }
        [Serializable] public sealed class Report
        {
            public int seatedFans,promenadeVisitors,legacyWalkerObjects,legacyWalkerSkins,legacyStandDrawableSlots,hiddenPlaceholderSlots,explicitSeatedGroups;
            public string status,reason;public RendererRecord[] legacyRenderers;
        }
        static string PathOf(Transform t){string p=t.name;while(t.parent){t=t.parent;p=t.name+"/"+p;}return p;}
        public static Report Inspect()
        {
            var transforms=Object.FindObjectsByType<Transform>(FindObjectsSortMode.None);
            var renderers=Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None);
            var records=renderers.Where(r=>r.name.StartsWith("Crowd_",StringComparison.Ordinal)||r.sharedMaterials.Any(m=>m&&(m.name.StartsWith("TropicalV3_004")||m.name.StartsWith("TropicalV3_005")||m.name.StartsWith("TropicalV3_006")||m.name.StartsWith("TropicalV3_007")||m.name.StartsWith("TropicalV3_013")||m.name=="Hidden placeholder"))).Select(r=>{
                var original=PrefabUtility.GetCorrespondingObjectFromOriginalSource(r);
                int hidden=r.sharedMaterials.Count(m=>m&&m.name=="Hidden placeholder");
                bool oldObject=r.name.StartsWith("Crowd_",StringComparison.Ordinal);
                int drawable=r.enabled&&r.gameObject.activeInHierarchy?r.sharedMaterials.Count(m=>m&&m.name!="Hidden placeholder"&&(oldObject||m.name.StartsWith("TropicalV3_004")||m.name.StartsWith("TropicalV3_005")||m.name.StartsWith("TropicalV3_006")||m.name.StartsWith("TropicalV3_007")||m.name.StartsWith("TropicalV3_013"))):0;
                return new RendererRecord{path=PathOf(r.transform),source=original?AssetDatabase.GetAssetPath(original):"runtime",enabled=r.enabled,active=r.gameObject.activeInHierarchy,visibleLastFrame=r.isVisible,skinned=r is SkinnedMeshRenderer,materials=r.sharedMaterials.Select(m=>m?m.name:"null").ToArray(),drawableSlots=drawable,hiddenSlots=hidden};
            }).ToArray();
            var seated=Object.FindFirstObjectByType<TennisStandsCrowd>();
            var report=new Report{seatedFans=transforms.Count(t=>t.name.StartsWith("Seated sporting fan ",StringComparison.Ordinal)),promenadeVisitors=transforms.Count(t=>t.name.StartsWith("Premium promenade visitor ",StringComparison.Ordinal)),legacyWalkerObjects=transforms.Count(t=>t.name.StartsWith("Resort walker ",StringComparison.Ordinal)),legacyWalkerSkins=renderers.Count(r=>r is SkinnedMeshRenderer&&PathOf(r.transform).Contains("Resort walker ")&&r.enabled&&r.gameObject.activeInHierarchy),legacyStandDrawableSlots=records.Sum(r=>r.drawableSlots),hiddenPlaceholderSlots=records.Sum(r=>r.hiddenSlots),explicitSeatedGroups=seated&&seated.InstancedSubmission?seated.InstanceGroupCount:0,legacyRenderers=records};
            bool valid=report.legacyWalkerObjects==0&&report.legacyWalkerSkins==0&&report.legacyStandDrawableSlots==0&&(!TennisVenue.IsResort||report.seatedFans==36&&report.promenadeVisitors==6);
            report.status=valid?"PASS":"FAIL";report.reason="Active production scene: expected36 seated +6 promenade visitors at Resort; zero legacy walking objects/skins and zero drawable legacy stand submeshes. Hidden placeholder pass slots are reported explicitly, not counted as people.";return report;
        }
        public static Report Save(string directory,string label="npc-inventory")
        {var report=Inspect();File.WriteAllText(Path.Combine(directory,label+".json"),JsonUtility.ToJson(report,true)+"\n");return report;}
    }
}
#endif
