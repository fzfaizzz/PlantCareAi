"""Evaluate validation/test separately; tune policy ONLY on validation predictions."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

from .common import load_json, preflight_memory, sha256_file, validate_manifests, write_json
from .metrics import choose_policy, classification_report, selective_report
from .train_model import ensure_manifest_integrity, make_dataset


def validate_bundle_files(bundle: Path):
    labels = load_json(bundle / 'class_labels.json')
    metadata = load_json(bundle / 'model_metadata.json')
    if not labels or not isinstance(labels, list) or len(set(labels)) != len(labels) or not all(isinstance(x, str) for x in labels):
        raise ValueError('Invalid ordered labels.')
    for name, key in [('plant_disease_model.keras', 'model_sha256'), ('class_labels.json', 'labels_sha256')]:
        if sha256_file(bundle / name) != metadata.get(key):
            raise ValueError(f'{name} checksum mismatch.')
    if (metadata.get('input_shape') != [224, 224, 3] or metadata.get('preprocessing') != 'mobilenet_v2'
            or metadata.get('normalization_in_model') is not True or metadata.get('output_type') != 'probabilities'):
        raise ValueError('Unsupported preprocessing/output contract. Model must normalize exactly once inside artifact.')
    if metadata.get('class_count') != len(labels):
        raise ValueError('Metadata class count differs from authoritative labels.')
    return labels, metadata


def load_verified_model(bundle: Path):
    labels, metadata = validate_bundle_files(bundle)
    import tensorflow as tf
    model = tf.keras.models.load_model(bundle / 'plant_disease_model.keras', compile=False, safe_mode=True)
    if tuple(model.input_shape[1:]) != (224, 224, 3) or tuple(model.output_shape[1:]) != (len(labels),):
        raise ValueError('Actual model input/output shapes differ from the bundle contract.')
    normalization = model.get_layer('mobilenet_v2_normalization')
    config = normalization.get_config()
    if abs(config.get('scale', 0) - 1 / 127.5) > 1e-9 or config.get('offset') != -1:
        raise ValueError('Expected exactly recorded MobileNet normalization in artifact.')
    if model.layers[-1].get_config().get('activation') != 'softmax':
        raise ValueError('Model output must already be softmax probabilities.')
    return tf, model, labels, metadata


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepared', type=Path, default=Path('data/plant_village'))
    parser.add_argument('--bundle', type=Path, default=Path('models'))
    parser.add_argument('--reports', type=Path, default=Path('reports'))
    parser.add_argument('--batch-size', type=int, default=16)
    parser.add_argument('--target-precision', type=float, default=.98)
    parser.add_argument('--min-accepted', type=int, default=100)
    parser.add_argument('--field-manifest', type=Path, help='Optional JSONL of permitted real field photos; evaluated separately.')
    parser.add_argument('--allow-low-memory', action='store_true')
    args = parser.parse_args(argv)
    if args.batch_size < 1 or not .5 < args.target_precision <= 1 or args.min_accepted < 1:
        parser.error('Invalid batch size, target precision or minimum validation support.')
    preflight_memory(2.0, args.allow_low_memory)
    dataset_meta = load_json(args.prepared / 'dataset_metadata.json')
    ensure_manifest_integrity(args.prepared, dataset_meta)
    prepared_labels, manifests = validate_manifests(args.prepared)
    tf, model, labels, metadata = load_verified_model(args.bundle)
    if prepared_labels != labels:
        raise ValueError('Dataset labels and model labels are not in identical order.')
    if metadata['dataset']['manifest_checksums'] != dataset_meta['manifest_checksums']:
        raise ValueError('Evaluation manifests differ from the split used to train this model.')
    import numpy as np
    args.reports.mkdir(parents=True, exist_ok=True)
    predictions = {}
    for split in ('validation', 'test'):
        scores = model.predict(make_dataset(tf, manifests[split], args.prepared, args.batch_size), verbose=1)
        targets = np.asarray([row['label_index'] for row in manifests[split]])
        report = classification_report(targets, scores, labels)
        report.update({'dataset': dataset_meta['dataset'], 'builder_version': dataset_meta['builder_version'],
                       'manifest_sha256': dataset_meta['manifest_checksums'][split], 'split': split,
                       'model_sha256': metadata['model_sha256'], 'image_domain': 'PlantVillage dataset images'})
        predictions[split] = (targets, scores, report)
        np.savez_compressed(args.reports / f'{split}_predictions.npz', targets=targets, scores=scores)
    targets, scores, _ = predictions['validation']
    policy = choose_policy(targets, scores, args.target_precision, args.min_accepted)
    write_json(args.reports / 'decision_policy.json', policy)
    for split, (targets, scores, report) in predictions.items():
        report['selective_policy'] = selective_report(targets, scores, policy)
        write_json(args.reports / f'{split}_report.json', report)
        write_json(args.reports / f'{split}_confusion_matrix.json', {'ordered_labels': labels, 'matrix': report['confusion_matrix']})
    metadata.update({'decision_policy': policy, 'calibration_status': 'uncalibrated_reliability_measured',
                     'evaluation': {
                         'domain': 'PlantVillage held-out dataset images; no field accuracy implied',
                         'validation': {key: predictions['validation'][2][key] for key in ['n', 'accuracy', 'macro_f1', 'reliability', 'selective_policy']},
                         'test': {key: predictions['test'][2][key] for key in ['n', 'accuracy', 'macro_f1', 'reliability', 'selective_policy']},
                         'validation_report_sha256': sha256_file(args.reports / 'validation_report.json'),
                         'test_report_sha256': sha256_file(args.reports / 'test_report.json'),
                     }})
    if args.field_manifest:
        field_report = evaluate_field(tf, model, labels, policy, args.field_manifest, args.batch_size)
        write_json(args.reports / 'field_report.json', field_report)
        metadata['evaluation']['field'] = {key: value for key, value in field_report.items() if key != 'images'}
    else:
        metadata['evaluation']['field'] = {'completed': False, 'reason': 'No permitted real field/non-leaf/out-of-scope manifest supplied.'}
    write_json(args.bundle / 'model_metadata.json', metadata)
    write_json(args.bundle / 'checksums.json', {name: sha256_file(args.bundle / name) for name in
               ['plant_disease_model.keras', 'class_labels.json', 'model_metadata.json']})
    print(json.dumps({'test_accuracy': metadata['evaluation']['test']['accuracy'],
                      'test_macro_f1': metadata['evaluation']['test']['macro_f1'],
                      'policy_validated': policy['validated'], 'field': metadata['evaluation']['field']}, indent=2))
    return 0


def evaluate_field(tf, model, labels, policy, manifest: Path, batch_size: int):
    """No remote downloads. Permissions and ground truth are curator-supplied."""
    import numpy as np
    root = manifest.resolve().parent
    rows = []
    for line in manifest.read_text(encoding='utf-8').splitlines():
        if not line:
            continue
        row = json.loads(line)
        if row.get('image_origin') != 'field' or not row.get('permission') or not isinstance(row.get('expected_supported'), bool):
            raise ValueError('Every field row requires image_origin=field, permission and expected_supported boolean.')
        image = (root / row['path']).resolve()
        if not image.is_relative_to(root) or not image.is_file():
            raise ValueError('Field image must exist inside the local manifest directory.')
        label = row.get('label')
        if label is not None and label not in labels:
            raise ValueError('Field ground-truth class must be an exact ordered label, or null.')
        rows.append(dict(row, label_index=labels.index(label) if label is not None else -1))
    if not rows:
        raise ValueError('Field manifest is empty.')
    scores = model.predict(make_dataset(tf, rows, root, batch_size), verbose=1)
    known = [index for index, row in enumerate(rows) if row['label_index'] >= 0]
    result = {'completed': True, 'manifest_sha256': sha256_file(manifest), 'n': len(rows),
              'image_domain': 'Curator-supplied real field photos and non-leaf/out-of-scope images',
              'permissions_status': 'User/curator supplied; inspect each permission before distribution',
              'supported_class_metrics': classification_report([rows[i]['label_index'] for i in known], scores[known], labels) if known else None,
              'limitations': 'No universal OOD claim. Compare actual measured field results separately from PlantVillage.', 'images': []}
    outside = accepted_outside = 0
    for row, vector in zip(rows, scores):
        order = np.argsort(vector)[::-1]
        accepted = bool(policy.get('validated') and vector[order[0]] >= policy['min_score']
                        and vector[order[0]] - vector[order[1]] >= policy['min_margin'])
        if not row['expected_supported']:
            outside += 1
            accepted_outside += int(accepted)
        result['images'].append({'path': row['path'], 'label': row.get('label'), 'expected_supported': row['expected_supported'],
                                 'predicted_class': labels[order[0]], 'score': float(vector[order[0]]), 'score_policy_accepted': accepted})
    result['out_of_scope_count'] = outside
    result['out_of_scope_score_policy_acceptance_rate'] = accepted_outside / outside if outside else None
    return result


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (RuntimeError, ValueError, FileNotFoundError) as error:
        print(f'Evaluation failed: {error}', file=sys.stderr)
        raise SystemExit(1)
