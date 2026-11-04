# Butter Pair: what each camera sees. The strip under the bed (diorama + two viewfinders) through state changes; the film; the phone's tag.
import sys,json,time;sys.path.insert(0,'/home/claude/stack/proof');import serve
from playwright.sync_api import sync_playwright
serve.start(8861);U='http://127.0.0.1:8861/cineosis-lab/lab/wg-butter-pair.html';OUT='/home/claude/stack/proof/out9'
T128='/tmp/claude-0/-home-claude/5dcbf124-08aa-5357-a87a-ec1f490e8f81/scratchpad/t128/node_modules/three/build/three.min.js'
R={};errs=[]
def log(k,v):R[k]=v;print(k,json.dumps(v)[:700])
SETUP="""(()=>{BP.resetModel();BP.setGeo(BP.geoFromImage(BP.SIM.flash(.0015),4/3),'t');BP.BCAM.on=true;BP.BCAM.p=Object.assign({},BP.B0);BP.BCAM.report={B_fov_deg:78,B_turn_deg:0,B_mirrored:false,used:true,lifts:0,fit_mm:{A:0,B:0,height:0},A_moved_mm:0,A_turned_deg:0};BP.GEO.L=.075;})()"""
with sync_playwright() as p:
    b=p.chromium.launch(args=['--use-angle=swiftshader','--enable-unsafe-swiftshader']);ctx=b.new_context(viewport={'width':1280,'height':800})
    ctx.route('**/three.min.js',lambda r:r.fulfill(path=T128,content_type='text/javascript'))
    pg=ctx.new_page();pg.on('pageerror',lambda e:errs.append(str(e)));pg.goto(U+'?sim');pg.wait_for_timeout(1500);E=lambda s:pg.evaluate(s)
    fl=ctx.new_page();fl.set_viewport_size({'width':844,'height':390});fl.on('pageerror',lambda e:errs.append('floor: '+str(e)));fl.goto(U+'?floor');fl.wait_for_timeout(1200);fl.evaluate("BP.PSET.done=true;FV.cam=true");pg.bring_to_front()
    E(SETUP);E("""(()=>{const H0=BP.SIM.H0,m=[.075,.0375,H0];BP.RUN={sc:{dur:30,hands:[[{t:0,P:m,closed:false},{t:4,P:m,closed:false},{t:5.5,P:[m[0],m[1],.07],closed:false},{t:10,P:[m[0],m[1],.07],closed:false},{t:11.5,P:[m[0],m[1]+.02,.44],closed:false},{t:16,P:[m[0],m[1]+.02,.44],closed:false},{t:17,P:m,closed:false},{t:30,P:m,closed:false}]]},t0:performance.now(),name:'eyes',next:[],last:null};})()""")
    states=[]
    for t,name in [(2.5,'both'),(7.4,'low'),(13.6,'high'),(19,'back')]:
        while True:
            el=E("(performance.now()-BP.RUN.t0)/1000")
            if el>=t:break
            pg.wait_for_timeout(150)
        states.append({'at':name,'health':E("BP.HEALTH.k"),'laptop':E("document.querySelector('#eyAt').textContent"),'phone':E("document.querySelector('#eyBt').textContent"),'transition':E("BP.EYES.trans&&BP.EYES.trans.to")})
        pg.screenshot(path=OUT+'/eyes-'+name+'.png')
        if name=='low':fl.screenshot(path=OUT+'/eyes-floor-tag.png')
    log('what each camera sees, through the states',states)
    E("BP.RUN=null")
    f=ctx.new_page();f.set_viewport_size({'width':1280,'height':760});f.on('pageerror',lambda e:errs.append('film: '+str(e)));f.goto(U+'?film');f.wait_for_timeout(1500)
    caps=[];want=['Two cameras','Both see it','Lower, close','Higher','Carry it','Hide the hand','Come back']
    t0=time.time()
    for w in want:
        while time.time()-t0<80 and not f.evaluate("document.querySelector('#filmCap').textContent").startswith(w):f.wait_for_timeout(150)
        f.wait_for_timeout(1300 if w in ('Lower, close','Higher','Hide the hand') else 600)
        caps.append({'caption':w,'state':f.evaluate("BP.HEALTH.k"),'laptop':f.evaluate("document.querySelector('#eyAt').textContent")[:60],'phone':f.evaluate("document.querySelector('#eyBt').textContent")[:60]})
        f.screenshot(path=OUT+'/film-'+w.split()[0].lower().strip(',')+'.png')
    log('the film',caps)
    m=ctx.new_page();m.set_viewport_size({'width':390,'height':844});m.goto(U+'?film');m.wait_for_timeout(9000);m.screenshot(path=OUT+'/film-phone.png')
    log('errors',errs);json.dump(R,open(OUT+'/eyes.json','w'),indent=1);b.close()
