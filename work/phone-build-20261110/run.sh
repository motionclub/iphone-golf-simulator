#!/bin/bash
cd "$(dirname "$0")"
./export.sh && ./xcode.sh && ./install.sh
echo "ALL DONE $?"
