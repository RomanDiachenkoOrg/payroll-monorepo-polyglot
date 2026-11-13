"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-09-01 09:00:00
"""
import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "departments",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(80), nullable=False, unique=True),
        sa.Column("code", sa.String(6), nullable=False, unique=True),
        sa.Column("manager_name", sa.String(120)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "employees",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("first_name", sa.String(80), nullable=False),
        sa.Column("last_name", sa.String(80), nullable=False),
        sa.Column("email", sa.String(160), nullable=False, unique=True),
        sa.Column("phone", sa.String(40)),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("department_id", sa.Integer, sa.ForeignKey("departments.id"), nullable=False, index=True),
        sa.Column("pay_type", sa.String(10), nullable=False),
        sa.Column("annual_salary", sa.Numeric(12, 2)),
        sa.Column("hourly_rate", sa.Numeric(10, 2)),
        sa.Column("pension_opt_in", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("hire_date", sa.Date, nullable=False),
        sa.Column("status", sa.String(10), nullable=False, server_default="ACTIVE", index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String(160), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(200), nullable=False),
        sa.Column("full_name", sa.String(160), nullable=False),
        sa.Column("role", sa.String(10), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("employee_id", sa.Integer, sa.ForeignKey("employees.id"), unique=True),
        sa.Column("department_id", sa.Integer, sa.ForeignKey("departments.id")),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "salary_history",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("employee_id", sa.Integer, sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("effective_date", sa.Date, nullable=False),
        sa.Column("annual_salary", sa.Numeric(12, 2)),
        sa.Column("hourly_rate", sa.Numeric(10, 2)),
        sa.Column("reason", sa.String(200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "deduction_types",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("code", sa.String(20), nullable=False, unique=True),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("default_amount", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
    )
    op.create_table(
        "employee_deductions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("employee_id", sa.Integer, sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("deduction_type_id", sa.Integer, sa.ForeignKey("deduction_types.id"), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.UniqueConstraint("employee_id", "deduction_type_id"),
    )
    op.create_table(
        "timesheets",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("employee_id", sa.Integer, sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("week_start", sa.Date, nullable=False),
        sa.Column("status", sa.String(10), nullable=False, server_default="DRAFT", index=True),
        sa.Column("notes", sa.String(500)),
        sa.Column("reject_reason", sa.String(500)),
        sa.Column("submitted_at", sa.DateTime(timezone=True)),
        sa.Column("decided_at", sa.DateTime(timezone=True)),
        sa.Column("decided_by_id", sa.Integer, sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("employee_id", "week_start"),
    )
    op.create_table(
        "timesheet_entries",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("timesheet_id", sa.Integer, sa.ForeignKey("timesheets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("day_index", sa.SmallInteger, nullable=False),
        sa.Column("hours", sa.Numeric(5, 2), nullable=False),
        sa.UniqueConstraint("timesheet_id", "day_index"),
    )
    op.create_table(
        "pay_runs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("period_start", sa.Date, nullable=False),
        sa.Column("period_end", sa.Date, nullable=False),
        sa.Column("pay_date", sa.Date, nullable=False),
        sa.Column("status", sa.String(12), nullable=False, server_default="DRAFT"),
        sa.Column("total_gross", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("total_net", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("calculated_at", sa.DateTime(timezone=True)),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column("paid_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "payslips",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("pay_run_id", sa.Integer, sa.ForeignKey("pay_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("employee_id", sa.Integer, sa.ForeignKey("employees.id"), nullable=False),
        sa.Column("pay_type", sa.String(10), nullable=False),
        sa.Column("regular_hours", sa.Numeric(7, 2), nullable=False, server_default="0"),
        sa.Column("overtime_hours", sa.Numeric(7, 2), nullable=False, server_default="0"),
        sa.Column("gross", sa.Numeric(12, 2), nullable=False),
        sa.Column("tax", sa.Numeric(12, 2), nullable=False),
        sa.Column("social", sa.Numeric(12, 2), nullable=False),
        sa.Column("pension", sa.Numeric(12, 2), nullable=False),
        sa.Column("other", sa.Numeric(12, 2), nullable=False),
        sa.Column("net", sa.Numeric(12, 2), nullable=False),
        sa.UniqueConstraint("pay_run_id", "employee_id"),
    )
    op.create_table(
        "tax_brackets",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("sort_order", sa.Integer, nullable=False),
        sa.Column("lower", sa.Numeric(12, 2), nullable=False),
        sa.Column("upper", sa.Numeric(12, 2)),
        sa.Column("rate", sa.Numeric(6, 4), nullable=False),
    )
    op.create_table(
        "settings",
        sa.Column("key", sa.String(60), primary_key=True),
        sa.Column("value", sa.String(200), nullable=False),
    )
    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer),
        sa.Column("user_email", sa.String(160), nullable=False),
        sa.Column("action", sa.String(40), nullable=False, index=True),
        sa.Column("entity", sa.String(40), nullable=False, index=True),
        sa.Column("entity_id", sa.String(40)),
        sa.Column("details", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
    )
    op.create_table(
        "mailbox",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("recipient", sa.String(160), nullable=False),
        sa.Column("subject", sa.String(200), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("event_type", sa.String(60), nullable=False),
        sa.Column("related_id", sa.Integer),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    for table in [
        "mailbox",
        "audit_log",
        "settings",
        "tax_brackets",
        "payslips",
        "pay_runs",
        "timesheet_entries",
        "timesheets",
        "employee_deductions",
        "deduction_types",
        "salary_history",
        "users",
        "employees",
        "departments",
    ]:
        op.drop_table(table)
