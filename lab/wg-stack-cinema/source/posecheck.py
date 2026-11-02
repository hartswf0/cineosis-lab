# One key, seek by clicking the strip inside the same shot, drag the figure: a second pose is added and the figure stays selected.
import sys,json;sys.path.insert(0,'/home/claude/stack/proof');import serve
from playwright.sync_api import sync_playwright
serve.start(8812)
P={"v":3,"c":0,"g":0,"s":[["","w:wg_003",0.3667,4.3667,1,[["m:shm:giraffe-walks-past|0|4.125|136",0.62,0,0,4,[[0,0.5,0.86,0.3]]]]]],"t":[]}
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page(viewport={'width':1280,'height':800})
    pg.goto('http://127.0.0.1:8812/cineosis-lab/lab/wg-film-test.html');pg.wait_for_timeout(2500)
    pg.evaluate("p=>{STK.openFilm(STK.filmFrom(p));STK.setMode('shot');}",P);pg.wait_for_timeout(800)
    fid=pg.evaluate("STK.film.shots[0].figs[0].id")
    pg.locator('#chips button[data-k="%s"]'%fid).click();pg.wait_for_timeout(200)
    r=pg.evaluate("(()=>{const s=document.querySelector('#strip')||document.querySelector('canvas');return null})()")
    # click the strip 3/4 along the only shot
    bx=pg.evaluate("(()=>{const e=document.querySelector('#strip');const r=e.getBoundingClientRect();return [r.x,r.y,r.width,r.height]})()")
    pg.mouse.click(bx[0]+bx[2]*0.75,bx[1]+bx[3]*0.5);pg.wait_for_timeout(300)
    sel=pg.evaluate("STK.SEL");t=pg.evaluate("STK.T")
    pt=pg.evaluate("(()=>{const e=STK.film.shots[0].figs[0];const b=STK.BOXES.find(x=>x.e===e);const cr=document.querySelector('#cv').getBoundingClientRect();const d=STK.dpr,bx=STK.box;const [x,y,w,h]=b.r;return [cr.x+(bx.x+x+w/2)/d,cr.y+(bx.y+y+h*0.6)/d]})()")
    pg.mouse.move(*pt);pg.mouse.down();
    for i in range(1,11): pg.mouse.move(pt[0]-12*i,pt[1],steps=1);pg.wait_for_timeout(16)
    pg.screenshot(path='out3/pose-during.png');pg.mouse.up();pg.wait_for_timeout(200)
    k=pg.evaluate("STK.film.shots[0].figs[0].keys");h=pg.evaluate("STK.H.undo.map(x=>x.label)")
    print('keys',k);print('history',h[-1:])
    b.close()
