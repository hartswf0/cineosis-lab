# Butter Pair: every input together. A simulated hand carries; arrow keys nudge; Enter places; a touch on the Floor places what the hand holds; Recover puts a held brick back.
import sys,json;sys.path.insert(0,'/home/claude/stack/proof');import serve
from playwright.sync_api import sync_playwright
serve.start(8847);U='http://127.0.0.1:8847/cineosis-lab/lab/wg-butter-pair.html';OUT='/home/claude/stack/proof/out9'
T128='/tmp/claude-0/-home-claude/5dcbf124-08aa-5357-a87a-ec1f490e8f81/scratchpad/t128/node_modules/three/build/three.min.js'
R={};errs=[]
def log(k,v):R[k]=v;print(k,json.dumps(v)[:400])
with sync_playwright() as p:
    b=p.chromium.launch(args=['--use-angle=swiftshader','--enable-unsafe-swiftshader']);ctx=b.new_context(viewport={'width':1280,'height':800})
    ctx.route('**/three.min.js',lambda r:r.fulfill(path=T128,content_type='text/javascript'))
    pg=ctx.new_page();pg.on('pageerror',lambda e:errs.append(str(e)));pg.goto(U+'?sim');pg.wait_for_timeout(1500);E=lambda s:pg.evaluate(s)
    # a hand lifts the butter brick and holds it still, pinched
    HOLD="""(()=>{const W=.075,D=.075,CW=W/8,CD=D/8,H0=BP.SIM.H0,P=[(4+2)*CW,(4+1)*CD,H0];BP.SIM.SCRIPTS._hold=()=>({dur:30,hands:[[{t:0,P,closed:false},{t:.5,P,closed:true},{t:30,P,closed:true}]]});BP.resetModel();BP.reset();BP.setGeo(BP.geoFromImage(BP.SIM.flash(.0015),4/3),'t');BP.RUN={sc:BP.SIM.SCRIPTS._hold(),t0:performance.now(),name:'hold',next:[],last:null};})()"""
    E(HOLD);pg.wait_for_timeout(2500)
    before=E("(()=>{const t=BP.TR.find(x=>x.grasp);return t&&{brick:t.grasp.brick,pv:t.grasp.pv}})()")
    pg.keyboard.press('ArrowLeft');pg.keyboard.press('ArrowLeft');pg.keyboard.press('ArrowUp');pg.wait_for_timeout(400)
    after=E("(()=>{const t=BP.TR.find(x=>x.grasp);return t&&t.grasp.pv})()")
    pg.keyboard.press('Enter');pg.wait_for_timeout(400)
    log('arrow keys nudge a carried brick, Enter places it',{'held':before,'after_left_left_up':after,'placed':E("BP.SCENE.bricks.find(b=>b.id==='butter')"),'last':E("BP.LOG[0]")})
    # the hand lifts again; a finger touches the Floor at (0.3, 0.2): the brick goes there
    E("BP.RUN=null");pg.wait_for_timeout(300);E(HOLD.replace("(4+2)*CW","(2+2)*CW").replace("(4+1)*CD","(1+1)*CD").replace("BP.reset();",""));pg.wait_for_timeout(2500)
    held=E("(()=>{const t=BP.TR.find(x=>x.grasp);return t&&t.grasp.brick})()")
    E("BP.floorTouch(.3,.2,true,performance.now(),'f1')");pg.wait_for_timeout(200);E("BP.floorTouch(.3,.2,false,performance.now(),'f1')");pg.wait_for_timeout(300)
    log('a hand carries, a finger places on the Floor',{'held':held,'placed':E("(id=>BP.SCENE.bricks.find(b=>b.id===id))('%s')"%held) if held else None,'last':E("BP.LOG[0]")})
    # recover: lift again, then Recover puts it back where it was
    E("BP.RUN=null");pg.wait_for_timeout(300);E(HOLD);pg.wait_for_timeout(2500)
    h2=E("(()=>{const t=BP.TR.find(x=>x.grasp);return t&&{brick:t.grasp.brick,from:t.grasp.from}})()")
    E("BP.RUN=null;BP.recover()");pg.wait_for_timeout(500)
    log('recover',{'held':h2,'after':E("({tracks:BP.TR.length,held:BP.TR.some(t=>t.grasp),brick:BP.SCENE.bricks.find(b=>b.id==='butter')})"),'log':E("BP.LOG.slice(0,2)")})
    log('errors',errs)
    json.dump(R,open(OUT+'/inputs.json','w'),indent=1);b.close()
