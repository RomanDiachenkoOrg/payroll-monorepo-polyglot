from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator, model_validator
from pydantic.alias_generators import to_camel

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

PayType = Literal["SALARIED", "HOURLY"]
EmployeeStatus = Literal["ACTIVE", "INACTIVE"]


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)


class MoneyModel(ApiModel):
    """Serialises Decimal fields as JSON numbers."""

    @field_serializer("*", when_used="json", check_fields=False)
    def _decimal_to_float(self, value):
        if isinstance(value, Decimal):
            return float(value)
        return value


T = TypeVar("T")


class Page(ApiModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int


# ---- auth ---------------------------------------------------------------


class LoginIn(ApiModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        v = v.strip().lower()
        if not v:
            raise ValueError("Email is required")
        if not EMAIL_RE.match(v):
            raise ValueError("Enter a valid email address")
        return v

    @field_validator("password")
    @classmethod
    def _password(cls, v: str) -> str:
        if not v:
            raise ValueError("Password is required")
        return v


class UserOut(ApiModel):
    id: int
    email: str
    name: str
    role: str
    employee_id: int | None
    department_id: int | None


class LoginOut(ApiModel):
    token: str
    user: UserOut


# ---- departments --------------------------------------------------------


class DepartmentIn(ApiModel):
    name: str = Field(min_length=2, max_length=80)
    code: str
    manager_name: str | None = Field(default=None, max_length=120)

    @field_validator("code")
    @classmethod
    def _code(cls, v: str) -> str:
        v = v.strip().upper()
        if not re.fullmatch(r"[A-Z]{2,6}", v):
            raise ValueError("Code must be 2-6 letters")
        return v

    @field_validator("name")
    @classmethod
    def _name(cls, v: str) -> str:
        return v.strip()


class DepartmentOut(ApiModel):
    id: int
    name: str
    code: str
    manager_name: str | None
    active_employees: int = 0
    total_employees: int = 0


# ---- employees ----------------------------------------------------------


class EmployeeIn(ApiModel):
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=80)
    email: str
    phone: str | None = Field(default=None, max_length=40)
    title: str = Field(min_length=1, max_length=120)
    department_id: int
    pay_type: PayType
    annual_salary: Decimal | None = None
    hourly_rate: Decimal | None = None
    pension_opt_in: bool = False
    health_insurance: Decimal = Decimal("0")
    hire_date: date

    @field_validator("first_name", "last_name", "title")
    @classmethod
    def _required(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("This field is required")
        return v

    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        v = v.strip().lower()
        if not EMAIL_RE.match(v):
            raise ValueError("Enter a valid email address")
        return v

    @field_validator("hire_date")
    @classmethod
    def _hire_date(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("Hire date cannot be in the future")
        return v

    @field_validator("health_insurance")
    @classmethod
    def _health(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("Cannot be negative")
        return v

    @model_validator(mode="after")
    def _pay(self) -> EmployeeIn:
        if self.pay_type == "SALARIED":
            if self.annual_salary is None or self.annual_salary <= 0:
                raise ValueError("Salary must be greater than 0")
            self.hourly_rate = None
        else:
            if self.hourly_rate is None or self.hourly_rate <= 0:
                raise ValueError("Hourly rate must be greater than 0")
            self.annual_salary = None
        return self


class EmployeeOut(MoneyModel):
    id: int
    first_name: str
    last_name: str
    full_name: str
    email: str
    phone: str | None
    title: str
    department_id: int
    department_name: str
    pay_type: str
    annual_salary: Decimal | None
    hourly_rate: Decimal | None
    pension_opt_in: bool
    health_insurance: Decimal
    hire_date: date
    status: str


class SalaryHistoryOut(MoneyModel):
    id: int
    effective_date: date
    annual_salary: Decimal | None
    hourly_rate: Decimal | None
    reason: str


class SalaryChangeIn(ApiModel):
    effective_date: date
    amount: Decimal = Field(gt=0)
    reason: str = Field(min_length=1, max_length=200)


class PayslipOut(MoneyModel):
    id: int
    pay_run_id: int
    employee_id: int
    employee_name: str
    department_name: str
    period_start: date
    period_end: date
    pay_date: date
    pay_run_status: str
    pay_type: str
    regular_hours: Decimal
    overtime_hours: Decimal
    gross: Decimal
    tax: Decimal
    social: Decimal
    pension: Decimal
    other: Decimal
    net: Decimal


class EmployeeDetailOut(EmployeeOut):
    salary_history: list[SalaryHistoryOut]
    payslips: list[PayslipOut]


class ProfileIn(ApiModel):
    phone: str | None = Field(default=None, max_length=40)
    pension_opt_in: bool | None = None


# ---- timesheets ---------------------------------------------------------


class TimesheetIn(ApiModel):
    employee_id: int | None = None
    week_start: date
    hours: list[Decimal]
    notes: str | None = Field(default=None, max_length=500)

    @field_validator("week_start")
    @classmethod
    def _monday(cls, v: date) -> date:
        if v.weekday() != 0:
            raise ValueError("The week must start on a Monday")
        return v

    @field_validator("hours")
    @classmethod
    def _hours(cls, v: list[Decimal]) -> list[Decimal]:
        if len(v) != 7:
            raise ValueError("A week has 7 days")
        if any(h < 0 or h > 24 for h in v):
            raise ValueError("Hours per day must be between 0 and 24")
        return v


class TimesheetUpdateIn(ApiModel):
    hours: list[Decimal]
    notes: str | None = Field(default=None, max_length=500)

    @field_validator("hours")
    @classmethod
    def _hours(cls, v: list[Decimal]) -> list[Decimal]:
        return TimesheetIn._hours(v)


class RejectIn(ApiModel):
    reason: str = Field(min_length=3, max_length=500)


class TimesheetOut(ApiModel):
    id: int
    employee_id: int
    employee_name: str
    department_id: int
    department_name: str
    week_start: date
    hours: list[float]
    total_hours: float
    status: str
    notes: str | None
    reject_reason: str | None
    submitted_at: datetime | None
    decided_at: datetime | None
    decided_by: str | None


# ---- pay runs -----------------------------------------------------------


class PayRunIn(ApiModel):
    period_start: date
    period_end: date
    pay_date: date

    @model_validator(mode="after")
    def _dates(self) -> PayRunIn:
        if self.period_end < self.period_start:
            raise ValueError("Period end must be after the start")
        if self.pay_date < self.period_end:
            raise ValueError("Pay date must be on or after the period end")
        return self


class PayRunOut(MoneyModel):
    id: int
    period_start: date
    period_end: date
    pay_date: date
    status: str
    employee_count: int = 0
    total_gross: Decimal
    total_net: Decimal
    created_at: datetime
    approved_at: datetime | None
    paid_at: datetime | None


class PayRunDetailOut(PayRunOut):
    lines: list[PayslipOut]


# ---- settings -----------------------------------------------------------


class BracketIo(MoneyModel):
    lower: Decimal = Field(ge=0)
    upper: Decimal | None = None
    rate: Decimal = Field(ge=0, le=1)


class TaxSettingsIo(MoneyModel):
    brackets: list[BracketIo]
    social_rate: Decimal = Field(ge=0, le=1)
    pension_rate: Decimal = Field(ge=0, le=1)


class UserRow(ApiModel):
    id: int
    email: str
    name: str
    role: str
    active: bool
    department: str | None
    last_login_at: datetime | None


class AuditOut(ApiModel):
    id: int
    created_at: datetime
    user_email: str
    action: str
    entity: str
    entity_id: str | None
    details: str | None


class DashboardOut(MoneyModel):
    headcount: int
    active_headcount: int
    last_payroll_gross: Decimal | None
    last_payroll_period: str | None
    pending_timesheets: int
    next_pay_date: date | None
    cost_by_department: list[dict]
    recent_pay_runs: list[PayRunOut]


class MailOut(ApiModel):
    id: int
    recipient: str
    subject: str
    body: str
    event_type: str
    created_at: datetime
