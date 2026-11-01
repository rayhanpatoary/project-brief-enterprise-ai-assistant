import pytest

from app.ingestion import InvalidDocument, prepare_document


def test_splitting_metadata_stable_ids(settings):
    data = ('A policy with useful company information. ' * 100).encode()
    key, docs = prepare_document('../../policy.md', data, settings)
    assert len(docs) > 1
    assert all(len(doc.page_content) <= 200 for doc in docs)
    assert all(doc.metadata['document_name'] == 'policy.md' for doc in docs)
    assert all(doc.metadata['page'] == 1 for doc in docs)
    assert len({doc.metadata['chunk_id'] for doc in docs}) == len(docs)
    assert prepare_document('renamed.md', data, settings)[0] == key
    assert prepare_document('policy.md', data, settings)[1] == docs


@pytest.mark.parametrize('filename,data', [
    ('bad.exe', b'not allowed'), ('empty.txt', b''), ('blank.md', b'  \n'),
    ('fake.pdf', b'not a pdf'), ('corrupt.pdf', b'%PDF-1.4\nbroken'),
    ('binary.txt', b'hello\x00world'), ('bad.txt', b'\xff'),
])
def test_invalid_files(settings, filename, data):
    with pytest.raises(InvalidDocument):
        prepare_document(filename, data, settings)


def test_limits(settings):
    settings.max_upload_bytes = 4
    with pytest.raises(InvalidDocument, match='limit'):
        prepare_document('big.txt', b'12345', settings)


def test_text_limit(settings):
    settings.max_document_chars = 4
    with pytest.raises(InvalidDocument, match='too large'):
        prepare_document('big.txt', b'12345', settings)


def test_real_assignment_pdf(settings):
    from zipfile import ZipFile
    with ZipFile('documents/documents.zip') as archive:
        name = next(n for n in archive.namelist() if n.endswith('.pdf') and not n.startswith('__MACOSX'))
        key, docs = prepare_document(name, archive.read(name), settings)
    assert docs and docs[0].metadata['document_id'] == key
    assert docs[0].metadata['page'] == 1
