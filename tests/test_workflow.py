import json
import io
from contextlib import redirect_stdout
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from etchguard.demo import generate
from etchguard.integrity import freeze
from etchguard.registry import Registry
from etchguard.workflow import evaluate_bundle, run_bundle
from etchguard.cli import main


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'bundle'
        generate(self.root, n_train=4, n_golden=2)
        self.policy = dict(evaluation_time_seconds=15, max_chamfer_um=.15,
                           max_depth_mae_um=.15, max_regression_ratio=1.1)
        self.write_policy()
        self.registry = Registry(Path(self.temp.name) / 'registry')

    def write_policy(self):
        (self.root / 'policy.json').write_text(json.dumps(self.policy), encoding='utf-8')

    def seal(self):
        return freeze(self.root)['content_fingerprint']

    def change_golden(self, change):
        p = self.root / 'golden/golden-0000.json'
        doc = json.loads(p.read_text())
        change(doc)
        p.write_text(json.dumps(doc), encoding='utf-8')

    def test_pass_binds_evidence(self):
        fp = self.seal()
        result = run_bundle(self.root, fp, self.registry, 'baseline')
        self.assertEqual(result['decision']['exit_code'], 0)
        saved = self.registry.champion()['evidence']
        self.assertEqual(saved['bundle_fingerprint'], fp)
        self.assertEqual(saved['evaluation_time_seconds'], 15)
        self.assertEqual(len(saved['model_digest']), 64)

    def test_mutation_blocks_and_preserves_champion(self):
        fp = self.seal()
        run_bundle(self.root, fp, self.registry, 'baseline')
        before = (self.registry.root / 'current.json').read_bytes()
        self.change_golden(lambda d: d.update(run_id='changed'))
        result = run_bundle(self.root, fp, self.registry, 'candidate')
        self.assertEqual(result['decision']['exit_code'], 2)
        self.assertEqual(before, (self.registry.root / 'current.json').read_bytes())
        self.assertEqual(len((self.registry.root / 'history.jsonl').read_text().splitlines()), 2)

    def test_added_and_deleted_file_block(self):
        fp = self.seal()
        extra = self.root / 'extra.txt'
        extra.write_text('unexpected')
        self.assertEqual(evaluate_bundle(self.root, fp)['decision']['exit_code'], 2)
        extra.unlink()
        (self.root / 'golden/golden-0000.json').unlink()
        self.assertEqual(evaluate_bundle(self.root, fp)['decision']['exit_code'], 2)

    def test_matching_manifest_cannot_replace_external_baseline(self):
        fp = self.seal()
        self.change_golden(lambda d: d.update(run_id='changed'))
        (self.root / 'manifest.sha256.json').unlink()
        freeze(self.root)
        self.assertEqual(evaluate_bundle(self.root, fp)['decision']['exit_code'], 2)

    def test_same_recipe_different_id_and_key_order_blocks(self):
        train = json.loads((self.root / 'train/train-0000.json').read_text())
        recipe = {k: float(v) for k, v in reversed(list(train['recipe'].items()))}
        self.change_golden(lambda d: d.update(recipe=recipe))
        result = evaluate_bundle(self.root, self.seal())
        self.assertEqual(result['decision']['exit_code'], 2)
        self.assertIn('recipe overlap', str(result))

    def test_wrong_final_time_blocks(self):
        self.change_golden(lambda d: d['snapshots'][-1].update(t_seconds=16))
        self.assertEqual(evaluate_bundle(self.root, self.seal())['decision']['exit_code'], 2)

    def test_training_time_mismatch_blocks(self):
        p = self.root / 'train/train-0000.json'
        d = json.loads(p.read_text()); d['snapshots'][-1]['t_seconds'] = 16
        p.write_text(json.dumps(d))
        self.assertEqual(evaluate_bundle(self.root, self.seal())['decision']['exit_code'], 2)

    def test_nonfinite_or_negative_policy_blocks(self):
        for v in [float('inf'), float('nan'), -1, True]:
            with self.subTest(value=v):
                self.policy['max_chamfer_um'] = v
                self.write_policy()
                manifest = self.root / 'manifest.sha256.json'
                if manifest.exists(): manifest.unlink()
                self.assertEqual(evaluate_bundle(self.root, self.seal())['decision']['exit_code'], 2)

    def test_manifest_wrong_type_blocks(self):
        (self.root / 'manifest.sha256.json').write_text('[]')
        self.assertEqual(evaluate_bundle(self.root, 'a'*64)['decision']['exit_code'], 2)

    def test_model_runtime_error_blocks(self):
        fp = self.seal()
        with patch('etchguard.model.NearestRecipeBaseline.predict', side_effect=RuntimeError('failed')):
            result = evaluate_bundle(self.root, fp)
        self.assertEqual(result['decision']['exit_code'], 1)

    def test_changed_during_prediction_blocks(self):
        fp = self.seal()
        def mutate(model, recipe):
            (self.root / 'changed.txt').write_text('mutation')
            return [[0, 0], [1, 0]]
        with patch('etchguard.model.NearestRecipeBaseline.predict', mutate):
            self.assertEqual(evaluate_bundle(self.root, fp)['decision']['exit_code'], 2)

    def test_output_inside_bundle_rejected_without_writing(self):
        fp = self.seal()
        with self.assertRaises(ValueError):
            run_bundle(self.root, fp, Registry(self.root / 'output'), 'baseline')
        self.assertFalse((self.root / 'output/history.jsonl').exists())

    def test_cli_verified_evaluation_and_failure(self):
        fp = self.seal()
        args = ['evaluate-bundle', str(self.root), '--expected-fingerprint', fp,
                '--registry', str(self.registry.root), '--model-id', 'cli-baseline']
        with redirect_stdout(io.StringIO()):
            self.assertEqual(main(args), 0)
            self.change_golden(lambda d: d.update(run_id='changed'))
            self.assertEqual(main(args), 2)

    def test_history_write_failure_does_not_promote(self):
        fp = self.seal()
        run_bundle(self.root, fp, self.registry, 'baseline')
        before = (self.registry.root / 'current.json').read_bytes()
        (self.registry.root / 'history.jsonl').unlink()
        (self.registry.root / 'history.jsonl').mkdir()
        with self.assertRaises(OSError):
            run_bundle(self.root, fp, self.registry, 'candidate')
        self.assertEqual(before, (self.registry.root / 'current.json').read_bytes())

    def test_strict_policy_blocks_without_champion(self):
        self.policy['max_chamfer_um'] = 0
        self.policy['max_depth_mae_um'] = 0
        self.write_policy()
        result = run_bundle(self.root, self.seal(), self.registry, 'candidate')
        self.assertEqual(result['decision']['exit_code'], 1)
        self.assertIsNone(self.registry.champion())

    def test_wrong_json_type_blocks(self):
        (self.root / 'golden/golden-0000.json').write_text('[]')
        self.assertEqual(evaluate_bundle(self.root, self.seal())['decision']['exit_code'], 2)
