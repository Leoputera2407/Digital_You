"""added joined_at for org

Revision ID: 984ef0c0d759
Revises: b2c1b69e582e
Create Date: 2023-07-02 23:40:00.860529

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '984ef0c0d759'
down_revision = 'b2c1b69e582e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user_organization_association', sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user_organization_association', 'joined_at')
    # ### end Alembic commands ###