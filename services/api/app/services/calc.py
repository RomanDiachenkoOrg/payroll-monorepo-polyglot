"""Payroll calculation rules (monthly).

All money is handled as Decimal and rounded to cents at each step.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import ROUND_HALF_EVEN, Decimal

CENT = Decimal("0.01")
ZERO = Decimal("0")


def money(value: Decimal | float | int | str) -> Decimal:
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_EVEN)


@dataclass(frozen=True)
class Bracket:
    lower: Decimal
    upper: Decimal | None
    rate: Decimal


DEFAULT_BRACKETS = [
    Bracket(Decimal("0"), Decimal("1000"), Decimal("0")),
    Bracket(Decimal("1000"), Decimal("4000"), Decimal("0.15")),
    Bracket(Decimal("4000"), None, Decimal("0.25")),
]


@dataclass(frozen=True)
class CalcConfig:
    brackets: list[Bracket] = field(default_factory=lambda: list(DEFAULT_BRACKETS))
    social_rate: Decimal = Decimal("0.05")
    pension_rate: Decimal = Decimal("0.03")
    overtime_threshold: Decimal = Decimal("40")
    overtime_multiplier: Decimal = Decimal("1.5")


@dataclass(frozen=True)
class Breakdown:
    regular_hours: Decimal
    overtime_hours: Decimal
    gross: Decimal
    tax: Decimal
    social: Decimal
    pension: Decimal
    other: Decimal
    net: Decimal

    @property
    def total_deductions(self) -> Decimal:
        return self.tax + self.social + self.pension + self.other


def split_week(daily_hours: list[float | Decimal], threshold: Decimal = Decimal("40")) -> tuple[Decimal, Decimal]:
    """Returns (regular, overtime) hours for one week. Overtime is every hour over the threshold."""
    total = sum((Decimal(str(h)) for h in daily_hours), ZERO)
    if total > threshold:
        return threshold, total - threshold
    return total, ZERO


def income_tax(gross: Decimal, brackets: list[Bracket] | None = None) -> Decimal:
    brackets = sorted(brackets or DEFAULT_BRACKETS, key=lambda b: b.lower)
    tax = ZERO
    for b in brackets:
        if gross <= b.lower:
            break
        upper = gross if b.upper is None else min(gross, b.upper)
        tax += (upper - b.lower) * b.rate
    return money(tax)


def calculate(
    *,
    pay_type: str,
    annual_salary: Decimal | None = None,
    hourly_rate: Decimal | None = None,
    weeks: list[list[float]] | None = None,
    pension_opt_in: bool = False,
    other_deductions: Decimal = ZERO,
    config: CalcConfig | None = None,
) -> Breakdown:
    config = config or CalcConfig()
    regular = overtime = ZERO
    if pay_type == "SALARIED":
        if not annual_salary or annual_salary <= 0:
            raise ValueError("Annual salary must be positive")
        gross = money(Decimal(annual_salary) / 12)
    else:
        if not hourly_rate or hourly_rate <= 0:
            raise ValueError("Hourly rate must be positive")
        for week in weeks or []:
            r, o = split_week(week, config.overtime_threshold)
            regular += r
            overtime += o
        rate = Decimal(hourly_rate)
        gross = money(rate * regular + rate * config.overtime_multiplier * overtime)

    tax = income_tax(gross, config.brackets)
    social = money(gross * config.social_rate)
    pension = money(gross * config.pension_rate) if pension_opt_in else ZERO.quantize(CENT)
    other = money(other_deductions)
    net = money(gross - tax - social - pension - other)
    return Breakdown(regular, overtime, gross, tax, social, pension, other, net)
