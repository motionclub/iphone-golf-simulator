from pathlib import Path
R=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');W=Path(__file__).parent
p=R/'Unity/Assets/Scripts/Tennis/TennisStandsCrowd.cs';s=p.read_text();s=s.replace('            public float phase,cheerAt=-9,style;','            public float phase,cheerAt=-9,style;public bool far;public Transform root;')
s=s.replace('public Matrix4x4[] matrices;','public Matrix4x4[] matrices;public bool far;')
s=s.replace('        Material spectatorMaterial;','''        readonly Dictionary<MeshRenderer,Fan> owners=new();
        readonly Plane[] planes=new Plane[6];
        public int DetailOverride {get;set;}=-1;
        public int NearFanCount {get;private set;}
        public int FarFanCount {get;private set;}
        Material spectatorMaterial;''')
s=s.replace('if(renderer)renderer.enabled=!instancedSubmission;','if(renderer)renderer.enabled=!instancedSubmission&&batch.far==owners[renderer].far;')
s=s.replace('Resources.Load<GameObject>("Tennis/Premium/TennisSpectators")','Resources.Load<GameObject>("Tennis/Premium/TennisSeatedHero3")')
s=s.replace('spectatorMaterial=material;','spectatorMaterial=material;if(material.HasProperty("_SurfaceRoles"))material.SetFloat("_SurfaceRoles",1);')
a=s.index('                foreach(var r in selected.GetComponentsInChildren<MeshRenderer>(true))');b=s.index('                f.headRest=',a);old=s[a:b];fline=old[old.index('                var f=new Fan'):];fline=fline.replace('phase=i*1.618f','root=selected,phase=i*1.618f');s=s[:a]+fline+'''                foreach(var r in selected.GetComponentsInChildren<MeshRenderer>(true))
                {
                    bool far=r.name.Contains("_FAR");
                    r.sharedMaterial=material;r.shadowCastingMode=far?ShadowCastingMode.Off:ShadowCastingMode.On;r.receiveShadows=true;
                    var filter=r.GetComponent<MeshFilter>();if(!filter||!filter.sharedMesh)continue;
                    var batch=batches.Find(b=>b.mesh==filter.sharedMesh);
                    if(batch==null){batch=new InstanceBatch{mesh=filter.sharedMesh,far=far};batches.Add(batch);}
                    batch.renderers.Add(r);owners.Add(r,f);
                }
'''+s[b:]
a=s.index('        void LateUpdate()');b=s.index('        void OnDestroy()',a)
s=s[:a]+'''        void LateUpdate()
        {
            var camera=game&&game.GameplayCamera?game.GameplayCamera:Camera.main;
            float tangent=camera?Mathf.Tan(camera.fieldOfView*.5f*Mathf.Deg2Rad):.53f;
            if(camera)GeometryUtility.CalculateFrustumPlanes(camera,planes);
            NearFanCount=0;FarFanCount=0;
            foreach(var fan in fans)
            {
                float distance=camera?Vector3.Distance(camera.transform.position,fan.root.position+Vector3.up*.6f):10;
                float height=camera&&camera.orthographic?1.75f/(camera.orthographicSize*2):1.75f/(2*Mathf.Max(.1f,distance)*tangent);
                fan.far=DetailOverride>=0?DetailOverride==1:height<.25f;
                if(fan.far)FarFanCount++;else NearFanCount++;
            }
            var parameters=new RenderParams(spectatorMaterial){receiveShadows=true,layer=gameObject.layer,lightProbeUsage=LightProbeUsage.BlendProbes};
            foreach(var batch in batches)
            {
                int visible=0;
                foreach(var renderer in batch.renderers)
                {
                    if(!renderer)continue;bool selected=batch.far==owners[renderer].far;
                    renderer.enabled=!instancedSubmission&&selected&&!SuppressRendering;
                    if(!selected||SuppressRendering||camera&&!GeometryUtility.TestPlanesAABB(planes,renderer.bounds))continue;
                    batch.matrices[visible++]=renderer.localToWorldMatrix;
                }
                if(!instancedSubmission||visible==0||!spectatorMaterial)continue;
                parameters.shadowCastingMode=batch.far?ShadowCastingMode.Off:batch.renderers[0].shadowCastingMode;
                for(int sub=0;sub<batch.mesh.subMeshCount;sub++)Graphics.RenderMeshInstanced(parameters,batch.mesh,sub,batch.matrices,visible);
            }
        }
'''+s[b:];(W/p.name).write_text(s)
p=R/'work/full-visual-overhaul/tennis/world12/TennisResortCrowd.cs';s=p.read_text().replace('Tennis/Premium/TennisPromenadeVisitors','Tennis/Premium/TennisPromenadeHero3');s=s.replace('        Material material;','''        public int DetailOverride {get;set;}=-1;
        public int NearVisitorCount {get;private set;}
        public int FarVisitorCount {get;private set;}
        Material material;''');s=s.replace('            public Leg l,r;','            public Leg l,r;public MeshRenderer[] near,far;')
s=s.replace('            var head=Part(', '            if(material.HasProperty("_SurfaceRoles"))material.SetFloat("_SurfaceRoles",1);\n            var head=Part(')
s=s.replace('                visitors.Add(v);','''                var near=new List<MeshRenderer>();var far=new List<MeshRenderer>();
                foreach(var renderer in selected.GetComponentsInChildren<MeshRenderer>(true))
                {renderer.sharedMaterial=material;renderer.shadowCastingMode=ShadowCastingMode.Off;renderer.receiveShadows=true;if(renderer.name.Contains("_FAR"))far.Add(renderer);else near.Add(renderer);}
                v.near=near.ToArray();v.far=far.ToArray();visitors.Add(v);''')
needle='        void OnDestroy()';at=s.index(needle);s=s[:at]+'''        void LateUpdate()
        {
            var game=GetComponent<TennisGame>();var camera=game&&game.GameplayCamera?game.GameplayCamera:Camera.main;
            float tangent=camera?Mathf.Tan(camera.fieldOfView*.5f*Mathf.Deg2Rad):.53f;NearVisitorCount=0;FarVisitorCount=0;
            foreach(var v in visitors)
            {
                float distance=camera?Vector3.Distance(camera.transform.position,v.actor.position+Vector3.up*.85f):10;
                float height=camera&&camera.orthographic?1.75f/(camera.orthographicSize*2):1.75f/(2*Mathf.Max(.1f,distance)*tangent);
                bool far=DetailOverride>=0?DetailOverride==1:height<.25f;if(far)FarVisitorCount++;else NearVisitorCount++;
                foreach(var renderer in v.near)renderer.enabled=!far;
                foreach(var renderer in v.far)renderer.enabled=far;
            }
        }
'''+s[at:];(W/p.name).write_text(s)
