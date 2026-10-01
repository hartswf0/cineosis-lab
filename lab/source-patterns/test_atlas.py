import importlib.util,json,unittest
from pathlib import Path
HERE=Path(__file__).parent
spec=importlib.util.spec_from_file_location('atlas',HERE/'build_atlas.py');atlas=importlib.util.module_from_spec(spec);spec.loader.exec_module(atlas)
class AtlasTest(unittest.TestCase):
 def test_gaps_are_coverage_not_story_time(self):
  rows=[{'position':0,'startSeconds':0,'endSeconds':10},{'position':2,'startSeconds':15,'endSeconds':20}]
  a=atlas.audit(rows);self.assertEqual(a['coverage'],.75);self.assertEqual(a['gaps'],[[10,15]]);self.assertEqual(a['positionGaps'],[[0,2]])
 def test_overlapping_intervals_are_counted_once(self):
  a=atlas.audit([{'position':0,'startSeconds':0,'endSeconds':10},{'position':1,'startSeconds':5,'endSeconds':12}]);self.assertEqual(a['coverage'],1);self.assertEqual(a['overlaps'],[[5,10]])
 def test_candidates_preserve_source_order_without_claiming_review(self):
  d=json.loads((HERE/'data.json').read_text());self.assertEqual(len(d['passages']),24);self.assertEqual(len(d['sources']),60)
  for p in d['passages']:
   self.assertEqual(p['reading']['type'],'unknown');self.assertFalse(p['inspection']['fullClipsReviewed']);self.assertFalse(p['inspection']['audioReviewed'])
   clips=[d['shots'][i] for i in p['members']];self.assertEqual(atlas.audit(clips)['gaps'],[]);self.assertEqual(atlas.audit(clips)['positionGaps'],[])
   self.assertEqual(p['interval'],[clips[0]['startSeconds'],clips[-1]['endSeconds']]);self.assertGreater(len(p['inspection']['clipsSampled']),0)
  self.assertEqual(sum(len(p['inspection']['clipsSampled']) for p in d['passages']),34)
if __name__=='__main__':unittest.main()
