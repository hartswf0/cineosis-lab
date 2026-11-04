# Butter Pair as a game: a simulated hand builds the Stairs blueprint from the tray; free build exports LDraw;
# the failure recorder catches a lost hand, an undo right after placing, a phone error; the phone asks for full screen on a tap.
import sys,json;sys.path.insert(0,'/home/claude/stack/proof');import serve
from playwright.sync_api import sync_playwright
serve.start(8853);U='http://127.0.0.1:8853/cineosis-lab/lab/wg-butter-pair.html';OUT='/home/claude/stack/proof/out9'
T128='/tmp/claude-0/-home-claude/5dcbf124-08aa-5357-a87a-ec1f490e8f81/scratchpad/t128/node_modules/three/build/three.min.js'
R={};errs=[]
def log(k,v):R[k]=v;print(k,json.dumps(v)[:800])
SETUP="""(()=>{BP.resetModel();BP.setGeo(BP.geoFromImage(BP.SIM.flash(.0015),4/3),'t');BP.BCAM.on=true;BP.BCAM.p=Object.assign({},BP.B0);BP.BCAM.report={B_fov_deg:78,B_turn_deg:0,B_mirrored:false,used:true,lifts:0,fit_mm:{A:0,B:0,height:0},A_moved_mm:0,A_turned_deg:0};BP.GEO.L=.075;})()"""
# move a hand over a brick, pinch, carry to the target cell, open
MOVE="""((id,ti,tj,occl)=>{const W=.075,D=.075,CW=W/8,CD=D/8,H0=BP.SIM.H0,b=BP.SCENE.bricks.find(x=>x.id===id),f=b.rot?{w:b.d,d:b.w}:{w:b.w,d:b.d},ci=b.i+Math.floor(f.w/2),cj=b.j+Math.floor(f.d/2),A=[(ci+.5)*CW,(cj+.5)*CD,H0],B=[(ti+Math.floor(f.w/2)+.5)*CW,(tj+Math.floor(f.d/2)+.5)*CD,H0];
 const K=[{t:0,P:[A[0],A[1],H0+.03],closed:false},{t:.7,P:A,closed:false},{t:1.1,P:A,closed:true},{t:2.6,P:B,closed:true},{t:3.2,P:B,closed:true},{t:3.6,P:[B[0],B[1],H0+.02],closed:false},{t:4.2,P:[B[0],B[1],H0+.04],closed:false}];const sc={dur:4.3,hands:[K]};if(occl)sc.occl=occl;BP.RUN={sc,t0:performance.now(),name:'move',next:[],last:null};return 4.3;})(%s)"""
with sync_playwright() as p:
    b=p.chromium.launch(args=['--use-angle=swiftshader','--enable-unsafe-swiftshader']);ctx=b.new_context(viewport={'width':1280,'height':800})
    ctx.route('**/three.min.js',lambda r:r.fulfill(path=T128,content_type='text/javascript'))
    pg=ctx.new_page();pg.on('pageerror',lambda e:errs.append(str(e)));pg.goto(U+'?sim');pg.wait_for_timeout(1500);E=lambda s:pg.evaluate(s)
    fl=ctx.new_page();fl.set_viewport_size({'width':844,'height':390});fl.on('pageerror',lambda e:errs.append('floor: '+str(e)));fl.goto(U+'?floor');fl.wait_for_timeout(1200);pg.bring_to_front()
    log('game mode by default',E("({workshop:BP.WORK,visible_panels:[...document.querySelectorAll('aside > *')].filter(e=>e.offsetParent).map(e=>e.id||e.tagName),header:[...document.querySelectorAll('header .hb')].filter(e=>e.offsetParent).map(e=>e.textContent)})"))
    E(SETUP);E("document.querySelector('[data-a=tab-blueprint]').click()");E("BP.playStart(1)");pg.wait_for_timeout(500);pg.screenshot(path=OUT+'/game-start.png')
    bp=E("BP.BLUEPRINTS[1].parts");steps=[]
    for k,part in enumerate(bp):
        pk=E("BP.PARTS.findIndex(p=>p.w===%d&&p.d===%d&&p.c==='%s')"%(part['w'],part['d'],part['c']))
        E("BP.RUN=null");E("BP.trayAdd(%d)"%pk);pg.wait_for_timeout(250)
        nb=E("BP.SCENE.bricks[BP.SCENE.bricks.length-1]")
        d=E(MOVE%("'%s',%d,%d,null"%(nb['id'],part['i'],part['j'])));pg.wait_for_timeout(int(d*1000)+700)
        got=E("(id=>{const b=BP.SCENE.bricks.find(x=>x.id===id);return [b.i,b.j,b.l]})('%s')"%nb['id'])
        steps.append({'part':k+1,'target':[part['i'],part['j'],part['l']],'placed':got,'matched':E("BP.PLAY.matched.filter(Boolean).length")})
        if k==2:pg.screenshot(path=OUT+'/game-mid.png');fl.evaluate("FV.cam=true;FV.everHand=true");fl.wait_for_timeout(300);fl.screenshot(path=OUT+'/game-floor.png')
    E("BP.RUN=null");pg.wait_for_timeout(500);pg.screenshot(path=OUT+'/game-done.png')
    log('a simulated hand builds Stairs from the tray',{'grades':E("BP.GRADE.list"),'report':E("BP.reportCard().replace(/<[^>]+>/g,' ').replace(/\\s+/g,' ')"),'steps':steps,'play':E("({done:BP.PLAY.done,stars:BP.PLAY.stars,lifts:BP.PLAY.lifts,undos:BP.PLAY.undos,wrong:BP.PLAY.wrong,secs:Math.round(BP.PLAY.secs)})")})
    # free build and LDraw
    E("BP.playStart(null,'free')");pg.wait_for_timeout(200);E("BP.trayAdd(0);BP.trayAdd(3);BP.trayAdd(2)");pg.wait_for_timeout(300)
    log('free build, exported as LDraw',{'ldr':E("BP.toLDraw()").split('\r\n')[:8]})
    # failures: a hand lost while carrying; an undo right after a place; a phone error; a page error
    E("BP.BOX.ev.length=0");E(SETUP)
    nb=E("BP.SCENE.bricks[0]")
    E(MOVE%("'%s',%d,%d,{A:[[1.6,2.4]],B:[[1.6,2.4]]}"%(nb['id'],8,5)));pg.wait_for_timeout(5200)
    E("BP.RUN=null;BP.cancelAll()");pg.wait_for_timeout(300)
    E(MOVE%("'%s',%d,%d,null"%(nb['id'],2,1)));pg.wait_for_timeout(5000);E("BP.RUN=null");E("document.querySelector('#undoB').click()");pg.wait_for_timeout(300)
    fl.evaluate("BP.fail('page','test failure raised on the phone')");fl.evaluate("setTimeout(()=>{throw new Error('a thrown error on the phone')},0)");pg.wait_for_timeout(800)
    ev=E("BP.BOX.ev.map(e=>({kind:e.kind,sev:e.sev,msg:e.msg.slice(0,110),health:e.ctx&&e.ctx.health,seen_by:e.ctx&&e.ctx.hand&&e.ctx.hand.live,samples_before:e.before.length}))")
    log('the failure recorder',{'events':ev,'kept_across_reload':E("JSON.parse(localStorage.getItem('butter-pair-failures')||'[]').length")})
    E("document.querySelector('#failC').click()");pg.wait_for_timeout(400);pg.screenshot(path=OUT+'/fail-panel.png')
    with pg.expect_download() as dl:E("document.querySelector('#failSave').click()")
    path=dl.value.path();rep=json.load(open(path))
    log('the report file',{'keys':list(rep.keys()),'failures':len(rep['failures']),'last20s_samples':len(rep['last20s'])})
    E("document.querySelector('#failX').click()")
    # the phone: a tap asks for full screen
    fl.bring_to_front();fl.mouse.click(400,200);fl.wait_for_timeout(500)
    log('phone tap asks for the whole screen',{'fullscreen_supported':fl.evaluate("fsOK()"),'fullscreen_now':fl.evaluate("!!document.fullscreenElement")})
    # tray taps on the phone add bricks on the laptop
    pg.bring_to_front();E("BP.playStart(null,'free')");pg.wait_for_timeout(300);n0=E("BP.SCENE.bricks.length")
    fl.evaluate("BP.PSET.done=true;FV.cam=true;FV.everHand=true;document.exitFullscreen&&document.fullscreenElement&&document.exitFullscreen()");fl.wait_for_timeout(400);r=fl.evaluate("FV.tray&&FV.tray[1]&&[FV.tray[1].x/Math.min(2,devicePixelRatio||1)+10,FV.tray[1].y/Math.min(2,devicePixelRatio||1)+10]")
    if r:fl.mouse.click(r[0],r[1]);pg.wait_for_timeout(600)
    log('a tap on the phone\'s tray',{'tray_slots':fl.evaluate("(FV.tray||[]).length"),'bricks_before':n0,'after':E("BP.SCENE.bricks.length"),'added':E("BP.SCENE.bricks.slice(-1)[0]")})
    fl.screenshot(path=OUT+'/game-floor-free.png')
    E("BP.workSet&&0");log('errors',errs)
    json.dump(R,open(OUT+'/play.json','w'),indent=1);b.close()
