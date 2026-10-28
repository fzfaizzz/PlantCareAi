"""Create the small, credential-free training source archive for Colab."""
import argparse
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('plantcare-training-code.zip'))
    args = parser.parse_args()
    backend = Path(__file__).resolve().parent.parent
    files = sorted((backend / 'ml').glob('*.py')) + [backend / 'requirements-training.txt']
    if args.output.resolve() in [path.resolve() for path in files]:
        parser.error('Output would overwrite a source file.')
    with ZipFile(args.output, 'w', compression=ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, path.relative_to(backend).as_posix())
    print(f'{args.output.resolve()} ({args.output.stat().st_size} bytes): only ml/*.py and requirements-training.txt; no images, keys or environment files.')


if __name__ == '__main__':
    main()
