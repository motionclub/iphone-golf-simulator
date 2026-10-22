#!/bin/zsh
# Blender's bundled python (has numpy). System python3 has Pillow but no numpy.
exec /Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13 "$@"
