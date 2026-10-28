import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from etchguard.integrity import freeze,verify,IntegrityError

class IntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory()
        self.root=Path(self.temp.name)
        (self.root/"run.json").write_text('{"recipe": 10, "snapshots": [1, 2]}',encoding="utf-8")
    def tearDown(self):self.temp.cleanup()
    def test_freeze_and_verify(self):
        locked=freeze(self.root)
        self.assertEqual(locked,verify(self.root))
    def test_raw_change_detected_without_recipe_change(self):
        # The recipe is unchanged but original snapshot bytes change.
        freeze(self.root)
        (self.root/"run.json").write_text('{"recipe": 10, "snapshots": [1, 3]}',encoding="utf-8")
        with self.assertRaises(IntegrityError):verify(self.root)
    def test_file_added_detected(self):
        freeze(self.root)
        (self.root/"new.vtp").write_bytes(b"new data")
        with self.assertRaises(IntegrityError):verify(self.root)
    def test_file_deleted_detected(self):
        freeze(self.root)
        (self.root/"run.json").unlink()
        with self.assertRaises(IntegrityError):verify(self.root)
    def test_deny_manifest_overwrite(self):
        freeze(self.root)
        with self.assertRaises(IntegrityError):freeze(self.root)
    def test_deny_symlink(self):
        target=self.root/"run.json"
        (self.root/"shortcut").symlink_to(target)
        with self.assertRaises(IntegrityError):freeze(self.root)

    def test_nested_manifest_named_file_is_not_ignored(self):
        nested = self.root / "nested"
        nested.mkdir()
        (nested / "manifest.sha256.json").write_text("nested data", encoding="utf-8")
        freeze(self.root)
        (nested / "manifest.sha256.json").write_text("tampered nested data", encoding="utf-8")
        with self.assertRaises(IntegrityError):
            verify(self.root)
