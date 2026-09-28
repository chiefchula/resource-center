"""Add quarterly item checks (ItemCheck + last_checked fields)

Revision ID: a88b957d007d
Revises: 15ef8481e337
Create Date: 2026-09-28 20:08:48.047407

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a88b957d007d'
down_revision = '15ef8481e337'
branch_labels = None
depends_on = None


def upgrade():
    # 1. New table: item_checks
    op.create_table(
        'item_checks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('checked_by_id', sa.Integer(), nullable=False),
        sa.Column('checked_at', sa.DateTime(), nullable=False),
        sa.Column('condition', sa.String(length=50), nullable=True),
        sa.Column('status_found', sa.String(length=30), nullable=True),
        sa.Column('location_note', sa.String(length=200), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['checked_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['item_id'], ['items.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )

    # 2. Add is_active to categories (with server default so existing rows get 1)
    with op.batch_alter_table('categories', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                'is_active',
                sa.Boolean(),
                nullable=False,
                server_default=sa.true(),
            )
        )

    # 3. Add last_checked fields to items + FK to users
    with op.batch_alter_table('items', schema=None) as batch_op:
        batch_op.add_column(sa.Column('last_checked_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('last_checked_by_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_items_last_checked_by_id_users',
            'users',
            ['last_checked_by_id'],
            ['id'],
        )


def downgrade():
    # 1. Drop the FK and last_checked columns from items
    with op.batch_alter_table('items', schema=None) as batch_op:
        batch_op.drop_constraint('fk_items_last_checked_by_id_users', type_='foreignkey')
        batch_op.drop_column('last_checked_by_id')
        batch_op.drop_column('last_checked_at')

    # 2. Drop is_active from categories
    with op.batch_alter_table('categories', schema=None) as batch_op:
        batch_op.drop_column('is_active')

    # 3. Drop the item_checks table
    op.drop_table('item_checks')