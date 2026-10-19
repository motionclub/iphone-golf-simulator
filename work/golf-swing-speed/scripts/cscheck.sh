#!/bin/zsh
# cscheck.sh <file.cs ...> : compile-check editor/runtime C# against the clone's last ScriptAssemblies + Unity's DLLs (no Unity launch).
# Runtime sources (Assets/Scripts) given here are compiled together INSTEAD of the clone's GolfArcade.dll.
U=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/Resources/Scripting
C=$HOME/golf-swing-speed-UnityClone
refs=()
for d in $U/Managed/UnityEngine/*.dll $U/NetStandard/ref/2.1.0/netstandard.dll $U/NetStandard/compat/2.1.0/shims/netfx/*.dll(N); do refs+=(-r:$d); done
for d in $C/Library/ScriptAssemblies/*.dll; do [[ ${d:t} == GolfArcade.Editor.dll || ${d:t} == GolfArcade.PlayTests.dll || ${d:t} == GolfArcade.Tests.dll ]] && continue; [[ -n ${NO_GA:-} && ${d:t} == GolfArcade.dll ]] && continue; refs+=(-r:$d); done
$U/NetCoreRuntime/dotnet $U/DotNetSdkRoslyn/csc.dll -nologo -noconfig -nostdlib -t:library -langversion:9 -define:UNITY_EDITOR -nowarn:CS0618,CS1701,CS0436 -out:/tmp/gss_check_$$.dll $refs "$@" 2>&1 | grep -v "warning" | head -30
rm -f /tmp/gss_check_$$.dll
