"""Verify and atomically import a trusted locally trained model bundle."""
from __future__ import annotations
import argparse
import os
import shutil
import sys
import tempfile
from pathlib import Path
from .common import load_json, preflight_memory, sha256_file
from .evaluate_model import load_verified_model, validate_bundle_files

REQUIRED = ('plant_disease_model.keras', 'class_labels.json', 'model_metadata.json', 'checksums.json')


def import_bundle(source: Path, destination: Path, allow_unevaluated=False):
    source, destination = source.resolve(), destination.resolve()
    if not source.is_dir() or source == destination or source.is_relative_to(destination) or destination.is_relative_to(source):
        raise ValueError('Source/destination must be separate, non-nested directories.')
    if destination.exists():
        raise ValueError('Destination exists. Import into a NEW versioned directory; never overwrite a running bundle.')
    checksums = load_json(source / 'checksums.json')
    for filename in REQUIRED:
        path = source / filename
        if not path.is_file() or path.is_symlink() or path.resolve().parent != source:
            raise ValueError(f'Required artifact is missing, linked or outside bundle: {filename}')
        if filename != 'checksums.json' and sha256_file(path) != checksums.get(filename):
            raise ValueError(f'Artifact checksum mismatch: {filename}')
    _, metadata = validate_bundle_files(source)
    if metadata.get('trained') is not True:
        raise ValueError('Bundle is not identified as a trained artifact.')
    if not allow_unevaluated and not (metadata.get('evaluation') or {}).get('test'):
        raise ValueError('No genuine held-out evaluation recorded; evaluate this bundle before production import.')
    # safe_mode reduces deserialization risk, but is not a sandbox: only import
    # artifacts that YOU trained or obtained through a verified trusted channel.
    load_verified_model(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='.plantcare-import-', dir=destination.parent)).resolve()
    try:
        for filename in REQUIRED:
            shutil.copy2(source / filename, staging / filename)
        load_verified_model(staging)
        os.replace(staging, destination)
    finally:
        if staging.exists() and staging.parent == destination.parent and staging.name.startswith('.plantcare-import-'):
            shutil.rmtree(staging)
    return destination


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--trust-local-artifact', action='store_true', required=True,
                        help='Required acknowledgement: source was trained by you or independently verified as trusted.')
    parser.add_argument('--allow-unevaluated', action='store_true', help='Development only; backend will keep unvalidated decisions uncertain.')
    parser.add_argument('--allow-low-memory', action='store_true')
    args = parser.parse_args(argv)
    preflight_memory(2.0, args.allow_low_memory)
    destination = import_bundle(args.source, args.output, args.allow_unevaluated)
    print(f'Verified model imported to {destination}. Configure MODEL_PATH, CLASS_LABELS_PATH and MODEL_METADATA_PATH for this version.')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (RuntimeError, ValueError, FileNotFoundError) as error:
        print(f'Model import failed: {error}', file=sys.stderr)
        raise SystemExit(1)
