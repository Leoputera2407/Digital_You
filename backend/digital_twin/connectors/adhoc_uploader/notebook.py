from .common import process_file
from langchain.document_loaders import NotebookLoader
from fastapi import UploadFile


def process_ipnyb(file: UploadFile):
    return process_file(file, NotebookLoader, "ipynb")
