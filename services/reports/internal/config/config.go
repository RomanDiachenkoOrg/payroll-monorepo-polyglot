package config

import "os"

// Config holds runtime settings read from the environment.
type Config struct {
	Port        string
	DatabaseURL string
	JWTSecret   string
}

func getenv(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}

// Load reads the configuration with local development defaults.
func Load() Config {
	return Config{
		Port:        getenv("PORT", "8081"),
		DatabaseURL: getenv("DATABASE_URL", "postgres://payroll:payroll@localhost:5432/payroll"),
		JWTSecret:   getenv("JWT_SECRET", "local-development-secret-change-me"),
	}
}
