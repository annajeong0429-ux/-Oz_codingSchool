"""ai_analysis heatmap_url Text + nullable

Revision ID: d34311c9179e
Revises: 92c71c6e6a20
Create Date: 2026-06-10 17:51:48.345243

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = 'd34311c9179e'
down_revision: Union[str, Sequence[str], None] = '92c71c6e6a20'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('ai_analysis_results', 'heatmap_url',
               existing_type=mysql.VARCHAR(length=255),
               type_=sa.Text(),
               nullable=True)
    # ↑ users.department alter_column 블록은 삭제 (우리 변경 아님)

    # ### end Alembic commands ###


def downgrade() -> None:
    op.alter_column('ai_analysis_results', 'heatmap_url',
               existing_type=sa.Text(),
               type_=mysql.VARCHAR(length=255),
               nullable=False)
    # ↑ users.department 블록도 삭제

    # ### end Alembic commands ###
