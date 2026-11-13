package auth

import (
	"net/http/httptest"
	"testing"
	"time"

	"github.com/golang-jwt/jwt/v5"
)

func sign(t *testing.T, secret string, claims Claims) string {
	t.Helper()
	tok, err := jwt.NewWithClaims(jwt.SigningMethodHS256, claims).SignedString([]byte(secret))
	if err != nil {
		t.Fatal(err)
	}
	return tok
}

func TestFromRequest(t *testing.T) {
	v := NewVerifier("secret-for-tests-secret-for-tests")
	tok := sign(t, "secret-for-tests-secret-for-tests", Claims{Role: "ADMIN", RegisteredClaims: jwt.RegisteredClaims{ExpiresAt: jwt.NewNumericDate(time.Now().Add(time.Hour))}})

	r := httptest.NewRequest("GET", "/", nil)
	r.Header.Set("Authorization", "Bearer "+tok)
	c, err := v.FromRequest(r)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if c.Role != "ADMIN" {
		t.Fatalf("role = %q", c.Role)
	}
}

func TestRejectsWrongSecretAndMissingHeader(t *testing.T) {
	v := NewVerifier("secret-for-tests-secret-for-tests")
	tok := sign(t, "another-secret-another-secret-xx", Claims{Role: "ADMIN"})
	r := httptest.NewRequest("GET", "/", nil)
	r.Header.Set("Authorization", "Bearer "+tok)
	if _, err := v.FromRequest(r); err == nil {
		t.Fatal("expected signature error")
	}
	if _, err := v.FromRequest(httptest.NewRequest("GET", "/", nil)); err != ErrMissingToken {
		t.Fatalf("expected ErrMissingToken, got %v", err)
	}
}
