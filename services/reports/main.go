package main

import (
	"context"
	"errors"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/RomanDiachenkoOrg/payroll-monorepo-polyglot/services/reports/internal/auth"
	"github.com/RomanDiachenkoOrg/payroll-monorepo-polyglot/services/reports/internal/config"
	"github.com/RomanDiachenkoOrg/payroll-monorepo-polyglot/services/reports/internal/httpapi"
	"github.com/RomanDiachenkoOrg/payroll-monorepo-polyglot/services/reports/internal/store"
)

func main() {
	logger := slog.New(slog.NewTextHandler(os.Stdout, nil))
	cfg := config.Load()

	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()

	db, err := store.Connect(ctx, cfg.DatabaseURL)
	if err != nil {
		logger.Error("database connection failed", "err", err)
		os.Exit(1)
	}
	defer db.Close()

	handler := httpapi.New(db, auth.NewVerifier(cfg.JWTSecret), logger)
	srv := &http.Server{
		Addr:              ":" + cfg.Port,
		Handler:           handler.Routes(),
		ReadHeaderTimeout: 5 * time.Second,
	}

	go func() {
		logger.Info("reports service listening", "addr", srv.Addr)
		if err := srv.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
			logger.Error("server error", "err", err)
			stop()
		}
	}()

	<-ctx.Done()
	shutdown, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	_ = srv.Shutdown(shutdown)
}
