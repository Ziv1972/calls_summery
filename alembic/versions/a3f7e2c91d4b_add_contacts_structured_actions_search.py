"""add contacts table, structured actions, search support

Revision ID: a3f7e2c91d4b
Revises: 0bd53e10f1f5
Create Date: 2026-02-20 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON


# revision identifiers, used by Alembic.
revision: str = 'a3f7e2c91d4b'
down_revision: Union[str, None] = '0bd53e10f1f5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create contacts table
    op.create_table(
        'contacts',
        sa.Column('id', UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('phone_number', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=True),
        sa.Column('company', sa.String(length=200), nullable=True),
        sa.Column('email', sa.String(length=320), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'phone_number', name='uq_contact_user_phone'),
    )
    op.create_index('ix_contacts_user_id', 'contacts', ['user_id'])

    # Add new columns to calls table
    op.add_column('calls', sa.Column('contact_id', UUID(as_uuid=True), nullable=True))
    op.add_column('calls', sa.Column('caller_phone', sa.String(length=20), nullable=True))
    op.create_foreign_key(
        'fk_calls_contact_id',
        'calls', 'contacts',
        ['contact_id'], ['id'],
        ondelete='SET NULL',
    )
    op.create_index('ix_calls_contact_id', 'calls', ['contact_id'])

    # Add new columns to summaries table
    op.add_column('summaries', sa.Column('structured_actions', JSON(), nullable=True))
    op.add_column('summaries', sa.Column('participants_details', JSON(), nullable=True))
    op.add_column('summaries', sa.Column('topics', JSON(), nullable=True))

    # Add new upload_source enum values for mobile
    op.execute("ALTER TYPE uploadsource ADD VALUE IF NOT EXISTS 'mobile_auto'")
    op.execute("ALTER TYPE uploadsource ADD VALUE IF NOT EXISTS 'mobile_manual'")


def downgrade() -> None:
    # Remove new summary columns
    op.drop_column('summaries', 'topics')
    op.drop_column('summaries', 'participants_details')
    op.drop_column('summaries', 'structured_actions')

    # Remove calls columns
    op.drop_constraint('fk_calls_contact_id', 'calls', type_='foreignkey')
    op.drop_index('ix_calls_contact_id', table_name='calls')
    op.drop_column('calls', 'caller_phone')
    op.drop_column('calls', 'contact_id')

    # Drop contacts table
    op.drop_index('ix_contacts_user_id', table_name='contacts')
    op.drop_table('contacts')
