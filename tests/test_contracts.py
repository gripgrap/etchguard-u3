import unittest
from copy import deepcopy
from etchguard.contracts import validate_profile,validate_recipe,validate_run
from etchguard.demo import generate,load_runs
from tempfile import TemporaryDirectory
from pathlib import Path

class ContractTests(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory()
        generate(Path(self.temp.name)/"data",n_train=2,n_golden=1)
        self.good=load_runs(Path(self.temp.name)/"data"/"train")[0]
    def tearDown(self):self.temp.cleanup()
    def test_valid_run(self):self.assertEqual(validate_run(self.good),[])
    def test_missing_key(self):
        row=deepcopy(self.good);del row["recipe"]["mask_width"]
        self.assertTrue(any("mask_width" in x for x in validate_run(row)))
    def test_nan(self):
        row=deepcopy(self.good);row["snapshots"][1]["points_um"][0][0]=float("nan")
        self.assertTrue(validate_run(row))
    def test_invalid_time(self):
        row=deepcopy(self.good);row["snapshots"][1]["t_seconds"]=0
        self.assertTrue(any("time" in x for x in validate_run(row)))
    def test_source_required(self):
        row=deepcopy(self.good);row["provenance"]["source_type"]="unknown"
        self.assertTrue(any("source_type" in x for x in validate_run(row)))
    def test_self_crossing(self):
        self.assertTrue(any("crossing" in x for x in validate_profile([[0,0],[1,1],[0,1],[1,0]])))
    def test_overhang_not_rejected(self):
        # Physical overhang can have non-monotone x; do not force x sorting.
        self.assertEqual(validate_profile([[0,0],[1,0],[0.5,-1],[1.2,-2]]),[])
