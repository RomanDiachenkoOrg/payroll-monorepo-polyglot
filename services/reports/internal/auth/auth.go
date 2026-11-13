package auth

import (
	"context"
	"errors"
	"net/http"
	"strings"

	"github.com/golang-jwt/jwt/v5"
)

// Claims mirrors the token issued by the payroll API.
type Claims struct {
	Email string `json:"email"`
	Name  string `json:"name"`
	Role  string `json:"role"`
	jwt.RegisteredClaims
}

type ctxKey struct{}

// Verifier validates HS256 bearer tokens.
type Verifier struct {
	secret []byte
}

func NewVerifier(secret string) *Verifier {
	return &Verifier{secret: []byte(secret)}
}

var ErrMissingToken = errors.New("missing bearer token")

// Parse validates a raw token string.
func (v *Verifier) Parse(raw string) (*Claims, error) {
	claims := &Claims{}
	_, err := jwt.ParseWithClaims(raw, claims, func(t *jwt.Token) (any, error) {
		return v.secret, nil
	}, jwt.WithValidMethods([]string{"HS256"}))
	if err != nil {
		return nil, err
	}
	return claims, nil
}

// FromRequest extracts and validates the Authorization header.
func (v *Verifier) FromRequest(r *http.Request) (*Claims, error) {
	h := r.Header.Get("Authorization")
	if len(h) < 8 || !strings.EqualFold(h[:7], "bearer ") {
		return nil, ErrMissingToken
	}
	return v.Parse(strings.TrimSpace(h[7:]))
}

// WithClaims stores claims on the context.
func WithClaims(ctx context.Context, c *Claims) context.Context {
	return context.WithValue(ctx, ctxKey{}, c)
}

// ClaimsFrom returns the claims stored on the context, if any.
func ClaimsFrom(ctx context.Context) *Claims {
	c, _ := ctx.Value(ctxKey{}).(*Claims)
	return c
}
