#!/bin/zsh
set -e
W=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/serve-toss-jump
cd $W
/usr/bin/swiftc -module-cache-path /private/tmp/serve-toss-jump-module-cache scripts/enc.swift -o scripts/enc
python3 scripts/make_proof_dj.py male > logs/make_proof_male.log 2>&1
python3 scripts/make_proof_dj.py female > logs/make_proof_female.log 2>&1
python3 scripts/package_visuals.py > logs/package_visuals.log 2>&1
python3 scripts/encode_full_game.py > logs/encode_full_game.log 2>&1
/usr/bin/swift -module-cache-path /private/tmp/serve-toss-jump-module-cache scripts/inspect_movies.swift proof/movie_decode film/serve_toss_jump_male_views.mp4 film/serve_toss_jump_female_views.mp4 film/serve_toss_jump_male_side_half_speed.mp4 film/serve_toss_jump_female_side_half_speed.mp4 film/serve_toss_jump_male_game_full.mp4 film/serve_toss_jump_female_game_full.mp4 > logs/movie_audit.log 2>&1
