#!/bin/bash
# round 2 finishing steps after run_final_pipeline.sh: extra previews + contact sheet + INSTALL.md + stage clean-up. usage: bash work/postcard-look/v2/hole09/round2_finish.sh
R="/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"; cd "$R"
O=work/postcard-look/v2/hole09; B=/Applications/Blender.app/Contents/MacOS/Blender
$B -b --factory-startup --python $O/tools/render_views.py -- --blend $R/$O/stage/hole_09.blend --json $R/$O/round2/views.json --out $R/$O/previews --samples 32 --only b_bunker1,b_bunker2,b_bunker3,c_ridge_n,c_ridge_s,c_ridge_fair,e_cliff,d_aerial_side > $O/logs/render_extra.log 2>&1
python3 $O/tools/make_contact_sheet.py
(cd $O && python3 tools/make_install_md.py)
rm -f $O/stage/hole_09.blend1
ls $O/previews
