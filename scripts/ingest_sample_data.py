"""Index synthetic demo files or the assignment ZIP without extracting untrusted paths."""
import argparse
import json
from pathlib import Path
from zipfile import ZipFile

from app.config import get_settings
from app.vector_store import KnowledgeStore


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assignment', action='store_true', help='Index original documents/documents.zip instead of demo files.')
    args = parser.parse_args()
    store = KnowledgeStore(get_settings())
    failures = 0

    def index(name, content):
        nonlocal failures
        try:
            print(json.dumps({'file': name, **store.ingest(name, content)}))
        except Exception:
            failures += 1
            print(json.dumps({'file': name, 'error': 'Indexing failed; check PDF content, provider quota and configuration.'}))

    if args.assignment:
        with ZipFile('documents/documents.zip') as archive:
            for entry in archive.infolist():
                if '__MACOSX' in entry.filename or Path(entry.filename).name.startswith('.'):
                    continue
                if Path(entry.filename).suffix.lower() in {'.pdf', '.txt', '.md'}:
                    if entry.file_size > store.settings.max_upload_bytes:
                        failures += 1
                        print(json.dumps({'file': entry.filename, 'error': 'File exceeds upload limit.'}))
                        continue
                    index(entry.filename, archive.read(entry))
    else:
        for file in sorted(Path('data/sample_documents').iterdir()):
            if file.suffix.lower() in {'.pdf', '.txt', '.md'}:
                index(file.name, file.read_bytes())
    raise SystemExit(1 if failures else 0)


if __name__ == '__main__':
    main()
