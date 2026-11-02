# Drawings tray in the film editor: real clicks, a search, a drag onto the picture, and "lift" into Source.
import sys,json;sys.path.insert(0,'/home/claude/stack/proof');import serve
from playwright.sync_api import sync_playwright
serve.start(8829);U='http://127.0.0.1:8829/cineosis-lab/lab/wg-film-test.html?nolessons';OUT='/home/claude/stack/proof/out8';import os;os.makedirs(OUT,exist_ok=True)
P={"v":3,"c":0,"g":0,"s":[["","w:wg_003",0.3667,4.3667,1,[]]],"t":[]}
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page(viewport={'width':1280,'height':800});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(U);pg.wait_for_timeout(2500);J=lambda s:pg.evaluate(s)
    J(f"STK.openFilm(STK.filmFrom({json.dumps(P)}))");pg.keyboard.press('3');pg.wait_for_timeout(800)
    print('PRE',J("[document.querySelector('#trayT').textContent,getComputedStyle(document.querySelector('#trayT')).display,document.querySelector('#trayH').textContent]"));pg.click('#trayT');pg.wait_for_timeout(400);n=J("document.querySelectorAll('#tray button[data-d]').length");head=pg.inner_text('#trayH')
    pg.fill('#q','horse');pg.keyboard.press('Enter');pg.wait_for_timeout(300);hs=J("[...document.querySelectorAll('#tray button[data-d]')].map(b=>b.dataset.d)")
    print("DBG",n,head,hs[:5]);pg.click('#tray button[data-d="horse"] img');pg.wait_for_timeout(1500);f1=J("STK.film.shots[0].figs.map(e=>[e.kind,e.slug])")
    pg.fill('#q','');pg.keyboard.press('Enter');pg.wait_for_timeout(300)
    t=pg.locator('#tray button[data-d="lion"]');t.scroll_into_view_if_needed();bb=t.bounding_box();cv=pg.locator('#cv').bounding_box()
    pg.mouse.move(bb['x']+bb['width']/2,bb['y']+bb['height']/2);pg.mouse.down();pg.mouse.move(cv['x']+cv['width']*.3,cv['y']+cv['height']*.7,steps=12);pg.mouse.up();pg.wait_for_timeout(1500)
    f2=J("STK.film.shots[0].figs.map(e=>[e.kind,e.slug,+e.keys[0].x.toFixed(2),+e.keys[0].y.toFixed(2)])");pg.screenshot(path=OUT+'/d1-drawings.png')
    hist=J("STK.H.undo.slice(-2).map(h=>h.label)")
    l=pg.locator('#tray button[data-d="ant"] .lift');l.scroll_into_view_if_needed();l.click();pg.wait_for_timeout(2000);src=[J("STK.MODE"),J("STK.SRC.src")];pg.screenshot(path=OUT+'/d2-lift-in-source.png')
    print(json.dumps({'tiles':n,'header':head,'search_horse':hs,'after_tap':f1,'after_drag':f2,'history':hist,'lift_opens':src,'errors':errs}))
    b.close()
