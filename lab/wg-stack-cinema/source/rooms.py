# Two devices in one room through an MQTT relay (a local broker standing in for the public ones). Separate browser contexts share
# nothing (no BroadcastChannel), so every message crosses the relay. Hands are SIMULATED; the room code is typed with the keyboard.
import sys,json,time;sys.path.insert(0,'/home/claude/stack/proof');import serve
from playwright.sync_api import sync_playwright
serve.start(8815);RL='ws://127.0.0.1:1884/mqtt';U='http://127.0.0.1:8815/cineosis-lab/lab/wg-film-test.html';OUT='/home/claude/stack/proof/out5'
P={"v":3,"c":0,"g":0,"s":[["","w:wg_003",0.3667,4.3667,1,[]],["","w:wg_289",0.3333,4.3333,1,[]],["","w:wg_009",0.9,4.6,1,[]]],"t":[]}
R=[];errs=[]
def log(step,**k):R.append(dict(step=step,**k));print(step,json.dumps(k)[:260])
def until(f,ms=8000):
    t=time.time()
    while time.time()-t<ms/1000:
        v=f()
        if v: return round((time.time()-t)*1000)
        time.sleep(.02)
    return None
with sync_playwright() as p:
    b=p.chromium.launch()
    lap=b.new_context(viewport={'width':1280,'height':800}).new_page();lap.on('pageerror',lambda e:errs.append('laptop: '+str(e)))
    lap.goto(U+'?relay='+RL);lap.wait_for_timeout(2500)
    lap.evaluate("p=>{STK.openFilm(STK.filmFrom(p));STK.openSource('shm:giraffe-walks-past');}",P);lap.wait_for_timeout(1200)
    J=lambda s:lap.evaluate(s)
    lap.click('#floorB');until(lambda:J("STK.relayOn()"));lap.wait_for_timeout(300)
    code=lap.inner_text('#roomC');lap.screenshot(path=OUT+'/l1-room.png')
    log('editor: Floor button opens a room',code=code,relay=J("STK.relayOn()"),panel=lap.inner_text('#peers'))
    phc=b.new_context(viewport={'width':390,'height':844},has_touch=True,is_mobile=True,device_scale_factor=2);ph=phc.new_page();ph.on('pageerror',lambda e:errs.append('phone: '+str(e)))
    ph.goto(U+'?floor&relay='+RL);ph.wait_for_timeout(2200);F=lambda s:ph.evaluate(s)
    vis=F("!document.querySelector('#flRoom').hidden");ph.screenshot(path=OUT+'/p1-code.png')
    ph.click('#flCode');ph.keyboard.type(code.lower());ph.click('#flRoomF button')
    ms=until(lambda:J("STK.floors().length")>0 and F("STK.film.shots.length")>0,10000)
    lap.wait_for_timeout(2100);ph.wait_for_timeout(300);ph.screenshot(path=OUT+'/p2-linked.png');lap.screenshot(path=OUT+'/l2-linked.png')
    log('phone: code screen, type the code, Join',code_screen_shown=vis,linked_after_ms=ms,editor_sees_floors=J("STK.floors().length"),button=lap.inner_text('#floorB'),phone_shots=F("STK.film.shots.length"),phone_room=F("STK.ROOM"))
    lap.click('#qrX')
    # swipe on the phone: the editor's shot follows
    s0=J("STK.film.shots.indexOf(STK.film.shots.find(s=>s.id===STK.SHOT))")
    ph.mouse.move(300,420);ph.mouse.down();ph.mouse.move(120,430,steps=6);ph.mouse.up()
    ms=until(lambda:J("STK.film.shots.indexOf(STK.film.shots.find(s=>s.id===STK.SHOT))")!=s0)
    until(lambda:F("STK.FLs.shot")==J("STK.film.shots.indexOf(STK.film.shots.find(s=>s.id===STK.SHOT))"))
    log('phone: swipe left shows the next shot on both',before=s0,after=J("STK.film.shots.indexOf(STK.film.shots.find(s=>s.id===STK.SHOT))"),ms=ms,phone_shot=F("STK.FLs.shot"))
    # hand-off across the relay
    gx,gy=J("(()=>{const a=STK.SB,r=document.querySelector('#cv').getBoundingClientRect();return [r.x+(a.x+a.w*.25)/STK.dpr,r.y+(a.y+a.h*.62)/STK.dpr]})()")
    H=lambda t:lap.evaluate("t=>STK.simHands(t)",t);FH=lambda t:ph.evaluate("t=>STK.floorHands(t)",t)
    n=J('STK.H.undo.length')
    H([{'id':'Right','x':gx,'y':gy,'closed':False,'pose':'open'}]);H([{'id':'Right','x':gx,'y':gy,'closed':True,'pose':'pinch'}]);held=J("STK.HOLD&&STK.HOLD.state")
    H([]);lap.wait_for_timeout(420);H([])
    ms=until(lambda:F("!!STK.FLs.hold"));ph.screenshot(path=OUT+'/p3-incoming.png')
    log('laptop pinches, hand leaves its camera; the phone shows the figure waiting',held=held,laptop=J("STK.HOLD&&STK.HOLD.state"),phone_got_hold_ms=ms,status=lap.inner_text('#heard'))
    FH([{'id':'Right','x':200,'y':600,'closed':True,'pose':'pinch'}])
    ms=until(lambda:J("STK.HOLD&&STK.HOLD.state==='away'"))
    for k in range(1,9): FH([{'id':'Right','x':200+k*10,'y':600-k*25,'closed':True,'pose':'pinch'}]);ph.wait_for_timeout(50)
    until(lambda:J("STK.HOLD&&STK.HOLD.prev&&STK.HOLD.prev.y<.6"));ph.screenshot(path=OUT+'/p4-carry.png');lap.screenshot(path=OUT+'/l4-carry.png')
    log('phone pinch catches it across the relay; carrying moves the laptop preview',catch_ms=ms,owner_is_phone=J("STK.HOLD&&STK.HOLD.owner")==F("STK.DEV"),laptop_preview=J("STK.HOLD&&STK.HOLD.prev"))
    # a second phone in the same room, joined by the scanned address, cannot take it
    p2=b.new_context(viewport={'width':390,'height':844},has_touch=True,is_mobile=True).new_page();p2.on('pageerror',lambda e:errs.append('phone2: '+str(e)))
    p2.goto(U+'?floor&room='+code+'&relay='+RL);until(lambda:p2.evaluate("!!STK.FLs.hold"),10000);p2.wait_for_timeout(300)
    p2.mouse.move(150,500);p2.mouse.down();p2.wait_for_timeout(500);p2.mouse.up();p2.wait_for_timeout(600)
    p2.screenshot(path=OUT+'/p5-second-phone.png')
    log('a second phone (opened from the QR address) cannot take a figure another Floor holds',floors=J("STK.floors().length"),owner_still_phone1=J("STK.HOLD&&STK.HOLD.owner")==F("STK.DEV"),phone2_says_other=p2.evaluate("STK.FLs.other"),undo_unchanged=J('STK.H.undo.length')==n)
    FH([{'id':'Right','x':280,'y':420,'closed':False,'pose':'open'}])
    ms=until(lambda:J('STK.H.undo.length')==n+1)
    shot=J("(()=>{const s=STK.film.shots.find(s=>s.figs.length);return s?STK.film.shots.indexOf(s):null})()")
    until(lambda:F("!STK.FLs.hold"));ph.wait_for_timeout(300);ph.screenshot(path=OUT+'/p6-placed.png');lap.screenshot(path=OUT+'/l6-placed.png')
    log('phone opens the hand: placed as one undo step, in the shot the phone shows',place_ms=ms,label=J("STK.H.undo.slice(-1)[0]&&STK.H.undo.slice(-1)[0].label"),in_shot=shot,phone_shot=F("STK.FLs.shot"),hold_after=J("STK.HOLD"))
    lap.keyboard.press('z');ms=until(lambda:p2.evaluate("STK.film.shots.every(s=>!s.figs.length)"))
    log('undo on the laptop reaches every Floor',ms=ms)
    log('page errors',errors=errs)
    json.dump(R,open(OUT+'/rooms.json','w'),indent=1);b.close()
