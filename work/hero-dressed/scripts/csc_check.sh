#!/bin/zsh
# Compile-check the DRESS_MATCH_HEROES C# against the project's last compiled assemblies with Unity's own Roslyn (no editor needed, safe while another session has the project open).
# New / changed sources shadow the same types inside GolfArcade.dll (warning CS0436).
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
UN=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/Resources/Scripting
DOTNET=$UN/NetCoreRuntime/dotnet
OUT=${1:-/tmp/dress_check.dll}
refs=()
for f in $UN/Managed/UnityEngine/*.dll $R/Unity/Library/ScriptAssemblies/*.dll; do
  case $f in *GolfArcade.Editor.dll|*GolfArcade.Tests.dll|*GolfArcade.PlayTests.dll) continue;; esac
  refs+=(-r:$f)
done
refs+=(-r:$UN/NetStandard/ref/2.1.0/netstandard.dll)
for f in $UN/NetStandard/compat/2.1.0/shims/netstandard/*.dll; do refs+=(-r:$f); done
srcs=($R/Unity/Assets/Scripts/Tennis/MatchHeroLook.cs $R/Unity/Assets/Scripts/Tennis/HeroKit.cs $R/Unity/Assets/Editor/MatchHeroKit.cs $R/Unity/Assets/Editor/MatchHeroKitTests.cs $R/Unity/Assets/Editor/MatchHeroKitBaseline.cs $R/Unity/Assets/Editor/MatchHeroKitProbe.cs $R/Unity/Assets/Editor/MatchHeroKitProof.cs $R/Unity/Assets/Editor/MatchHeroBuild.cs $R/Unity/Assets/Editor/MatchHeroImport.cs $R/Unity/Assets/Editor/MatchHeroLockerExport.cs)
for extra in "$@"; do [[ $extra == --* ]] && continue; done
$DOTNET $UN/DotNetSdkRoslyn/csc.dll -nologo -nostdlib+ -target:library -out:$OUT -langversion:9 -nullable:disable -unsafe- -nowarn:CS0436,CS0618,CS0649,CS0169,CS0414,CS8632 "${refs[@]}" "${srcs[@]}" 2>&1 | grep -v "warning" | head -60
echo "csc exit: ${pipestatus[1]}"
