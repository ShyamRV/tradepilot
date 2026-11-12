"""Create typed sandbox execution control-plane tables.

Revision ID: 0003_typed_execution
Revises: None
"""

from alembic import op

from tradepilot.db.models import Base

revision = "0003_typed_execution"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind(), checkfirst=True)


def downgrade() -> None:
    # Downgrade is intentionally explicit: execution/audit data must not be
    # destructively rolled back in production. Use a reviewed forward fix.
    raise RuntimeError("typed execution tables require a forward-only migration")
