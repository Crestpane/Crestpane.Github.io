import os,re,sys,json,collections
from html.parser import HTMLParser
ROOT=sys.argv[1] if len(sys.argv)>1 else '/home/claude/site'
pages=[]
for d,_,fs in os.walk(ROOT):
    if '_generator' in d or '__pycache__' in d: continue
    for f in fs:
        if f.endswith('.html'): pages.append(os.path.relpath(os.path.join(d,f),ROOT))
pages.sort()
class P(HTMLParser):
    def __init__(s):
        super().__init__();s.imgs=[];s.links=[];s.h=[];s.title='';s.in_t=False;s.meta={};s.buttons=[];s.cur=None;s.linktext={};s.stack=[];s.canon=None;s.ids=set();s.forms=[];s.inputs=[];s.labels=set()
    def handle_starttag(self,t,a):
        a=dict(a)
        if 'id' in a:self.ids.add(a['id'])
        if t=='title':self.in_t=True
        if t=='meta':
            k=a.get('name') or a.get('property')
            if k:self.meta[k]=a.get('content','')
        if t=='link' and a.get('rel')=='canonical':self.canon=a.get('href')
        if t=='img':self.imgs.append(a)
        if t=='a':
            self.cur={'href':a.get('href'),'text':'','attrs':a};self.links.append(self.cur)
        if t in 'h1 h2 h3 h4 h5 h6'.split():self.h.append(int(t[1]));self.cur_h=t
        if t=='label' and a.get('for'):self.labels.add(a['for'])
        if t in('input','select','textarea'):self.inputs.append(a)
    def handle_endtag(self,t):
        if t=='title':self.in_t=False
        if t=='a':self.cur=None
    def handle_data(self,d):
        if self.in_t:self.title+=d
        if self.cur is not None:self.cur['text']+=d
res=collections.defaultdict(list)
titles=collections.defaultdict(list);descs=collections.defaultdict(list)
allids={}
for p in pages:
    s=open(os.path.join(ROOT,p),encoding='utf8').read()
    q=P();q.feed(s);allids[p]=q.ids
    titles[q.title].append(p);descs[q.meta.get('description','')].append(p)
    if len(q.title)>65:res['P28 title>65'].append((p,len(q.title)))
    dl=len(q.meta.get('description',''))
    if dl<70 or dl>165:res['P28 desc length'].append((p,dl))
    if q.h.count(1)!=1:res['P29 h1 count'].append((p,q.h.count(1)))
    for a,b in zip(q.h,q.h[1:]):
        if b-a>1:res['P29 skipped heading'].append((p,f'h{a}->h{b}'));break
    for im in q.imgs:
        if 'alt' not in im:res['P30 missing alt'].append((p,im.get('src')))
        if not im.get('width') or not im.get('height'):res['P32 img no dims'].append((p,im.get('src')))
        if im.get('alt','x')!='' and re.search(r'(image|picture|photo) of',im.get('alt',''),re.I):res['P30 alt wording'].append((p,im.get('alt')))
    if not q.meta.get('og:image') or not q.meta.get('twitter:card'):res['SEO og/twitter'].append(p)
    if 'twitter:title' not in q.meta:res['SEO twitter:title missing'].append(p)
    if 'og:image:alt' not in q.meta:res['SEO og:image:alt missing'].append(p)
    if 'color-scheme' not in q.meta:res['meta color-scheme missing'].append(p)
    for l in q.links:
        h=l['href'];t=' '.join(l['text'].split()).lower()
        if h is None or h in('','#'):res['P39 empty href'].append((p,t))
        if t in('here','click here','read more','more','learn more','link'):res['P27 generic link'].append((p,t))
        if h and l['attrs'].get('target')=='_blank' and 'noopener' not in l['attrs'].get('rel',''):res['ext noopener'].append((p,h))
        if h and l['attrs'].get('target')=='_blank' and 'new tab' not in (l['attrs'].get('aria-label','')+t).lower():res['P18 new-tab not announced'].append((p,h))
        if h and not re.match(r'(https?:|mailto:|tel:|#|javascript:)',h):
            path=h.split('#')[0].split('?')[0]
            if path:
                tgt=os.path.normpath(os.path.join(ROOT,os.path.dirname(p),path))
                if not os.path.exists(tgt):res['P39 broken link'].append((p,h))
    for i in q.inputs:
        if i.get('type') in('hidden','submit','checkbox','radio','search') and False:continue
        if i.get('type')=='hidden':continue
        if i.get('id') not in q.labels and 'aria-label' not in i and i.get('type') not in('checkbox','radio'):res['form unlabeled'].append((p,i.get('name')))
for t,ps in titles.items():
    if len(ps)>1:res['P28 duplicate title'].append(ps)
for t,ps in descs.items():
    if len(ps)>1:res['P28 duplicate desc'].append(ps)
out={k:v for k,v in res.items()}
print('pages',len(pages))
for k,v in sorted(out.items()):print(f'{k}: {len(v)}',v[:3])
json.dump(out,open('/home/claude/audit/static.json','w'),ensure_ascii=False,indent=1)
