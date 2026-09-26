import json,pathlib,subprocess,hashlib,sys
source_dir=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "/tmp")
root=pathlib.Path(__file__).resolve().parent
sources={
'wheat':dict(title='A Corner in Wheat',year=1909,creator='D. W. Griffith / Biograph',url='https://archive.org/details/ACornerInWheat',download='https://archive.org/download/ACornerInWheat/CornerInWheat_512kb.mp4',sound='Silent-era film; this transfer’s accompaniment is retained. The reading relies on visual relations.',archive=None),
'villa':dict(title='The Lonely Villa',year=1909,creator='D. W. Griffith / Biograph',url='https://archive.org/details/LonelyVilla',download='https://archive.org/download/LonelyVilla/LonelyVilla_512kb.mp4',sound='Silent-era film; transfer audio retained. Telephone gestures, not audible speech, establish the exchange.',archive=None),
'duck':dict(title='Duck and Cover',year=1951,creator='Archer Productions / Federal Civil Defense Administration',url='https://archive.org/details/DuckandC1951',download='https://archive.org/download/DuckandC1951/DuckandC1951_512kb.mp4',sound='Original instructional narration retained; archive ASR transcript consulted alongside frame inspection.',archive='https://www.movingimagearchive.com/sources/duck-and-cover')}
# Blocks retain continuous source intervals. Some blocks deliberately contain multiple shots.
def b(i,a,z,strand,label,sign,why,kind='shot'):
 return dict(id=i,start=a,end=z,strand=strand,label=label,sign=sign,signEvidence=why,unit=kind)
P=[]
def add(id,source,type,title,claim,rival,limit,question,operation,blocks):
 P.append(dict(id=id,source=source,type=type,title=title,claim=claim,rival=rival,limit=limit,question=question,operation=operation,blocks=blocks,start=blocks[0]['start'],end=blocks[-1]['end'],readingStatus='editorial working reading',reader='Codex · 2026-09-26',inspection='Complete source file retrieved; temporal contact sheets and candidate cut boundaries inspected. Visual interpretation, not an independently validated label.'))
add('telephone','villa','alternate','A call across two rooms',
'The mother and father take turns at connected telephones. The burglar cuts the line. These are developing actions linked in the same present, not just similar images.',
'Parallel montage would leave the temporal relation unspecified. Here the call and its interruption supply a causal link.',
'This is a selected passage inside the longer siege. Its first boundary follows the setup of the call; it is not a claim to have segmented the whole film.',
'Does grouping each location destroy the experience of the live call?', 'group',[
 b('v1',336.6,339.65,'A','Father listens','12','A telephone gesture directs the next action.'),b('v2',339.65,342.55,'B','Mother calls','12','Her gesture carries the appeal across the cut.'),b('v3',342.55,347.05,'A','Father reacts','12','He responds and turns from the telephone.'),b('v4',347.05,350.85,'B','Mother waits','14','The besieged family is one pole of the confrontation.'),b('v5',350.85,353.7,'A','Father listens again','12','A repeated directed action maintains the exchange.'),b('v6',353.7,359.5,'B','Mother at the receiver','14','Threat outside the room constrains her action.'),b('v7',359.5,366.35,'A','Father tries the line','12','He acts through the receiver, visibly seeking a response.'),b('v8',366.35,370.95,'C','Burglar cuts the wire','14','An opposing agent materially breaks the exchange.'),b('v9',370.95,374.3,'A','Father loses contact','12','Receiver and bodily reaction carry the interruption.'),b('v10',374.3,378.8,'B','Mother tries to answer','14','The family remains trapped after the line is cut.'),b('v11',378.8,384.75,'A','Father abandons the call','12','The failed exchange becomes a new course of action.')])
add('feast','wheat','parallel','The feast and the price of bread',
'The film repeatedly places abundance beside exclusion from bread. It does not establish a shared clock between banquet and shop; the alternation makes a comparison.',
'Alternate syntagma is a possible rival if one argues a simultaneous social present. There is no phone, shared event or deadline synchronizing these shots.',
'The “Chaff of the Wheat” title stays with the first shop block. Blocks are motifs, not a claim that every block is one camera shot.',
'What remains of the comparison when all the feast shots come first?', 'group',[
 b('w1',327.494,364.631,'A','Banquet: abundance','17','A staged group tableau presents social relations through collective gesture.'),b('w2',364.631,442.910,'B','Title → bread shop','17','The frontal shop tableau makes exclusion legible through bodies and props.','title + shot'),b('w3',442.910,460.561,'A','Return to the banquet','17','The repeated social tableau answers the shop.'),b('w4',460.561,471.638,'B','Return to the queue','17','A near-static group holds poverty before the camera.'),b('w5',471.638,497.764,'A','The toast continues','17','Celebratory gestures reframe the return to wealth.')])
add('sower','wheat','autonomous','One field, one uninterrupted view',
'The field tableau runs without a cut: sowing and ploughing unfold in one camera view. It forms a distinct episode between the farmyard and the Wheat King title.',
'A single file is not sufficient evidence. This reading rests on the uninterrupted view and the changes of episode on both sides.',
'The autonomy belongs to this field episode in this film. Shortening it does not automatically create another autonomous shot.',
'What does cutting the duration in half remove from the field’s unfolding?', 'halve',[
 b('s1',64.865,133.1,'A','Sowing and ploughing','17','Actors, animals and depth form a staged ensemble rather than a privileged face.')])
add('alley','duck','scene','Flash, duck, cover',
'In the alley, two children approach, react to a flash and remain under cover. Closer views specify the same action and place without a stated passage of story time.',
'Ordinary sequence would require meaningful omitted story intervals. The house departure before this passage does contain an ellipsis; it is excluded here.',
'A scene-like instructional enactment, extending Metz beyond fiction. The out-point precedes the dissolve to an alternative doorway example; it is an editorial boundary.',
'Does reversing the shot order turn preparation and reaction into explanation after the fact?', 'reverse',[
 b('d1',356.490,370.804,'A','Children approach in the alley','12','Their directed movement establishes the route.'),b('d2',370.804,373.841,'A','Flash and immediate cover','12','The flash is answered by bodily action.'),b('d3',373.841,376.376,'A','Both under cover','14','The pair’s defensive posture responds to an external threat.'),b('d4',376.376,379.847,'A','Paul covers his neck','12','A close view specifies a useful protective action.'),b('d5',379.847,382.916,'A','Patty uses her coat','12','Clothing becomes an instrument of directed protection.'),b('d6',382.916,386.8,'A','Return to the alley','13','The wider environment locates the completed action.')])
add('places','duck','bracket','Two places to take cover',
'Corridor and lunchroom demonstrations are examples of a general instruction. The film offers situations one might be in, not successive stages of one child’s day.',
'Episodic sequence would summarize dated phases of a development. These situations are alternatives under a rule.',
'A bracket-like didactic organization outside Metz’s original fiction corpus. Each node contains a demonstration with internal cuts; the outer relation is the object of this test.',
'If the examples change order, does the general instruction survive?', 'reverse',[
 b('b1',309.75,334.8,'A','In a corridor','12','Several directed protective actions instantiate one instruction.','multi-shot demonstration'),b('b2',334.8,345.0,'B','At lunch','12','The same instruction is realized with tables as protection.','multi-shot demonstration')])
add('fire','duck','ordinary','Down the pole, into the engine',
'Firefighters descend, then board an engine, then drive out. The cut omits the route from pole to vehicle while maintaining one response action.',
'Scene is the rival if that omitted movement is treated as negligible. The selected reading stresses the unseen transfer between two spaces.',
'A short sequence embedded in an instructional film. The final out-point is before the dissolve to traffic safety; this is a qualified working reading, not a textbook attribution.',
'Can the order be reversed without breaking the action’s causal direction?', 'reverse',[
 b('f1',102.669,109.209,'A','Descend the fire pole','12','Movement has a concrete task and destination.'),b('f2',109.209,112.846,'A','Board the engine','12','The destination is reached across omitted travel.'),b('f3',112.846,114.5,'A','Engine leaves','12','The response continues toward an offscreen destination.')])
for p in P:
 p['media']='syntagm/operative/media/'+p['id']+'.mp4';p['poster']='syntagm/operative/media/'+p['id']+'.jpg'
 p['relations']=[]
 for i in range(1,len(p['blocks'])):
  a,z=p['blocks'][i-1:i+1];p['relations'].append(dict(left=a['id'],right=z['id'],kind={'parallel':'comparison','alternate':'simultaneous action','autonomous':'within shot','scene':'continuous action','bracket':'category example','ordinary':'action with omission'}[p['type']],evidence=p['claim']))
 subprocess.run(['ffmpeg','-y','-loglevel','error','-ss',str(p['start']),'-i',str(source_dir/(p['source']+'.mp4')),'-t',str(p['end']-p['start']),'-vf','scale=480:-2,setsar=1','-c:v','libx264','-preset','fast','-crf','29','-g','25','-c:a','aac','-b:a','64k','-movflags','+faststart',str(root/'media'/f"{p['id']}.mp4")],check=True)
 subprocess.run(['ffmpeg','-y','-loglevel','error','-ss','1','-i',str(root/'media'/f"{p['id']}.mp4"),'-frames:v','1','-vf','scale=240:-2',str(root/'media'/f"{p['id']}.jpg")],check=True)
 subprocess.run(['ffprobe','-v','error','-show_entries','format=duration',str(root/'media'/f"{p['id']}.mp4")],check=True,capture_output=True)
 p['mediaSha256']=hashlib.sha256((root/'media'/f"{p['id']}.mp4").read_bytes()).hexdigest()
for k,s in sources.items():s['fileSha256']=hashlib.sha256((source_dir/(k+'.mp4')).read_bytes()).hexdigest()
signs=json.load(open(root.parent/'data.json'))['signs']
(root/'examples.json').write_text(json.dumps(dict(version=1,sources=sources,examples=P,signs=signs),indent=2)+'\n')
print([(p['id'],(root/'media'/f"{p['id']}.mp4").stat().st_size) for p in P])
