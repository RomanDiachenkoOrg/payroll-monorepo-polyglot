from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    code: Mapped[str] = mapped_column(String(6), unique=True)
    manager_name: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    employees: Mapped[list[Employee]] = relationship(back_populates="department")


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(80))
    last_name: Mapped[str] = mapped_column(String(80))
    email: Mapped[str] = mapped_column(String(160), unique=True)
    phone: Mapped[str | None] = mapped_column(String(40))
    title: Mapped[str] = mapped_column(String(120))
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"), index=True)
    pay_type: Mapped[str] = mapped_column(String(10))
    annual_salary: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    hourly_rate: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    pension_opt_in: Mapped[bool] = mapped_column(Boolean, default=False)
    hire_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(10), default="ACTIVE", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    department: Mapped[Department] = relationship(back_populates="employees", lazy="joined")
    salary_history: Mapped[list[SalaryHistory]] = relationship(
        back_populates="employee", cascade="all, delete-orphan", order_by="desc(SalaryHistory.effective_date)"
    )
    deductions: Mapped[list[EmployeeDeduction]] = relationship(cascade="all, delete-orphan", lazy="selectin")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def other_deductions(self) -> Decimal:
        return sum((d.amount for d in self.deductions), Decimal("0"))


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(160), unique=True)
    password_hash: Mapped[str] = mapped_column(String(200))
    full_name: Mapped[str] = mapped_column(String(160))
    role: Mapped[str] = mapped_column(String(10))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    employee_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id"), unique=True)
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    department: Mapped[Department | None] = relationship(lazy="joined")


class SalaryHistory(Base):
    __tablename__ = "salary_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), index=True)
    effective_date: Mapped[date] = mapped_column(Date)
    annual_salary: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    hourly_rate: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    reason: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    employee: Mapped[Employee] = relationship(back_populates="salary_history")


class DeductionType(Base):
    __tablename__ = "deduction_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True)
    name: Mapped[str] = mapped_column(String(80))
    default_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class EmployeeDeduction(Base):
    __tablename__ = "employee_deductions"
    __table_args__ = (UniqueConstraint("employee_id", "deduction_type_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"))
    deduction_type_id: Mapped[int] = mapped_column(ForeignKey("deduction_types.id"))
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    deduction_type: Mapped[DeductionType] = relationship(lazy="joined")


class Timesheet(Base):
    __tablename__ = "timesheets"
    __table_args__ = (UniqueConstraint("employee_id", "week_start"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"))
    week_start: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(10), default="DRAFT", index=True)
    notes: Mapped[str | None] = mapped_column(String(500))
    reject_reason: Mapped[str | None] = mapped_column(String(500))
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decided_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    employee: Mapped[Employee] = relationship(lazy="joined")
    decided_by: Mapped[User | None] = relationship(lazy="joined")
    entries: Mapped[list[TimesheetEntry]] = relationship(
        cascade="all, delete-orphan", lazy="selectin", order_by="TimesheetEntry.day_index"
    )

    @property
    def hours(self) -> list[float]:
        days = [0.0] * 7
        for e in self.entries:
            days[e.day_index] = float(e.hours)
        return days

    @property
    def total_hours(self) -> float:
        return sum(self.hours)


class TimesheetEntry(Base):
    __tablename__ = "timesheet_entries"
    __table_args__ = (UniqueConstraint("timesheet_id", "day_index"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    timesheet_id: Mapped[int] = mapped_column(ForeignKey("timesheets.id", ondelete="CASCADE"))
    day_index: Mapped[int] = mapped_column(SmallInteger)
    hours: Mapped[Decimal] = mapped_column(Numeric(5, 2))


class PayRun(Base):
    __tablename__ = "pay_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    period_start: Mapped[date] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date)
    pay_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(12), default="DRAFT")
    total_gross: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    total_net: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    calculated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    payslips: Mapped[list[Payslip]] = relationship(back_populates="pay_run", cascade="all, delete-orphan")


class Payslip(Base):
    __tablename__ = "payslips"
    __table_args__ = (UniqueConstraint("pay_run_id", "employee_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    pay_run_id: Mapped[int] = mapped_column(ForeignKey("pay_runs.id", ondelete="CASCADE"))
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"))
    pay_type: Mapped[str] = mapped_column(String(10))
    regular_hours: Mapped[Decimal] = mapped_column(Numeric(7, 2), default=Decimal("0"))
    overtime_hours: Mapped[Decimal] = mapped_column(Numeric(7, 2), default=Decimal("0"))
    gross: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    tax: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    social: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    pension: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    other: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    net: Mapped[Decimal] = mapped_column(Numeric(12, 2))

    pay_run: Mapped[PayRun] = relationship(back_populates="payslips", lazy="joined")
    employee: Mapped[Employee] = relationship(lazy="joined")


class TaxBracket(Base):
    __tablename__ = "tax_brackets"

    id: Mapped[int] = mapped_column(primary_key=True)
    sort_order: Mapped[int] = mapped_column(Integer)
    lower: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    upper: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    rate: Mapped[Decimal] = mapped_column(Numeric(6, 4))


class Setting(Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(60), primary_key=True)
    value: Mapped[str] = mapped_column(String(200))


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(Integer)
    user_email: Mapped[str] = mapped_column(String(160))
    action: Mapped[str] = mapped_column(String(40), index=True)
    entity: Mapped[str] = mapped_column(String(40), index=True)
    entity_id: Mapped[str | None] = mapped_column(String(40))
    details: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class MailboxMessage(Base):
    __tablename__ = "mailbox"

    id: Mapped[int] = mapped_column(primary_key=True)
    recipient: Mapped[str] = mapped_column(String(160))
    subject: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)
    event_type: Mapped[str] = mapped_column(String(60))
    related_id: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
