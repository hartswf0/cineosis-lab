import sys,json,time;sys.path.insert(0,'/home/claude/stack/proof');import serve
from playwright.sync_api import sync_playwright
serve.start(8830);U='http://127.0.0.1:8830/cineosis-lab/lab/wg-butter-pair.html';OUT='/home/claude/stack/proof/out7'
T128='/tmp/claude-0/-home-claude/5dcbf124-08aa-5357-a87a-ec1f490e8f81/scratchpad/t128/node_modules/three/build/three.min.js'
with sync_playwright() as p:
    b=p.chromium.launch(args=['--use-angle=swiftshader','--enable-unsafe-swiftshader']);ctx=b.new_context(viewport={'width':1280,'height':800});ctx.route('**/three.min.js',lambda r:r.fulfill(path=T128,content_type='text/javascript'))
    pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.goto(U);fl=ctx.new_page();fl.set_viewport_size({'width':844,'height':390});fl.goto(U+'?floor');pg.bring_to_front();pg.wait_for_timeout(1500)
    pg.evaluate("BP.resetModel();BP.calStart();BP.measure('calibrate');BP.resetModel();BP.reset();BP.RUN={sc:BP.SIM.SCRIPTS.palms(),t0:performance.now(),name:'palms',next:[],last:null};document.querySelector('#sim').hidden=false;")
    def wait(k):
        t=time.time()
        while time.time()-t<15:
            if pg.evaluate("BP.CONSTR&&BP.CONSTR.kind")==k and pg.evaluate("BP.TR.some(t=>t.state==='carrying')"): return True
            time.sleep(.05)
    wait('floor');pg.screenshot(path=OUT+'/p1-palm-floor.png');fl.screenshot(path=OUT+'/p1-floor.png')
    wait('top');pg.screenshot(path=OUT+'/p2-palm-top.png');fl.screenshot(path=OUT+'/p2-floor.png')
    print(errs,pg.evaluate("BP.LOG.slice(0,6).reverse()"));b.close()
