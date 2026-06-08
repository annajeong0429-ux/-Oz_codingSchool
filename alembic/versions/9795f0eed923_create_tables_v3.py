"""create tables v3

Revision ID: 9795f0eed923
Revises: 
Create Date: 2026-06-05 14:46:28.671123

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '9795f0eed923'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('patients',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('name', sa.String(length=30), nullable=False),
    sa.Column('age', sa.SmallInteger(), nullable=False),
    sa.Column('gender', sa.Enum('male','female'), nullable=False),
    sa.Column('phone', sa.String(length=11), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('users',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('hashed_password', sa.String(length=255), nullable=False),
    sa.Column('name', sa.String(length=20), nullable=True),
    sa.Column('phone_number', sa.String(length=20), nullable=True),
    sa.Column('gender', sa.Enum('male','female'), nullable=False),
    sa.Column('department', sa.Enum('radiology','internal','emergency'), nullable=False),
    sa.Column('role', sa.Enum('admin','doctor'), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('phone_number')
    )
    op.create_table('medical_records',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('patient_id', sa.BigInteger(), nullable=False),
    sa.Column('chart_number', sa.String(length=50), nullable=False),
    sa.Column('symptoms', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('chart_number')
    )
    op.create_table('ai_analysis_results',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('record_id', sa.BigInteger(), nullable=False),
    sa.Column('is_pneumonia', sa.Boolean(), nullable=False),
    sa.Column('confidence', sa.Numeric(precision=5, scale=2), nullable=False),
    sa.Column('heatmap_url', sa.String(length=255), nullable=False),
    sa.Column('ai_model', sa.String(length=50), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['record_id'], ['medical_records.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('xray_images',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('record_id', sa.BigInteger(), nullable=False),
    sa.Column('uploader_id', sa.BigInteger(), nullable=False),
    sa.Column('image_url', sa.String(length=2048), nullable=False),
    sa.Column('shooting_datetime', sa.DateTime(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['record_id'], ['medical_records.id'], ),
    sa.ForeignKeyConstraint(['uploader_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    op.drop_table('xray_images')
    op.drop_table('ai_analysis_results')
    op.drop_table('medical_records')
    op.drop_table('users')
    op.drop_table('patients')
    # ### end Alembic commands ###
