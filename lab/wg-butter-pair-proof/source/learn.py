# Butter Pair: Learn (each control as a graded drill, with a simulated hand), Challenges (properties, many answers), grades on placements.
import sys,json,time;sys.path.insert(0,'/home/claude/stack/proof');import serve
from playwright.sync_api import sync_playwright
serve.start(8857);U='http://127.0.0.1:8857/cineosis-lab/lab/wg-butter-pair.html';OUT='/home/claude/stack/proof/out9'
T128='/tmp/claude-0/-home-claude/5dcbf124-08aa-5357-a87a-ec1f490e8f81/scratchpad/t128/node_modules/three/build/three.min.js'
R={};errs=[]
def log(k,v):R[k]=v;print(k,json.dumps(v)[:700])
SETUP="""(()=>{BP.resetModel();BP.setGeo(BP.geoFromImage(BP.SIM.flash(.0015),4/3),'t');BP.BCAM.on=true;BP.BCAM.p=Object.assign({},BP.B0);BP.BCAM.report={B_fov_deg:78,B_turn_deg:0,B_mirrored:false,used:true,lifts:0,fit_mm:{A:0,B:0,height:0},A_moved_mm:0,A_turned_deg:0};BP.GEO.L=.075;})()"""
# a simulated hand for each drill, built from the drill's own scene and outline
HAND="""((id)=>{const H0=BP.SIM.H0,CW=.075/8,CD=.075/8,cen=(i,j,l)=>[(i+.5)*CW,(j+.5)*CD,H0+.0096*(l||0)],sk=BP.SKILLS.find(s=>s.id===id),b=BP.SCENE.bricks[0],f=b?(b.rot?{w:b.d,d:b.w}:{w:b.w,d:b.d}):null,A=b?cen(b.i+Math.floor(f.w/2),b.j+Math.floor(f.d/2)):[.075,.0375,H0];let K,K2=null,pc=null,oc=null;
 const carry=(g,extra)=>{const B=cen(g.i+Math.floor(f.w/2),g.j+Math.floor(f.d/2),0);return [{t:0,P:[A[0],A[1],H0+.03],closed:false},{t:.8,P:A,closed:false},{t:1.2,P:A,closed:true},{t:3,P:B,closed:true},{t:3.4+(extra||0),P:B,closed:true},{t:3.8+(extra||0),P:[B[0],B[1],H0+.02],closed:false},{t:20,P:[B[0],B[1],H0+.03],closed:false}];};
 if(id==='see')K=[{t:0,P:[.075,.0375,H0],closed:false},{t:20,P:[.075,.0375,H0],closed:false}];
 else if(id==='pinch'){K=[{t:0,P:A,closed:false}];let t=.6;for(let k=0;k<3;k++){K.push({t:t+=.5,P:A,closed:false},{t:t+=.05,P:A,closed:true},{t:t+=.6,P:A,closed:true},{t:t+=.05,P:A,closed:false});}K.push({t:20,P:A,closed:false});}
 else if(id==='lift')K=[{t:0,P:[A[0],A[1],H0+.03],closed:false},{t:.8,P:A,closed:false},{t:1.2,P:A,closed:true},{t:20,P:A,closed:true}];
 else if(id==='across'||id==='depth'||id==='stack')K=carry(sk.ghost[0]);
 else if(id==='turn'){const B=cen(6,3,0);K=[{t:0,P:[A[0],A[1],H0+.03],closed:false},{t:.8,P:A,closed:false},{t:1.2,P:A,closed:true},{t:3,P:B,closed:true},{t:4.6,P:B,closed:true},{t:5,P:[B[0],B[1],H0+.02],closed:false},{t:20,P:[B[0],B[1],H0+.03],closed:false}];setTimeout(()=>window.dispatchEvent(new KeyboardEvent('keydown',{key:'r'})),2600);}
 else if(id==='copy'){K=[{t:0,P:A,closed:false,pose:'V'},{t:20,P:A,closed:false,pose:'V'}];pc={V:[[0,20,'B']]};}
 else if(id==='undo'){K=[{t:0,P:A,closed:false,pose:'fist'},{t:20,P:A,closed:false,pose:'fist'}];}
 else if(id==='lock'){K=[{t:0,P:[A[0],A[1],H0+.03],closed:false},{t:.8,P:A,closed:false},{t:1.2,P:A,closed:true},{t:20,P:A,closed:true}];const O=[-.02,.075*.5,H0];K2=[{t:0,P:O,closed:false,label:'Left'},{t:20,P:O,closed:false,label:'Left'}];}
 else if(id==='pause'){K=[{t:0,P:[A[0],A[1],H0+.03],closed:false},{t:.8,P:A,closed:false},{t:1.2,P:A,closed:true},{t:2.2,P:A,closed:true},{t:4.4,P:A,closed:false},{t:4.9,P:A,closed:true},{t:6,P:cen(10,4),closed:true},{t:6.4,P:cen(10,4),closed:false},{t:20,P:cen(10,4),closed:false}];oc={A:[[2.3,4.2]],B:[[2.3,4.2]]};}
 const sc={dur:20,hands:K2?[K,K2]:[K]};if(pc)sc.poseCam=pc;if(oc)sc.occl=oc;BP.RUN={sc,t0:performance.now(),name:'drill-'+id,next:[],last:null};})(%s)"""
with sync_playwright() as p:
    b=p.chromium.launch(args=['--use-angle=swiftshader','--enable-unsafe-swiftshader']);ctx=b.new_context(viewport={'width':1280,'height':800})
    ctx.route('**/three.min.js',lambda r:r.fulfill(path=T128,content_type='text/javascript'))
    pg=ctx.new_page();pg.on('pageerror',lambda e:errs.append(str(e)));pg.goto(U+'?sim');pg.wait_for_timeout(1500);E=lambda s:pg.evaluate(s)
    fl=ctx.new_page();fl.set_viewport_size({'width':844,'height':390});fl.on('pageerror',lambda e:errs.append('floor: '+str(e)));fl.goto(U+'?floor');fl.wait_for_timeout(1200);fl.evaluate("BP.PSET.done=true;FV.cam=true");pg.bring_to_front()
    E(SETUP);ids=E("BP.SKILLS.map(s=>s.id)");res=[]
    for k,i in enumerate(ids):
        E("BP.RUN=null");pg.wait_for_timeout(150);E("BP.learnStart(%d)"%k);pg.wait_for_timeout(300);E(HAND%json.dumps(i));t0=time.time();shot=False
        while time.time()-t0<22:
            pg.wait_for_timeout(250)
            if not shot and time.time()-t0>2.2 and i in('depth','pinch'):pg.screenshot(path=OUT+'/learn-'+i+'.png');fl.screenshot(path=OUT+'/learn-'+i+'-floor.png');shot=True
            if E("!!BP.LEARN.res"):break
        r=E("BP.LEARN.res");res.append({'skill':i,'stars':r and r['stars'],'text':r and r['text'],'fault':r and r.get('fault'),'secs':round(time.time()-t0,1)})
        if i=='depth':pg.screenshot(path=OUT+'/learn-result.png')
        print(i,'bricks',E("BP.SCENE.bricks&&BP.SCENE.bricks.length"));E("BP.LEARN.res=null;BP.LEARN.on=false")
    log('Learn: each drill with a simulated hand',res)
    E("BP.RUN=null");E("BP.LEARN.on=false;BP.PLAY.mode='learn';BP.drawPlay&&0");pg.wait_for_timeout(300);E("document.querySelector('[data-a=tab-learn]').click()");pg.wait_for_timeout(400);pg.screenshot(path=OUT+'/learn-panel.png')
    # a drill where the Floor camera cannot see: the grade should say it was the system
    E(SETUP);E("BP.learnStart(BP.SKILLS.findIndex(s=>s.id==='depth'))");pg.wait_for_timeout(300);E(HAND%json.dumps('depth'));E("BP.RUN.sc.occl={B:[[0,99]]}");t0=time.time()
    while time.time()-t0<22 and not E("!!BP.LEARN.res"):pg.wait_for_timeout(300)
    log('a drill with the Floor camera blocked',E("({result:BP.LEARN.res,note:BP.LEARN.D.note})"));E("BP.LEARN.on=false;BP.RUN=null")
    # challenges: properties, more than one answer
    out={}
    def ch(k,bricks):
        E("BP.chStart(%d)"%k);pg.wait_for_timeout(200);E("BP.apply?0:0");E("(b=>{for(const x of b)BP.trayAdd?0:0;})([])")
        E("(bs=>{const L=bs.map((x,n)=>Object.assign({id:'c'+n,name:'x',rot:0},x));document.dispatchEvent(new Event('x'));BP.CH.done=false;BP.SCENE.rev;window.__l=L;})(%s)"%json.dumps(bricks))
        E("BP.command?0:0")
        E("(()=>{const c={type:'load',bricks:window.__l,label:'test'};BP.cmdLoad?BP.cmdLoad(c):document.querySelector('#play')&&0;})()")
    print('before ch',E("({b:BP.SCENE.bricks,h:BP.HIST.slice(-4).map(h=>h.label),tr:BP.TR.map(t=>[t.state,t.grasp&&t.grasp.brick])})"))
    E("window.__cmd=c=>{BP.SCENE.bricks=c;BP.SCENE.rev++;};0")
    for k,name,bricks in [(0,'tower, 4 bricks',[{'c':'red','w':2,'d':2,'i':5,'j':3,'l':l} for l in range(4)]),(0,'tower, 6 bricks',[{'c':'red','w':2,'d':2,'i':5,'j':3,'l':l} for l in range(4)]+[{'c':'blue','w':2,'d':2,'i':9,'j':3,'l':0},{'c':'blue','w':2,'d':2,'i':9,'j':3,'l':1}]),
        (1,'bridge on two posts',[{'c':'blue','w':2,'d':2,'i':3,'j':3,'l':0},{'c':'blue','w':2,'d':2,'i':7,'j':3,'l':0},{'c':'green','w':6,'d':2,'i':3,'j':3,'l':1}]),(1,'a brick on one post',[{'c':'blue','w':2,'d':2,'i':3,'j':3,'l':0},{'c':'green','w':6,'d':2,'i':3,'j':3,'l':1}]),
        (2,'stairs rising toward the laptop',[{'c':'yellow','w':4,'d':2,'i':6,'j':1,'l':0},{'c':'yellow','w':4,'d':2,'i':6,'j':3,'l':0},{'c':'yellow','w':4,'d':2,'i':6,'j':3,'l':1},{'c':'yellow','w':4,'d':2,'i':6,'j':5,'l':0},{'c':'yellow','w':4,'d':2,'i':6,'j':5,'l':1},{'c':'yellow','w':4,'d':2,'i':6,'j':5,'l':2}]),
        (2,'stairs going the other way',[{'c':'yellow','w':4,'d':2,'i':6,'j':5,'l':0},{'c':'yellow','w':4,'d':2,'i':6,'j':3,'l':0},{'c':'yellow','w':4,'d':2,'i':6,'j':3,'l':1}]),
        (3,'wall of four 4x1 bricks',[{'c':'white','w':4,'d':1,'i':2,'j':4,'l':0},{'c':'white','w':4,'d':1,'i':6,'j':4,'l':0},{'c':'white','w':4,'d':1,'i':2,'j':4,'l':1},{'c':'white','w':4,'d':1,'i':6,'j':4,'l':1}])]:
        print('ch',name,E("BP.SCENE.bricks===null"));E("BP.chStart(%d)"%k);pg.wait_for_timeout(250);E("window.__cmd(%s)"%json.dumps([dict(x,id='c%d'%n,name='x',rot=0) for n,x in enumerate(bricks)]));pg.wait_for_timeout(400)
        out[name]=E("({solved:BP.CH.done,stars:BP.CH.stars||0,progress:BP.CHALLENGES[BP.CH.k].check().t})")
    log('Challenges',out);pg.screenshot(path=OUT+'/challenge.png')
    # blueprint grades: a placement two rows short, then exact
    E(SETUP);E("BP.playStart(1)");pg.wait_for_timeout(300);E("BP.trayAdd(BP.PARTS.findIndex(p=>p.w===4&&p.d===2&&p.c==='yellow'))");pg.wait_for_timeout(200)
    nb=E("BP.SCENE.bricks.slice(-1)[0].id")
    E("(id=>{BP.SCENE.bricks.find(b=>b.id===id);})('%s')"%nb)
    E("(id=>{const c={id:'g1',type:'place',brick:id,i:6,j:1,l:0,rot:0,by:'seen by A+B'};BP.command?0:0;})('%s')"%nb)
    log('grades',{'note':'placement grading runs in the game; see play.py for a hand-built blueprint'})
    log('errors',errs);json.dump(R,open(OUT+'/learn.json','w'),indent=1);b.close()
