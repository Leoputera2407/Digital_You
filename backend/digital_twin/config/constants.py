from enum import Enum

DOCUMENT_ID = "document_id"
CHUNK_ID = "chunk_id"
BLURB = "blurb"
CONTENT = "content"
SOURCE_TYPE = "source_type"
SOURCE_LINKS = "source_links"
SOURCE_LINK = "link"
METADATA = "metadata"
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
            "groups:read",
            "users:read.email",
        ]
SLACK_USER_SCOPES = [
    "chat:write"
]

DEFAULT_SLACK_CONVERSATION_STYLE="""
The style of conversation is formal, precise, and usually in third person perspective. 
It uses business jargon and technical language when necessary, and is devoid of slang, 
abbreviations or colloquialisms. This style is characterized by clear and direct statements, 
with a courteous and respectful tone. Responses are generally thorough, providing complete 
information and avoiding ambiguity. This style prioritizes maintaining a serious, business-like 
tone, even when the other party is more casual.
"""

class DocumentSource(str, Enum):
    SLACK = "slack"
    WEB = "web"
    GOOGLE_DRIVE = "google_drive"
    GITHUB = "github"
    CONFLUENCE = "confluence"
    ADHOC_UPLOAD = "file_upload"
    NOTION = "notion"
    JIRA = "jira"
    LINEAR = "linear"

class UserRole(str, Enum):
    BASIC = "basic"
    ADMIN = "admin"
