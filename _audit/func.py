import http.server,socketserver,threading,functools,json
from playwright.sync_api import sync_playwright
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a):pass
srv=socketserver.TCPServer(('127.0.0.1',0),functools.partial(Q,directory='/home/claude/site'));port=srv.server_address[1]
threading.Thread(target=srv.serve_forever,daemon=True).start()
B=f'http://127.0.0.1:{port}/'
res={}
with sync_playwright() as p:
    b=p.chromium.launch()
    # focus visibility over 40 tabs
    pg=b.new_page(viewport={'width':1280,'height':800});pg.goto(B+'index.html');bad=[];n=0
    for i in range(45):
        pg.keyboard.press('Tab')
        r=pg.evaluate('''()=>{const e=document.activeElement;if(!e||e===document.body)return null;const cs=getComputedStyle(e);const vis=(cs.outlineStyle!=='none'&&parseFloat(cs.outlineWidth)>=2)||cs.boxShadow!=='none';return [e.tagName+'.'+e.className,vis,e.getBoundingClientRect().width>0]}''')
        if r and r[2]:
            n+=1
            if not r[1]:bad.append(r[0])
    res['focus_checked']=n;res['focus_without_ring']=bad[:5]
    # reduced motion
    ctx=b.new_context(reduced_motion='reduce',viewport={'width':1280,'height':800});pg=ctx.new_page();pg.goto(B+'index.html');pg.wait_for_timeout(300)
    res['reduced_motion_hidden_reveals']=pg.evaluate("[...document.querySelectorAll('.reveal')].filter(e=>getComputedStyle(e).opacity<1).length")
    # card aspect ratios
    pg=b.new_page(viewport={'width':1280,'height':800});pg.goto(B+'insights/index.html');pg.wait_for_timeout(300)
    res['blog_img_ratios']=pg.evaluate("[...new Set([...document.querySelectorAll('#bgrid .ac .im')].filter(e=>e.offsetWidth).map(e=>(e.offsetWidth/e.offsetHeight).toFixed(2)))]")
    # empty state + reset (blog)
    pg.fill('#bs','zzzzqq');pg.wait_for_timeout(200)
    res['blog_empty_shown']=pg.evaluate("document.querySelector('#bempty').classList.contains('show')")
    pg.click('#bempty [data-reset]');pg.wait_for_timeout(200)
    res['blog_after_reset_visible']=pg.evaluate("[...document.querySelectorAll('#bgrid .ac')].filter(e=>e.offsetParent).length")
    pg=b.new_page(viewport={'width':1280,'height':800});pg.goto(B+'portfolio.html');pg.fill('#ps','zzzz');pg.wait_for_timeout(200)
    res['portfolio_empty']=pg.evaluate("document.querySelector('#pempty').classList.contains('show')")
    pg.click('#pempty [data-reset]');pg.wait_for_timeout(200)
    res['portfolio_after_reset']=pg.evaluate("[...document.querySelectorAll('#pgrid .pj')].filter(e=>e.offsetParent).length")
    # form flow with mocked FormSubmit
    ctx=b.new_context(viewport={'width':390,'height':800});pg=ctx.new_page()
    pg.route('https://formsubmit.co/**',lambda r:r.fulfill(status=200,content_type='application/json',body='{"success":"true"}'))
    pg.goto(B+'contact.html');pg.wait_for_timeout(2800)
    pg.fill('input[name=Name]','Test');pg.fill('input[name=Email]','a@b.co');pg.fill('textarea[name=Message]','Hello there');
    pg.click('form[data-brief] button[type=submit]');pg.wait_for_timeout(900)
    res['form_success_url']=pg.url.replace(B,'')
    res['thanks_h1']=pg.inner_text('h1')
    # failure path
    pg=ctx.new_page();pg.route('https://formsubmit.co/**',lambda r:r.abort())
    pg.goto(B+'contact.html');pg.wait_for_timeout(2800)
    pg.fill('input[name=Name]','Test');pg.fill('input[name=Email]','a@b.co');pg.fill('textarea[name=Message]','Hello there');
    pg.click('form[data-brief] button[type=submit]');pg.wait_for_timeout(900)
    res['form_failure_fallback']=pg.evaluate("document.querySelector('.stat.warn.show')?document.querySelector('.stat.warn.show').innerText.slice(0,70):None")
    res['form_busy_cleared']=pg.evaluate("!document.querySelector('form').hasAttribute('aria-busy')")
    # nav parent state
    pg=b.new_page(viewport={'width':1280,'height':800});pg.goto(B+'services/website-redesign.html')
    res['services_parent_marked']=pg.evaluate("!!document.querySelector('.dd.cur-sec')")
    res['mega_items']=pg.evaluate("document.querySelectorAll('.mega:not(.sm2) li:not(.all) a').length")
    # new-tab announcements
    res['newtab_unannounced']=pg.evaluate("[...document.querySelectorAll('a[target=_blank]')].filter(a=>!(a.textContent+a.getAttribute('aria-label')).toLowerCase().includes('new tab')).length")
    res['data_cta_count']=pg.evaluate("document.querySelectorAll('[data-cta]').length")
    # estimator still works + email href
    pg.goto(B+'pricing.html');pg.wait_for_timeout(300)
    res['calc_total']=pg.inner_text('#tp');res['email_href']=pg.get_attribute('#cm','href')[:40]
    # theme toggle persists
    pg.click('.th');res['theme_after_click']=pg.evaluate("document.documentElement.dataset.theme")
    b.close()
for k,v in res.items():print(k,'=',v)
