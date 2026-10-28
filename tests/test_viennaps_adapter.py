import unittest
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from etchguard.adapters.viennaps import ordered_material_profile, inspect_run
from etchguard.contracts import RECIPE_KEYS
from etchguard.integrity import manifest_for


class ConnectivityTests(unittest.TestCase):
    def test_orders_by_edges_not_x(self):
        points = [[0, 0, 0], [2, -1, 0], [1, -2, 0], [3, 1, 0]]
        self.assertEqual(ordered_material_profile(points, [3, 2, 1, 0, 2, 0, 3], [10, 0]),
                         [[0, 0], [2, -1], [1, -2]])

    def test_branch_rejected(self):
        with self.assertRaisesRegex(ValueError, 'branch'):
            ordered_material_profile([[0,0,0],[1,0,0],[2,0,0],[1,1,0]],
                                     [2,0,1,2,1,2,2,1,3], [10,10,10])

    def test_disconnected_rejected(self):
        with self.assertRaises(ValueError):
            ordered_material_profile([[0,0,0],[1,0,0],[2,0,0],[3,0,0]],
                                     [2,0,1,2,2,3], [10,10])

    def test_nonplanar_rejected(self):
        with self.assertRaisesRegex(ValueError, 'plane'):
            ordered_material_profile([[0,0,0],[1,0,1]], [2,0,1], [10])

    def test_invalid_material_and_cell_counts(self):
        for materials in ([], [float('nan')], [10.5]):
            with self.subTest(materials=materials), self.assertRaises(ValueError):
                ordered_material_profile([[0,0,0],[1,0,0]], [2,0,1], materials)

    def test_duplicate_edge_rejected(self):
        with self.assertRaises(ValueError):
            ordered_material_profile([[0,0,0],[1,0,0]], [2,0,1,2,1,0], [10,10])

    def test_closed_curve_rejected(self):
        with self.assertRaises(ValueError):
            ordered_material_profile([[0,0,0],[1,0,0],[0,1,0]], [4,0,1,2,0], [10])

    def test_missing_material_rejected(self):
        with self.assertRaisesRegex(ValueError, 'selected material'):
            ordered_material_profile([[0,0,0],[1,0,0]], [2,0,1], [0])

    def test_invalid_connectivity_rejected(self):
        for cells in ([2,0,8], [3,0,1], [1,0], [2,0,0]):
            with self.subTest(cells=cells), self.assertRaises(ValueError):
                ordered_material_profile([[0,0,0],[1,0,0]], cells, [10])


@unittest.skipUnless(importlib.util.find_spec('pyvista'), 'optional PyVista not installed')
class VTPReaderTests(unittest.TestCase):
    def setUp(self):
        import pyvista as pv
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root/'snapshots').mkdir()
        for i in (0, 1):
            mesh = pv.PolyData([[0.,0.,0.],[1.,-float(i),0.]], lines=[2,0,1])
            mesh.cell_data['MaterialIds'] = [10]
            mesh.save(self.root/f'snapshots/t{i:03d}.vtp', binary=True)
        (self.root/'meta.json').write_text(json.dumps({
            'params': {k: 1 for k in RECIPE_KEYS}, 'actual_k': 1,
            'step_min': 1, 'viennaps': 'test_fixture_not_simulation'}))
        self.fp = manifest_for(self.root)['content_fingerprint']

    def inspect(self, fingerprint=None):
        return inspect_run(self.root, fingerprint or self.fp, source_revision='test-only')

    def test_compressed_vtp_roundtrip_and_no_source_writes(self):
        before = manifest_for(self.root)
        run = self.inspect()
        self.assertEqual(run['snapshots'][1]['points_um'], [[0.,0.],[1.,-1.]])
        self.assertEqual(run['snapshots'][1]['t_seconds'], 60)
        self.assertEqual(run['provenance']['source_type'], 'external_research')
        self.assertIn('derived_not_observed', run['provenance']['time_basis'])
        self.assertEqual(before, manifest_for(self.root))

    def test_changed_file_blocks_before_reader(self):
        with (self.root/'snapshots/t001.vtp').open('ab') as f:
            f.write(b' ')
        with self.assertRaisesRegex(ValueError, 'fingerprint'):
            self.inspect()

    def test_missing_snapshot_does_not_renumber(self):
        (self.root/'snapshots/t001.vtp').rename(self.root/'snapshots/t002.vtp')
        with self.assertRaisesRegex(ValueError, 'snapshot index'):
            self.inspect(manifest_for(self.root)['content_fingerprint'])

    def test_missing_material_array_rejected(self):
        import pyvista as pv
        p = self.root/'snapshots/t001.vtp'
        mesh = pv.read(p)
        del mesh.cell_data['MaterialIds']
        mesh.save(p)
        with self.assertRaisesRegex(ValueError, 'MaterialIds'):
            self.inspect(manifest_for(self.root)['content_fingerprint'])

    def test_missing_source_revision_rejected(self):
        with self.assertRaisesRegex(ValueError, 'source revision'):
            inspect_run(self.root, self.fp, source_revision='')
