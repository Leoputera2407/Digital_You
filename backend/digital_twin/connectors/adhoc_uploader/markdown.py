from .common import process_file
from langchain.document_loaders import UnstructuredMarkdownLoader
from fastapi import UploadFile


def process_markdown(file: UploadFile):
    return process_file(file, UnstructuredMarkdownLoader, ".md")
