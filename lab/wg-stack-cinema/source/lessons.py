# The six lessons, done the way a new person would: real mouse and keyboard; SIMULATED hands for step 6; the Floor in a second window.
import sys,json,time;sys.path.insert(0,'/home/claude/stack/proof');import serve
from playwright.sync_api import sync_playwright
serve.start(8818);U='http://127.0.0.1:8818/cineosis-lab/lab/wg-film-test.html';OUT='/home/claude/stack/proof/out6';R=[];errs=[]
def log(step,**k):R.append(dict(step=step,**k));print(step,json.dumps(k)[:240])
def until(f,ms=8000):
    t=time.time()
    while time.time()-t<ms/1000:
        try:
            if f(): return round((time.time()-t)*1000)
        except Exception: pass
        time.sleep(.05)
    return None
with sync_playwright() as p:
    b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required']);ctx=b.new_context(viewport={'width':1280,'height':800})
    pg=ctx.new_page();pg.on('pageerror',lambda e:errs.append(str(e)));pg.goto(U);J=lambda s:pg.evaluate(s)
    vis=until(lambda:J("!document.querySelector('#coach').hidden"),5000);pg.screenshot(path=OUT+'/l0-coach.png')
    step=lambda:pg.inner_text('#coachN')
    log('first visit: the lessons open by themselves',shown_after_ms=vis,card=step(),title=pg.inner_text('#coachT'))
    pg.keyboard.press('1');pg.wait_for_timeout(500);pg.locator('#wall .wt[data-s="w:wg_003"]').scroll_into_view_if_needed();pg.click('#wall .wt[data-s="w:wg_003"] img')
    ms=until(lambda:'2 OF' in step());pg.wait_for_timeout(1200);pg.screenshot(path=OUT+'/l1-picked.png');log('1 pick a clip (archive, one tap)',advanced_ms=ms,src=J("STK.SRC.src"))
    pg.click('#sIns');ms=until(lambda:'3 OF' in step());log('2 put it in the film (+ with no marks)',advanced_ms=ms,take=J("STK.film.shots.map(s=>[s.take.src,s.take.in,s.take.out])"))
    pg.keyboard.press('1');pg.wait_for_timeout(400);pg.locator('#wall .wt[data-s="shm:giraffe-walks-past"]').scroll_into_view_if_needed();pg.click('#wall .wt[data-s="shm:giraffe-walks-past"] img');pg.wait_for_timeout(1500)
    gx,gy=J("(()=>{const a=STK.SB,r=document.querySelector('#cv').getBoundingClientRect();return [r.x+(a.x+a.w*.25)/STK.dpr,r.y+(a.y+a.h*.62)/STK.dpr]})()")
    fx,fy=J("(()=>{const a=STK.FB,r=document.querySelector('#cv').getBoundingClientRect();return [r.x+(a.x+a.w*.5)/STK.dpr,r.y+(a.y+a.h*.85)/STK.dpr]})()")
    pg.mouse.move(gx,gy);pg.mouse.down();pg.mouse.move(fx,fy,steps=14);pg.wait_for_timeout(200);pg.screenshot(path=OUT+'/l2-carry.png');pg.mouse.up()
    ms=until(lambda:'4 OF' in step());log('3 lift a cutout (press, carry, let go)',advanced_ms=ms,history=J("STK.H.undo.slice(-1)[0].label"))
    pg.keyboard.press('3');pg.wait_for_timeout(600)
    pt=J("(()=>{const b=STK.BOXES.find(x=>x.e.kind==='mfig');if(!b)return null;const r=document.querySelector('#cv').getBoundingClientRect(),[x,y,w,h]=b.r;return [r.x+(STK.box.x+x+w/2)/STK.dpr,r.y+(STK.box.y+y+h*.6)/STK.dpr]})()")
    if pt:
        pg.mouse.move(*pt);pg.mouse.down();pg.mouse.move(pt[0]-80,pt[1],steps=8);pg.mouse.up();pg.wait_for_timeout(300)
    pg.keyboard.press('r');pg.keyboard.press('r');pg.wait_for_timeout(300);pg.screenshot(path=OUT+'/l3-turned.png')
    ms=until(lambda:'5 OF' in step());log('4 move it, turn it (drag, R)',advanced_ms=ms,keys=J("(()=>{const e=STK.film.shots.flatMap(s=>s.figs).find(e=>e.kind==='mfig');return e&&e.keys})()"),last=J("STK.H.undo.slice(-3).map(h=>h.label)"))
    pg.keyboard.press(' ');ms=until(lambda:'6 OF' in step());pg.keyboard.press(' ');log('5 watch it (Space)',advanced_ms=ms)
    # step 6: the joint hand space, with the Floor as a second window and simulated hands on both
    pg.keyboard.press('2');pg.wait_for_timeout(300)
    f=ctx.new_page();f.set_viewport_size({'width':844,'height':390});f.on('pageerror',lambda e:errs.append('floor: '+str(e)));f.goto(U+'?floor');pg.bring_to_front()
    H=lambda t:pg.evaluate("t=>STK.simHands(t)",t);FH=lambda t:f.evaluate("t=>STK.floorHands(t)",t)
    until(lambda:J("STK.floors().length")>0,8000)
    H([{'id':'Right','x':gx+40,'y':gy-80,'closed':False,'pose':'open'}]);pg.wait_for_timeout(300);H([{'id':'Right','x':gx,'y':gy,'closed':False,'pose':'open'}]);H([{'id':'Right','x':gx,'y':gy,'closed':True,'pose':'pinch'}]);pg.wait_for_timeout(300)
    H([]);pg.wait_for_timeout(450);H([]);until(lambda:f.evaluate("!!STK.FLs.hold"))
    FH([{'id':'Right','x':400,'y':250,'closed':False,'pose':'open'}]);f.wait_for_timeout(200)
    FH([{'id':'Right','x':400,'y':250,'closed':True,'pose':'pinch'}]);f.wait_for_timeout(200);FH([{'id':'Right','x':420,'y':300,'closed':True,'pose':'pinch'}]);f.wait_for_timeout(300)
    checks=J("[...document.querySelectorAll('#coachC li')].map(l=>[l.textContent,l.classList.contains('ok')])");pg.screenshot(path=OUT+'/l4-two-cameras.png')
    FH([{'id':'Right','x':420,'y':300,'closed':False,'pose':'open'}]);ms=until(lambda:'DONE' in step())
    pg.wait_for_timeout(300);pg.screenshot(path=OUT+'/l5-done.png')
    log('6 two cameras, one hand (calibration checks)',checks=checks,finished_ms=ms,history=J("STK.H.undo.slice(-1)[0].label"))
    pg.reload();pg.wait_for_timeout(2500);log('after finishing, a reload does not reopen the lessons',coach_hidden=J("document.querySelector('#coach').hidden"))
    log('page errors',errors=errs);json.dump(R,open(OUT+'/lessons.json','w'),indent=1);b.close()
