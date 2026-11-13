package store

import (
	"context"
	"time"

	"github.com/RomanDiachenkoOrg/payroll-monorepo-polyglot/services/reports/internal/report"
	"github.com/jackc/pgx/v5/pgxpool"
)

// Store reads report data from the payroll database.
type Store struct {
	pool *pgxpool.Pool
}

// Connect opens a pool and retries for a short while so the service can start alongside the database.
func Connect(ctx context.Context, url string) (*Store, error) {
	var lastErr error
	for attempt := 0; attempt < 20; attempt++ {
		pool, err := pgxpool.New(ctx, url)
		if err == nil {
			if err = pool.Ping(ctx); err == nil {
				return &Store{pool: pool}, nil
			}
			pool.Close()
		}
		lastErr = err
		select {
		case <-ctx.Done():
			return nil, ctx.Err()
		case <-time.After(2 * time.Second):
		}
	}
	return nil, lastErr
}

func (s *Store) Close() { s.pool.Close() }

func (s *Store) Ping(ctx context.Context) error { return s.pool.Ping(ctx) }

const departmentCostSQL = `
SELECT d.id, d.name,
       COUNT(DISTINCT p.employee_id),
       COALESCE(SUM(p.gross), 0)::float8,
       COALESCE(SUM(p.tax), 0)::float8,
       COALESCE(SUM(p.social), 0)::float8,
       COALESCE(SUM(p.pension), 0)::float8,
       COALESCE(SUM(p.other), 0)::float8,
       COALESCE(SUM(p.net), 0)::float8
FROM payslips p
JOIN pay_runs pr ON pr.id = p.pay_run_id
JOIN employees e ON e.id = p.employee_id
JOIN departments d ON d.id = e.department_id
WHERE pr.status IN ('APPROVED', 'PAID')
  AND pr.period_start >= $1
  AND pr.period_end < $2
GROUP BY d.id, d.name
ORDER BY d.name`

// DepartmentCost returns payroll cost per department for approved and paid runs inside the period.
func (s *Store) DepartmentCost(ctx context.Context, from, to time.Time) ([]report.DepartmentCost, error) {
	rows, err := s.pool.Query(ctx, departmentCostSQL, from, to)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	out := []report.DepartmentCost{}
	for rows.Next() {
		var r report.DepartmentCost
		if err := rows.Scan(&r.DepartmentID, &r.Department, &r.Employees, &r.Gross, &r.Tax, &r.Social, &r.Pension, &r.Other, &r.Net); err != nil {
			return nil, err
		}
		out = append(out, r)
	}
	return out, rows.Err()
}

const payRunSummarySQL = `
SELECT pr.id, to_char(pr.period_start, 'YYYY-MM-DD'), to_char(pr.period_end, 'YYYY-MM-DD'), pr.status,
       COUNT(p.id),
       COALESCE(SUM(p.gross), 0)::float8,
       COALESCE(SUM(p.tax), 0)::float8,
       COALESCE(SUM(p.net), 0)::float8
FROM pay_runs pr
LEFT JOIN payslips p ON p.pay_run_id = pr.id
WHERE EXTRACT(YEAR FROM pr.period_start) = $1
GROUP BY pr.id
ORDER BY pr.period_start`

// PayRunSummaries returns per pay run totals for a year.
func (s *Store) PayRunSummaries(ctx context.Context, year int) ([]report.PayRunSummary, error) {
	rows, err := s.pool.Query(ctx, payRunSummarySQL, year)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	out := []report.PayRunSummary{}
	for rows.Next() {
		var r report.PayRunSummary
		if err := rows.Scan(&r.PayRunID, &r.PeriodStart, &r.PeriodEnd, &r.Status, &r.Employees, &r.Gross, &r.Tax, &r.Net); err != nil {
			return nil, err
		}
		out = append(out, r)
	}
	return out, rows.Err()
}
