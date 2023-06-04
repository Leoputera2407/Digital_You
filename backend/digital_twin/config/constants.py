from enum import Enum

DOCUMENT_ID = "document_id"
CHUNK_ID = "chunk_id"
BLURB = "blurb"
CONTENT = "content"
SOURCE_TYPE = "source_type"
SOURCE_LINKS = "source_links"
SOURCE_LINK = "link"
SEMANTIC_IDENTIFIER = "semantic_identifier"
SECTION_CONTINUATION = "section_continuation"


class DocumentSource(str, Enum):
    SLACK = "slack"
    WEB = "web"
    GOOGLE_DRIVE = "google_drive"
    GITHUB = "github"
    CONFLUENCE = "confluence"
    ADHOC_UPLOAD = "file_upload"

class SupportedPromptType(str, Enum):
    STUFF = "stuff"
    REFINE = "refine"

class UserRole(str, Enum):
    BASIC = "basic"
    ADMIN = "admin"