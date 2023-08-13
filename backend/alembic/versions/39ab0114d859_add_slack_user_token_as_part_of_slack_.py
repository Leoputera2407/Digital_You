"""add slack user token as part of slack users

Revision ID: 39ab0114d859
Revises: 3ff354bead41
Create Date: 2023-07-25 20:19:48.034709

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "39ab0114d859"
down_revision = "3ff354bead41"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("slack_users", sa.Column("slack_user_token", sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("slack_users", "slack_user_token")
    # ### end Alembic commands ###
