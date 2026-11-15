#!/bin/bash
# Rebuilds the trailer from what is already filmed: the cut (edit.json), captions (captions.json), sound (score.py), then joins them.
# Change a caption in captions.json or a cut in edit.json and run this; nothing is re-filmed.   build.sh [--half]
cd "$(dirname "$0")" || exit 1
python3 edit.py --timeline || exit 1
python3 score.py || exit 1
python3 render.py "$@" || exit 1
