from datetime import datetime
from typing import Any, Generic, Literal, Optional, TypeVar, TYPE_CHECKING
from pydantic import BaseModel
from pydantic.generics import GenericModel

from digital_twin.config.constants import DocumentSource
from digital_twin.connectors.model import InputType
from digital_twin.vectordb.interface import VectorDBFilter
from digital_twin.db.model import Connector, IndexingStatus, DBAPIKeyType, DBSupportedModelType
from digital_twin.db.connectors.connectors import get_connector_credentials

DataT = TypeVar("DataT")

class StatusResponse(GenericModel, Generic[DataT]):
    success: bool
    message: Optional[str] = None
    data: Optional[DataT] = None


class DataRequest(BaseModel):
    data: str


class GoogleAppWebCredentials(BaseModel):
    client_id: str
    project_id: str
    auth_uri: str
    token_uri: str
    auth_provider_x509_cert_url: str
    client_secret: str
    redirect_uris: list[str]
    javascript_origins: list[str]


class GoogleAppCredentials(BaseModel):
    web: GoogleAppWebCredentials


class HealthCheckResponse(BaseModel):
    status: Literal["ok"]


class ObjectCreationIdResponse(BaseModel):
    id: int | str


class AuthStatus(BaseModel):
    authenticated: bool


class AuthUrl(BaseModel):
    auth_url: str


class GDriveCallback(BaseModel):
    state: str
    code: str


class UserRoleResponse(BaseModel):
    role: str


class SearchDoc(BaseModel):
    semantic_identifier: str
    link: str | None
    blurb: str
    source_type: str


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
        credentials = get_connector_credentials(connector.id)
        return ConnectorSnapshot(
            id=connector.id,
            name=connector.name,
            source=connector.source,
            input_type=connector.input_type,
            connector_specific_config=connector.connector_specific_config,
            refresh_freq=connector.refresh_freq,
            credential_ids=[credential.id for credential in credentials],
            created_at=connector.created_at,
            updated_at=connector.updated_at,
            disabled=connector.disabled,
        )

class ConnectorIndexingStatus(BaseModel):
    """Represents the latest indexing status of a connector"""

    connector: ConnectorSnapshot
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
    user_id: int | None
    created_at: datetime
    updated_at: datetime


class IndexAttemptSnapshot(BaseModel):
    source: DocumentSource
    input_type: InputType
    status: IndexingStatus
    connector_specific_config: dict[str, Any]
    docs_indexed: int
    created_at: datetime
    updated_at: datetime


class ApiKey(BaseModel):
    api_key: str

class APIKeyBase(BaseModel):
    key_type: DBAPIKeyType
    key_value: str
    user_id: str


class BaseModelConfig(BaseModel):
    supported_model_enum: DBSupportedModelType
    temperature: float
    user_id: str