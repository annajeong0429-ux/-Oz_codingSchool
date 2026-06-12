"""heatmap_url Text to MediumText

Revision ID: a9c8ce6ef706
Revises: f3a9d2b1c847
Create Date: 2026-06-13 07:13:53.476825

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


# revision identifiers, used by Alembic.
revision: str = 'a9c8ce6ef706'
down_revision: Union[str, Sequence[str], None] = 'f3a9d2b1c847'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('ai_analysis_results', 'heatmap_url',
               existing_type=sa.Text(),
               type_=mysql.MEDIUMTEXT(),
               existing_nullable=True)


def downgrade() -> None:
    op.alter_column('ai_analysis_results', 'heatmap_url',
               existing_type=mysql.MEDIUMTEXT(),
               type_=sa.Text(),
               existing_nullable=True)
