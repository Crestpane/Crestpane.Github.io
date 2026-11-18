import sys,os,json,collections,http.server,threading,socketserver,functools
from playwright.sync_api import sync_playwright
ROOT=sys.argv[1] if len(sys.argv)>1 else '/home/claude/site'
WIDTHS=[int(x) for x in (sys.argv[2].split(',') if len(sys.argv)>2 else ['320','390','768','1024','1440'])]
THEMES=['light','dark']
PAGES=sys.argv[3].split(',') if len(sys.argv)>3 else None
H=functools.partial(http.server.SimpleHTTPRequestHandler,directory=ROOT)
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a):pass
H=functools.partial(Q,directory=ROOT)
srv=socketserver.TCPServer(('127.0.0.1',0),H);port=srv.server_address[1]
threading.Thread(target=srv.serve_forever,daemon=True).start()
pages=[]
for d,_,fs in os.walk(ROOT):
    if '_generator' in d:continue
    for f in fs:
        if f.endswith('.html'):pages.append(os.path.relpath(os.path.join(d,f),ROOT))
pages.sort()
if PAGES:pages=[p for p in pages if p in PAGES]
JS=r'''
()=>{
const out={overflow:0,tap:[],contrast:[],line:[],clip:[],jsErr:0,aspect:[],fixedH:[],tiny:[]};
const de=document.documentElement;
out.overflow=Math.max(0,de.scrollWidth-de.clientWidth);
function lum(c){const f=v=>{v/=255;return v<=.03928?v/12.92:Math.pow((v+.055)/1.055,2.4)};return .2126*f(c[0])+.7152*f(c[1])+.0722*f(c[2])}
function parse(s){const m=s.match(/rgba?\(([^)]+)\)/);if(!m)return null;const p=m[1].split(/[ ,\/]+/).filter(Boolean).map(Number);return {r:p[0],g:p[1],b:p[2],a:p.length>3?p[3]:1}}
function bgOf(el){let e=el;let layers=[];while(e){const cs=getComputedStyle(e);const b=parse(cs.backgroundColor);if(cs.backgroundImage!=='none'&&!cs.backgroundImage.includes('gradient(')&&false){return null}
 if(b&&b.a>0){layers.push(b);if(b.a>=1)break}e=e.parentElement}
 let base={r:255,g:255,b:255};for(let i=layers.length-1;i>=0;i--){const L=layers[i];base={r:L.r*L.a+base.r*(1-L.a),g:L.g*L.a+base.g*(1-L.a),b:L.b*L.a+base.b*(1-L.a)}}return base}
const vis=el=>{const r=el.getBoundingClientRect();const cs=getComputedStyle(el);return r.width>0&&r.height>0&&cs.visibility!=='hidden'&&cs.display!=='none'&&parseFloat(cs.opacity)>0.05}
const mobile=innerWidth<=820;
// tap targets
document.querySelectorAll('a[href],button,summary,input:not([type=hidden]),select,textarea,label.opt,[role=button]').forEach(el=>{
 if(!vis(el))return;if(el.closest('.sr-only')||el.classList.contains('skip'))return;
 const r=el.getBoundingClientRect();
 // inline links inside running text are exempt (WCAG 2.5.8 inline exception)
 const cs=getComputedStyle(el);
 const inline=el.tagName==='A'&&cs.display==='inline'&&el.closest('p,li,dd');
 if(inline)return;
 if(el.type==='checkbox'||el.type==='radio'){const l=el.closest('label');if(l){const lr=l.getBoundingClientRect();if(lr.height>=44)return}}
 if(r.height<44||r.width<44){ if(r.height<44&&r.width>=44&&r.height>=36&&!mobile)return; out.tap.push((el.className||el.tagName)+' '+Math.round(r.width)+'x'+Math.round(r.height)+' '+(el.textContent||'').trim().slice(0,20))}
});
// contrast on text nodes
const w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);let n;const seen=new Set();
while(n=w.nextNode()){const t=n.textContent.trim();if(!t)continue;const el=n.parentElement;if(!el||seen.has(el))continue;seen.add(el);
 if(['SCRIPT','STYLE','NOSCRIPT'].includes(el.tagName))continue;if(!vis(el)||el.closest('[aria-hidden=true]'))continue;
 const cs=getComputedStyle(el);const fg=parse(cs.color);const bg=bgOf(el);if(!fg||!bg)continue;
 // skip elements over images/gradients
 let over=false;let e=el;while(e){const c=getComputedStyle(e);if(c.backgroundImage!=='none'){over=true;break}e=e.parentElement}
 if(over)continue;
 const a=fg.a;const f=[fg.r*a+bg.r*(1-a),fg.g*a+bg.g*(1-a),fg.b*a+bg.b*(1-a)];
 const L1=lum(f),L2=lum([bg.r,bg.g,bg.b]);const cr=(Math.max(L1,L2)+.05)/(Math.min(L1,L2)+.05);
 const size=parseFloat(cs.fontSize);const bold=parseInt(cs.fontWeight)>=700;const large=size>=24||(size>=18.66&&bold);
 const need=large?3:4.5;if(cr<need)out.contrast.push((el.className||el.tagName)+' '+cr.toFixed(2)+' '+t.slice(0,24));
 if(size<12)out.tiny.push(el.tagName+'.'+el.className+' '+size+'px '+t.slice(0,20));
}
// line length
document.querySelectorAll('main p, main li').forEach(p=>{if(!vis(p))return;const cs=getComputedStyle(p);const fs=parseFloat(cs.fontSize);const ch=p.getBoundingClientRect().width/(fs*.5);const len=p.textContent.length;if(ch>90&&len>180)out.line.push(Math.round(ch)+'ch '+(p.className||p.tagName)+' '+len)});
// text clipped horizontally
document.querySelectorAll('h1,h2,h3,p,a,button,span,li,b').forEach(el=>{if(!vis(el))return;const cs=getComputedStyle(el);if(el.scrollWidth>el.clientWidth+2&&cs.overflow!=='visible'&&cs.overflowX!=='auto'&&cs.overflowX!=='scroll'&&cs.textOverflow!=='ellipsis'&&!el.closest('.mq,.vp,.sr-only,.chrome,.skip'))out.clip.push(el.tagName+'.'+el.className+' '+el.scrollWidth+'>'+el.clientWidth)});
// sibling card image aspect
document.querySelectorAll('.bg,.fw,.pg').forEach(g=>{const rs=[...g.querySelectorAll(':scope > a .im img, :scope > a .im')].filter(vis).map(i=>{const r=i.getBoundingClientRect();return +(r.width/r.height).toFixed(2)});});
// fixed pixel heights on text blocks
document.querySelectorAll('main p,main h1,main h2,main h3,main li').forEach(el=>{const s=el.getAttribute('style')||'';if(/(^|;)\s*height:\s*\d+px/.test(s))out.fixedH.push(el.tagName+' '+s)});
return out}
'''
agg=collections.defaultdict(lambda:collections.defaultdict(list))
with sync_playwright() as p:
    b=p.chromium.launch()
    for th in THEMES:
        for w in WIDTHS:
            ctx=b.new_context(viewport={'width':w,'height':800},color_scheme=th,device_scale_factor=1)
            ctx.add_init_script(f"try{{localStorage.setItem('theme','{th}')}}catch(e){{}}")
            for pg in pages:
                page=ctx.new_page();errs=[]
                page.on('pageerror',lambda e:errs.append(str(e)));page.on('console',lambda m:errs.append(m.text) if m.type=='error' else None)
                page.goto(f'http://127.0.0.1:{port}/{pg}',wait_until='load')
                page.add_style_tag(content='*{animation:none!important;transition:none!important}.reveal,.reveal *{opacity:1!important;transform:none!important;clip-path:none!important}')
                page.wait_for_timeout(60)
                r=page.evaluate(JS)
                key=f'{th}@{w}'
                if r['overflow']>0:agg[key]['overflow'].append((pg,r['overflow']))
                for k in('tap','contrast','line','clip','tiny','fixedH'):
                    if r[k]:agg[key][k].append((pg,r[k][:4],len(r[k])))
                if errs:agg[key]['jsErr'].append((pg,errs[:2]))
                page.close()
            ctx.close()
    b.close()
summary=collections.defaultdict(lambda:collections.Counter())
for key,d in agg.items():
    for k,v in d.items():summary[k][key]=len(v)
print('pages',len(pages))
for k,v in summary.items():print(k,dict(v))
json.dump({k:{kk:vv for kk,vv in d.items()} for k,d in agg.items()},open('/home/claude/audit/browser.json','w'),ensure_ascii=False,indent=1,default=str)
