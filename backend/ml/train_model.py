"""Train a genuine MobileNetV2 classifier from prepared, group-separated manifests."""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from .common import load_json, preflight_memory, sha256_file, validate_manifests, write_json


def make_dataset(tf, rows, prepared: Path, batch_size: int, training: bool = False, seed: int = 42):
    from .preprocessing import path_to_array
    paths = [str((prepared / row['path']).resolve()) for row in rows]
    labels = [row['label_index'] for row in rows]
    dataset = tf.data.Dataset.from_tensor_slices((paths, labels))
    if training:
        dataset = dataset.shuffle(min(len(paths), 10000), seed=seed, reshuffle_each_iteration=True)
    def read(path, label):
        def decode(value):
            return path_to_array(value.item().decode() if hasattr(value, 'item') else value.decode())
        image = tf.numpy_function(decode, [path], tf.float32)
        image.set_shape((224, 224, 3))
        return image, label
    options = tf.data.Options()
    options.experimental_deterministic = True
    options.threading.private_threadpool_size = 2
    dataset = dataset.with_options(options).map(read, num_parallel_calls=2, deterministic=True)
    # Never .cache() decoded images: full PlantVillage would need many GiB.
    return dataset.batch(batch_size).prefetch(1)


def ensure_manifest_integrity(prepared: Path, metadata: dict) -> None:
    if metadata.get('prepared') is not True:
        raise ValueError('Dataset metadata is inspection-only, not a completed preparation.')
    for split in ('train', 'validation', 'test'):
        expected = metadata.get('manifest_checksums', {}).get(split)
        if not expected or sha256_file(prepared / f'{split}.jsonl') != expected:
            raise ValueError(f'{split} manifest checksum does not match prepared dataset metadata.')
    if sha256_file(prepared / 'class_labels.json') != metadata.get('labels_sha256'):
        raise ValueError('Prepared ordered labels changed after splitting.')


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepared', type=Path, default=Path('data/plant_village'))
    parser.add_argument('--output', type=Path, default=Path('models'))
    parser.add_argument('--reports', type=Path, default=Path('reports'))
    parser.add_argument('--model-version', default='plant-village-mobilenet-v2-1')
    parser.add_argument('--epochs', type=int, default=15)
    parser.add_argument('--fine-tune-epochs', type=int, default=5)
    parser.add_argument('--batch-size', type=int, default=16)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--class-weight', action='store_true')
    parser.add_argument('--allow-low-memory', action='store_true')
    arguments = parser.parse_args(argv)
    if arguments.epochs < 1 or arguments.fine_tune_epochs < 0 or arguments.batch_size < 1:
        parser.error('Use positive epochs/batch size; fine-tune epochs may be zero.')
    available = preflight_memory(3.0, arguments.allow_low_memory)
    dataset_metadata = load_json(arguments.prepared / 'dataset_metadata.json')
    ensure_manifest_integrity(arguments.prepared, dataset_metadata)
    labels, manifests = validate_manifests(arguments.prepared)
    if (arguments.output / 'plant_disease_model.keras').exists():
        raise ValueError('Output already contains a model. Use a NEW versioned --output directory to preserve existing artifacts.')
    os.environ.setdefault('TF_DETERMINISTIC_OPS', '1')
    import numpy as np
    import tensorflow as tf
    tf.keras.utils.set_random_seed(arguments.seed)
    try:
        tf.config.experimental.enable_op_determinism()
    except (AttributeError, RuntimeError):
        pass
    arguments.output.mkdir(parents=True, exist_ok=True)
    arguments.reports.mkdir(parents=True, exist_ok=True)
    train = make_dataset(tf, manifests['train'], arguments.prepared, arguments.batch_size, True, arguments.seed)
    validation = make_dataset(tf, manifests['validation'], arguments.prepared, arguments.batch_size)
    counts = Counter(row['label_index'] for row in manifests['train'])
    if len(counts) != len(labels):
        raise ValueError('Every ordered class must have training examples.')
    weights = ({index: len(manifests['train']) / (len(labels) * count) for index, count in counts.items()}
               if arguments.class_weight else None)
    backbone = tf.keras.applications.MobileNetV2(input_shape=(224, 224, 3), include_top=False, weights='imagenet')
    backbone.trainable = False
    inputs = tf.keras.Input(shape=(224, 224, 3), name='rgb_0_255')
    # Augmentation executes only during training; validation/inference are unchanged.
    augmentation = tf.keras.Sequential([
        tf.keras.layers.RandomFlip('horizontal_and_vertical', seed=arguments.seed),
        tf.keras.layers.RandomRotation(.08, fill_mode='reflect', seed=arguments.seed + 1),
        tf.keras.layers.RandomZoom(.1, fill_mode='reflect', seed=arguments.seed + 2),
        tf.keras.layers.RandomContrast(.1, seed=arguments.seed + 3),
    ], name='training_only_augmentation')
    values = augmentation(inputs)
    values = tf.keras.layers.Rescaling(1.0 / 127.5, offset=-1, name='mobilenet_v2_normalization')(values)
    # BatchNorm always inference mode; controlled fine-tuning updates convolution weights.
    values = backbone(values, training=False)
    values = tf.keras.layers.GlobalAveragePooling2D()(values)
    values = tf.keras.layers.Dropout(.25, seed=arguments.seed + 4)(values)
    outputs = tf.keras.layers.Dense(len(labels), activation='softmax', dtype='float32', name='class_probabilities')(values)
    model = tf.keras.Model(inputs, outputs, name='plant_disease_mobilenet_v2')
    model.compile(optimizer=tf.keras.optimizers.Adam(1e-3), loss='sparse_categorical_crossentropy', metrics=['accuracy'])
    head_checkpoint = arguments.output / 'head_best.keras'
    callbacks = lambda path: [
        tf.keras.callbacks.ModelCheckpoint(str(path), monitor='val_loss', save_best_only=True),
        tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=4, restore_best_weights=True),
        tf.keras.callbacks.ReduceLROnPlateau(monitor='val_loss', patience=2, factor=.5, min_lr=1e-6),
        tf.keras.callbacks.TerminateOnNaN(),
    ]
    start = time.monotonic()
    history = model.fit(train, validation_data=validation, epochs=arguments.epochs,
                        class_weight=weights, callbacks=callbacks(head_checkpoint))
    if not head_checkpoint.is_file():
        raise RuntimeError('Training produced no successful validation checkpoint.')
    head_loss = min(history.history['val_loss'])
    chosen = head_checkpoint
    histories = {'head': history.history}
    if arguments.fine_tune_epochs:
        model = tf.keras.models.load_model(head_checkpoint, compile=False, safe_mode=True)
        backbone = model.get_layer('mobilenetv2_1.00_224')
        backbone.trainable = True
        for layer in backbone.layers[:-30]:
            layer.trainable = False
        for layer in backbone.layers:
            if isinstance(layer, tf.keras.layers.BatchNormalization):
                layer.trainable = False
        model.compile(optimizer=tf.keras.optimizers.Adam(1e-5), loss='sparse_categorical_crossentropy', metrics=['accuracy'])
        fine_checkpoint = arguments.output / 'fine_tune_best.keras'
        fine = model.fit(train, validation_data=validation, epochs=arguments.fine_tune_epochs,
                         class_weight=weights, callbacks=callbacks(fine_checkpoint))
        histories['fine_tune'] = fine.history
        if fine_checkpoint.is_file() and min(fine.history['val_loss']) < head_loss:
            chosen = fine_checkpoint
    final_path = arguments.output / 'plant_disease_model.keras'
    shutil.copy2(chosen, final_path)
    shutil.copy2(arguments.prepared / 'class_labels.json', arguments.output / 'class_labels.json')
    write_json(arguments.reports / 'training_history.json', histories)
    environment = {
        'python': platform.python_version(), 'tensorflow': tf.__version__, 'keras': tf.keras.__version__,
        'numpy': np.__version__, 'platform': platform.platform(),
        'devices': [device.name for device in tf.config.list_physical_devices()],
        'seed': arguments.seed, 'available_ram_bytes_at_start': available,
        'requested_head_epochs': arguments.epochs, 'completed_head_epochs': len(histories['head']['loss']),
        'requested_fine_tune_epochs': arguments.fine_tune_epochs,
        'completed_fine_tune_epochs': len(histories.get('fine_tune', {}).get('loss', [])),
        'batch_size': arguments.batch_size, 'class_weights': weights,
        'chosen_checkpoint': chosen.name, 'elapsed_seconds': round(time.monotonic() - start, 3),
        'reproducibility_limits': 'Seeded deterministic operations requested. Hardware/library changes can still alter results.',
    }
    write_json(arguments.reports / 'training_environment.json', environment)
    metadata = {
        'schema_version': '1.0', 'model_version': arguments.model_version,
        'created_at': datetime.now(timezone.utc).isoformat(), 'architecture': 'MobileNetV2',
        'pretrained_weights': 'ImageNet', 'trained': True,
        'input_shape': [224, 224, 3], 'input_dtype': 'float32', 'input_range': [0, 255],
        'preprocessing': 'mobilenet_v2', 'normalization_in_model': True,
        'normalization': 'Rescaling(1/127.5, offset=-1) exactly once inside model',
        'resize_policy': 'bilinear_stretch', 'color_mode': 'EXIF-oriented RGB',
        'output_type': 'probabilities', 'score_type': 'uncalibrated_softmax_score',
        'calibration_status': 'uncalibrated', 'class_count': len(labels),
        'model_sha256': sha256_file(final_path),
        'labels_sha256': sha256_file(arguments.output / 'class_labels.json'),
        'dataset': {'name': dataset_metadata['dataset'], 'builder_version': dataset_metadata['builder_version'],
                    'tfds_version': dataset_metadata['tfds_version'],
                    'preparation_metadata_sha256': sha256_file(arguments.prepared / 'dataset_metadata.json'),
                    'manifest_checksums': dataset_metadata['manifest_checksums'],
                    'split_counts': dataset_metadata['split_counts'], 'source_url': dataset_metadata['source_url']},
        'training': environment,
        'decision_policy': {'min_score': 1.0, 'min_margin': 1.0, 'validated': False,
                            'reason': 'Evaluation not run; every result must remain uncertain.'},
        'evaluation': None,
        'limitations': dataset_metadata['limitations'] + [
            'Closed-set crop classifier; softmax scores do not identify all unknown plants/non-leaf inputs.',
            'Healthy predicts resemblance to a dataset class, not absence of every plant problem.'
        ],
    }
    write_json(arguments.output / 'model_metadata.json', metadata)
    write_json(arguments.output / 'checksums.json', {name: sha256_file(arguments.output / name) for name in
               ['plant_disease_model.keras', 'class_labels.json', 'model_metadata.json']})
    print(json.dumps({'model': str(final_path), 'training_completed': True, 'evaluation_completed': False,
                      'next': f'python -m ml.evaluate_model --prepared {arguments.prepared} --bundle {arguments.output} --reports {arguments.reports}'}, indent=2))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (RuntimeError, ValueError, FileNotFoundError) as error:
        print(f'Training failed: {error}', file=sys.stderr)
        raise SystemExit(1)
