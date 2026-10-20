import bpy,json,sys,math
from pathlib import Path
from mathutils import Matrix,Vector
W=Path(__file__).resolve().parents[1];s=(W/'scripts/render_review.py').read_text();s=s.replace("stages=[('Address',0),('Top',d['backswingTop']),('Impact',d['impact']),('Finish',d['duration'])]","stages=[]")
s=s.replace("sc.frame_set(0);bpy.context.view_layer.update();hands=","sc.frame_set(0);bpy.context.view_layer.update();\n"+"grips=json.loads((W/'data/grip_Female_LH.json').read_text())\nfor side,sd in [('L','Left'),('R','Right')]:\n row=grips[side]\n for nm,angle in row['angles'].items():\n  pb=rig.pose.bones[nm];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=(Matrix.Rotation(math.radians(row['spreads'].get(nm,0)),4,'Z')@Matrix.Rotation(math.radians(angle),4,Vector(row.get('flexAxes',{}).get(nm,[1,0,0])))).to_quaternion()\n bpy.context.view_layer.update();pb=rig.pose.bones[sd+'Hand'];pb.matrix=rig.matrix_world.inverted()@club.matrix_world@Matrix(row['anchor'])\nbpy.context.view_layer.update();hands=")
exec(compile(s,'preview','exec'),{'__file__':str(W/'scripts/render_review.py'),'Matrix':Matrix})
