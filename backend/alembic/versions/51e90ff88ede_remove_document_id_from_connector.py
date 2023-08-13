"""remove document_id from connector

Revision ID: 51e90ff88ede
Revises: 90c27498c973
Create Date: 2023-08-12 21:28:44.528670

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "51e90ff88ede"
down_revision = "90c27498c973"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "google_app_credentials",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("credentials_json", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "organizations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("whitelisted_email_domain", sa.String(), nullable=True),
        sa.Column(
            "qdrant_collection_key", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column(
            "typesense_collection_key", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("first_name", sa.String(), nullable=True),
        sa.Column("last_name", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "connector",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column(
            "source",
            sa.Enum(
                "SLACK",
                "WEB",
                "GOOGLE_DRIVE",
                "GITHUB",
                "CONFLUENCE",
                "ADHOC_UPLOAD",
                "NOTION",
                "JIRA",
                "LINEAR",
                name="documentsource",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "input_type",
            sa.Enum("LOAD_STATE", "POLL", "EVENT", name="inputtype", native_enum=False),
            nullable=True,
        ),
        sa.Column("connector_specific_config", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("refresh_freq", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("disabled", sa.Boolean(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "credential",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("credential_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("organization_id", sa.UUID(), nullable=True),
        sa.Column("public_doc", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "invitations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("inviter_id", sa.UUID(), nullable=False),
        sa.Column("invitee_email", sa.String(), nullable=False),
        sa.Column("token", sa.String(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("PENDING", "ACCEPTED", name="invitationstatus", native_enum=False),
            server_default="pending",
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["inviter_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "slack_bots",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("client_id", sa.String(length=32), nullable=False),
        sa.Column("app_id", sa.String(length=32), nullable=False),
        sa.Column("enterprise_id", sa.String(length=32), nullable=True),
        sa.Column("enterprise_name", sa.String(length=200), nullable=True),
        sa.Column("team_id", sa.String(length=32), nullable=False),
        sa.Column("team_name", sa.String(length=200), nullable=True),
        sa.Column("bot_token", sa.String(length=200), nullable=False),
        sa.Column("bot_id", sa.String(length=32), nullable=False),
        sa.Column("bot_user_id", sa.String(length=32), nullable=False),
        sa.Column("bot_scopes", sa.String(length=1000), nullable=False),
        sa.Column("bot_refresh_token", sa.String(length=200), nullable=True),
        sa.Column("bot_token_expires_at", sa.DateTime(), nullable=True),
        sa.Column("is_enterprise_install", sa.Boolean(), nullable=False),
        sa.Column("installed_at", sa.DateTime(), nullable=False),
        sa.Column("prosona_organization_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["prosona_organization_id"],
            ["organizations.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "bots_idx", "slack_bots", ["client_id", "enterprise_id", "team_id", "installed_at"], unique=False
    )
    op.create_table(
        "slack_installations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("client_id", sa.String(length=32), nullable=False),
        sa.Column("app_id", sa.String(length=32), nullable=False),
        sa.Column("enterprise_id", sa.String(length=32), nullable=True),
        sa.Column("enterprise_name", sa.String(length=200), nullable=True),
        sa.Column("enterprise_url", sa.String(length=200), nullable=True),
        sa.Column("team_id", sa.String(length=32), nullable=False),
        sa.Column("team_name", sa.String(length=200), nullable=True),
        sa.Column("bot_token", sa.String(length=200), nullable=True),
        sa.Column("bot_id", sa.String(length=32), nullable=False),
        sa.Column("bot_user_id", sa.String(length=32), nullable=False),
        sa.Column("bot_scopes", sa.String(length=1000), nullable=False),
        sa.Column("bot_refresh_token", sa.String(length=200), nullable=True),
        sa.Column("bot_token_expires_at", sa.DateTime(), nullable=True),
        sa.Column("user_id", sa.String(length=32), nullable=False),
        sa.Column("user_token", sa.String(length=200), nullable=True),
        sa.Column("user_scopes", sa.String(length=1000), nullable=True),
        sa.Column("user_refresh_token", sa.String(length=200), nullable=True),
        sa.Column("user_token_expires_at", sa.DateTime(), nullable=True),
        sa.Column("incoming_webhook_url", sa.String(length=200), nullable=True),
        sa.Column("incoming_webhook_channel", sa.String(length=200), nullable=True),
        sa.Column("incoming_webhook_channel_id", sa.String(length=200), nullable=True),
        sa.Column("incoming_webhook_configuration_url", sa.String(length=200), nullable=True),
        sa.Column("is_enterprise_install", sa.Boolean(), nullable=False),
        sa.Column("token_type", sa.String(length=32), nullable=True),
        sa.Column("installed_at", sa.DateTime(), nullable=False),
        sa.Column("prosona_organization_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["prosona_organization_id"],
            ["organizations.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "installations_idx",
        "slack_installations",
        ["client_id", "enterprise_id", "team_id", "user_id", "installed_at"],
        unique=False,
    )
    op.create_table(
        "slack_oauth_states",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("state", sa.String(length=200), nullable=False),
        sa.Column("expire_at", sa.DateTime(), nullable=False),
        sa.Column("prosona_organization_id", sa.UUID(), nullable=False),
        sa.Column("prosona_user_id", sa.UUID(), nullable=False),
        sa.Column(
            "slack_integration_type",
            sa.Enum("CONNECTOR", "USER", name="slackintegration", native_enum=False),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["prosona_organization_id"],
            ["organizations.id"],
        ),
        sa.ForeignKeyConstraint(
            ["prosona_user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "slack_organization_associations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("team_id", sa.String(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("team_name", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("team_id", "organization_id"),
    )
    op.create_table(
        "user_organization_association",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column(
            "role",
            sa.Enum("BASIC", "ADMIN", name="userrole", native_enum=False),
            server_default="basic",
            nullable=False,
        ),
        sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("user_id", "organization_id"),
    )
    op.create_table(
        "connector_credential_pair",
        sa.Column("connector_id", sa.Integer(), nullable=False),
        sa.Column("credential_id", sa.Integer(), nullable=False),
        sa.Column("last_successful_index_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "last_attempt_status",
            sa.Enum("NOT_STARTED", "IN_PROGRESS", "SUCCESS", "FAILED", name="indexingstatus"),
            nullable=False,
        ),
        sa.Column("total_docs_indexed", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["connector_id"],
            ["connector.id"],
        ),
        sa.ForeignKeyConstraint(
            ["credential_id"],
            ["credential.id"],
        ),
        sa.PrimaryKeyConstraint("connector_id", "credential_id"),
    )
    op.create_table(
        "csrf_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("credential_id", sa.Integer(), nullable=False),
        sa.Column("csrf_token", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["credential_id"],
            ["credential.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "index_attempt",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("connector_id", sa.Integer(), nullable=True),
        sa.Column("credential_id", sa.Integer(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("NOT_STARTED", "IN_PROGRESS", "SUCCESS", "FAILED", name="indexingstatus"),
            nullable=False,
        ),
        sa.Column("error_msg", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["connector_id"],
            ["connector.id"],
        ),
        sa.ForeignKeyConstraint(
            ["credential_id"],
            ["credential.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "slack_users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("team_id", sa.String(), nullable=False),
        sa.Column("slack_user_email", sa.String(), nullable=False),
        sa.Column("slack_user_id", sa.String(), nullable=False),
        sa.Column("slack_display_name", sa.String(), nullable=True),
        sa.Column("conversation_style", sa.String(), nullable=True),
        sa.Column("contiguous_chat_transcript", sa.String(), nullable=True),
        sa.Column("chat_pairs", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("slack_organization_association_id", sa.Integer(), nullable=False),
        sa.Column("slack_user_token", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["slack_organization_association_id"],
            ["slack_organization_associations.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("team_id", "slack_user_email", name="_team_id_slack_user_email_uc"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("slack_users")
    op.drop_table("index_attempt")
    op.drop_table("csrf_tokens")
    op.drop_table("connector_credential_pair")
    op.drop_table("user_organization_association")
    op.drop_table("slack_organization_associations")
    op.drop_table("slack_oauth_states")
    op.drop_index("installations_idx", table_name="slack_installations")
    op.drop_table("slack_installations")
    op.drop_index("bots_idx", table_name="slack_bots")
    op.drop_table("slack_bots")
    op.drop_table("invitations")
    op.drop_table("credential")
    op.drop_table("connector")
    op.drop_table("users")
    op.drop_table("organizations")
    op.drop_table("google_app_credentials")
    # ### end Alembic commands ###
