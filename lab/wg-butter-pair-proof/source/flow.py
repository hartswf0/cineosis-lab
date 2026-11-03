# Butter Pair: the phone's start-up in one fixed order, the laptop's join card, and the live flow view.
import sys,json;sys.path.insert(0,'/home/claude/stack/proof');import serve
from playwright.sync_api import sync_playwright
serve.start(8854);U='http://127.0.0.1:8854/cineosis-lab/lab/wg-butter-pair.html';OUT='/home/claude/stack/proof/out9'
T128='/tmp/claude-0/-home-claude/5dcbf124-08aa-5357-a87a-ec1f490e8f81/scratchpad/t128/node_modules/three/build/three.min.js'
R={};errs=[]
def log(k,v):R[k]=v;print(k,json.dumps(v)[:600])
with sync_playwright() as p:
    b=p.chromium.launch(args=['--use-angle=swiftshader','--enable-unsafe-swiftshader']);ctx=b.new_context(viewport={'width':1280,'height':800})
    ctx.route('**/three.min.js',lambda r:r.fulfill(path=T128,content_type='text/javascript'))
    pg=ctx.new_page();pg.on('pageerror',lambda e:errs.append(str(e)));pg.goto(U);pg.wait_for_timeout(1500);E=lambda s:pg.evaluate(s)
    E("BP.launchRun(BP.GO_STEPS);0");pg.wait_for_timeout(1500)
    fl=ctx.new_page();fl.set_viewport_size({'width':844,'height':390});fl.on('pageerror',lambda e:errs.append('floor: '+str(e)));fl.goto(U+'?floor');fl.wait_for_timeout(1500)
    S=lambda: fl.evaluate("({step:BP.PSET.step,overlay:!document.querySelector('#flSetup').hidden,main:document.querySelector('#fsMain').textContent,sub:document.querySelector('#fsSub').textContent.slice(0,90),button:document.querySelector('#fsBtn').hidden?null:document.querySelector('#fsBtn').textContent,alt:document.querySelector('#fsAlt').hidden?null:document.querySelector('#fsAlt').textContent})")
    seq=[];seq.append(S());fl.screenshot(path=OUT+'/setup-1-camera.png')
    pg.bring_to_front();pg.wait_for_timeout(1200);pg.screenshot(path=OUT+'/join-card.png');fl.bring_to_front()
    fl.click('#fsBtn');fl.wait_for_timeout(2500);seq.append(S());fl.screenshot(path=OUT+'/setup-1b-camera-error.png')
    fl.evaluate("FV.cam=true");fl.set_viewport_size({'width':390,'height':844});fl.wait_for_timeout(500);seq.append(S());fl.screenshot(path=OUT+'/setup-2-sideways.png')
    fl.set_viewport_size({'width':844,'height':390});fl.wait_for_timeout(500);seq.append(S());fl.screenshot(path=OUT+'/setup-3-screen.png')
    fl.click('#fsBtn');fl.wait_for_timeout(700);seq.append(dict(S(),fullscreen=fl.evaluate("!!document.fullscreenElement")));fl.screenshot(path=OUT+'/setup-4-flat.png')
    if fl.evaluate("!document.querySelector('#fsBtn').hidden"):fl.click('#fsBtn')
    fl.wait_for_timeout(700);seq.append(dict(S(),done=fl.evaluate("BP.PSET.done")))
    log('phone setup, one step at a time',seq)
    fl.evaluate("document.exitFullscreen&&document.fullscreenElement&&document.exitFullscreen()");fl.wait_for_timeout(500)
    log('after setup',{'full screen button shown':fl.evaluate("!document.querySelector('#flFS').hidden"),'rotate notice in landscape':fl.evaluate("!document.querySelector('#flRot').hidden")})
    fl.set_viewport_size({'width':390,'height':844});fl.wait_for_timeout(500);log('turned upright after setup',{'rotate notice':fl.evaluate("!document.querySelector('#flRot').hidden")});fl.screenshot(path=OUT+'/setup-rotate.png');fl.set_viewport_size({'width':844,'height':390})
    pg.bring_to_front();pg.wait_for_timeout(1500)
    log('laptop sees the phone\'s steps',E("({phone_step:BP.FREM&&BP.FREM.step,flow:BP.flowState(performance.now())})") if E("!!BP.FREM") else E("({flow:BP.flowState(performance.now())})"))
    E("document.querySelector('#flowB').click()");pg.wait_for_timeout(800);pg.screenshot(path=OUT+'/flow-live.png')
    open(OUT+'/flow-static.svg','w').write(E("BP.flowSvg(BP.flowState(performance.now()))"))
    log('errors',errs);json.dump(R,open(OUT+'/flow.json','w'),indent=1);b.close()
