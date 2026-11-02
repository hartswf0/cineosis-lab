"""Compare the exported film with the editor's own preview: duration, streams, sound, and frames at times inside every shot."""
import json, subprocess, os, numpy as np
from PIL import Image
OUT=os.path.join(os.path.dirname(__file__),'out'); E=OUT+'/export.webm'; T=json.load(open(OUT+'/times.json'))['times']; steps=json.load(open(OUT+'/steps.json'))
total=[s for s in steps if s['step']=='save, reload'] and None
probe=json.loads(subprocess.run(['ffprobe','-v','error','-show_entries','stream=codec_type,codec_name:format=duration','-of','json',E],capture_output=True,text=True).stdout)
# webm from MediaRecorder carries no duration header: count it by decoding
dur=float(subprocess.run(['ffprobe','-v','error','-count_frames','-select_streams','v','-show_entries','stream=nb_read_frames','-of','csv=p=0',E],capture_output=True,text=True).stdout.strip() or 0)
pkt=subprocess.run(['ffprobe','-v','error','-select_streams','v','-show_entries','packet=pts_time','-of','csv=p=0',E],capture_output=True,text=True).stdout.split()
last=max(float(x.strip(',')) for x in pkt if x.strip(','))
vol=subprocess.run(['ffmpeg','-i',E,'-af','volumedetect','-vn','-f','null','-'],capture_output=True,text=True).stderr
mean=[l for l in vol.splitlines() if 'mean_volume' in l]; mx=[l for l in vol.splitlines() if 'max_volume' in l]
def load(p): return np.asarray(Image.open(p).convert('L').resize((320,180)),dtype=np.float32)
res=[]
prev={t:load(f'{OUT}/prev_{t:.3f}.png') for t in T}
for t in T:
    best=(1e9,None)
    for d in np.arange(-0.2,0.21,1/30):
        tt=max(0,t+d); fp=f'{OUT}/exp_tmp.png'
        subprocess.run(['ffmpeg','-y','-v','error','-ss',f'{tt:.3f}','-i',E,'-frames:v','1',fp])
        if not os.path.exists(fp): continue
        diff=float(np.abs(load(fp)-prev[t]).mean()); os.remove(fp)
        if diff<best[0]: best=(diff,round(float(d),3))
    subprocess.run(['ffmpeg','-y','-v','error','-ss',f'{max(0,t+(best[1] or 0)):.3f}','-i',E,'-frames:v','1',f'{OUT}/exp_{t:.3f}.png'])
    others=[float(np.abs(prev[t]-prev[u]).mean()) for u in T if abs(u-t)>1]
    res.append({'t':t,'diff_to_preview':round(best[0],2),'best_offset_s':best[1],'diff_to_other_shots_min':round(min(others),2) if others else None})
out={'streams':probe['streams'],'video_frames':int(dur),'last_frame_time':round(last,3),'sound':{'mean':mean[0].split(':')[-1].strip() if mean else None,'max':mx[0].split(':')[-1].strip() if mx else None},'frames':res}
json.dump(out,open(OUT+'/compare.json','w'),indent=1);print(json.dumps(out,indent=1))
