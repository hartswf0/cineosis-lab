"""Refresh public-domain texts only; preserve the source and edition statement."""
import requests,json,re
from bs4 import BeautifulSoup
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
P=Path(__file__).parent
sources={'keats':'ode-grecian-urn','coleridge':'kubla-khan','hopkins':'felix-randal','stevens':'thirteen-ways-looking-blackbird','macleish':'ars-poetica','williams':'red-wheelbarrow','frost':'road-not-taken'}
def get(row):
 id,slug=row;url='https://poets.org/poem/'+slug+'/print'
 try:
  r=requests.get(url,timeout=40);r.raise_for_status();s=BeautifulSoup(r.text,'html.parser');body=s.select_one('.field--body')
  if not body or 'public domain' not in s.get_text().lower():return id,None
  # Preserve stanza boundaries and line breaks in the publisher's markup.
  for br in body.find_all('br'):br.replace_with('\n')
  paragraphs=body.find_all('p')
  text='\n\n'.join(p.get_text().strip() for p in paragraphs if p.get_text().strip()) if paragraphs else body.get_text('\n').strip()
  text=re.sub(r'\n[ \t]*\n[ \t]*\n+','\n\n',text)
  return id,{'text':text,'source':url.removesuffix('/print'),'textStatus':'Full text · public domain · Academy of American Poets'}
 except Exception as e:print(id,str(e));return id,None
with ThreadPoolExecutor(max_workers=4) as pool:updates=dict(pool.map(get,sources.items()))
updates={k:v for k,v in updates.items() if v};(P/'public-texts.json').write_text(json.dumps(updates,ensure_ascii=False,indent=2))
cases=json.load(open(P/'tests.json'))
for c in cases:
 if c['id'] in updates:c.update(updates[c['id']])
(P/'tests.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2));print('Added full texts',list(updates))
