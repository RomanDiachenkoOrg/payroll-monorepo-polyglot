package report

import (
	"bytes"
	"strings"
	"testing"
)

func TestParseRange(t *testing.T) {
	if _, _, err := ParseRange("2026-01-01", "2026-01-31"); err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if _, _, err := ParseRange("2026-02-01", "2026-01-31"); err == nil {
		t.Fatal("expected error for reversed range")
	}
	if _, _, err := ParseRange("01/02/2026", "2026-01-31"); err == nil {
		t.Fatal("expected error for bad format")
	}
}

func TestWriteDepartmentCostCSV(t *testing.T) {
	rows := []DepartmentCost{
		{Department: "Engineering", Employees: 2, Gross: 1000, Tax: 100, Social: 50, Pension: 30, Other: 20, Net: 800},
		{Department: "Sales, EMEA", Employees: 1, Gross: 500.5, Tax: 50, Social: 25.03, Pension: 0, Other: 0, Net: 425.47},
	}
	var buf bytes.Buffer
	if err := WriteDepartmentCostCSV(&buf, rows); err != nil {
		t.Fatal(err)
	}
	lines := strings.Split(strings.TrimSpace(buf.String()), "\r\n")
	if len(lines) != 4 {
		t.Fatalf("expected header, 2 rows and totals, got %d lines", len(lines))
	}
	if lines[2] != `"Sales, EMEA",1,500.50,50.00,25.03,0.00,0.00,425.47` {
		t.Fatalf("unexpected row: %s", lines[2])
	}
	if !strings.HasPrefix(lines[3], "Total,3,1500.50") {
		t.Fatalf("unexpected totals: %s", lines[3])
	}
}
