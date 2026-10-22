using UnityEngine;
using UnityEngine.UI;
using GolfArcade.Course;
namespace GolfArcade.EnvironmentArt
{
    /// Observation belongs to the golfer; cameras, TV and quality levels cannot move it.
    public static class DreamVisibility
    {
        public static bool Fog {get; private set;}
        public static Vector3 Observer {get; private set;}
        public static System.Func<CoursePoint,double> Ground;
        public static int Revision {get; private set;}
        public static void Set(bool fog,Vector3 observer)
        {
            if(Fog!=fog || (Observer-observer).sqrMagnitude>.01f){Fog=fog;Observer=observer;Revision++;}
            Shader.SetGlobalVector("_DreamObserver",new Vector4(Observer.x,Observer.y,Observer.z,Fog?1:0));
        }
        public static float Transmission(Vector3 p) => !Fog?1:(float)DreamConditions.Visibility(p.x,p.y,p.z,Observer.x,Observer.y,Observer.z);
        public static bool Visible(Vector3 p) => !Fog || Transmission(p)>=.24f;
        public static void Reset(){Ground=null;Set(false,Vector3.zero);}
        public static void Mask(RawImage image,Camera map)
        {
            if(!image || !map)return;
            var mask=image.GetComponent<DreamMapFog>();
            if(!mask && !Fog)return;
            if(!mask)mask=image.gameObject.AddComponent<DreamMapFog>();
            mask.Draw(map);
        }
    }
    /// Small terrain-aware mask laid above cached terrain AND every overlay, on all map views.
    public sealed class DreamMapFog : MonoBehaviour
    {
        Texture2D texture;RawImage veil;Color32[] pixels;int revision=-1;Matrix4x4 matrix,projection;int children;
        const int Size=64;
        public void Draw(Camera camera)
        {
            if(!veil){
                var go=new GameObject("Observation fog",typeof(RectTransform),typeof(RawImage));go.transform.SetParent(transform,false);
                veil=go.GetComponent<RawImage>();veil.raycastTarget=false;
                var rt=veil.rectTransform;rt.anchorMin=Vector2.zero;rt.anchorMax=Vector2.one;rt.offsetMin=rt.offsetMax=Vector2.zero;
                texture=new Texture2D(Size,Size,TextureFormat.RGBA32,false){wrapMode=TextureWrapMode.Clamp,filterMode=FilterMode.Bilinear};pixels=new Color32[Size*Size];veil.texture=texture;
            }
            veil.enabled=DreamVisibility.Fog;veil.transform.SetAsLastSibling();
            if(!DreamVisibility.Fog)return;
            if(revision==DreamVisibility.Revision && matrix==camera.cameraToWorldMatrix && projection==camera.projectionMatrix && children==transform.childCount)return;
            revision=DreamVisibility.Revision;matrix=camera.cameraToWorldMatrix;projection=camera.projectionMatrix;children=transform.childCount;
            for(int y=0;y<Size;y++)for(int x=0;x<Size;x++) {
                var ray=camera.ViewportPointToRay(new Vector3((x+.5f)/Size,(y+.5f)/Size,0));
                var p=ray.GetPoint(Mathf.Abs(ray.direction.y)>.001f?(DreamVisibility.Observer.y-ray.origin.y)/ray.direction.y:0);
                double ground=DreamVisibility.Ground?.Invoke(new CoursePoint(p.x,p.z))??DreamVisibility.Observer.y;
                p.y=(float)ground;float t=DreamVisibility.Transmission(p);
                // Fully occlude precise overlays wherever the shared visibility policy hides them.
                float a=t<.24f?1:Mathf.Clamp01((1-t)*1.15f);
                pixels[y*Size+x]=new Color32(61,76,90,(byte)(a*255));
            }
            texture.SetPixels32(pixels);texture.Apply(false,false);
        }
        void OnDestroy(){if(texture)Destroy(texture);if(veil)Destroy(veil.gameObject);}
    }
}
