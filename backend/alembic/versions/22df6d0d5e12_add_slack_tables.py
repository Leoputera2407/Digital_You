"""add slack tables

Revision ID: 22df6d0d5e12
Revises: cd675875f017
Create Date: 2023-06-23 11:21:45.427315

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '22df6d0d5e12'
down_revision = 'cd675875f017'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('slack_bots',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('client_id', sa.String(length=32), nullable=False),
    sa.Column('app_id', sa.String(length=32), nullable=False),
    sa.Column('enterprise_id', sa.String(length=32), nullable=True),
    sa.Column('enterprise_name', sa.String(length=200), nullable=True),
    sa.Column('team_id', sa.String(length=32), nullable=True),
    sa.Column('team_name', sa.String(length=200), nullable=True),
    sa.Column('bot_token', sa.String(length=200), nullable=True),
    sa.Column('bot_id', sa.String(length=32), nullable=True),
    sa.Column('bot_user_id', sa.String(length=32), nullable=True),
    sa.Column('bot_scopes', sa.String(length=1000), nullable=True),
    sa.Column('bot_refresh_token', sa.String(length=200), nullable=True),
    sa.Column('bot_token_expires_at', sa.DateTime(), nullable=True),
    sa.Column('is_enterprise_install', sa.Boolean(), nullable=False),
    sa.Column('installed_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('bots_idx', 'slack_bots', ['client_id', 'enterprise_id', 'team_id', 'installed_at'], unique=False)
    op.create_table('slack_installations',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('client_id', sa.String(length=32), nullable=False),
    sa.Column('app_id', sa.String(length=32), nullable=False),
    sa.Column('enterprise_id', sa.String(length=32), nullable=True),
    sa.Column('enterprise_name', sa.String(length=200), nullable=True),
    sa.Column('enterprise_url', sa.String(length=200), nullable=True),
    sa.Column('team_id', sa.String(length=32), nullable=True),
    sa.Column('team_name', sa.String(length=200), nullable=True),
    sa.Column('bot_token', sa.String(length=200), nullable=True),
    sa.Column('bot_id', sa.String(length=32), nullable=True),
    sa.Column('bot_user_id', sa.String(length=32), nullable=True),
    sa.Column('bot_scopes', sa.String(length=1000), nullable=True),
    sa.Column('bot_refresh_token', sa.String(length=200), nullable=True),
    sa.Column('bot_token_expires_at', sa.DateTime(), nullable=True),
    sa.Column('user_id', sa.String(length=32), nullable=False),
    sa.Column('user_token', sa.String(length=200), nullable=True),
    sa.Column('user_scopes', sa.String(length=1000), nullable=True),
    sa.Column('user_refresh_token', sa.String(length=200), nullable=True),
    sa.Column('user_token_expires_at', sa.DateTime(), nullable=True),
    sa.Column('incoming_webhook_url', sa.String(length=200), nullable=True),
    sa.Column('incoming_webhook_channel', sa.String(length=200), nullable=True),
    sa.Column('incoming_webhook_channel_id', sa.String(length=200), nullable=True),
    sa.Column('incoming_webhook_configuration_url', sa.String(length=200), nullable=True),
    sa.Column('is_enterprise_install', sa.Boolean(), nullable=False),
    sa.Column('token_type', sa.String(length=32), nullable=True),
    sa.Column('installed_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('installations_idx', 'slack_installations', ['client_id', 'enterprise_id', 'team_id', 'user_id', 'installed_at'], unique=False)
    op.create_table('slack_oauth_states',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('state', sa.String(length=200), nullable=False),
    sa.Column('expire_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('slack_oauth_states')
    op.drop_index('installations_idx', table_name='slack_installations')
    op.drop_table('slack_installations')
    op.drop_index('bots_idx', table_name='slack_bots')
    op.drop_table('slack_bots')
    # ### end Alembic commands ###
