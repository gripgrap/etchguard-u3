import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from etchguard.demo import generate,load_runs
from etchguard.model import NearestRecipeBaseline
from etchguard.metrics import chamfer_um,depth_um,score_pairs
from etchguard.integrity import freeze
from etchguard.gate import evaluate_candidate
from etchguard.registry import Registry
from etchguard.cli import DegradedModel,main

class MetricTests(unittest.TestCase):
    def test_exact_chamfer(self):
        pts=[[0,0],[1,0],[2,0]]
        self.assertEqual(chamfer_um(pts,pts),0.0)
    def test_parallel_lines(self):
        self.assertAlmostEqual(chamfer_um([[0,0],[1,0]],[[0,-0.25],[1,-0.25]]),0.25)
    def test_depth(self):
        self.assertAlmostEqual(depth_um([[0,0],[1,-0.4]]),0.4)
    def test_empty_eval(self):
        with self.assertRaises(ValueError):score_pairs([])

class GateTests(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory()
        base=Path(self.temp.name)/"data"
        generate(base,n_train=40,n_golden=8)
        self.train=load_runs(base/"train");self.golden=load_runs(base/"golden")
        self.fp=freeze(base/"golden")["content_fingerprint"]
        self.model=NearestRecipeBaseline(self.train)
        self.kw=dict(max_chamfer_um=0.15,max_depth_mae_um=0.15,
                     expected_fingerprint=self.fp,actual_fingerprint=self.fp)
    def tearDown(self):self.temp.cleanup()
    def test_train_gold_no_duplicate(self):
        self.assertFalse(set(r["run_id"] for r in self.train) & set(r["run_id"] for r in self.golden))
        self.assertFalse(set(tuple(r["recipe"].values()) for r in self.train) &
                         set(tuple(r["recipe"].values()) for r in self.golden))
    def test_pass(self):
        self.assertEqual(evaluate_candidate(self.model,self.golden,**self.kw).exit_code,0)
    def test_model_degradation_block(self):
        self.assertEqual(evaluate_candidate(DegradedModel(self.model),self.golden,**self.kw).exit_code,1)
    def test_fingerprint_block(self):
        kwargs={**self.kw,"actual_fingerprint":"broken"}
        self.assertEqual(evaluate_candidate(self.model,self.golden,**kwargs).exit_code,2)
    def test_empty_golden_block(self):
        self.assertEqual(evaluate_candidate(self.model,[],**self.kw).exit_code,2)
    def test_incumbent_preserved(self):
        reg=Registry(Path(self.temp.name)/"registry")
        good=evaluate_candidate(self.model,self.golden,**self.kw)
        reg.submit("baseline",good,fingerprint=self.fp)
        bad=evaluate_candidate(DegradedModel(self.model),self.golden,**self.kw)
        reg.submit("degraded",bad,fingerprint=self.fp)
        self.assertEqual(reg.champion()["model_id"],"baseline")
        self.assertEqual(len((Path(self.temp.name)/"registry"/"history.jsonl").read_text().splitlines()),2)
    def test_cli_smoke(self):
        out=Path(self.temp.name)/"fresh-demo"
        self.assertEqual(main(["demo","--output",str(out)]),0)
        self.assertTrue((out/"report.html").exists())
        self.assertTrue((out/"summary.json").exists())
        self.assertEqual(main(["demo","--output",str(out)]),2)  # no overwriting
