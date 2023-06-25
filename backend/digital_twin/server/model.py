from datetime import datetime
from typing import Any, Generic, Literal, Optional, TypeVar, TYPE_CHECKING
from pydantic import BaseModel
from pydantic.generics import GenericModel

from digital_twin.config.constants import DocumentSource
from digital_twin.connectors.model import InputType
from digital_twin.indexdb.interface import IndexDBFilter
from digital_twin.db.model import Connector, IndexingStatus, DBAPIKeyType, DBSupportedModelType

DataT = TypeVar("DataT")

class StatusResponse(GenericModel, Generic[DataT]):
    success: bool
    message: Optional[str] = None
    data: Optional[DataT] = None


class DataRequest(BaseModel):
    data: str


class GoogleAppCredentials(BaseModel):
    client_id: str
    project_id: str
    auth_uri: str
    token_uri: str
    auth_provider_x509_cert_url: str
    client_secret: str
    redirect_uris: list[str]
    javascript_origins: Optional[list[str]]


class GoogleAppWebCredentials(BaseModel):
    web: GoogleAppCredentials



class ObjectCreationIdResponse(BaseModel):
    id: int | str


class AuthStatus(BaseModel):
    authenticated: bool


class AuthUrl(BaseModel):
    auth_url: str


class GDriveCallback(BaseModel):
    state: str
    code: str

class NotionCallback(BaseModel):
    code: str

class UserRoleResponse(BaseModel):
    role: str


class SearchDoc(BaseModel):
    semantic_identifier: str
    link: str | None
    blurb: str
    source_type: str

class QuestionRequest(BaseModel):
    query: str
    collection: str
    filters: list[IndexDBFilter] | None
    offset: int | None

class SearchResponse(BaseModel):
    # For semantic search, top docs are reranked, the remaining are as ordered from retrieval
    top_ranked_docs: list[SearchDoc] | None
    lower_ranked_docs: list[SearchDoc] | None

class QAResponse(SearchResponse):
    answer: str | None
    quotes: dict[str, dict[str, str | int | None]] | None

class UserByEmail(BaseModel):
    user_email: str


class IndexAttemptRequest(BaseModel):
    input_type: InputType = InputType.POLL
    connector_specific_config: dict[str, Any]

class ConnectorBase(BaseModel):
    name: str
    source: DocumentSource
    input_type: InputType
    connector_specific_config: dict[str, Any]
    refresh_freq: int | None  # In seconds, None for one time index with no refresh
    disabled: bool


class ConnectorSnapshot(ConnectorBase):
    id: int
    credential_ids: list[int]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_connector_db_model(cls, connector: Connector) -> "ConnectorSnapshot":
        return ConnectorSnapshot(
            id=connector.id,
            name=connector.name,
            source=connector.source,
            input_type=connector.input_type,
            connector_specific_config=connector.connector_specific_config,
            refresh_freq=connector.refresh_freq,
            credential_ids=[
                association.credential.id for association in connector.credentials
            ],
            created_at=connector.created_at,
            updated_at=connector.updated_at,
            disabled=connector.disabled,
        )


class ConnectorIndexingStatus(BaseModel):
    """Represents the latest indexing status of a connector"""

    connector: ConnectorSnapshot
    owner: str
    public_doc: bool
    last_status: IndexingStatus
    last_success: datetime | None
    docs_indexed: int


class RunConnectorRequest(BaseModel):
    connector_id: int
    credential_ids: list[int] | None


class CredentialBase(BaseModel):
    credential_json: dict[str, Any]
    public_doc: bool


class CredentialSnapshot(CredentialBase):
    id: int
    user_id: str
    created_at: datetime
    updated_at: datetime


class APIKeyBase(BaseModel):
    key_type: DBAPIKeyType
    key_value: str

class BaseModelConfig(BaseModel):
    supported_model_enum: DBSupportedModelType
    temperature: float
