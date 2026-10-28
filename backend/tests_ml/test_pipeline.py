"""Synthetic fixtures test plumbing, never production disease accuracy."""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from ml.common import group_records, preflight_memory, sha256_file, stratified_group_split, validate_manifests, write_json
from ml.evaluate_model import validate_bundle_files
from ml.prepare_dataset import source_group


def record(index, label=0, group=None, pixel=None, dhash=None):
    return {'filename': f'image-{index}.jpg', 'label_index': label, 'label': ['apple', 'corn'][label],
            'pixel_sha256': pixel or f'{index:064x}', 'dhash': dhash or f'{index:016x}',
            'group_id': group or f'group-{index}', 'source_group': f'source-{index}', 'path': f'images/{index}.jpg'}


class GroupingTests(unittest.TestCase):
    def test_exact_duplicate_and_source_groups_stay_together(self):
        rows = [record(1), record(2, pixel=f'{1:064x}'), record(3)]
        rows[2]['source_group'] = rows[1]['source_group']
        accepted, conflicts = group_records(rows, near_distance=-1)
        self.assertFalse(conflicts)
        self.assertEqual(len({row['group_id'] for row in accepted}), 1)

    def test_near_duplicate_candidates_group_but_distant_hashes_do_not(self):
        accepted, _ = group_records([record(1, dhash='0000000000000000'), record(2, dhash='0000000000000001'), record(3, dhash='ffffffffffffffff')], near_distance=1)
        self.assertEqual(accepted[0]['group_id'], accepted[1]['group_id'])
        self.assertNotEqual(accepted[1]['group_id'], accepted[2]['group_id'])

    def test_duplicate_cross_label_conflict_is_quarantined(self):
        accepted, conflicts = group_records([record(1), record(2, label=1, pixel=f'{1:064x}')], near_distance=-1)
        self.assertEqual(accepted, [])
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0]['reason'], 'duplicate_group_label_conflict')

    def test_group_split_is_stratified_deterministic_and_never_leaks(self):
        rows = [record(i + label * 100, label=label, group=f'{label}:{i//2}') for label in range(2) for i in range(24)]
        first, statistics = stratified_group_split(rows, ['apple', 'corn'])
        second, _ = stratified_group_split(list(reversed(rows)), ['apple', 'corn'])
        self.assertEqual(first, second)
        location = {}
        for name, split in first.items():
            self.assertEqual({row['label_index'] for row in split}, {0, 1})
            for row in split:
                self.assertEqual(location.setdefault(row['group_id'], name), name)
        self.assertEqual(sum(len(rows) for rows in first.values()), 48)
        self.assertEqual(statistics['apple']['total'], 24)

    def test_small_class_does_not_silently_skip_test(self):
        with self.assertRaisesRegex(ValueError, 'independent groups'):
            stratified_group_split([record(1), record(2)], ['apple'])

    def test_augmented_source_uuid_is_not_split(self):
        identifier = '001baf35-86fd-4de4-9c76-401e39d76fdb'
        self.assertEqual(source_group(identifier + '_rotated_90.jpg', 'apple'), source_group(identifier + '.jpg', 'apple'))
        self.assertNotEqual(source_group('image1.jpg', 'apple'), source_group('image1.jpg', 'corn'))

    def test_manifest_rejects_cross_split_group_and_label_order_change(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'images').mkdir()
            write_json(root / 'class_labels.json', ['apple'])
            for index, split in enumerate(['train', 'validation', 'test']):
                (root / 'images' / f'{index}.jpg').write_bytes(b'fixture')
                row = record(index, group='same' if index < 2 else 'other')
                (root / f'{split}.jsonl').write_text(json.dumps(row) + '\n')
            with self.assertRaisesRegex(ValueError, 'spans'):
                validate_manifests(root)
            rows = json.loads((root / 'validation.jsonl').read_text())
            rows['group_id'] = 'new'
            rows['label'] = 'changed'
            (root / 'validation.jsonl').write_text(json.dumps(rows))
            with self.assertRaisesRegex(ValueError, 'ordering'):
                validate_manifests(root)

    def test_ram_guard_happens_before_tensorflow_import(self):
        with patch('ml.common.available_memory_bytes', return_value=200_000_000):
            with self.assertRaisesRegex(RuntimeError, 'before importing TensorFlow'):
                preflight_memory(3)

    def test_training_cli_help_does_not_import_tensorflow(self):
        completed = subprocess.run([sys.executable, '-c', "import ml.train_model, sys; assert 'tensorflow' not in sys.modules"], capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)


class ArtifactTests(unittest.TestCase):
    def test_missing_and_corrupt_bundle_fail_before_model_deserialization(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with self.assertRaises(FileNotFoundError):
                validate_bundle_files(root)
            write_json(root / 'class_labels.json', ['synthetic_fixture_a', 'synthetic_fixture_b'])
            (root / 'plant_disease_model.keras').write_bytes(b'NOT A MODEL: checksum validation fixture only')
            metadata = {'input_shape': [224,224,3], 'class_count': 2, 'preprocessing':'mobilenet_v2',
                        'normalization_in_model':True, 'output_type':'probabilities',
                        'model_sha256':sha256_file(root / 'plant_disease_model.keras'),
                        'labels_sha256':sha256_file(root / 'class_labels.json')}
            write_json(root / 'model_metadata.json', metadata)
            validate_bundle_files(root)
            (root / 'plant_disease_model.keras').write_bytes(b'corrupt')
            with self.assertRaisesRegex(ValueError, 'checksum'):
                validate_bundle_files(root)

    def test_preprocessing_metadata_rejects_double_normalization(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            write_json(root / 'class_labels.json', ['fixture'])
            (root / 'plant_disease_model.keras').write_bytes(b'fixture only')
            metadata = {'input_shape': [224,224,3], 'class_count':1, 'preprocessing':'mobilenet_v2',
                        'normalization_in_model':False, 'output_type':'probabilities',
                        'model_sha256':sha256_file(root / 'plant_disease_model.keras'),
                        'labels_sha256':sha256_file(root / 'class_labels.json')}
            write_json(root / 'model_metadata.json', metadata)
            with self.assertRaisesRegex(ValueError, 'normalize exactly once'):
                validate_bundle_files(root)


@unittest.skipUnless(importlib.util.find_spec('numpy') and importlib.util.find_spec('PIL'), 'NumPy/Pillow not installed')
class PreprocessingTests(unittest.TestCase):
    def test_shared_geometry_retains_raw_rgb_range_without_backbone_normalization(self):
        from PIL import Image
        from ml.preprocessing import image_to_array
        image = Image.new('RGB', (300,100), (255,0,128))
        values = image_to_array(image)
        self.assertEqual(values.shape, (224,224,3))
        self.assertEqual(str(values.dtype), 'float32')
        self.assertEqual(values[0,0].tolist(), [255.,0.,128.])
        image.close()


if __name__ == '__main__':
    unittest.main()
