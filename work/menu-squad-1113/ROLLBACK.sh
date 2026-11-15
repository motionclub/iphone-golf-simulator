#!/bin/bash
# Takes the MENU SQUAD 11-13 install back out: each file is restored to how it was before ONLY if it is still exactly as this install left it.
cd "$(dirname "$0")/../.."; W=work/menu-squad-1113
r() { if cmp -s "$W/src/new/$1" "$2"; then cp "$W/src/orig/$1" "$2"; echo "restored $2"; else echo "SKIPPED $2 (changed since the install)"; fi; }
for f in $(cd $W/src/new && find Hub -name '*.cs'); do r "$f" "Unity/Assets/Scripts/$f"; done
r MenuArrowFocusTests.cs Unity/Assets/Tests/PlayMode/MenuArrowFocusTests.cs
r MenuPointerTests.cs Unity/Assets/Tests/PlayMode/MenuPointerTests.cs
