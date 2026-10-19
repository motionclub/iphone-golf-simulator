# patch_g0_instancers.py <Unity Assets dir> : make-room (PLAN §3 M1) for the coastal instancer (shared file -> chat 6 patch).
# Tree groups keep drawing their artist mesh exactly as before, but no longer cast from it: a vertex-clustered proxy
# (MajesticBudget.Cluster) is drawn ShadowsOnly in its place. Idempotent; MAJESTIC_BUDGET=0 keeps the old behaviour.
import sys, os
p = os.path.join(sys.argv[1], 'Scripts/Course/GolfCoastalInstances.cs'); s = open(p).read()
if 'shadowProxy' in s: print('already patched'); sys.exit(0)
s = s.replace("public Mesh nearMesh,farMesh;public Material[] nearMaterials,farMaterials;public bool tree;",
              "public Mesh nearMesh,farMesh,shadowProxy;public Material[] nearMaterials,farMaterials;public bool tree;")
s = s.replace("                foreach(var material in farMaterials)material.enableInstancing=true;\n",
              "                foreach(var material in farMaterials)material.enableInstancing=true;\n"
              "                // chat 10 make-room: trees cast from a coarse proxy (same shadow at shadow-map resolution)\n"
              "                if(tree&&near.isReadable&&GolfArcade.Majestic.MajesticBudget.Enabled)group.shadowProxy=GolfArcade.Majestic.MajesticBudget.Cluster(near,.5f);\n")
s = s.replace("            var shadow=near&&group.tree?ShadowCastingMode.On:ShadowCastingMode.Off;",
              "            var shadow=near&&group.tree&&!group.shadowProxy?ShadowCastingMode.On:ShadowCastingMode.Off;\n"
              "            if(near&&group.tree&&group.shadowProxy&&SystemInfo.supportsInstancing)Graphics.DrawMeshInstanced(group.shadowProxy,0,GolfArcade.Majestic.MajesticBudget.ShadowMaterial,matrices,null,ShadowCastingMode.ShadowsOnly,false,gameObject.layer,null,LightProbeUsage.Off);")
open(p, 'w').write(s); print('patched', p)
