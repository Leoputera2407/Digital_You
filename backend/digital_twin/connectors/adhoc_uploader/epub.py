from .common import process_file
from langchain.document_loaders.epub import UnstructuredEPubLoader
from fastapi import UploadFile


def process_epub(file: UploadFile):
    return process_file(file, UnstructuredEPubLoader, ".epub")
