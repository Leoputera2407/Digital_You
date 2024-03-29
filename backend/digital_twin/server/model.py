from datetime import datetime
from typing import Any, Generic, List, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel
from pydantic.generics import GenericModel

from digital_twin.config.constants import DocumentSource
from digital_twin.connectors.linear.model import LinearTeam
from digital_twin.connectors.model import InputType
from digital_twin.db.model import Connector, IndexingStatus, User, UserRole
from digital_twin.indexdb.interface import IndexDBFilter

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
    state: str


class LinearCallback(BaseModel):
    state: str
    code: str


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


class UserAdminData(UserByEmail):
    user_id: UUID
    role: UserRole


class InvitationBase(BaseModel):
    email: str
    status: str


class OrganizationData(BaseModel):
    name: str
    id: UUID


class SlackUserDataResponse(BaseModel):
    slack_user_name: str
    slack_user_email: str
    slack_team_name: str


class OrganizationAdminInfo(OrganizationData):
    whitelisted_email_domain: Optional[str]
    pending_invitations: List[InvitationBase]
    users: List[UserAdminData]


class OrganizationUpdateInfoRequest(BaseModel):
    name: Optional[str] = None
    whitelisted_email_domain: Optional[str] = None


class OrganizationCreateRequest(BaseModel):
    name: str
    invited_users: List[UserByEmail]


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
            credential_ids=[association.credential.id for association in connector.credentials],
            created_at=connector.created_at,
            updated_at=connector.updated_at,
            disabled=connector.disabled,
            user=connector.user,
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


class OrganizationAssociationBase(BaseModel):
    id: UUID
    name: str
    role: UserRole
    joined_at: datetime


class UserOrgResponse(BaseModel):
    organizations: List[OrganizationAssociationBase]


class GithubTestRequest(BaseModel):
    access_token_value: str
    repository_name: str
    repository_owner: str


class ConfluenceTestRequest(BaseModel):
    confluence_access_token: str
    confluence_username: str
    wiki_page_url: str


class LinearOrganizationSnapshot(BaseModel):
    name: str
    teams: List[LinearTeam]


class NotionWorkspaceSnapshot(BaseModel):
    name: str
