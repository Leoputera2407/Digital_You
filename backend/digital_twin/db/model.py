from typing import Optional, List
from enum import Enum
from uuid import UUID
from pydantic import BaseModel, EmailStr
from datetime import datetime

from digital_twin.config.constants import DocumentSource
from digital_twin.connectors.model import InputType

# TODO: Make this a more localized somehow
map_platform_to_db_api_key_type = {
    "slack": "slack_bot_token",
    "openai": "openai_api_key", 
    "anthropic": "anthropic_api_key"
}

DB_MODEL_PLATFORM = ["anthrophic_api_key", "openai_api_key"]
    
class DBAPIKeyType(str, Enum):
    ANTHROPHIC_API_KEY = "anthrophic_api_key"
    OPENAI_API_KEY = "openai_api_key"
    SLACK_BOT_KEY = "slack_bot_key"

class DBSupportedModelType(str, Enum):
    GPT3_5 = "GPT3_5"
    GPT4 = "GPT4"
    ANTHROPIC = "ANTHROPIC"

class IndexingStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"

class User(BaseModel):
    id: UUID
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: EmailStr
    qdrant_collection_key: UUID

class Credential(BaseModel):
    id: int
    credential_json: dict
    public_doc: bool
    user_id: Optional[str]
    created_at: str
    updated_at: str


class IndexAttempt(BaseModel):
    id: int
    connector_id: int
    credential_id: int
    status: IndexingStatus
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    document_ids: Optional[List[str]] = None
    error_msg: Optional[str] = None

class Connector(BaseModel):
    id: int
    name: str
    user_id: Optional[str]
    source: DocumentSource
    input_type: InputType
    connector_specific_config: dict
    refresh_freq: int
    created_at: str
    updated_at: str
    disabled: bool

class ConnectorCredentialAssociation(BaseModel):
    connector_id: int
    credential_id: int

class APIKey(BaseModel):
    id: int
    key_type: DBAPIKeyType
    key_value: str
    created_at: str
    updated_at: str
    user_id: str

class ModelConfig(BaseModel):
    id: int
    supported_model_enum: DBSupportedModelType
    temperature: float
    user_id: str
    
# slack_bots
class SlackBot(BaseModel):
    id: int
    app_id: str
    enterprise_id: Optional[str]
    team_id: str
    user_id: str
    bot_token: str
    bot_refresh_token: Optional[str]
    bot_token_expires_at: Optional[datetime]
    bot_id: str
    bot_user_id: str
    bot_scopes: str
    installed_at: datetime
    
# slack_installations
class Installation(BaseModel):
    id: int
    enterprise_id: Optional[str]
    team_id: str
    user_id: str
    bot: str
    installed_at: datetime

    
# slack_states
class SlackState(BaseModel):
    id: int
    state: str # confirm this type
    consumed: bool
    created_at: datetime

# slack_users
class SlackUser(BaseModel):
    id: int
    team_id: str
    slack_user_id: str
    user_id: str
    slack_display_name: Optional[str]
    conversation_style: Optional[str]
    contiguous_chat_transcript: Optional[str]
    chat_pairs: Optional[str]



class DBGoogleAppCredential(BaseModel):
    credentials_json: str
    created_at: str
    updated_at: str

class DBCSRFToken(BaseModel):
    credential_id: int
    csrf_token: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
