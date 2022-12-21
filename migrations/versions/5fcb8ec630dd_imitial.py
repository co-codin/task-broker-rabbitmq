"""imitial

Revision ID: 5fcb8ec630dd
Revises: 
Create Date: 2022-11-29 20:50:32.911053

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5fcb8ec630dd'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('queries',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('guid', sa.String(length=36), nullable=False),
    sa.Column('query', sa.Text(), nullable=False),
    sa.Column('compiled_query', sa.Text(), nullable=True),
    sa.Column('status', sa.String(length=64), nullable=False),
    sa.Column('error_description', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_queries_guid'), 'queries', ['guid'], unique=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_queries_guid'), table_name='queries')
    op.drop_table('queries')
    # ### end Alembic commands ###