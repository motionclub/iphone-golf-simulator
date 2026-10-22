from pathlib import Path
W=Path(__file__).resolve().parents[1];p=W/'candidate/GolfArcade/Unity/MatchHeroMotion.swift';s=p.read_text();needle='        let samples=motion.samples(data,at:time)\n';s=s.replace(needle,'''        applyGolfSamples(motion.samples(data,at:time))
    }
    func previewGolfClip(_ clip:RigData.Clip,at time:Double) {
        apply(clip.pose(at:time,loop:false));applyGolfSamples([(clip,time,1)])
    }
    private func applyGolfSamples(_ samples:[(RigData.Clip,Double,Float)]) {
''',1);p.write_text(s)

s=p.read_text();needle='    private func applyGolfSamples('
s=s.replace(needle,"    func previewGolfTransition(_ from:RigData.Clip,_ to:RigData.Clip,weight:Float) {\n        apply(RigData.blend(from.pose(at:from.length*0.5,loop:false),to.pose(at:0,loop:false),weight));applyGolfSamples([(from,from.length*0.5,1-weight),(to,0,weight)])\n    }\n"+needle,1);p.write_text(s)
