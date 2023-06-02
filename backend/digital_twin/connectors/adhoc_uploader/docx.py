from .common import process_file
from langchain.document_loaders import Docx2txtLoader
from fastapi import UploadFile


def process_docx(file: UploadFile):
    return process_file(file, Docx2txtLoader, ".docx")
