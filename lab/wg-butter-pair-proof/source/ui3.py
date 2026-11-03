# Butter Pair scope: small-space calibration (A never sees the phone), the position and gesture tests, live video both ways.
import sys,json,time;sys.path.insert(0,'/home/claude/stack/proof');import serve
from playwright.sync_api import sync_playwright
serve.start(8828);U='http://127.0.0.1:8828/cineosis-lab/lab/wg-butter-pair.html';OUT='/home/claude/stack/proof/out9'
T128='/tmp/claude-0/-home-claude/5dcbf124-08aa-5357-a87a-ec1f490e8f81/scratchpad/t128/node_modules/three/build/three.min.js'
R={};errs=[]
def log(k,**v):R[k]=v;print(k,json.dumps(v)[:700])
with sync_playwright() as p:
    b=p.chromium.launch(args=['--use-angle=swiftshader','--enable-unsafe-swiftshader','--autoplay-policy=no-user-gesture-required']);ctx=b.new_context(viewport={'width':1280,'height':860})
    ctx.route('**/three.min.js',lambda r:r.fulfill(path=T128,content_type='text/javascript'))
    pg=ctx.new_page();pg.on('pageerror',lambda e:errs.append(str(e)));pg.goto(U+'?sim');pg.wait_for_timeout(1800);E=lambda s:pg.evaluate(s)
    # 1. small space: no flash. Touch-and-lift gives B its map; then the hand moves about and A learns from B
    log('small space calibration',**E("""(()=>{BP.resetModel();BP.reset();BP.CAL.A=null;BP.CAL.B=null;BP.CAL.rev=0;BP.GEO={A:null,rev:BP.GEO.rev+1,L:.09,Ln:0,Lsum:0};BP.BPAIRS.length=0;BP.APAIRS.length=0;
      BP.startTcal();BP.measure('tapcal');const Bmap=BP.CAL.B&&BP.CAL.B.src;BP.resetModel();BP.measure('path');BP.resetModel();BP.measure('path',{seed:11});const Amap=BP.CAL.A&&BP.CAL.A.src;
      const r={B_map:Bmap,A_map:Amap,pairs:BP.APAIRS.length};BP.resetModel();r.A_only=BP.measure('path',{mask:{A:true,B:false}}).rms_mm;BP.resetModel();r.B_only=BP.measure('path',{mask:{A:false,B:true}}).rms_mm;BP.resetModel();r.both=BP.measure('path').rms_mm;BP.resetModel();const h=BP.measure('handoff');r.handoff={tracks:h.track_ids,commands:h.commands,max_jump_mm:h.max_jump_mm};BP.resetModel();BP.reset();const g=BP.measure('gestures');r.gestures=g.commands;r.reg=BP.regText(performance.now());return r;})()"""))
    # 2. the tests, with a simulated hand acting out each prompt in real time
    def script(kind):
        return E("""(kind=>{const W=.15,D=.075,H0=BP.SIM.H0,st=1.8+2.0,K=[],pc=[];const steps=BP.TEST.steps;let t=0;
          steps.forEach((s,k)=>{const t0=k*st;let P=[W/2,D/2,H0],closed=false,pose,orient;if(s.dot)P=[s.dot.U,s.dot.V,H0],closed=true;
            if(s.id==='pinch')closed=true;if(s.id==='Vflat'||s.id==='Vup'){pose='V';pc.push([t0,t0+st,s.id==='Vflat'?'B':'A']);}if(s.id==='fist')pose='fist';if(s.id==='palmTop')orient='wall';
            K.push({t:t0+.05,P:k?K[K.length-1].P:P,closed:false});K.push({t:t0+.9,P,closed,pose,orient});K.push({t:t0+st-.05,P,closed,pose,orient});});
          return K.length;})('"""+kind+"""')""")
    def runtest(kind):
        E("""(kind=>{BP.resetModel();BP.reset();BP.scopeToggle(true);BP.testStart(kind);const W=.15,D=.075,H0=BP.SIM.H0,st=1.8+2.0,K=[],pc=[];
          BP.TEST.steps.forEach((s,k)=>{const t0=k*st;let P=[W/2,D/2,H0],closed=false,pose,orient;if(s.dot){P=[s.dot.U,s.dot.V,H0];closed=true;}
            if(s.id==='pinch')closed=true;if(s.id==='Vflat'||s.id==='Vup'){pose='V';pc.push([t0,t0+st,s.id==='Vflat'?'B':'A']);}if(s.id==='fist')pose='fist';if(s.id==='palmTop'){orient='wall';P=[W*.55,D*.95,.26];}
            K.push({t:t0+.05,P:k?K[K.length-1].P:P,closed:false,pose:k?K[K.length-1].pose:pose,orient:k?K[K.length-1].orient:orient});K.push({t:t0+.8,P,closed,pose,orient});K.push({t:t0+st-.02,P,closed,pose,orient});});
          BP.RUN={sc:{dur:BP.TEST.steps.length*st+.5,hands:[K],poseCam:{V:pc}},t0:performance.now(),name:'test-'+kind,next:[],last:null};})('"""+kind+"""')""")
        shot=False
        for i in range(400):
            pg.wait_for_timeout(100)
            if not shot and E("BP.TEST.on&&BP.TEST.phase==='cap'&&BP.TEST.i===1"):pg.wait_for_timeout(900);pg.screenshot(path=OUT+'/scope-'+kind+'.png');shot=True
            if not E("BP.TEST.on"):break
        pg.wait_for_timeout(300);pg.screenshot(path=OUT+'/scope-'+kind+'-report.png')
        rs=E("BP.TEST.report&&BP.TEST.report.results")
        return [{k:r[k] for k in ('id','ok')}|{'A':r['A'],'B':r['B'],'one':r['one']} for r in rs] if rs else None
    log('position test (small-space calibration)',results=runtest('positions'))
    log('gesture test',results=runtest('gestures'))
    E("BP.RUN=null")
    # 3. live video both ways: two windows, each with a synthetic camera
    lap=ctx.new_page();lap.on('pageerror',lambda e:errs.append('laptop: '+str(e)));lap.goto(U);lap.wait_for_timeout(1200)
    fl=ctx.new_page();fl.set_viewport_size({'width':844,'height':390});fl.on('pageerror',lambda e:errs.append('floor: '+str(e)));fl.goto(U+'?floor');fl.wait_for_timeout(1500)
    FAKE="""(col=>{const cv=document.createElement('canvas');cv.width=320;cv.height=240;const x=cv.getContext('2d');let k=0;(function d(){x.fillStyle=col;x.fillRect(0,0,320,240);x.fillStyle='#fff';x.fillRect((k++*3)%300,100,20,20);requestAnimationFrame(d);})();const v=document.querySelector('#vidA');v.srcObject=cv.captureStream(20);v.play();BP.HND={stop(){}};return 1;})"""
    lap.evaluate(FAKE+"('#335')");fl.evaluate(FAKE+"('#533')");fl.evaluate("BP.FV.cam=true;BP.fsend({type:'rtcwant'})")
    lap.evaluate("BP.scopeToggle(true)")
    for i in range(60):
        lap.wait_for_timeout(200)
        if lap.evaluate("BP.rtcLive()") and fl.evaluate("BP.rtcLive()"):break
    log('live video between the laptop and the Floor',laptop=lap.evaluate("({state:BP.RTC.state,size:BP.RTC.vid&&[BP.RTC.vid.videoWidth,BP.RTC.vid.videoHeight]})"),floor=fl.evaluate("({state:BP.RTC.state,size:BP.RTC.vid&&[BP.RTC.vid.videoWidth,BP.RTC.vid.videoHeight]})"),status=lap.evaluate("document.querySelector('#svBst').textContent"))
    lap.wait_for_timeout(500);lap.screenshot(path=OUT+'/scope-live.png');fl.screenshot(path=OUT+'/floor-live.png')
    log('page errors',errors=errs)
    json.dump(R,open(OUT+'/ui3.json','w'),indent=1);b.close()
