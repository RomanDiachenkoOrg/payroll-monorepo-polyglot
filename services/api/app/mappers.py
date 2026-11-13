from .models import Employee, PayRun, Payslip, Timesheet, User
from .schemas import EmployeeOut, PayRunOut, PayslipOut, TimesheetOut, UserOut


def user_out(u: User) -> UserOut:
    return UserOut(id=u.id, email=u.email, name=u.full_name, role=u.role, employee_id=u.employee_id, department_id=u.department_id)


def employee_out(e: Employee) -> EmployeeOut:
    return EmployeeOut(
        id=e.id,
        first_name=e.first_name,
        last_name=e.last_name,
        full_name=e.full_name,
        email=e.email,
        phone=e.phone,
        title=e.title,
        department_id=e.department_id,
        department_name=e.department.name,
        pay_type=e.pay_type,
        annual_salary=e.annual_salary,
        hourly_rate=e.hourly_rate,
        pension_opt_in=e.pension_opt_in,
        health_insurance=e.other_deductions,
        hire_date=e.hire_date,
        status=e.status,
    )


def payslip_out(p: Payslip) -> PayslipOut:
    return PayslipOut(
        id=p.id,
        pay_run_id=p.pay_run_id,
        employee_id=p.employee_id,
        employee_name=p.employee.full_name,
        department_name=p.employee.department.name,
        period_start=p.pay_run.period_start,
        period_end=p.pay_run.period_end,
        pay_date=p.pay_run.pay_date,
        pay_run_status=p.pay_run.status,
        pay_type=p.pay_type,
        regular_hours=p.regular_hours,
        overtime_hours=p.overtime_hours,
        gross=p.gross,
        tax=p.tax,
        social=p.social,
        pension=p.pension,
        other=p.other,
        net=p.net,
    )


def timesheet_out(t: Timesheet) -> TimesheetOut:
    return TimesheetOut(
        id=t.id,
        employee_id=t.employee_id,
        employee_name=t.employee.full_name,
        department_id=t.employee.department_id,
        department_name=t.employee.department.name,
        week_start=t.week_start,
        hours=t.hours,
        total_hours=t.total_hours,
        status=t.status,
        notes=t.notes,
        reject_reason=t.reject_reason,
        submitted_at=t.submitted_at,
        decided_at=t.decided_at,
        decided_by=t.decided_by.full_name if t.decided_by else None,
    )


def pay_run_out(r: PayRun, count: int = 0) -> PayRunOut:
    return PayRunOut(
        id=r.id,
        period_start=r.period_start,
        period_end=r.period_end,
        pay_date=r.pay_date,
        status=r.status,
        employee_count=count,
        total_gross=r.total_gross,
        total_net=r.total_net,
        created_at=r.created_at,
        approved_at=r.approved_at,
        paid_at=r.paid_at,
    )
