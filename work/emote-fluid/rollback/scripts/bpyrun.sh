#!/bin/zsh
# bpyrun.sh <script.py> [args...] : run a numpy/mathutils script in Blender's python (background, factory settings); the args follow `--`
S=$1; shift
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python $S -- "$@" 2>&1 | grep -v -E "^(Blender|Read|Warning: |Color management|Info: )" | grep -v "^$"
