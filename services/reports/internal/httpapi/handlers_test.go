package httpapi

import (
	"context"
	"encoding/json"
	"io"
	"log/slog"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"

	"github.com/RomanDiachenkoOrg/payroll-monorepo-polyglot/services/reports/internal/auth"
	"github.com/RomanDiachenkoOrg/payroll-monorepo-polyglot/services/reports/internal/report"
	"github.com/golang-jwt/jwt/v5"
)

const secret = "test-secret-test-secret-test-secret"

type fakeStore struct {
	from, to time.Time
}

func (f *fakeStore) Ping(context.Context) error { return nil }

func (f *fakeStore) DepartmentCost(_ context.Context, from, to time.Time) ([]report.DepartmentCost, error) {
	f.from, f.to = from, to
	return []report.DepartmentCost{{DepartmentID: 1, Department: "Engineering", Employees: 3, Gross: 3000, Net: 2200}}, nil
}

func (f *fakeStore) PayRunSummaries(context.Context, int) ([]report.PayRunSummary, error) {
	return []report.PayRunSummary{{PayRunID: 1, Status: "PAID"}}, nil
}

func token(t *testing.T, role string) string {
	t.Helper()
	s, err := jwt.NewWithClaims(jwt.SigningMethodHS256, auth.Claims{Role: role}).SignedString([]byte(secret))
	if err != nil {
		t.Fatal(err)
	}
	return s
}

func newServer(store *fakeStore) http.Handler {
	return New(store, auth.NewVerifier(secret), slog.New(slog.NewTextHandler(io.Discard, nil))).Routes()
}

func do(h http.Handler, path, role string, t *testing.T) *httptest.ResponseRecorder {
	r := httptest.NewRequest("GET", path, nil)
	if role != "" {
		r.Header.Set("Authorization", "Bearer "+token(t, role))
	}
	w := httptest.NewRecorder()
	h.ServeHTTP(w, r)
	return w
}

func TestHealth(t *testing.T) {
	w := do(newServer(&fakeStore{}), "/reports/health", "", t)
	if w.Code != http.StatusOK {
		t.Fatalf("status = %d", w.Code)
	}
}

func TestAuthorization(t *testing.T) {
	h := newServer(&fakeStore{})
	if w := do(h, "/reports/department-cost?from=2026-01-01&to=2026-01-31", "", t); w.Code != http.StatusUnauthorized {
		t.Fatalf("anonymous status = %d", w.Code)
	}
	if w := do(h, "/reports/department-cost?from=2026-01-01&to=2026-01-31", "EMPLOYEE", t); w.Code != http.StatusForbidden {
		t.Fatalf("employee status = %d", w.Code)
	}
}

func TestDepartmentCostJSON(t *testing.T) {
	store := &fakeStore{}
	w := do(newServer(store), "/reports/department-cost?from=2026-01-01&to=2026-03-31", "MANAGER", t)
	if w.Code != http.StatusOK {
		t.Fatalf("status = %d: %s", w.Code, w.Body.String())
	}
	var body struct {
		Rows   []report.DepartmentCost `json:"rows"`
		Totals report.DepartmentCost   `json:"totals"`
	}
	if err := json.Unmarshal(w.Body.Bytes(), &body); err != nil {
		t.Fatal(err)
	}
	if len(body.Rows) != 1 || body.Totals.Gross != 3000 {
		t.Fatalf("unexpected body: %+v", body)
	}
	if store.from.Format(time.DateOnly) != "2026-01-01" {
		t.Fatalf("from passed to store = %v", store.from)
	}
}

func TestDepartmentCostValidation(t *testing.T) {
	w := do(newServer(&fakeStore{}), "/reports/department-cost?from=2026-05-01&to=2026-01-31", "ADMIN", t)
	if w.Code != http.StatusBadRequest {
		t.Fatalf("status = %d", w.Code)
	}
}

func TestDepartmentCostCSV(t *testing.T) {
	w := do(newServer(&fakeStore{}), "/reports/department-cost.csv?from=2026-01-01&to=2026-01-31", "ADMIN", t)
	if ct := w.Header().Get("Content-Type"); !strings.HasPrefix(ct, "text/csv") {
		t.Fatalf("content type = %q", ct)
	}
	if !strings.Contains(w.Body.String(), "Engineering,3,3000.00") {
		t.Fatalf("unexpected csv: %s", w.Body.String())
	}
}
