"""Add author_name to BlogPost

Revision ID: b0fff1d3dfe6
Revises: b7b09a965041
Create Date: 2025-02-22 14:00:53.658947

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b0fff1d3dfe6'
down_revision = 'b7b09a965041'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('blog_posts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('author_name', sa.String(length=100), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('blog_posts', schema=None) as batch_op:
        batch_op.drop_column('author_name')

    # ### end Alembic commands ###
