#if UNITY_EDITOR
using System.IO;
using GolfArcade.UI;
using UnityEditor;
using UnityEngine;

namespace GolfArcade.EditorTools
{
    /// Writes the two sport themes and the library under Resources/UI/Themes from UITheme's built-in values.
    /// Existing assets are left alone (edit them in the Inspector); delete one to have it rebuilt.
    public static class UiThemeAssets
    {
        const string Dir = "Assets/Resources/UI/Themes";

        [MenuItem("Tools/UI/Create Theme Assets")]
        public static void Create()
        {
            Directory.CreateDirectory(Dir);
            var golf = Ensure("Theme_Golf_EmeraldGold", UITheme.GolfEmeraldGold);
            var tennis = Ensure("Theme_Tennis_RoyalBlue", UITheme.TennisRoyalBlue);
            string libPath = $"{Dir}/UIThemeLibrary.asset";
            var lib = AssetDatabase.LoadAssetAtPath<UIThemeLibrary>(libPath);
            if (!lib) { lib = ScriptableObject.CreateInstance<UIThemeLibrary>(); AssetDatabase.CreateAsset(lib, libPath); }
            lib.defaultTheme = golf;
            lib.sportThemes = new[]
            {
                new UIThemeLibrary.SportTheme { sport = "golf", theme = golf },
                new UIThemeLibrary.SportTheme { sport = "tennis", theme = tennis },
            };
            EditorUtility.SetDirty(lib);
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
            Debug.Log("[UiThemeAssets] themes ready in " + Dir);
        }

        static UITheme Ensure(string name, System.Func<UITheme> make)
        {
            string path = $"{Dir}/{name}.asset";
            var existing = AssetDatabase.LoadAssetAtPath<UITheme>(path);
            if (existing) return existing;
            var t = make();
            AssetDatabase.CreateAsset(t, path);
            return t;
        }
    }
}
#endif
