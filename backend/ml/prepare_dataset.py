"""Download/cache TFDS PlantVillage and split duplicate groups BEFORE augmentation.

Run from backend: python -m ml.prepare_dataset --output data/plant_village
A metadata-only run does not download images and is not a prepared/trained model.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import platform
import re
import shutil
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from .common import group_records, preflight_memory, sha256_file, stratified_group_split, write_json

SOURCE = 'https://data.mendeley.com/datasets/tywbtsjrjv/1'
CATALOG = 'https://www.tensorflow.org/datasets/catalog/plant_village'
UUID = re.compile(r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', re.I)


def source_group(filename: str, label: str) -> str:
    match = UUID.search(filename)
    if match:
        return 'uuid:' + match.group(1).lower()
    # Only explicit augmentation suffixes are stripped. Ordinary numbered names
    # are not proof of a shared source photograph.
    stem = Path(filename).stem.lower()
    stem = re.sub(r'_(?:rotated|flipped|augmented|gamma|scaled|noise)(?:_?\d+)?$', '', stem)
    return f'filename:{label}:{stem}'


def difference_hash(image) -> str:
    from PIL import Image
    resized = image.convert('L').resize((9, 8), Image.Resampling.LANCZOS)
    pixels = list(resized.getdata())
    value = 0
    for row in range(8):
        for column in range(8):
            value = (value << 1) | int(pixels[row * 9 + column] > pixels[row * 9 + column + 1])
    resized.close()
    return f'{value:016x}'


def packaged_checksums(builder) -> list[dict]:
    import inspect
    module_directory = Path(inspect.getfile(type(builder))).parent
    candidates = [module_directory / 'checksums.tsv', module_directory / 'url_checksums' / 'plant_village.txt']
    # Older TFDS layouts keep checksums centrally rather than beside the builder.
    import tensorflow_datasets as tfds
    candidates.append(Path(tfds.__file__).parent / 'url_checksums' / 'plant_village.txt')
    result = []
    for candidate in candidates:
        if candidate.is_file():
            result.append({'filename': candidate.name, 'file_sha256': sha256_file(candidate),
                           'source_records': candidate.read_text(encoding='utf-8').splitlines()})
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('data/plant_village'))
    parser.add_argument('--tfds-dir', type=Path, default=Path('data/tfds'))
    parser.add_argument('--download-dir', type=Path, default=Path('data/downloads'))
    parser.add_argument('--dataset-version', default='1.0.2')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--train-fraction', type=float, default=.70)
    parser.add_argument('--validation-fraction', type=float, default=.15)
    parser.add_argument('--near-distance', type=int, choices=range(-1, 6), default=2,
                        help='64-bit dHash Hamming radius. -1 disables near grouping; exact/source groups remain.')
    parser.add_argument('--metadata-only', action='store_true', help='Inspect installed builder labels/provenance; no image download/splits.')
    parser.add_argument('--no-download', action='store_true', help='Require the previously prepared TFDS cache.')
    parser.add_argument('--allow-low-memory', action='store_true')
    arguments = parser.parse_args(argv)
    if not (0 < arguments.train_fraction < 1 and 0 < arguments.validation_fraction < 1
            and arguments.train_fraction + arguments.validation_fraction < 1):
        parser.error('Train/validation fractions must be positive and leave a positive test fraction.')
    available = preflight_memory(.3 if arguments.metadata_only else 1.5, arguments.allow_low_memory)
    try:
        import tensorflow_datasets as tfds
    except ImportError as error:
        raise RuntimeError('Install backend/requirements-training.txt in the training environment first.') from error
    arguments.output.mkdir(parents=True, exist_ok=True)
    builder = tfds.builder(f'plant_village:{arguments.dataset_version}', data_dir=str(arguments.tfds_dir), try_gcs=False)
    labels = list(builder.info.features['label'].names)
    metadata = {
        'schema_version': '1.0', 'prepared': False, 'created_at': datetime.now(timezone.utc).isoformat(),
        'dataset': 'plant_village', 'tfds_version': tfds.__version__, 'builder_version': str(builder.version),
        'ordered_labels': labels, 'label_count': len(labels), 'filename_feature': 'image/filename',
        'catalog_url': CATALOG, 'source_url': SOURCE, 'source_doi': '10.17632/tywbtsjrjv.1',
        'source_license': {'name': 'CC0 1.0', 'source': SOURCE, 'verified_at': '2026-10-23',
                           'note': 'Mendeley version 1 dataset license; separate from TensorFlow documentation/site license.'},
        'provenance_notes': [
            'TFDS uses republished unaugmented images and excludes Background_without_leaves.',
            'Mendeley describes a larger 39-class collection; installed TFDS builder and its actual records define this run.',
            'Class categories combine crops and conditions; they are not all distinct diseases or universal plant coverage.'
        ],
        'download_size_bytes': int(builder.info.download_size), 'dataset_size_bytes': int(builder.info.dataset_size),
        'checksums': packaged_checksums(builder), 'seed': arguments.seed,
        'available_ram_bytes_at_start': available, 'python_version': platform.python_version(),
        'grouping': {'exact': 'EXIF-oriented RGB pixel SHA256', 'source': 'filename UUID or explicit augmentation suffix',
                     'near': '64-bit difference hash', 'near_hamming_distance': arguments.near_distance},
        'limitations': [
            'No reliable plant/source-collection IDs are supplied for every photo; residual source leakage is possible.',
            'Perceptual grouping is conservative and may both miss near duplicates and over-group visually similar leaves.',
            'Cross-label duplicate components are excluded, never silently reassigned.',
            'Dataset holdout is not evidence of field-photo accuracy or unknown-species rejection.'
        ]
    }
    write_json(arguments.output / 'class_labels.json', labels)
    write_json(arguments.output / 'dataset_metadata.json', metadata)
    if arguments.metadata_only:
        print(json.dumps(metadata, indent=2))
        return 0
    if shutil.disk_usage(arguments.output).free < 5 * 1024**3 and not arguments.no_download:
        raise RuntimeError('Preparation needs at least 5 GiB free for archive, extracted data, TFRecords and exported images.')
    if not arguments.no_download:
        builder.download_and_prepare(download_dir=str(arguments.download_dir))
    import tensorflow as tf
    from PIL import Image, ImageOps, UnidentifiedImageError
    Image.MAX_IMAGE_PIXELS = 20_000_000
    dataset = builder.as_dataset(split='train', shuffle_files=False, decoders={'image': tfds.decode.SkipDecoding()})
    metadata['source_splits'] = {name: int(split.num_examples) for name, split in builder.info.splits.items()}
    metadata['tensorflow_version'] = tf.__version__
    metadata['download_size_bytes'] = int(builder.info.download_size)
    metadata['dataset_size_bytes'] = int(builder.info.dataset_size)
    (arguments.output / 'images').mkdir(exist_ok=True)
    records, invalid = [], []
    start = time.monotonic()
    for index, example in enumerate(tfds.as_numpy(dataset)):
        encoded = bytes(example['image'])
        filename = example['image/filename'].decode('utf-8', errors='replace')
        label_index = int(example['label'])
        label = labels[label_index]
        try:
            with Image.open(io.BytesIO(encoded)) as image:
                if image.width * image.height > 20_000_000 or getattr(image, 'n_frames', 1) != 1:
                    raise ValueError('Oversized or multi-frame dataset image')
                image.load()
                oriented = ImageOps.exif_transpose(image)
                rgb = oriented.convert('RGB')
                pixel_hash = hashlib.sha256(f'{rgb.size}:'.encode() + rgb.tobytes()).hexdigest()
                perceptual = difference_hash(rgb)
                rgb.close()
                if oriented is not image:
                    oriented.close()
        except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as error:
            invalid.append({'filename': filename, 'label_index': label_index, 'reason': type(error).__name__})
            continue
        encoded_hash = hashlib.sha256(encoded).hexdigest()
        relative = f'images/{encoded_hash}.jpg'
        destination = arguments.output / relative
        if not destination.exists():
            destination.write_bytes(encoded)
        records.append({'filename': filename, 'path': relative, 'label_index': label_index, 'label': label,
                        'encoded_sha256': encoded_hash, 'pixel_sha256': pixel_hash, 'dhash': perceptual,
                        'source_group': source_group(filename, label)})
        if (index + 1) % 1000 == 0:
            print(f'Validated/exported {index + 1} records in {time.monotonic() - start:.1f}s', flush=True)
    write_json(arguments.output / 'invalid_images.json', invalid)
    accepted, conflicts = group_records(records, arguments.near_distance)
    write_json(arguments.output / 'conflicting_groups.json', conflicts)
    fractions = (arguments.train_fraction, arguments.validation_fraction,
                 1 - arguments.train_fraction - arguments.validation_fraction)
    splits, class_counts = stratified_group_split(accepted, labels, arguments.seed, fractions)
    manifest_checksums = {}
    for split, rows in splits.items():
        destination = arguments.output / f'{split}.jsonl'
        with destination.open('w', encoding='utf-8', newline='\n') as handle:
            for row in rows:
                handle.write(json.dumps(row, sort_keys=True) + '\n')
        manifest_checksums[split] = sha256_file(destination)
    raw_counts = Counter(row['label'] for row in records)
    metadata.update({
        'prepared': True, 'records_read': len(records) + len(invalid), 'valid_images': len(records),
        'invalid_count': len(invalid), 'conflict_group_count': len(conflicts),
        'conflict_image_count': sum(len(group['records']) for group in conflicts),
        'retained_count': len(accepted), 'raw_class_counts': dict(raw_counts), 'class_split_counts': class_counts,
        'unique_exact_pixel_count': len({row['pixel_sha256'] for row in records}),
        'exact_duplicate_count': len(records) - len({row['pixel_sha256'] for row in records}),
        'split_counts': {split: len(rows) for split, rows in splits.items()},
        'class_imbalance_max_min': max(raw_counts.values()) / min(raw_counts.values()),
        'manifest_checksums': manifest_checksums, 'labels_sha256': sha256_file(arguments.output / 'class_labels.json'),
        'elapsed_seconds': round(time.monotonic() - start, 3)
    })
    write_json(arguments.output / 'dataset_metadata.json', metadata)
    print(json.dumps({key: metadata[key] for key in ['builder_version', 'valid_images', 'invalid_count',
                     'conflict_group_count', 'split_counts', 'manifest_checksums']}, indent=2))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (RuntimeError, ValueError) as error:
        print(f'Preparation failed: {error}', file=sys.stderr)
        raise SystemExit(1)
