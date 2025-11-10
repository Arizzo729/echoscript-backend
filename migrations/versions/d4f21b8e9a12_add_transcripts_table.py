"""Add transcripts table

Revision ID: d4f21b8e9a12
Revises: c8d32658ca23
Create Date: 2025-11-06 19:54:00

"""
from alembic import op
import sqlalchemy as sa

revision = 'd4f21b8e9a12'
down_revision = 'c8d32658ca23'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'transcripts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('original_filename', sa.String(length=500), nullable=True),
        sa.Column('storage_filename', sa.String(length=500), nullable=False),
        sa.Column('content', sa.String(), nullable=True),
        sa.Column('duration', sa.Integer(), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('language', sa.String(length=10), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='completed'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_transcripts_user_id', 'transcripts', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_transcripts_user_id', table_name='transcripts')
    op.drop_table('transcripts')
