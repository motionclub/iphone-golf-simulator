#!/bin/zsh
# usage: blend.sh <file.blend> <script.py> [args after --]
f="$1"; s="$2"; shift 2
exec /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup "$f" --python "$s" -- "$@"
