// Level 3 - Advanced: Godog BDD Step Definitions in Go
// ======================================================
// Godog is the official Cucumber implementation for Go.
//
// Install:  go get github.com/cucumber/godog
// Run:      go test -v ./...

package level3

import (
	"context"
	"fmt"
	"strings"
	"testing"

	"github.com/cucumber/godog"
)

// ── Simple AuthService (SUT) ──────────────────────────────────────────────────

type authService struct {
	users map[string]struct{ password, name string }
}

func newAuthService() *authService {
	return &authService{users: make(map[string]struct{ password, name string })}
}

func (a *authService) register(email, password, name string) {
	a.users[email] = struct{ password, name string }{password, name}
}

func (a *authService) login(email, password string) (map[string]string, error) {
	u, ok := a.users[email]
	if !ok || u.password != password {
		return nil, fmt.Errorf("invalid credentials")
	}
	return map[string]string{"token": "tok_" + email, "name": u.name}, nil
}

// ── Shared scenario state ─────────────────────────────────────────────────────

type loginState struct {
	service     *authService
	email       string
	password    string
	loginResult map[string]string
	loginErr    error
}

// ── Step definitions ──────────────────────────────────────────────────────────

func (s *loginState) aRegisteredUser(email, password string) error {
	s.service.register(email, password, "Test User")
	s.email    = email
	s.password = password
	return nil
}

func (s *loginState) theyLogInWithCorrectPassword() error {
	s.loginResult, s.loginErr = s.service.login(s.email, s.password)
	return nil
}

func (s *loginState) theyLogInWithWrongPassword(wrongPassword string) error {
	s.loginResult, s.loginErr = s.service.login(s.email, wrongPassword)
	return nil
}

func (s *loginState) shouldReceiveValidToken() error {
	if s.loginResult == nil {
		return fmt.Errorf("expected login result but got nil")
	}
	token, ok := s.loginResult["token"]
	if !ok || !strings.HasPrefix(token, "tok_") {
		return fmt.Errorf("expected token starting with 'tok_', got %q", token)
	}
	return nil
}

func (s *loginState) shouldSeeInvalidCredentialsError() error {
	if s.loginErr == nil {
		return fmt.Errorf("expected an error but got none")
	}
	if !strings.Contains(s.loginErr.Error(), "invalid credentials") {
		return fmt.Errorf("expected 'invalid credentials' in error, got: %v", s.loginErr)
	}
	return nil
}

func (s *loginState) shouldNotReceiveToken() error {
	if s.loginResult != nil {
		return fmt.Errorf("expected no token but received one: %v", s.loginResult)
	}
	return nil
}

// ── Godog suite initialiser ───────────────────────────────────────────────────

func initScenario(sc *godog.ScenarioContext) {
	state := &loginState{service: newAuthService()}

	sc.Step(`^a registered user with email "([^"]*)" and password "([^"]*)"$`, state.aRegisteredUser)
	sc.Step(`^they log in with the correct password$`, state.theyLogInWithCorrectPassword)
	sc.Step(`^they log in with the wrong password "([^"]*)"$`, state.theyLogInWithWrongPassword)
	sc.Step(`^they should receive a valid auth token$`, state.shouldReceiveValidToken)
	sc.Step(`^they should see an invalid credentials error$`, state.shouldSeeInvalidCredentialsError)
	sc.Step(`^they should not receive a token$`, state.shouldNotReceiveToken)
}

func TestGodog(t *testing.T) {
	suite := godog.TestSuite{
		Name:                 "login",
		ScenarioInitializer:  initScenario,
		Options: &godog.Options{
			Format:   "pretty",
			Paths:    []string{"features"},
			TestingT: t,
		},
	}
	if suite.Run() != 0 {
		t.Fatal("godog scenarios failed")
	}
}

// Ensure context is used (required by godog API)
var _ = context.Background
