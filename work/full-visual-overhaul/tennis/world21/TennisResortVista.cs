using UnityEngine;

namespace GolfArcade.Tennis
{
    /// Court-facing resort landmarks. All geometry is render-only and stays
    /// outside the live court/runoff; no collider or gameplay actor is created.
    public static class TennisResortVista
    {
        public static void Build(Transform root)
        {
            var green = new TennisVenueBuilder.MB();
            var rock = new TennisVenueBuilder.MB();
            var beach = new TennisVenueBuilder.MB();
            Island(green,rock,beach,new Vector2(-15,490),new Vector2(228,95),1);
            Island(green,rock,beach,new Vector2(285,690),new Vector2(130,72),3);
            Island(green,rock,beach,new Vector2(-340,720),new Vector2(144,64),6);
            var foliage=TennisVenueArt.Surface("Resort distant island vegetation",new Color(.24f,.41f,.27f),.10f,0,.08f,.004f);
            var mineral=TennisVenueArt.Surface("Resort distant weathered limestone",new Color(.55f,.59f,.50f),.14f,0,.055f,.006f);
            mineral.SetTexture("_WorldMap",Resources.Load<Texture2D>("Course/Resort/Limestone_C"));
            mineral.SetFloat("_WorldMapWeight",.25f);mineral.SetFloat("_WorldMapScale",.036f);
            Make(root,"Distant lush resort islands",green,foliage);
            Make(root,"Distant exposed island ridges",rock,mineral);
            Make(root,"Distant island beaches",beach,TennisVenueArt.Surface("Resort distant warm beaches",new Color(.78f,.76f,.64f),.12f));
        }

        static void Island(TennisVenueBuilder.MB green,TennisVenueBuilder.MB rock,TennisVenueBuilder.MB beach,
                           Vector2 centre,Vector2 extent,int seed)
        {
            const int around=120,rings=28;
            var points=new Vector3[rings+1,around+1];
            for(int j=0;j<=rings;j++)for(int i=0;i<=around;i++)
            {
                float r=j/(float)rings,a=(i%around)*Mathf.PI*2/around;
                float outline=1+.075f*Mathf.Sin(a*3+seed)+.045f*Mathf.Cos(a*5+seed*.31f);
                float x=Mathf.Cos(a)*r*extent.x*outline,z=Mathf.Sin(a)*r*extent.y*outline;
                float p0=Mathf.Exp(-((x+extent.x*.35f)*(x+extent.x*.35f)/5500+(z+12)*(z+12)/1300));
                float p1=Mathf.Exp(-((x-extent.x*.10f)*(x-extent.x*.10f)/3500+(z-16)*(z-16)/1200));
                float p2=Mathf.Exp(-((x-extent.x*.48f)*(x-extent.x*.48f)/2200+(z+4)*(z+4)/1050));
                float fade=Mathf.SmoothStep(0,1,Mathf.Clamp01((1-r)/.22f));
                float ridge=(Mathf.PerlinNoise(x*.018f+seed*9,z*.028f+31)-.5f)*7;
                float scale=extent.x/228;
                float y=-4.1f+(p0*56+p1*83+p2*49+ridge+3)*fade*scale;
                points[j,i]=new Vector3(centre.x+x,y,centre.y+z);
            }
            for(int j=0;j<rings;j++)for(int i=0;i<around;i++)
            {
                var a=points[j,i];var b=points[j,i+1];var c=points[j+1,i+1];var d=points[j+1,i];
                var normal=Vector3.Cross(c-a,d-a).normalized;
                var average=(a+b+c+d)*.25f;
                var target=average.y<-.15f?beach:normal.y<.70f&&average.y>9?rock:green;
                // All four points are on the same continuous authored landform.
                if(j==0)
                    target.Tri(target.Add(a,new Vector2(a.x,a.z)*.03f),target.Add(d,new Vector2(d.x,d.z)*.03f),target.Add(c,new Vector2(c.x,c.z)*.03f));
                else target.Face4(a,d,c,b,new Vector2(a.x,a.z)*.03f,new Vector2(d.x,d.z)*.03f,
                    new Vector2(c.x,c.z)*.03f,new Vector2(b.x,b.z)*.03f);
            }
        }

        internal static void Pergola(TennisVenueBuilder.MB limestone,TennisVenueBuilder.MB timber)
        {
            const float x=-21.5f;
            for(int i=0;i<5;i++)
            {
                float z=-13.4f+i*6.7f;
                TennisVenueArt.BevelBox(limestone,new Vector3(x,.13f,z),new Vector3(1.36f,.26f,1.36f),.10f);
                Column(limestone,new Vector3(x,.26f,z));
                TennisVenueArt.BevelBox(limestone,new Vector3(x,5.29f,z),new Vector3(1.34f,.30f,1.34f),.06f);
            }
            // Deep beam ends, a shadowed double entablature and close-cut rafters
            // carry the same warm timber craft as the resort reference portico.
            foreach(float side in new[]{-1f,1f})
                TennisVenueArt.BevelBox(timber,new Vector3(x+side*1.62f,5.65f,0),new Vector3(.25f,.44f,29.6f),.045f);
            TennisVenueArt.BevelBox(timber,new Vector3(x,5.54f,0),new Vector3(.70f,.55f,29.4f),.055f);
            for(int i=0;i<20;i++)
            {
                float z=-14.4f+i*1.52f;
                TennisVenueArt.BevelBox(timber,new Vector3(x,5.98f,z),new Vector3(4.50f,.27f,.20f),.035f);
                TennisVenueArt.BevelBox(timber,new Vector3(x+1.84f,5.80f,z),new Vector3(.44f,.27f,.22f),.030f);
            }
        }

        static void Column(TennisVenueBuilder.MB mesh,Vector3 origin)
        {
            // Rounded architectural torus/scotia steps flow into the tapered
            // shaft. Shared rings produce clean radial lighting, unlike cubes.
            var profile=new Vector2[]{new(.54f,0),new(.57f,.035f),new(.57f,.14f),new(.54f,.19f),
                new(.44f,.25f),new(.41f,.32f),new(.38f,.45f),new(.375f,.58f),
                new(.33f,4.27f),new(.35f,4.43f),new(.43f,4.52f),new(.47f,4.62f),
                new(.47f,4.77f),new(.43f,4.84f),new(.43f,4.91f)};
            const int sides=48;var rings=new int[profile.Length,sides+1];
            for(int j=0;j<profile.Length;j++)for(int i=0;i<=sides;i++)
            {
                float angle=i*Mathf.PI*2/sides;
                rings[j,i]=mesh.Add(origin+new Vector3(Mathf.Cos(angle)*profile[j].x,profile[j].y,Mathf.Sin(angle)*profile[j].x),new Vector2(i/(float)sides,profile[j].y));
            }
            for(int j=0;j<profile.Length-1;j++)for(int i=0;i<sides;i++)
                mesh.Quad(rings[j,i],rings[j,i+1],rings[j+1,i+1],rings[j+1,i]);
        }

        static void Make(Transform root,string name,TennisVenueBuilder.MB geometry,Material material)
        {
            if(geometry.Count>0)TennisVenueBuilder.MeshObject(root,name,geometry.ToMesh(name),material,false);
        }
    }
}
