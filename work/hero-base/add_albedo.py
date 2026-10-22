from pathlib import Path
p=Path('Tools/HeroBase/build_static.py');s=p.read_text();s=s.replace('    uv(body)\n    # Hair cap', '''    uv(body)
    atlas=bpy.data.images.load(str(D/'unity_import/Textures'/('Head_'+sex.title()+'_Albedo.png')))
    atlas.colorspace_settings.name='sRGB'
    node=mats[1].node_tree.nodes.new('ShaderNodeTexImage');node.image=atlas;node.extension='EXTEND';mats[1].node_tree.links.new(node.outputs['Color'],mats[1].node_tree.nodes['Principled BSDF'].inputs['Base Color'])
    for poly in body.data.polygons:
        if poly.material_index!=1:continue
        for ix in poly.loop_indices:
            v=body.data.vertices[body.data.loops[ix].vertex_index].co;y=sole-v.z/scale
            body.data.uv_layers.active.data[ix].uv=((math.atan2(v.x,-v.y)/TAU+.5),(205-y)/155) if y<205 else (.02,.02)
    # Hair cap''')
p.write_text(s)
p=Path('Unity/Assets/Editor/HeroBaseStaticImport.cs');s=p.read_text();s=s.replace('Directory.CreateDirectory(Dir+"/Materials");','Directory.CreateDirectory(Dir+"/Materials");Directory.CreateDirectory(Dir+"/Textures");')
s=s.replace('AssetDatabase.Refresh();\n   foreach(var sex', '''foreach(var sex in new[]{"Male","Female"})File.Copy("../ArtDir/hero/base_lock/unity_import/Textures/Head_"+sex+"_Albedo.png",Dir+"/Textures/Head_"+sex+"_Albedo.png",true);
   AssetDatabase.Refresh();
   foreach(var sex in new[]{"Male","Female"}){var ti=(TextureImporter)AssetImporter.GetAtPath(Dir+"/Textures/Head_"+sex+"_Albedo.png");ti.sRGBTexture=true;ti.crunchedCompression=false;ti.textureCompression=TextureImporterCompression.Uncompressed;ti.maxTextureSize=2048;ti.mipmapEnabled=true;ti.SaveAndReimport();}
   foreach(var sex''')
s=s.replace('material.SetColor("_BaseColor",c);', '''if(clean.StartsWith("Skin_")){material.SetTexture("_BaseMap",AssetDatabase.LoadAssetAtPath<Texture2D>(Dir+"/Textures/Head_"+sex+"_Albedo.png"));c=Color.white;}
  material.SetColor("_BaseColor",c);''')
p.write_text(s)
