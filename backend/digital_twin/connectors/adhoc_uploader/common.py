
import os
import tempfile
import time

from fastapi import UploadFile
from digital_twin.config.constants import DocumentSource
from digital_twin.connectors.model import Document, Section
from digital_twin.utils.indexing_pipeline import build_indexing_pipeline

from utils import compute_sha1_from_file, compute_sha1_from_content, documents_vector_store


async def process_file(file: UploadFile, loader_class, file_suffix):
    file_name = file.filename
    # Here, we're writing the uploaded file to a temporary file, so we can use it with your existing code.
    with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmp_file:
        await file.seek(0)
        content = await file.read()
        tmp_file.write(content)
        tmp_file.flush()

        loader = loader_class(tmp_file.name)
        langchain_docs = loader.load()
        # Ensure this function works with FastAPI
        file_sha1 = compute_sha1_from_file(tmp_file.name)

    os.remove(tmp_file.name)
    sections = []
    for doc in langchain_docs:
        sections.append(Section(link=None, text=doc.page_content))

    doc = Document(
        id=file_sha1,
        sections=sections,
        source=DocumentSource.ADHOC_UPLOAD,
        semantic_identifier=file_name,
        metadata={},
    )

    build_indexing_pipeline()([doc])

    return


async def file_already_exists(supabase, file):
    file_content = await file.read()
    file_sha1 = compute_sha1_from_content(file_content)
    response = supabase.table("documents").select("id").eq(
        "metadata->>file_sha1", file_sha1).execute()
    return len(response.data) > 0
