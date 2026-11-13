package report

import (
	"encoding/csv"
	"fmt"
	"io"
	"time"
)

// DepartmentCost is the payroll cost of one department over a period.
type DepartmentCost struct {
	DepartmentID int     `json:"departmentId"`
	Department   string  `json:"department"`
	Employees    int     `json:"employees"`
	Gross        float64 `json:"gross"`
	Tax          float64 `json:"tax"`
	Social       float64 `json:"social"`
	Pension      float64 `json:"pension"`
	Other        float64 `json:"other"`
	Net          float64 `json:"net"`
}

// PayRunSummary aggregates one pay run.
type PayRunSummary struct {
	PayRunID    int     `json:"payRunId"`
	PeriodStart string  `json:"periodStart"`
	PeriodEnd   string  `json:"periodEnd"`
	Status      string  `json:"status"`
	Employees   int     `json:"employees"`
	Gross       float64 `json:"gross"`
	Tax         float64 `json:"tax"`
	Net         float64 `json:"net"`
}

// Totals sums the rows of a department cost report.
func Totals(rows []DepartmentCost) DepartmentCost {
	t := DepartmentCost{Department: "Total"}
	for _, r := range rows {
		t.Employees += r.Employees
		t.Gross += r.Gross
		t.Tax += r.Tax
		t.Social += r.Social
		t.Pension += r.Pension
		t.Other += r.Other
		t.Net += r.Net
	}
	return t
}

// ParseRange validates a from/to pair of YYYY-MM-DD dates.
func ParseRange(from, to string) (time.Time, time.Time, error) {
	f, err := time.Parse(time.DateOnly, from)
	if err != nil {
		return time.Time{}, time.Time{}, fmt.Errorf("invalid 'from' date %q, use YYYY-MM-DD", from)
	}
	t, err := time.Parse(time.DateOnly, to)
	if err != nil {
		return time.Time{}, time.Time{}, fmt.Errorf("invalid 'to' date %q, use YYYY-MM-DD", to)
	}
	if t.Before(f) {
		return time.Time{}, time.Time{}, fmt.Errorf("'to' must not be before 'from'")
	}
	return f, t, nil
}

func money(v float64) string {
	return fmt.Sprintf("%.2f", v)
}

// WriteDepartmentCostCSV writes the report including a totals row.
func WriteDepartmentCostCSV(w io.Writer, rows []DepartmentCost) error {
	cw := csv.NewWriter(w)
	cw.UseCRLF = true
	header := []string{"Department", "Employees", "Gross", "Income tax", "Social", "Pension", "Other", "Net"}
	if err := cw.Write(header); err != nil {
		return err
	}
	write := func(r DepartmentCost) error {
		return cw.Write([]string{
			r.Department, fmt.Sprint(r.Employees), money(r.Gross), money(r.Tax),
			money(r.Social), money(r.Pension), money(r.Other), money(r.Net),
		})
	}
	for _, r := range rows {
		if err := write(r); err != nil {
			return err
		}
	}
	if len(rows) > 0 {
		if err := write(Totals(rows)); err != nil {
			return err
		}
	}
	cw.Flush()
	return cw.Error()
}
