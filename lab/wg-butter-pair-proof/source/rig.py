# Rig: the setup model. Pose against the simulator's camera; verdicts for typical setups; a phone measuring the screen angle.
import sys,json;sys.path.insert(0,'/home/claude/stack/proof');import serve
from playwright.sync_api import sync_playwright
serve.start(8830);B='http://127.0.0.1:8830/cineosis-lab/lab/';OUT='/home/claude/stack/proof/out9'
T128='/tmp/claude-0/-home-claude/5dcbf124-08aa-5357-a87a-ec1f490e8f81/scratchpad/t128/node_modules/three/build/three.min.js'
R={};errs=[]
def log(k,v):R[k]=v;print(k,json.dumps(v)[:600])
with sync_playwright() as p:
    b=p.chromium.launch(args=['--use-angle=swiftshader','--enable-unsafe-swiftshader']);ctx=b.new_context(viewport={'width':1280,'height':820})
    ctx.route('**/three.min.js',lambda r:r.fulfill(path=T128,content_type='text/javascript'))
    rg=ctx.new_page();rg.on('pageerror',lambda e:errs.append('rig: '+str(e)));rg.on('console',lambda m:m.type=='error' and errs.append('rig console: '+m.text));rg.goto(B+'wg-butter-pair-rig.html');rg.wait_for_timeout(1500)
    G=lambda s:rg.evaluate(s)
    # a typical laptop: screen at 110°, Floor 20 cm in front
    G("RIG.P=Object.assign(RIG.P,{setup:'laptop',gap:20,open:110,scr:14,base:22,off:0,fov:62,turn:0})");rg.wait_for_timeout(400)
    log('typical laptop',G("(()=>{const c=RIG.coverage(RIG.camA(),RIG.camB());return {verdict:document.querySelector('#verdict').innerText,fixes:[...document.querySelectorAll('#fix button')].map(b=>b.innerText),corners:c.corners,best:c.best,band:c.band}})()"))
    rg.screenshot(path=OUT+'/rig-laptop.png')
    # apply the first fix
    G("document.querySelector('#fix button')&&document.querySelector('#fix button').click()");rg.wait_for_timeout(400)
    log('after the first suggested fix',G("({open:RIG.P.open,gap:RIG.P.gap,verdict:document.querySelector('#verdict').innerText})"))
    rg.screenshot(path=OUT+'/rig-fixed.png')
    # the simulator's camera A as a wall/stand camera: 27 cm up, 43.75 cm from the Floor's middle, 18.6° down
    G("RIG.P=Object.assign(RIG.P,{setup:'wall',wh:27,wd:43.75,wt:18.6,off:0,fov:62,turn:0})");rg.wait_for_timeout(300)
    log('wall preset as the simulator camera',G("(()=>{const c=RIG.camA(),p=RIG.poseOf(c);return {C:p.C.map(x=>Math.round(x*1000)),f:+p.f.toFixed(3),fwd:c.f.map(x=>+x.toFixed(3)),verdict:document.querySelector('#verdict').innerText}})()"))
    G("setView('side')");rg.wait_for_timeout(300);rg.screenshot(path=OUT+'/rig-wall-side.png')
    # Butter Pair uses the rig: compare its pose with the simulator's own camera, then measure
    bp=ctx.new_page();bp.on('pageerror',lambda e:errs.append('bp: '+str(e)));bp.goto(B+'wg-butter-pair.html?sim');bp.wait_for_timeout(1500)
    G("document.querySelector('#saveB').click()");bp.wait_for_timeout(500)
    log('Butter Pair took the rig',bp.evaluate("""(()=>{const g=BP.GEO.A;if(!g)return null;const t=BP.geoFromImage(BP.SIM.flash(0),4/3);BP.resetModel();BP.reset();const r=BP.measure('path',{mask:{A:true,B:false}});return {src:g.src,C:g.C.map(x=>Math.round(x*1000)),true_C:t.C.map(x=>Math.round(x*1000)),axis_angle_deg:+(Math.acos(Math.min(1,g.R[0][2]*t.R[0][2]+g.R[1][2]*t.R[1][2]+g.R[2][2]*t.R[2][2]))*180/Math.PI).toFixed(2),A_only_path_mm:r.rms_mm,reg:BP.regText(performance.now())}})()"""))
    # a phone measures the screen angle: it lies against a screen opened to 115°, so its own screen is 65° from level
    ph=ctx.new_page();ph.set_viewport_size({'width':390,'height':780});ph.on('pageerror',lambda e:errs.append('phone: '+str(e)));ph.goto(B+'wg-butter-pair-rig.html?phone');ph.wait_for_timeout(1000)
    G("RIG.P=Object.assign(RIG.P,{setup:'laptop'})")
    ph.evaluate("(()=>{document.querySelector('#sensB').click();})()");ph.wait_for_timeout(300)
    ph.evaluate("window.dispatchEvent(Object.assign(new Event('deviceorientation'),{beta:65,gamma:0,alpha:0}))");ph.wait_for_timeout(200)
    ph.click('[data-m=screen]');ph.wait_for_timeout(600)
    log('phone measures the screen',{'laptop_open':G("RIG.P.open"),'phone_status':ph.evaluate("document.querySelector('#phStatus').innerText"),'laptop_note':G("document.querySelector('#meas').innerText")})
    ph.screenshot(path=OUT+'/rig-phone.png')
    # the Floor shows the band and where camera A is
    fl=ctx.new_page();fl.set_viewport_size({'width':844,'height':390});fl.on('pageerror',lambda e:errs.append('floor: '+str(e)));fl.goto(B+'wg-butter-pair.html?floor');fl.wait_for_timeout(1500)
    bp2=ctx.new_page();bp2.goto(B+'wg-butter-pair.html');bp2.wait_for_timeout(800)
    G("RIG.P=Object.assign(RIG.P,{setup:'laptop',gap:20,open:100,scr:14,base:22,off:0,fov:62,turn:0});document.querySelector('#saveB').click()");fl.wait_for_timeout(1500)
    log('the Floor knows where camera A is',fl.evaluate("(v=>v&&{band:v.band,aCam:v.aCam})(BP.FV.view)"))
    fl.screenshot(path=OUT+'/rig-floor.png');G("setView('three')");rg.wait_for_timeout(300);rg.screenshot(path=OUT+'/rig-laptop100.png')
    log('errors',[e for e in errs if 'ERR_TUNNEL' not in e])
    json.dump(R,open(OUT+'/rig.json','w'),indent=1);b.close()
