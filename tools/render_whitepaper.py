#!/usr/bin/env python3
"""Render reviewed JSON papers as linked PDF, Markdown and native SVG figures."""
from pathlib import Path
import argparse, json, re, textwrap, math
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, PageBreak, Table, TableStyle, Flowable, KeepTogether
from reportlab.platypus.tableofcontents import TableOfContents

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'docs'
INK = colors.HexColor('#11251e')
MUTED = colors.HexColor('#56645f')
SIGNAL = colors.HexColor('#c34420')
LIGHT = colors.HexColor('#eff3ef')
RULE = colors.HexColor('#c9d3ce')
W, H = 612, 792
LEFT, RIGHT, TOP, BOTTOM = 52, 52, 59, 49
CW = W-LEFT-RIGHT
ST = {
 'title': ParagraphStyle('Title', fontName='Helvetica-Bold',fontSize=30,leading=34,textColor=INK,spaceAfter=20),
 'subtitle': ParagraphStyle('Subtitle',fontName='Helvetica',fontSize=13,leading=20,textColor=MUTED,spaceAfter=18),
 'body': ParagraphStyle('Body',fontName='Helvetica',fontSize=10.1,leading=15.7,textColor=INK,spaceAfter=10),
 'h1': ParagraphStyle('Heading',fontName='Helvetica-Bold',fontSize=17,leading=21,textColor=INK,spaceBefore=17,spaceAfter=11,keepWithNext=True),
 'small': ParagraphStyle('Small',fontName='Helvetica',fontSize=8.3,leading=12.4,textColor=MUTED,spaceAfter=8),
 'caption': ParagraphStyle('Caption',fontName='Helvetica',fontSize=8.4,leading=12.3,textColor=MUTED,spaceBefore=6,spaceAfter=14),
 'label': ParagraphStyle('Label',fontName='Helvetica-Bold',fontSize=9,leading=13,textColor=SIGNAL,spaceAfter=8,keepWithNext=True),
 'cell': ParagraphStyle('Cell',fontName='Helvetica',fontSize=8.1,leading=11.6,textColor=INK),
 'cellh': ParagraphStyle('CellHead',fontName='Helvetica-Bold',fontSize=8.1,leading=11.6,textColor=INK),
 'code': ParagraphStyle('Formula',fontName='Courier',fontSize=8.4,leading=13,textColor=INK,spaceAfter=8),
}

def norm(s):
 for a,b in {'\u2011':'-', '\u2013':'-', '\u2014':' - ', '\u2018':"'", '\u2019':"'", '\u201c':'"', '\u201d':'"', '\u2192':' -> ', '\u2194':' <-> ', '\u2264':' <= ', '\u2265':' >= ', '\u2260':' != ', '\u2227':' and ', '\u2228':' or ', '\u00d7':' x ', '\u2026':'...', '\u00a0':' ', '\u03b1':'alpha', '\u03b2':'beta', '\u03bc':'mu', '\u03b5':'epsilon', '\u03b4':'delta', '\u03c3':'sigma', '\u2200':'forall ', '\u2208':' in ', '\u03a3':'sum', '\u21a6':' maps to ', '\u22a2':'proves ', '\u221a':'sqrt', '\u2212':'-', '\u2261':'=', '\u21d2':' implies ', '\u2205':'empty', '\u22a5':'false'}.items(): s=s.replace(a,b)
 return s.replace('\u2022', '*').replace('\u226a', '<<').replace('\u226b', '>>')

def markup(s):
 s=escape(norm(s))
 # Refer to local PDF bibliography anchors; source titles there link out.
 return re.sub(r'\[(\d+(?:\s*,\s*\d+)*)\]', lambda m: '<super>'+', '.join('<link href="#ref-'+n.strip()+'" color="#c34420">['+n.strip()+']</link>' for n in m[1].split(','))+'</super>', s)

def P(s, style='body'): return Paragraph(markup(s),ST[style])

class Diagram(Flowable):
 def __init__(self, figure, width=CW):
  Flowable.__init__(self); self.figure=figure; self.width=width
  self.cols=2; self.rows=math.ceil(len(figure['nodes'])/2)
  self.height=self.rows*120+25
 def draw(self):
  c=self.canv; gap=20; bw=(self.width-gap)/2; bh=100
  for i,node in enumerate(self.figure['nodes']):
   row,col=divmod(i,2); x=col*(bw+gap); y=self.height-18-row*120-bh
   c.setFillColor(LIGHT);c.setStrokeColor(RULE);c.roundRect(x,y,bw,bh,5,fill=1,stroke=1)
   c.setFillColor(SIGNAL);c.setFont('Helvetica-Bold',8);c.drawString(x+13,y+bh-17,f'{i+1:02d}')
   title=Paragraph(escape(norm(node['label'])),ParagraphStyle('DT',fontName='Helvetica-Bold',fontSize=9.8,leading=12,textColor=INK))
   _,th=title.wrap(bw-48,35);title.drawOn(c,x+38,y+bh-13-th)
   details=Paragraph(escape(norm(node['detail'])),ParagraphStyle('DD',fontName='Helvetica',fontSize=8.3,leading=11.8,textColor=MUTED))
   _,dh=details.wrap(bw-26,55);details.drawOn(c,x+13,y+10)
   if col==1 and i+1<len(self.figure['nodes']):
    # Continue the ordered flow across rows; connect around the right edge.
    c.setStrokeColor(SIGNAL); ax=self.width-4; ay=y-6
    c.line(ax,ay,ax,ay-10); c.line(ax,ay-10,12,ay-10); c.line(12,ay-10,12,ay-17)
    c.line(9,ay-13,12,ay-17); c.line(15,ay-13,12,ay-17)
   if col==0 and i+1<len(self.figure['nodes']):
    c.setStrokeColor(SIGNAL);c.line(x+bw+4,y+bh/2,x+bw+gap-4,y+bh/2)
    c.line(x+bw+gap-8,y+bh/2+3,x+bw+gap-4,y+bh/2);c.line(x+bw+gap-8,y+bh/2-3,x+bw+gap-4,y+bh/2)

class PaperDoc(BaseDocTemplate):
 def __init__(self,path,paper):
  super().__init__(str(path),pagesize=(W,H),leftMargin=LEFT,rightMargin=RIGHT,topMargin=TOP,bottomMargin=BOTTOM,title=paper['title'],author='; '.join(paper['authors']),subject=paper['subtitle'],pageCompression=1,invariant=1)
  self.paper=paper;self.addPageTemplates(PageTemplate('body',[Frame(LEFT,BOTTOM,CW,H-TOP-BOTTOM,id='normal')],onPage=self.page))
 def page(self,c,doc):
  c.saveState();c.setStrokeColor(RULE);c.line(LEFT,H-40,W-RIGHT,H-40)
  c.setFont('Helvetica-Bold',8);c.setFillColor(SIGNAL);c.drawString(LEFT,H-29,'MATHA LABS / RESEARCH')
  c.setFont('Helvetica',7);c.setFillColor(MUTED);c.drawRightString(W-RIGHT,H-29,'ILLUSTRATED WHITEPAPER 2.0')
  c.line(LEFT,35,W-RIGHT,35);c.setFont('Helvetica',7);c.drawString(LEFT,23,self.paper['project']+' | 16 November 2026');c.drawRightString(W-RIGHT,23,str(doc.page));c.restoreState()
 def afterFlowable(self,flowable):
  if isinstance(flowable,Paragraph) and hasattr(flowable,'toc_label'):
   text=flowable.toc_label;key=flowable.toc_key
   self.canv.bookmarkPage(key);self.canv.addOutlineEntry(text,key,0,False);self.notify('TOCEntry',(0,text,self.page,key))

def heading(title,key):
 p=P(title,'h1');p.toc_label=norm(title);p.toc_key=key;return p

def render_pdf(paper,path):
 doc=PaperDoc(path,paper);story=[]
 story += [Spacer(1,25),P('FORMAL METHODS / DECISION SYSTEMS','label'),P(paper['title'],'title'),P(paper['subtitle'],'subtitle'),P('Revanth Matha · Matha Labs\nResearch whitepaper 2.0 | Revised 16 November 2026','small'),Spacer(1,12)]
 intro=Table([[P('CENTRAL CONTRIBUTION','label')],[P(paper['contributions'][0])]],colWidths=[CW-28]);intro.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),LIGHT),('BOX',(0,0),(-1,-1),.5,RULE),('TOPPADDING',(0,0),(-1,-1),12),('BOTTOMPADDING',(0,0),(-1,-1),9),('LEFTPADDING',(0,0),(-1,-1),14),('RIGHTPADDING',(0,0),(-1,-1),14)]))
 story += [intro,Spacer(1,16),P(paper['scope'],'small'),P('Original publication: 15 November 2026 at 3:12:52 PM PST. This edition expands the paper; it does not claim a new trained model or a new clinical, municipal or financial deployment.','small'),PageBreak()]
 toc=TableOfContents();toc.levelStyles=[ParagraphStyle('TOC',fontName='Helvetica',fontSize=10,leading=18,textColor=INK,leftIndent=0,firstLineIndent=0,spaceBefore=3)]
 story += [P('Contents','h1'),toc,PageBreak(),heading('Abstract','abstract'),P(paper['abstract']),P('Keywords: '+', '.join(paper['keywords']),'small'),heading('Contributions','contributions')]
 for i,item in enumerate(paper['contributions']):story.append(P(str(i+1)+'. '+item))
 for section in paper['sections']:
  story.append(heading(section['title'],section['id']))
  for para in section['paragraphs']:story.append(P(para))
  if section.get('formula'):
   f=section['formula'];story += [P(f['expression'],'code'),P(f['explanation'],'caption')]
  if section.get('figure'):
   f=section['figure'];story += [KeepTogether([P(f['title'],'label'),Diagram(f),P(f['caption'],'caption')])]
  if section.get('table'):
   t=section['table'];n=len(t['columns']);widths=[CW/n]*n
   data=[[P(x,'cellh') for x in t['columns']]]+[[P(x,'cell') for x in row] for row in t['rows']]
   table=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT');table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),LIGHT),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),.7,RULE),('LINEBELOW',(0,1),(-1,-1),.35,RULE),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7)]))
   story += [P(t['title'],'label'),table,P(t['caption'],'caption')]
 story.append(heading('References','references'))
 for ref in paper['references']:
  title=escape(norm(ref['title'])); url=escape(ref['url'],{'"':'&quot;'})
  text=f'<a name="ref-{ref["id"]}"/>[{ref["id"]}] <link href="{url}" color="#c34420"><u>{title}</u></link>. '+escape(norm(ref['detail']))+' Accessed '+ref['accessed']+'.'
  story += [KeepTogether([Paragraph(text,ST['small'])])]
 story += [KeepTogether([Spacer(1,10),P('Reproducibility record','label'),P('Source: https://github.com/RevanthM/'+paper['project']+' | Evaluated implementation: '+paper['codeRef'],'small')])]
 doc.multiBuild(story)

def svg_figure(paper,f,path):
 width=960;cols=2;rows=math.ceil(len(f['nodes'])/2);height=rows*142+32;bw=436;gap=36;bh=120
 out=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',f'<title id="title">{escape(f["title"])}</title>',f'<desc id="desc">{escape(f["caption"])}</desc>','<rect width="960" height="100%" rx="12" fill="#111e1b"/>','<style>text{font-family:Arial,Helvetica,sans-serif}.label{fill:#f4f2ec;font-size:19px;font-weight:600}.detail{fill:#b5c4bc;font-size:16px}.num{fill:#ff8a62;font-size:14px;font-weight:700}</style>']
 for i,n in enumerate(f['nodes']):
  row,col=divmod(i,2);x=26+col*(bw+gap);y=20+row*142
  out += [f'<rect x="{x}" y="{y}" width="{bw}" height="{bh}" rx="7" fill="#182d26" stroke="#52685d"/>',f'<text class="num" x="{x+18}" y="{y+29}">{i+1:02d}</text>']
  label=textwrap.wrap(n['label'],width=35)
  for j,line in enumerate(label):out.append(f'<text class="label" x="{x+52}" y="{y+30+j*22}">{escape(line)}</text>')
  detail=textwrap.wrap(n['detail'],width=48)
  for j,line in enumerate(detail):out.append(f'<text class="detail" x="{x+18}" y="{y+64+j*20}">{escape(line)}</text>')
  if col==0 and i+1<len(f['nodes']):out.append(f'<path d="M {x+bw+7} {y+60} h 21 m -7 -6 l 7 6 -7 6" fill="none" stroke="#ff8a62" stroke-width="2"/>')
 out.append('</svg>');path.write_text('\n'.join(out)+'\n')

def markdown(p):
 s=[f'# {p["title"]}', '',p['subtitle'],'',f'**Revanth Matha · Matha Labs | Whitepaper {p["paperVersion"]} | Revised 16 November 2026**','',f'First published 15 November 2026 at 3:12:52 PM PST. Evaluated code: `{p["codeRef"]}`.','','## Abstract','',p['abstract'],'','Keywords: '+', '.join(p['keywords']),'','## Contributions','']
 s += [f'{i+1}. {v}' for i,v in enumerate(p['contributions'])]
 for sec in p['sections']:
  s += ['',f'## {sec["title"]}','']
  for para in sec['paragraphs']:s += [para,'']
  if sec.get('formula'):s += ['```text',sec['formula']['expression'],'```','',sec['formula']['explanation'],'']
  if sec.get('figure'):
   f=sec['figure'];s += [f'### {f["title"]}','',f'![{f["title"]}](figures/{p["project"]}-{f["id"]}.svg)','',f['caption'],'']
  if sec.get('table'):
   t=sec['table'];s += [f'### {t["title"]}','','| '+' | '.join(t['columns'])+' |','| '+' | '.join(['---']*len(t['columns']))+' |']
   s += ['| '+' | '.join(v.replace('|','/') for v in row)+' |' for row in t['rows']];s += ['',t['caption'],'']
 s += ['## Scope','',p['scope'],'','## References','']
 for r in p['references']:s += [f'[{r["id"]}] [{r["title"]}]({r["url"]}). {r["detail"]} Accessed {r["accessed"]}.','']
 return '\n'.join(s)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('projects',nargs='*');args=ap.parse_args()
 (DEST/'figures').mkdir(parents=True,exist_ok=True)
 for src in [ROOT/'docs/whitepaper.json']:
  p=json.loads(src.read_text());project=p['project']
  if args.projects and project not in args.projects:continue
  for sec in p['sections']:
   if sec.get('figure'):svg_figure(p,sec['figure'],DEST/'figures'/f'{project}-{sec["figure"]["id"]}.svg')
  (DEST/'whitepaper.md').write_text(markdown(p)); (DEST/'whitepaper.json').write_text(json.dumps(p,indent=2,ensure_ascii=False)+'\n'); render_pdf(p,DEST/'whitepaper.pdf')
  print(project, 'PDF bytes', (DEST/'whitepaper.pdf').stat().st_size,'words',len(markdown(p).split()))
if __name__=='__main__':main()
