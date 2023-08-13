import hashlib
import os
import tempfile
import zipfile
from collections.abc import Generator
from pathlib import Path
from typing import IO, Any

from langchain.document_loaders import (
    Docx2txtLoader,
    PyPDFLoader,
    TextLoader,
    UnstructuredHTMLLoader,
    UnstructuredMarkdownLoader,
    UnstructuredPowerPointLoader,
)
from langchain.document_loaders.epub import UnstructuredEPubLoader

from digital_twin.config.constants import DocumentSource
from digital_twin.connectors.model import Document, Section
from digital_twin.utils.clients import get_supabase_client

BUCKET_NAME = "documents"
_VALID_FILE_EXTENSIONS = [
    ".md",
    ".markdown",
    ".pdf",
    ".html",
    ".pptx",
    ".ppt",
    ".docx",
    ".doc",
    ".epub",
    ".txt",
    ".zip",
]
file_processors = {
    ".txt": TextLoader,
    ".md": UnstructuredMarkdownLoader,
    ".markdown": UnstructuredMarkdownLoader,
    ".pdf": PyPDFLoader,
    ".html": UnstructuredHTMLLoader,
    ".pptx": UnstructuredPowerPointLoader,
    ".ppt": UnstructuredPowerPointLoader,
    ".docx": Docx2txtLoader,
    ".doc": Docx2txtLoader,
    ".epub": UnstructuredEPubLoader,
}


def get_files_from_zip(
    zip_location: str | Path,
) -> Generator[tuple[str, IO[Any]], None, None]:
    with zipfile.ZipFile(zip_location, "r") as zip_file:
        for file_name in zip_file.namelist():
            with zip_file.open(file_name, "r") as file:
                yield os.path.basename(file_name), file


def get_file_ext(file_path_or_name: str | Path) -> str:
    _, extension = os.path.splitext(file_path_or_name)
    return extension


def check_file_ext_is_valid(ext: str) -> bool:
    return ext in _VALID_FILE_EXTENSIONS


def compute_sha1_from_content(content):
    readable_hash = hashlib.sha1(content).hexdigest()
    return readable_hash


def write_temp_files(
    files: list[tuple[str, IO[Any]]],
    supabase_user_id: str,
) -> list[str]:
    """Writes temporary files to disk and returns their paths

    NOTE: need to pass in (file_name, File) tuples since FastAPI's `UploadFile` class
    exposed SpooledTemporaryFile does not include a name.
    """
    supabase = get_supabase_client()

    file_paths: list[str] = []
    for file_name, file in files:
        extension = get_file_ext(file_name)
        if not check_file_ext_is_valid(extension):
            raise ValueError(
                f"Invalid file extension for file: '{file_name}'. Must be one of {_VALID_FILE_EXTENSIONS}"
            )

        bucket_file_path = f"{supabase_user_id}/{file_name}"
        file_content = file.read()
        res = supabase.storage.from_(BUCKET_NAME).upload(bucket_file_path, file_content, upsert=True)

        if "error" in res:
            raise Exception(f"Error uploading file to Supabase: {res['error']['message']}")

        file_paths.append(bucket_file_path)

    return file_paths


def process_file(
    file_path: str,
) -> Generator[Document, None, None]:
    supabase = get_supabase_client()
    res = supabase.storage.from_(BUCKET_NAME).download(file_path)
    extension = get_file_ext(file_path)

    if extension == ".zip":
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=True) as temp_file:
            temp_file.write(res["data"].read())
            for file_name, file in get_files_from_zip(temp_file.name):
                if not check_file_ext_is_valid(get_file_ext(file_name)):
                    continue
                file_content = file.read()
                loader_class = file_processors[get_file_ext(file_name)]
                loader = loader_class(file_content)
                langchain_docs = loader.load()
                file_sha1 = compute_sha1_from_content(file_content)
                for doc in langchain_docs:
                    yield Document(
                        id=file_name,
                        sections=[Section(link="", text=doc.page_content)],
                        source=DocumentSource.ADHOC_UPLOAD,
                        semantic_identifier=file_name,
                        metadata={
                            "sha1": file_sha1,
                        },
                    )
    else:
        file_content = res["data"].read()
        loader_class = file_processors[extension]
        loader = loader_class(file_content)
        langchain_docs = loader.load()
        file_sha1 = compute_sha1_from_content(file_content)

        for doc in langchain_docs:
            yield Document(
                id=file_name,
                sections=[Section(link="", text=doc.page_content)],
                source=DocumentSource.ADHOC_UPLOAD,
                semantic_identifier=file_name,
                metadata={
                    "sha1": file_sha1,
                },
            )
