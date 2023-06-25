from enum import Enum

DOCUMENT_ID = "document_id"
CHUNK_ID = "chunk_id"
BLURB = "blurb"
CONTENT = "content"
SOURCE_TYPE = "source_type"
SOURCE_LINKS = "source_links"
SOURCE_LINK = "link"
ALLOWED_USERS = "allowed_users"
ALLOWED_GROUPS = "allowed_groups"
SEMANTIC_IDENTIFIER = "semantic_identifier"
SECTION_CONTINUATION = "section_continuation"
HTML_SEPARATOR = "\n"
PUBLIC_DOC_PAT = "PUBLIC"


SLACK_APP_PERMISSIONS = [
            "app_mentions:read",
            "channels:history",
            "channels:join",
            "channels:read",
            "chat:write",
            "chat:write.customize",
            "commands",
            "users.profile:read",
            "users:read",
        ]

class DocumentSource(str, Enum):
    SLACK = "slack"
    WEB = "web"
    GOOGLE_DRIVE = "google_drive"
    GITHUB = "github"
    CONFLUENCE = "confluence"
    ADHOC_UPLOAD = "file_upload"
    NOTION = "notion"

class UserRole(str, Enum):
    BASIC = "basic"
    ADMIN = "admin"