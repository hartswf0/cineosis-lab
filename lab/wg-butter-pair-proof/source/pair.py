# Butter Pair: the shared hand model measured with two SIMULATED pinhole cameras (no hardware here).
import sys,json;sys.path.insert(0,'/home/claude/stack/proof');import serve
from playwright.sync_api import sync_playwright
serve.start(8820);U='http://127.0.0.1:8820/cineosis-lab/lab/wg-butter-pair.html';OUT='/home/claude/stack/proof/out7'
T128='/tmp/claude-0/-home-claude/5dcbf124-08aa-5357-a87a-ec1f490e8f81/scratchpad/t128/node_modules/three/build/three.min.js'
R={};errs=[]
with sync_playwright() as p:
    b=p.chromium.launch(args=['--use-angle=swiftshader','--enable-unsafe-swiftshader']);ctx=b.new_context(viewport={'width':1280,'height':800})
    ctx.route('**/three.min.js',lambda r:r.fulfill(path=T128,content_type='text/javascript'))
    pg=ctx.new_page();pg.on('pageerror',lambda e:errs.append(str(e)));pg.goto(U+'?sim');pg.wait_for_timeout(2000)
    E=lambda s:pg.evaluate(s)
    R["calibrate"]=E("(()=>{BP.resetModel();BP.calStart();const r=BP.measure('calibrate');return {...r,residual_mm:BP.CAL.res,centre_check_mm:BP.CAL.check,rev:BP.CAL.rev,pts:BP.CALF.pts.map(p=>({U:+(p.U*1000).toFixed(0),V:+(p.V*1000).toFixed(0),A:p.A,B:p.B}))}})()")
    def run(name,mask=None,reset=True):
        return E(f"(()=>{{BP.resetModel();{'BP.reset();' if reset else ''}return BP.measure('{name}',{{mask:{json.dumps(mask) if mask else 'null'}}});}})()")
    R['path_B_only_before_learning']=run('path',{'A':False,'B':True})
    R['path_A_only_before_learning']=run('path',{'A':True,'B':False})
    R['path_both']=run('path')
    R['learned']=E("({B_height_from_A:BP.XF.Bh.ok,A_depth_from_B:BP.XF.Av.ok})")
    R['path_B_only_after_learning']=run('path',{'A':False,'B':True})
    R['path_A_only_after_learning']=run('path',{'A':True,'B':False})
    R['handoff']=run('handoff');R['handoff_scene']=E("BP.SCENE.bricks.find(b=>b.id==='butter')")
    R['blackout']=run('blackout');R['blackout_scene']=E("BP.SCENE.bricks.find(b=>b.id==='red')")
    R['crossing']=run('crossing')
    R['gestures']=run('gestures');R['gestures_scene']=E("BP.SCENE.bricks.map(b=>[b.id,b.i,b.j,b.l,b.rot])")
    R['errors']=errs
    json.dump(R,open(OUT+'/pair.json','w'),indent=1)
    for k,v in R.items(): print(k,json.dumps(v)[:330])
    b.close()
