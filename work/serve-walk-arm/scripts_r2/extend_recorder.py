from pathlib import Path
P=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');W=P/'work/serve-walk-arm'
s=(W/'rollback/r2/Unity/Assets/Editor/ServeWalkFilm.cs').read_text()
s=s.replace('List<int> arm; int[] dominant;', 'List<int> arm, pelvis; int[] dominant;')
s=s.replace('bool female, lefty, ad, keyboard, opponent;', 'bool female, lefty, ad, keyboard, opponent, adapter, controlOnly, images;\n        string resetReason = "", ballExclusion = ""; int resetAt = -999;')
s=s.replace('opponent = ServeWalkFilm.Env("SW_ROLE", "player") == "opponent";', 'opponent = ServeWalkFilm.Env("SW_ROLE", "player") == "opponent";\n            adapter = ServeWalkFilm.Env("SW_INPUT_PATH", "fixture") == "adapter";\n            controlOnly = ServeWalkFilm.Env("SW_CONTROL_ONLY", "0") == "1"; images = ServeWalkFilm.Env("SW_IMAGES", "1") == "1";')
s=s.replace('game.NativeControlled = !keyboard;', 'game.NativeControlled = !keyboard && !adapter;')
s=s.replace('ConfigurePoint();\n            cam', '''ConfigurePoint();
            if (adapter)
            {
                // Test adapter calls the production input-handler method. Keep the physical-keyboard
                // fallback from overwriting it by holding the existing motion-control guard active.
                var phone = game.GetComponent<TennisPhoneInput>();
                if (phone) { phone.enabled = false; SetField(phone, "clock", 0d); SetField(phone, "lastSampleAt", 0d); }
            }
            cam''')
s=s.replace('header += ",palm_trunk_clearance_m,wrist_above_hips_m,carry_blend";', 'header += ",palm_trunk_clearance_m,wrist_above_hips_m,carry_blend,side_visible,in_hand,ball_exclusion,reset_reason,root_frame,target_frame,unity_frame,input_path,supported,pelvis_top_y,wrist_above_belt_m,pelvis_top_above_hips_m,pelvis_vertices,signed_ttc,swinging,kind,contact_age,camera_x,camera_y,camera_z,runtime_belt_y,runtime_belt_error_mm";')
s=s.replace('SetField(game, "match", match); game.Refeed();','SetField(game, "match", match); game.Refeed(); resetReason = "fixture_point_reset"; resetAt = frame;')
s=s.replace('mark + 2.5f', 'mark + (controlOnly ? 0 : 2.5f)')
s=s.replace('if (frame < 0) { game.ServeNudge = 0; return; }','if (frame < 0) { game.ServeNudge = 0; if (adapter) game.SetLateralInput(0, false); return; }\n            resetReason = frame - resetAt <= 1 ? "fixture_point_reset" : "";')
s=s.replace('            if (opponent)\n            {\n                if (frame == 0', '''            if (controlOnly)
            {
                segment = "control"; game.ServeNudge = 0;
                if (!opponent && !tossed && t >= 3.7f) { game.Toss(1); tossed = true; }
                if (!opponent && !swung && game.Flow == TennisGame.Phase.PlayerServeToss && Field(game, "phaseTimer") >= TennisRules.ServeApex - .08f) { game.RequestSwing(.75f); swung = true; }
                if (t >= float.Parse(ServeWalkFilm.Env("SW_DURATION", "8"), CI)) Complete();
                return;
            }
            if (opponent)
            {
                if (frame == 0''')
s=s.replace('game.ServeNudge = segment == "walk_left" || segment == "tap_left" ? -1 : segment == "walk_right" || segment == "tap_right" ? 1 : 0;', '''float input = segment == "walk_left" || segment == "tap_left" ? -1 : segment == "walk_right" || segment == "tap_right" ? 1 : 0;
            if (adapter) { game.ServeNudge = 0; game.SetLateralInput(input, false); }
            else game.ServeNudge = input;''')
s=s.replace('controls = true; tossed = swung = false; game.Refeed();', 'controls = true; tossed = swung = false; game.Refeed(); resetAt = frame; resetReason = "fixture_point_reset";')
s=s.replace('if (Field(game, "serveWalkSpeed") > .2f)', 'if (Field(game, "serveWalkSpeed") > .2f)')
s=s.replace('else if (Field(game, "serveWalkSpeed") > .2f) routine = 0;', 'else if (Field(game, "serveWalkSpeed") > .2f) routine = 0;')
s=s.replace('arm = new List<int>(); dominant', 'arm = new List<int>(); pelvis = new List<int>(); dominant')
s=s.replace('if (aw > .5f) arm.Add(i);', 'if (aw > .5f) arm.Add(i); float hw = 0; for (int k = 0; k < 4; k++) if (boneNames[bi[k]] == \"Hips\") hw += bw[k]; if (hw > .5f) pelvis.Add(i);')
# Add logical state measurement without depending on candidate-only runtime API.
pos='        void Record()\n'
helper='''        bool Held(float t)
        {
            float windStart = TennisRules.ServeTossDelay - TennisServeRoutine.WindUp;
            if (t >= windStart) return t < TennisRules.ServeTossDelay;
            float h = TennisServeRoutine.Hold(driver.actor).y - .08f - driver.actor.transform.position.y;
            float fall = (-3.5f + Mathf.Sqrt(3.5f * 3.5f + 2 * 9.81f * Mathf.Max(.1f, h - TennisRules.BallRadius))) / 9.81f;
            float rise = (3.5f + 9.81f * fall) * .7f / 9.81f, cycle = .06f + fall + rise + .18f;
            float b = t - Mathf.Max(0, windStart - TennisServeRoutine.Gather - TennisServeRoutine.Bounces * cycle);
            int n = Mathf.FloorToInt(b / cycle); float u = b - n * cycle;
            return b < 0 || n >= TennisServeRoutine.Bounces || u < .06f || u >= .06f + fall + rise;
        }
        object Diagnostic(string key) => driver.GetType().GetProperty(key)?.GetValue(driver);
'''
s=s.replace(pos,helper+pos)
s=s.replace('if (opponent) routine = Field(game, "serveTimer");', 'if (opponent) routine = Field(game, "serveTimer");')
s=s.replace('            trace.WriteLine(string.Join(",", parts)); trace.Flush();', '''            bool pre = opponent ? game.Flow == TennisGame.Phase.OpponentServe && routine < TennisRules.ServeTossDelay : game.Flow == TennisGame.Phase.PlayerServeHold;
            bool held = pre && Held(routine);
            var state = Diagnostic("ServeBallInHand"); if (state != null && pre) held = (bool)state;
            ballExclusion = frame == resetAt ? "refeed_before_rebind" : !pre ? "released_or_unbound" : routine >= TennisRules.ServeTossDelay ? "release_boundary" : !held ? "intentional_bounce_flight" : "";
            if (ballExclusion.Length > 0) held = false;
            parts.Add(Visible(root.position - root.right * 3.3f + Vector3.up * 1.2f) ? "1" : "0");
            parts.Add(held ? "1" : "0"); parts.Add(ballExclusion); parts.Add(resetReason);
            parts.Add((Diagnostic("ServeRootFrame") ?? -1).ToString()); parts.Add((Diagnostic("ServeTargetFrame") ?? -1).ToString());
            parts.Add(Time.frameCount.ToString()); parts.Add(adapter ? "SetLateralInput" : keyboard ? "keyboard" : "fixture_ServeNudge"); parts.Add(lefty ? "0" : "1");
            float pelvisTop = pelvis.Max(i => world[i].y);
            parts.Add(F(pelvisTop)); parts.Add(F(hand.position.y - pelvisTop)); parts.Add(F(pelvisTop - Bone(HumanBodyBones.Hips).position.y)); parts.Add(pelvis.Count.ToString());
            parts.Add(F(server.SignedTimeToContact)); parts.Add(server.Swinging ? "1" : "0"); parts.Add(server.Kind.ToString()); parts.Add(F(server.ContactAge)); parts.Add(V(cam.transform.position));
            var runtimeBelt = Diagnostic("ServeBeltHeight"); float runtimeY = runtimeBelt != null ? (float)runtimeBelt : -99; parts.Add(F(runtimeY)); parts.Add(F(runtimeBelt != null ? (runtimeY - pelvisTop) * 1000 : -99999));
            trace.WriteLine(string.Join(",", parts)); trace.Flush();''')
s=s.replace('if (depth > worstAll)', 'if (images && depth > worstAll)')
s=s.replace('            if (frame % 2 == 0)\n', '            if (images && frame % 2 == 0)\n')
# Keep raw derivatives across Refeed; only actual opponent fixture teleports are exempt.
s=s.replace(' haveLast = false;', '')
s=s.replace('string resetReason = "", ballExclusion = ""; int resetAt = -999;', 'string resetReason = "", ballExclusion = ""; int resetAt = -999, actualTeleportAt = -999; Vector3 lastMeasuredRoot; bool haveMeasuredRoot;')
s=s.replace('            hero.body.BakeMesh(baked); baked.GetVertices(verts);', '            Vector3 measuredRoot = (opponent ? game.Opponent : game.Player).transform.position;\n            if (opponent && frame == resetAt && (!haveMeasuredRoot || Vector3.Distance(measuredRoot, lastMeasuredRoot) > .3f)) actualTeleportAt = frame;\n            resetReason = opponent && frame - actualTeleportAt <= 1 ? "fixture_opponent_root_teleport" : "";\n            lastMeasuredRoot = measuredRoot; haveMeasuredRoot = true;\n            hero.body.BakeMesh(baked); baked.GetVertices(verts);')
s=s.replace('            Directory.CreateDirectory(dir);', '            Directory.CreateDirectory(dir);\n            string[] proofSources = { "Scripts/Tennis/HeroTennisDriver.cs", "Scripts/Tennis/TennisActor.cs", "Scripts/Tennis/TennisServeRoutine.cs", "Scripts/Tennis/TennisGame.cs", "Editor/ServeWalkFilm.cs" };\n            string[] hashes = proofSources.Select(f => { using (var hash = System.Security.Cryptography.SHA256.Create()) return BitConverter.ToString(hash.ComputeHash(File.ReadAllBytes(Path.Combine(Application.dataPath, f)))).Replace("-", "").ToLowerInvariant(); }).ToArray();\n            File.WriteAllText(Path.Combine(dir, "source.json"), JsonUtility.ToJson(new ProofSourceRecord { projectPath = Path.GetDirectoryName(Application.dataPath), inputPath = adapter ? "SetLateralInput" : keyboard ? "keyboard" : "fixture_ServeNudge", sources = proofSources, sha256 = hashes }, true));')
s=s.replace('    [DefaultExecutionOrder(2000)]', '    [Serializable] public sealed class ProofSourceRecord { public string projectPath, inputPath; public string[] sources, sha256; }\n\n    [DefaultExecutionOrder(2000)]')
s=s.replace('            lastHand = hand.position; lastVelocity = velocity;', '            if ((images || ServeWalkFilm.Env("SW_PLANT_SNAPSHOT", "0") == "1") && frame == 547)\n            {\n                GameCapture.Save(Path.Combine(dir, "plant547-game.png"), 960, 540);\n                Shot("plant547-front", "00547", frontFrom, root.position + Vector3.up * .98f, 480);\n                Shot("plant547-side", "00547", root.position - root.right * 3.3f + Vector3.up * 1.2f, root.position + Vector3.up * .98f, 480);\n            }\n            lastHand = hand.position; lastVelocity = velocity;')
(P/'Unity/Assets/Editor/ServeWalkFilm.cs').write_text(s)
for clone in ['CandidateR2Clone','BeforeR2Clone']:
    (W/clone/'Assets/Editor/ServeWalkFilm.cs').write_text(s)
print('Recorder extended in production editor and both clones')
