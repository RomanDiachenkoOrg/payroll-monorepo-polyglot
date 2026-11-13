from decimal import Decimal

import pytest

from app.services.calc import calculate, income_tax, money, split_week
from app.services.settings_store import validate_brackets
from app.services.calc import Bracket, DEFAULT_BRACKETS


def test_income_tax_brackets():
    assert income_tax(Decimal("800")) == Decimal("0.00")
    assert income_tax(Decimal("1000")) == Decimal("0.00")
    assert income_tax(Decimal("2000")) == Decimal("150.00")
    assert income_tax(Decimal("4000")) == Decimal("450.00")
    assert income_tax(Decimal("5000")) == Decimal("700.00")


def test_split_week_overtime_over_40():
    assert split_week([8, 8, 8, 8, 8, 0, 0]) == (Decimal("40"), Decimal("0"))
    assert split_week([10, 10, 10, 10, 5, 0, 0]) == (Decimal("40"), Decimal("5"))


def test_salaried_payslip():
    b = calculate(pay_type="SALARIED", annual_salary=Decimal("60000"), pension_opt_in=True, other_deductions=Decimal("120"))
    assert b.gross == Decimal("5000.00")
    assert b.tax == Decimal("700.00")
    assert b.social == Decimal("250.00")
    assert b.pension == Decimal("150.00")
    assert b.net == Decimal("3780.00")


def test_hourly_payslip_with_overtime():
    b = calculate(
        pay_type="HOURLY",
        hourly_rate=Decimal("20"),
        weeks=[[8, 8, 8, 8, 8, 0, 0], [9, 9, 9, 9, 9, 0, 0]],
    )
    assert b.regular_hours == Decimal("80")
    assert b.overtime_hours == Decimal("5")
    assert b.gross == Decimal("1750.00")
    assert b.net == Decimal("1550.00")


def test_invalid_salary_rejected():
    with pytest.raises(ValueError):
        calculate(pay_type="SALARIED", annual_salary=Decimal("0"))


def test_money_quantizes_to_cents():
    assert money("10.1") == Decimal("10.10")


def test_validate_brackets():
    assert validate_brackets(list(DEFAULT_BRACKETS)) == []
    assert validate_brackets([Bracket(Decimal("0"), Decimal("1000"), Decimal("0")), Bracket(Decimal("1500"), None, Decimal("0.2"))])
