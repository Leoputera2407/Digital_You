import os
from tempfile import NamedTemporaryFile
import tempfile
import time
import openai

from utils import compute_sha1_from_content, documents_vector_store
from fastapi import UploadFile

from digital_twin.config.app_config import OPENAI_API_KEY
from digital_twin.config.constants import DocumentSource
from digital_twin.connectors.models import Document, Section
from digital_twin.utils.indexing_pipeline import build_indexing_pipeline

async def process_audio(upload_file: UploadFile):

    dateshort = time.strftime("%Y%m%d-%H%M%S")
    file_name = upload_file.filename
    file_meta_name = f"audiotranscript_{dateshort}.txt"

    # TODO: Get OPENAI_API_KEY from supabase
    openai_api_key = OPENAI_API_KEY

    # Here, we're writing the uploaded file to a temporary file, so we can use it with your existing code.
    with tempfile.NamedTemporaryFile(delete=False, suffix=upload_file.filename) as tmp_file:
        await upload_file.seek(0)
        content = await upload_file.read()
        tmp_file.write(content)
        tmp_file.flush()
        tmp_file.close()

        with open(tmp_file.name, "rb") as audio_file:
            transcript = openai.Audio.transcribe("whisper-1", audio_file, api_key=openai_api_key)

    file_sha1 = compute_sha1_from_content(transcript.text.encode("utf-8"))

    doc = Document(
        id=file_sha1,
        sections=Section(link=None, text=transcript.text),
        source=DocumentSource.ADHOC_UPLOAD,
        semantic_identifier=file_name,
        metadata={file_meta_name: file_meta_name},
    )

    build_indexing_pipeline()([doc])

    return
