"""Build a small Syntagm Lab entry point; source manifests load on demand.

Run from any directory: python3 lab/syntagm/build_data.py
No inference of Metz categories is performed here.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parent


def build():
    corpus = json.loads((LAB / 'lab-data.json').read_text())
    by_id = {s['id']: s for s in corpus['shots']}
    sources = []
    for path in sorted((LAB / 'cutbastard/forage/sources').glob('*.json')):
        source = json.loads(path.read_text())
        clips = source['clips']
        if not clips:
            continue
        sources.append({'slug': source['slug'], 'title': clips[0]['sourceTitle'],
                        'count': len(clips), 'path': 'cutbastard/forage/sources/' + path.name})
    cuts, ids = {}, set()
    for name in ('suite', 'scenes', 'cineosis', 'drift'):
        plan = json.loads((LAB / f'wygwyl/cuts/{name}/plan.json').read_text())
        cuts[name] = {'title': plan['title'], 'idea': plan['idea'], 'patches': []}
        for p in plan['patches']:
            c = p['clip']
            ids.add(c['id'])
            cuts[name]['patches'].append({
                'id': p['id'], 'shotId': c['id'], 'in': c['in'], 'out': c['out'],
                'record': [p['t0'], p['t1']], 'chapter': p['chapter'],
                'title': p['film'], 'words': p['line'], 'beatSigns': p['codes']})
    read_ids = [s['id'] for s in corpus['shots'] if s.get('signs')]
    ids.update(read_ids)
    fields = ('id', 'title', 'year', 'slug', 'page', 'video', 'clip', 'thumb',
              'start', 'end', 'aff_top', 'signs', 'subjects', 'scale')
    shots = {i: {k: by_id[i].get(k) for k in fields} for i in sorted(ids) if i in by_id}
    assert len(shots) == len(ids), 'A cut or reading refers to an absent shot'
    data = {'version': 1, 'signs': corpus['signs'], 'shots': shots, 'readIds': read_ids,
            'sources': sources, 'cuts': cuts,
            'counts': {'corpus': len(corpus['shots']), 'read': len(read_ids)}}
    (HERE / 'data.json').write_text(json.dumps(data, separators=(',', ':'), ensure_ascii=False) + '\n')
    print(f'{len(shots)} entry shots; {len(sources)} source manifests; no syntagm labels inferred')


if __name__ == '__main__':
    build()
