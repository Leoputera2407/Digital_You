from typing import Optional, List
from enum import Enum
from pydantic import BaseModel

from digital_twin.config.constants import DocumentSource
from digital_twin.connectors.model import InputType

# TODO: Make this a more localized somehow
map_platform_to_db_api_key_type = {
    "slack": "slack_bot_token",
    "openai": "openai_api_key", 
    "anthropic": "anthropic_api_key"
}

class DBAPIKeyType(str, Enum):
    SLACK_BOT_KEY = "slack_bot_key"
    ANTHROPHIC_API_KEY = "anthrophic_api_key"
    OPENAI_API_KEY = "openai_api_key"

class IndexingStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"

class DBSupportedModelType(str, Enum):
    GPT3_5 = "GPT3_5"
    GPT4 = "GPT4"
    ANTHROPIC = "ANTHROPIC"

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
    
    
# slack_installations
class Installation(BaseModel):
    id: int
    enterprise_id: str
    team_id: str
    user_id: str
    bot: dict
    installed_at: str
    

# slack_bots
class SlackBot(BaseModel):
    id: int
    app_id: str
    enterprise_id: str
    team_id: str
    user_id: str
    bot_token: str
    bot_refresh_token: str
    bot_token_expires_at: str
    bot_id: str
    bot_user_id: str
    bot_scopes: str
    installed_at: str
    
# slack_states
class SlackState(BaseModel):
    id: int
    state: str # HG: supabase says 'uuid' so not sure about this type
    consumed: bool
    created_at: str

# slack_users
class SlackUser(BaseModel):
    id: int
    team_id: str
    slack_user_id: str
    user_id: str
    slack_display_name: str
    conversation_style: str
    contiguous_chat_transcript: str
    chat_pairs: str
