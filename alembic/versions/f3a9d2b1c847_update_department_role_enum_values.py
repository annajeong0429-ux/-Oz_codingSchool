"""update department and role enum values

Revision ID: f3a9d2b1c847
Revises: 92c71c6e6a20
Create Date: 2026-06-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'f3a9d2b1c847'
down_revision: Union[str, Sequence[str], None] = '92c71c6e6a20'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # department: radiology/internal/emergency → research/medical/development
    op.execute(
        "ALTER TABLE users MODIFY COLUMN department "
        "ENUM('research', 'medical', 'development') NOT NULL"
    )
    # role: admin/doctor → pending/staff/admin
    op.execute(
        "ALTER TABLE users MODIFY COLUMN role "
        "ENUM('pending', 'staff', 'admin') NOT NULL"
    )


def downgrade() -> None:
    # role: pending/staff/admin → admin/doctor
    op.execute(
        "ALTER TABLE users MODIFY COLUMN role "
        "ENUM('admin', 'doctor') NOT NULL"
    )
    # department: research/medical/development → radiology/internal/emergency
    op.execute(
        "ALTER TABLE users MODIFY COLUMN department "
        "ENUM('radiology', 'internal', 'emergency') NOT NULL"
    )
