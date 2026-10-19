from pathlib import Path
import hashlib, json, re, html
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pypdf import PdfReader, PdfWriter

ROOT = Path(__file__).resolve().parent
FONTDIR = Path('/Users/adnanyonathan/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/pdfjs-dist/standard_fonts')
for name, filename in [('Helvetica','LiberationSans-Regular.ttf'),('Helvetica-Bold','LiberationSans-Bold.ttf'),('Helvetica-Oblique','LiberationSans-Italic.ttf'),('Helvetica-BoldOblique','LiberationSans-BoldItalic.ttf')]:
    pdfmetrics.registerFont(TTFont(name,str(FONTDIR/filename)))
pdfmetrics.registerFontFamily('Helvetica',normal='Helvetica',bold='Helvetica-Bold',italic='Helvetica-Oblique',boldItalic='Helvetica-BoldOblique')
TMP = ROOT / "proof"
TMP.mkdir(exist_ok=True)
NAVY = HexColor("#172738")
TEAL = HexColor("#15756f")
INK = HexColor("#334252")
PALE = HexColor("#f3f1ec")

sheets = sorted((ROOT / "sheets").glob("*.png"))
sources = sorted((ROOT / "sources").glob("*.png")) + [ROOT / "sources/female_body_plain.jpg"]
assert len(sheets) == 12 and len(sources) == 4
manifest = []
for p in sheets + sources:
    im = ImageReader(str(p))
    w,h = im.getSize()
    manifest.append(dict(file=str(p.relative_to(ROOT)), width=w, height=h,
                         bytes=p.stat().st_size, sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
(ROOT / "MANIFEST.json").write_text(json.dumps({"panels":60,"sheets":12,"sources":4,"files":manifest},indent=2)+"\n")

def footer(c,w,h,label):
    c.setStrokeColor(HexColor("#d3d8db")); c.line(36,31,w-36,31)
    c.setFont("Helvetica",8); c.setFillColor(INK)
    c.drawString(36,18,"FEMALE HERO  /  REFERENCE HANDOFF  /  2026-10-15")
    c.drawRightString(w-36,18,label)

cover = TMP / "cover.pdf"
c=canvas.Canvas(str(cover),pagesize=(1080,720))
c.setFillColor(PALE);c.rect(0,0,1080,720,fill=1,stroke=0)
c.setFillColor(TEAL);c.setFont("Helvetica-Bold",12);c.drawString(44,681,"THE GOAL COMES FIRST")
c.setFillColor(NAVY);c.setFont("Helvetica-Bold",34);c.drawString(44,638,"BRIGHT. LIVELY. SOULFUL.")
c.setFont("Helvetica",15);c.drawString(44,608,"A neutral construction baseline for a character with real personality.")
c.drawImage(str(ROOT/"sources/01-playful-competitor.png"),44,102,width=700,height=466.67,preserveAspectRatio=True,mask="auto")
styles=getSampleStyleSheet()
side=ParagraphStyle("side",fontName="Helvetica",fontSize=12,leading=18,textColor=INK)
items=[
"<b>ONE PORTABLE FILE</b><br/>12 new sheets / 60 reference panels<br/>3 expressive direction boards<br/>Locked female identity plate<br/>Full copyable master prompt",
"<b>USE IN ANOTHER CHAT</b><br/>Attach this PDF and ask the agent to read the master prompt and inspect every image. The embedded text files also preserve the exact handoff and generation prompts.",
"<b>THE PRIORITY</b><br/>Neutral poses aid construction. The expressive boards remain the ambition. A dull, blank character is a failure even if the mesh is technically tidy.",
"<b>STATUS</b><br/>Reference generation only.<br/>Female hero only.<br/>Game implementation awaits instruction."
]
y=552
for item in items:
    p=Paragraph(item,side);pw,ph=p.wrap(270,600);p.drawOn(c,777,y-ph);y-=ph+26
footer(c,1080,720,"START HERE")
c.showPage();c.save()

# Selectable master prompt, automatically paginated with headings kept with text.
md=(ROOT/"START_HERE.md").read_text()
body=TMP/"master-prompt.pdf"
styles = {
"body": ParagraphStyle("body",fontName="Helvetica",fontSize=10,leading=14,textColor=INK,spaceAfter=8,splitLongWords=True),
"h1": ParagraphStyle("h1",fontName="Helvetica-Bold",fontSize=22,leading=27,textColor=NAVY,spaceAfter=14,keepWithNext=True),
"h2": ParagraphStyle("h2",fontName="Helvetica-Bold",fontSize=13,leading=18,textColor=TEAL,spaceBefore=10,spaceAfter=7,keepWithNext=True),
}
flow=[]
for block in re.split(r"\n\s*\n",md):
    lines=block.strip().splitlines()
    if not lines:continue
    for line in lines:
        if line.startswith("# "): flow.append(Paragraph(html.escape(line[2:]),styles["h1"]))
        elif line.startswith("## "):flow.append(Paragraph(html.escape(line[3:]),styles["h2"]))
        else:flow.append(Paragraph(html.escape(line),styles["body"]))
def page_footer(c,doc):
    footer(c,612,792,"MASTER PROMPT / "+str(doc.page))
doc=SimpleDocTemplate(str(body),pagesize=(612,792),leftMargin=44,rightMargin=44,topMargin=42,bottomMargin=48,
    title="Female Hero - Complete Reference",author="Codex / user-directed art development")
doc.build(flow,onFirstPage=page_footer,onLaterPages=page_footer)

gallery=TMP/"gallery.pdf"
c=canvas.Canvas(str(gallery),pagesize=(1080,760))
gallery_rows=[]
# Start with the expressive ambition before the neutral technical sheets.
ordered=[sources[0],sources[1],sources[2]]+sheets+[sources[3]]
captions={
"01-playful-competitor.png":"SOURCE S1 / APPEAL TARGET - Personality and emotional warmth; neutral geometry comes from the master sheets.",
"02-acting-range.png":"SOURCE S2 / ACTING TARGET - Clear emotional contrast and whole-body intent. Timing remains to be proven.",
"03-clothes-with-weight.png":"SOURCE S3 / GARMENT QUALITY - Substantial edges, cloth volume and material separation.",
"female_body_plain.jpg":"SOURCE S4 / LOCKED FEMALE IDENTITY - Preserve adult proportions and identity; grey suit is not the clothing target."
}
for p in ordered:
    c.setFillColor(PALE);c.rect(0,0,1080,760,fill=1,stroke=0)
    c.setFillColor(NAVY);c.setFont("Helvetica-Bold",12)
    label=caption=captions.get(p.name,p.name.replace(".png","").replace("-"," ").upper())
    c.drawString(36,732,label)
    iw,ih=ImageReader(str(p)).getSize()
    boxw,boxh=1008,672
    scale=min(boxw/iw,boxh/ih)
    w,h=iw*scale,ih*scale
    c.drawImage(str(p),(1080-w)/2,46+(672-h)/2,width=w,height=h,mask="auto")
    footer(c,1080,760,"CONCEPT REFERENCE / "+p.stem)
    c.showPage()
    gallery_rows.append(str(p.relative_to(ROOT)))
c.save()

writer=PdfWriter()
for src in [cover,body,gallery]:
    writer.append(str(src),import_outline=False)
nbrief=len(PdfReader(str(body)).pages)
writer.add_outline_item("Start here: bright, lively, soulful",0)
writer.add_outline_item("Complete copyable master prompt",1)
for i,p in enumerate(ordered):
    writer.add_outline_item(p.stem,1+nbrief+i)
for name in ["START_HERE.md","GENERATION_PROMPTS.json","MANIFEST.json"]:
    writer.add_attachment(name,(ROOT/name).read_bytes())
writer.add_metadata({"/Title":"Female Hero - Bright, Lively, Soulful - Complete Reference",
                     "/Author":"User-directed character reference / Codex",
                     "/Subject":"12 neutral reference sheets, 60 panels, expressive targets and master prompt"})
out=ROOT/"FEMALE_HERO_COMPLETE_REFERENCE.pdf"
with out.open("wb") as f:writer.write(f)
r=PdfReader(str(out))
fulltext="\n".join(p.extract_text() or "" for p in r.pages)
assert "BRIGHT" in fulltext and "lively" in fulltext and "Soul" in fulltext
assert len(r.pages)==1+nbrief+16
assert set(r.attachments)=={"START_HERE.md","GENERATION_PROMPTS.json","MANIFEST.json"}
for name in r.attachments:
    assert r.attachments[name][0]==(ROOT/name).read_bytes()
image_page_count=sum(1 for p in r.pages if len(p.images)>0)
assert image_page_count==17
summary={"pages":len(r.pages),"brief_pages":nbrief,"embedded_image_pages":image_page_count,
"attachments":list(r.attachments),"bytes":out.stat().st_size,
"gallery_pages":[{"page":2+nbrief+i,"file":p} for i,p in enumerate(gallery_rows)]}
(ROOT/"proof/package-validation.json").write_text(json.dumps(summary,indent=2)+"\n")
print(json.dumps(summary,indent=2))

