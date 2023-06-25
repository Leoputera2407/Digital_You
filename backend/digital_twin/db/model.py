from enum import Enum as pyEnum
from datetime import datetime
from typing import List, Any
from sqlalchemy import (
    Index,
    Enum, 
    ForeignKey, 
    Integer, 
    String, 
    Integer, 
    DateTime, 
    Boolean,
    Float,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects import postgresql
from sqlalchemy import func
from sqlalchemy.orm import (
    DeclarativeBase,
    relationship, 
    Mapped,
    mapped_column,
)

from digital_twin.config.constants import DocumentSource
from digital_twin.connectors.model import InputType

# TODO: Make this a more localized somehow
map_platform_to_db_api_key_type = {
    "slack": "slack_bot_token",
    "openai": "openai_api_key", 
    "anthropic": "anthropic_api_key"
}

DB_MODEL_PLATFORM = ["anthrophic_api_key", "openai_api_key"]

class DBAPIKeyType(str, pyEnum):
    ANTHROPHIC_API_KEY = "anthrophic_api_key"
    OPENAI_API_KEY = "openai_api_key"
    SLACK_BOT_KEY = "slack_bot_key"

class DBSupportedModelType(str, pyEnum):
    GPT3_5 = "GPT3_5"
    GPT4 = "GPT4"
    ANTHROPIC = "ANTHROPIC"

class IndexingStatus(str, pyEnum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"

class UserRole(str, pyEnum):
    BASIC = "basic"
    ADMIN = "admin"


class Base(DeclarativeBase):
    pass

class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    qdrant_collection_key: Mapped[UUID] = mapped_column(UUID(as_uuid=True), server_default=func.gen_random_uuid())
    typesense_collection_key: Mapped[UUID] = mapped_column(UUID(as_uuid=True), server_default=func.gen_random_uuid())

    users: Mapped[List["User"]] = relationship(
        "User",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    connectors: Mapped[List["Connector"]] = relationship(
        "Connector",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    api_keys: Mapped[List["APIKey"]] = relationship(
        "APIKey",
        back_populates="organization",
        lazy="joined",
    )
    model_configs: Mapped[List["ModelConfig"]] = relationship(
        "ModelConfig",
        back_populates="organization",
        lazy="joined",
    )

    # Remember UUID == str even if the contents are the same, so we need to use this.
    def get_qdrant_collection_key_str(self) -> str:
        return str(self.qdrant_collection_key)

    def get_typesense_collection_key_str(self) -> str:
        return str(self.typesense_collection_key)
    
class User(Base):
    __tablename__ = "users"

    # TODO: Supabase doesn't expose their auth.users schema, so we can't put a reference it as a foreign key
    # This is handled in the handle_new_users() trigger that can be found in the Supabase UI
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    organization_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"))
    first_name: Mapped[str | None] = mapped_column(String, nullable=True)
    last_name: Mapped[str | None] = mapped_column(String, nullable=True)
    email: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False, default=UserRole.BASIC), server_default=UserRole.BASIC.value
    )
    organization: Mapped[Organization] = relationship(
        "Organization", back_populates="users", lazy="joined"
    )

    credentials: Mapped[List["Credential"]] = relationship(
        "Credential", back_populates="user", lazy="joined"
    )

    slack_users: Mapped[List["SlackUser"]] = relationship(
        "SlackUser",
        back_populates="user",
        lazy="joined",
    )


class ConnectorCredentialPair(Base):
    """Connectors and Credentials can have a many-to-many relationship
    I.e. A Confluence Connector may have multiple admin users who can run it with their own credentials
    I.e. An admin user may use the same credential to index multiple Confluence Spaces
    """

    __tablename__ = "connector_credential_pair"
    connector_id: Mapped[int] = mapped_column(
        ForeignKey("connector.id"), primary_key=True
    )
    credential_id: Mapped[int] = mapped_column(
        ForeignKey("credential.id"), primary_key=True
    )
    last_successful_index_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    last_attempt_status: Mapped[IndexingStatus] = mapped_column(Enum(IndexingStatus))
    total_docs_indexed: Mapped[int] = mapped_column(Integer, default=0)

    connector: Mapped["Connector"] = relationship(
        "Connector", back_populates="credentials"
    )
    credential: Mapped["Credential"] = relationship(
        "Credential", back_populates="connectors"
    )


class Connector(Base):
    __tablename__ = "connector"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)
    source: Mapped[DocumentSource] = mapped_column(
        Enum(DocumentSource, native_enum=False)
    )
    input_type = mapped_column(Enum(InputType, native_enum=False))
    connector_specific_config: Mapped[dict[str, Any]] = mapped_column(
        postgresql.JSONB()
    )
    refresh_freq: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    disabled: Mapped[bool] = mapped_column(Boolean, default=False)
    organization_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('organizations.id'))


    organization: Mapped[Organization] = relationship(
                "Organization", 
                back_populates="connectors"
    )
    credentials: Mapped[List["ConnectorCredentialPair"]] = relationship(
        "ConnectorCredentialPair",
        back_populates="connector",
        cascade="all, delete-orphan",
    )
    index_attempts: Mapped[List["IndexAttempt"]] = relationship(
        "IndexAttempt", back_populates="connector"
    )


class Credential(Base):
    __tablename__ = "credential"

    id: Mapped[int] = mapped_column(primary_key=True)
    credential_json: Mapped[dict[str, Any]] = mapped_column(postgresql.JSONB())
    user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    # This means anyone can read the index
    public_doc: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    connectors: Mapped[List["ConnectorCredentialPair"]] = relationship(
        "ConnectorCredentialPair",
        back_populates="credential",
        cascade="all, delete-orphan",
    )
    index_attempts: Mapped[List["IndexAttempt"]] = relationship(
        "IndexAttempt", back_populates="credential"
    )
    csrf_tokens: Mapped[List["CSRFToken"]] = relationship(
        "CSRFToken", back_populates="credential", cascade="all, delete-orphan"
    )
    user: Mapped[User] = relationship("User", back_populates="credentials")


class IndexAttempt(Base):
    """
    Represents an attempt to index a group of 1 or more documents from a
    source. For example, a single pull from Google Drive, a single event from
    slack event API, or a single website crawl.
    """

    __tablename__ = "index_attempt"

    id: Mapped[int] = mapped_column(primary_key=True)
    connector_id: Mapped[int | None] = mapped_column(
        ForeignKey("connector.id"),
        nullable=True,
    )
    credential_id: Mapped[int | None] = mapped_column(
        ForeignKey("credential.id"),
        nullable=True,
    )
    status: Mapped[IndexingStatus] = mapped_column(Enum(IndexingStatus))
    document_ids: Mapped[list[str] | None] = mapped_column(
        postgresql.ARRAY(String()), default=None
    )  # only filled if status = "complete"
    error_msg: Mapped[str | None] = mapped_column(
        String(), default=None
    )  # only filled if status = "failed"
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    connector: Mapped[Connector] = relationship(
        "Connector", back_populates="index_attempts"
    )
    credential: Mapped[Credential] = relationship(
        "Credential", back_populates="index_attempts"
    )

    def __repr__(self) -> str:
        return (
            f"<IndexAttempt(id={self.id!r}, "
            f"connector_id={self.connector_id!r}, "
            f"status={self.status!r}, "
            f"document_ids={self.document_ids!r}, "
            f"error_msg={self.error_msg!r})>"
            f"created_at={self.created_at!r}, "
            f"updated_at={self.updated_at!r}, "
        )

class APIKey(Base):
    __tablename__ = 'api_keys'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key_type: Mapped[DBAPIKeyType] = mapped_column(Enum(DBAPIKeyType))
    key_value: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    organization_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('organizations.id'))

    organization: Mapped[Organization] = relationship("Organization", back_populates="api_keys")


class ModelConfig(Base):
    __tablename__ = 'model_configs'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    supported_model_enum: Mapped[DBSupportedModelType] = mapped_column(Enum(DBSupportedModelType))
    temperature: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    organization_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('organizations.id'))

    organization: Mapped[Organization] = relationship("Organization", back_populates="model_configs")


class SlackUser(Base):
    __tablename__ = 'slack_users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    team_id: Mapped[str] = mapped_column(String)
    slack_user_id: Mapped[str] = mapped_column(String)
    slack_display_name: Mapped[str | None] = mapped_column(String, nullable=True)
    conversation_style: Mapped[str | None] = mapped_column(String, nullable=True)
    contiguous_chat_transcript: Mapped[str | None] = mapped_column(String, nullable=True)
    chat_pairs: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.id'))

    user: Mapped[User] = relationship("User", back_populates="slack_users")

class GoogleAppCredential(Base):
    __tablename__ = 'google_app_credentials'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    credentials_json: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

class CSRFToken(Base):
    __tablename__ = 'csrf_tokens'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    credential_id: Mapped[int] = mapped_column(Integer, ForeignKey('credential.id'))
    csrf_token: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    credential: Mapped[Credential] = relationship("Credential", back_populates="csrf_tokens")


# These are copied over from Slack_SDK 
#  OuathStore (https://github.com/slackapi/python-slack-sdk/blob/main/slack_sdk/oauth/state_store/sqlalchemy/__init__.py)
#  InstallationStore (https://github.com/slackapi/python-slack-sdk/blob/main/slack_sdk/oauth/installation_store/sqlalchemy/__init__.py)
# The function they provide doesn't allow us to expose it to our Base.
class SlackOAuthStates(Base):
    __tablename__ = "slack_oauth_states"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    state: Mapped[str] = mapped_column(String(200), nullable=False)
    expire_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

class SlackInstallations(Base):
    __tablename__ = "slack_installations"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    client_id: Mapped[str] = mapped_column(String(32), nullable=False)
    app_id: Mapped[str] = mapped_column(String(32), nullable=False)
    enterprise_id: Mapped[str] = mapped_column(String(32), nullable=True)
    enterprise_name: Mapped[str] = mapped_column(String(200), nullable=True)
    enterprise_url: Mapped[str] = mapped_column(String(200), nullable=True)
    team_id: Mapped[str] = mapped_column(String(32), nullable=False)
    team_name: Mapped[str] = mapped_column(String(200), nullable=True)
    bot_token: Mapped[str] = mapped_column(String(200), nullable=True)
    bot_id: Mapped[str] = mapped_column(String(32), nullable=False)
    bot_user_id: Mapped[str] = mapped_column(String(32), nullable=False)
    bot_scopes: Mapped[str] = mapped_column(String(1000), nullable=False)
    bot_refresh_token: Mapped[str] = mapped_column(String(200), nullable=True)
    bot_token_expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    user_id: Mapped[str] = mapped_column(String(32), nullable=False)
    user_token: Mapped[str] = mapped_column(String(200), nullable=True)
    user_scopes: Mapped[str] = mapped_column(String(1000), nullable=True)
    user_refresh_token: Mapped[str] = mapped_column(String(200), nullable=True)
    user_token_expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    incoming_webhook_url: Mapped[str] = mapped_column(String(200), nullable=True)
    incoming_webhook_channel: Mapped[str] = mapped_column(String(200), nullable=True)
    incoming_webhook_channel_id: Mapped[str] = mapped_column(String(200), nullable=True)
    incoming_webhook_configuration_url: Mapped[str] = mapped_column(String(200), nullable=True)
    is_enterprise_install: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    token_type: Mapped[str] = mapped_column(String(32), nullable=True)
    installed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    
    __table_args__ = (
        Index(
            "installations_idx",
            "client_id",
            "enterprise_id",
            "team_id",
            "user_id",
            "installed_at",
        ),
    )

class SlackBots(Base):
    __tablename__ = "slack_bots"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    client_id: Mapped[str] = mapped_column(String(32), nullable=False)
    app_id: Mapped[str] = mapped_column(String(32), nullable=False)
    enterprise_id: Mapped[str] = mapped_column(String(32), nullable=True)
    enterprise_name: Mapped[str] = mapped_column(String(200), nullable=True)
    team_id: Mapped[str] = mapped_column(String(32), nullable=False)
    team_name: Mapped[str] = mapped_column(String(200), nullable=True)
    bot_token: Mapped[str] = mapped_column(String(200), nullable=False)
    bot_id: Mapped[str] = mapped_column(String(32), nullable=False)
    bot_user_id: Mapped[str] = mapped_column(String(32), nullable=False)
    bot_scopes: Mapped[str] = mapped_column(String(1000), nullable=False)
    bot_refresh_token: Mapped[str] = mapped_column(String(200), nullable=True)
    bot_token_expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    is_enterprise_install: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    installed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    
    __table_args__ = (
        Index(
            "bots_idx",
            "client_id",
            "enterprise_id",
            "team_id",
            "installed_at",
        ),
    )
