from .common import process_file
from langchain.document_loaders import UnstructuredPowerPointLoader
from fastapi import UploadFile


def process_powerpoint(file: UploadFile):
    return process_file(file, UnstructuredPowerPointLoader, ".pptx")
