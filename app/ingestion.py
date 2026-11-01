"""Validate and split untrusted files without writing uploaded filenames to disk."""
import hashlib
from io import BytesIO
from pathlib import PurePosixPath

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from app.config import Settings


class InvalidDocument(ValueError):
    pass


def prepare_document(filename: str, content: bytes, settings: Settings) -> tuple[str, list[Document]]:
    name = PurePosixPath(filename.replace('\\', '/')).name
    extension = PurePosixPath(name).suffix.lower()
    if extension not in {'.pdf', '.txt', '.md'}:
        raise InvalidDocument('Supported files: PDF, TXT and Markdown.')
    if not content:
        raise InvalidDocument('The file is empty.')
    if len(content) > settings.max_upload_bytes:
        raise InvalidDocument(f'File exceeds {settings.max_upload_bytes // 1024 // 1024} MB limit.')
    document_id = hashlib.sha256(content).hexdigest()
    try:
        if extension == '.pdf':
            if not content.startswith(b'%PDF-'):
                raise InvalidDocument('File is not a valid PDF.')
            reader = PdfReader(BytesIO(content))
            if reader.is_encrypted:
                raise InvalidDocument('Encrypted PDFs are unsupported.')
            pages = []
            total = 0
            for number, page in enumerate(reader.pages, 1):
                text = page.extract_text() or ''
                total += len(text)
                if total > settings.max_document_chars:
                    raise InvalidDocument('Extracted document is too large.')
                pages.append((number, text))
        else:
            text = content.decode('utf-8-sig')
            if '\x00' in text or any(ord(c) < 32 and c not in '\n\r\t' for c in text):
                raise InvalidDocument('Text files must contain readable UTF-8 text.')
            pages = [(1, text)]
    except InvalidDocument:
        raise
    except Exception as exc:
        raise InvalidDocument('Could not read file. Use an unencrypted text PDF or UTF-8 text.') from exc
    if sum(len(text) for _, text in pages) > settings.max_document_chars:
        raise InvalidDocument('Extracted document is too large.')
    if not any(text.strip() for _, text in pages):
        raise InvalidDocument('No readable text found. Scanned PDFs require OCR before upload.')
    if settings.chunk_overlap >= settings.chunk_size:
        raise InvalidDocument('Chunk overlap must be smaller than chunk size.')
    splitter = RecursiveCharacterTextSplitter(chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_overlap)
    chunks = []
    for page, text in pages:
        for part in splitter.split_text(text):
            index = len(chunks)
            chunk_id = f'{document_id}:{index}'
            chunks.append(Document(page_content=part, metadata={
                'document_id': document_id, 'document_name': name, 'source': name,
                'page': page, 'chunk_index': index, 'chunk_id': chunk_id,
            }))
    return document_id, chunks
