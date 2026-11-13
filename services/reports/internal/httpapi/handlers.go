package httpapi

import (
	"context"
	"encoding/json"
	"fmt"
	"log/slog"
	"net/http"
	"strconv"
	"time"

	"github.com/RomanDiachenkoOrg/payroll-monorepo-polyglot/services/reports/internal/auth"
	"github.com/RomanDiachenkoOrg/payroll-monorepo-polyglot/services/reports/internal/report"
)

// Store is the data access the handlers need.
type Store interface {
	Ping(ctx context.Context) error
	DepartmentCost(ctx context.Context, from, to time.Time) ([]report.DepartmentCost, error)
	PayRunSummaries(ctx context.Context, year int) ([]report.PayRunSummary, error)
}

type Handler struct {
	store    Store
	verifier *auth.Verifier
	log      *slog.Logger
}

func New(store Store, verifier *auth.Verifier, log *slog.Logger) *Handler {
	return &Handler{store: store, verifier: verifier, log: log}
}

func (h *Handler) Routes() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /reports/health", h.health)
	mux.Handle("GET /reports/department-cost", h.authorized(h.departmentCost))
	mux.Handle("GET /reports/department-cost.csv", h.authorized(h.departmentCostCSV))
	mux.Handle("GET /reports/payroll-summary", h.authorized(h.payrollSummary))
	return h.logRequests(mux)
}

func writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(v)
}

func writeError(w http.ResponseWriter, status int, msg string) {
	writeJSON(w, status, map[string]string{"message": msg})
}

func (h *Handler) logRequests(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		next.ServeHTTP(w, r)
		h.log.Info("request", "method", r.Method, "path", r.URL.Path, "duration", time.Since(start))
	})
}

func (h *Handler) authorized(next http.HandlerFunc) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		claims, err := h.verifier.FromRequest(r)
		if err != nil {
			writeError(w, http.StatusUnauthorized, "Please sign in")
			return
		}
		if claims.Role != "ADMIN" && claims.Role != "MANAGER" {
			writeError(w, http.StatusForbidden, "You do not have permission to view reports")
			return
		}
		next(w, r.WithContext(auth.WithClaims(r.Context(), claims)))
	})
}

func (h *Handler) health(w http.ResponseWriter, r *http.Request) {
	if err := h.store.Ping(r.Context()); err != nil {
		writeError(w, http.StatusServiceUnavailable, "database unavailable")
		return
	}
	writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
}

func (h *Handler) loadDepartmentCost(w http.ResponseWriter, r *http.Request) ([]report.DepartmentCost, string, string, bool) {
	q := r.URL.Query()
	fromS, toS := q.Get("from"), q.Get("to")
	from, to, err := report.ParseRange(fromS, toS)
	if err != nil {
		writeError(w, http.StatusBadRequest, err.Error())
		return nil, "", "", false
	}
	rows, err := h.store.DepartmentCost(r.Context(), from, to)
	if err != nil {
		h.log.Error("department cost query failed", "err", err)
		writeError(w, http.StatusInternalServerError, "Could not build the report")
		return nil, "", "", false
	}
	return rows, fromS, toS, true
}

func (h *Handler) departmentCost(w http.ResponseWriter, r *http.Request) {
	rows, _, _, ok := h.loadDepartmentCost(w, r)
	if !ok {
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"rows": rows, "totals": report.Totals(rows)})
}

func (h *Handler) departmentCostCSV(w http.ResponseWriter, r *http.Request) {
	rows, from, to, ok := h.loadDepartmentCost(w, r)
	if !ok {
		return
	}
	w.Header().Set("Content-Type", "text/csv; charset=utf-8")
	w.Header().Set("Content-Disposition", fmt.Sprintf(`attachment; filename="payroll-cost-%s-%s.csv"`, from, to))
	if err := report.WriteDepartmentCostCSV(w, rows); err != nil {
		h.log.Error("csv write failed", "err", err)
	}
}

func (h *Handler) payrollSummary(w http.ResponseWriter, r *http.Request) {
	year := time.Now().Year()
	if y := r.URL.Query().Get("year"); y != "" {
		v, err := strconv.Atoi(y)
		if err != nil || v < 2000 || v > 2100 {
			writeError(w, http.StatusBadRequest, "invalid year")
			return
		}
		year = v
	}
	rows, err := h.store.PayRunSummaries(r.Context(), year)
	if err != nil {
		h.log.Error("summary query failed", "err", err)
		writeError(w, http.StatusInternalServerError, "Could not build the report")
		return
	}
	writeJSON(w, http.StatusOK, rows)
}
