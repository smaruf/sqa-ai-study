// Level 2 - Intermediate: Interface-Based Mocking and HTTP Handler Testing in Go
// ================================================================================
// Go uses interfaces for dependency injection. A test simply provides a struct
// that implements the interface — no mocking library needed for many cases.
// For richer assertions, testify/mock is also available.
//
// Run:  go test -v ./...

package level2

import (
	"encoding/json"
	"errors"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// ── Interfaces (boundaries) ───────────────────────────────────────────────────

// EmailSender defines the email-sending boundary.
type EmailSender interface {
	Send(to, subject, body string) error
}

// UserRepository is the storage boundary.
type UserRepository interface {
	Save(name, email string) (User, error)
	FindByID(id int) (User, error)
}

// ── Domain ────────────────────────────────────────────────────────────────────

type User struct {
	ID    int    `json:"id"`
	Name  string `json:"name"`
	Email string `json:"email"`
}

// NotificationService sends emails via the EmailSender interface.
type NotificationService struct {
	Sender EmailSender
}

func (n *NotificationService) Welcome(to, name string) error {
	return n.Sender.Send(to, "Welcome!", "Hello "+name+", welcome!")
}

// UserHandler handles HTTP requests and delegates to a UserRepository.
type UserHandler struct {
	Repo          UserRepository
	Notifications *NotificationService
}

func (h *UserHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	switch {
	case r.Method == http.MethodPost && r.URL.Path == "/users":
		h.createUser(w, r)
	default:
		http.NotFound(w, r)
	}
}

func (h *UserHandler) createUser(w http.ResponseWriter, r *http.Request) {
	var payload struct {
		Name  string `json:"name"`
		Email string `json:"email"`
	}
	if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
		http.Error(w, "invalid JSON", http.StatusBadRequest)
		return
	}
	if !strings.Contains(payload.Email, "@") {
		http.Error(w, "invalid email", http.StatusUnprocessableEntity)
		return
	}
	user, err := h.Repo.Save(payload.Name, payload.Email)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	_ = h.Notifications.Welcome(user.Email, user.Name)
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	_ = json.NewEncoder(w).Encode(user)
}

// ── Test doubles (fakes / stubs) ──────────────────────────────────────────────

// fakeEmailSender records calls and never fails.
type fakeEmailSender struct {
	Calls []struct{ To, Subject, Body string }
}

func (f *fakeEmailSender) Send(to, subject, body string) error {
	f.Calls = append(f.Calls, struct{ To, Subject, Body string }{to, subject, body})
	return nil
}

// fakeUserRepo is an in-memory UserRepository.
type fakeUserRepo struct {
	store  map[int]User
	nextID int
}

func newFakeUserRepo() *fakeUserRepo {
	return &fakeUserRepo{store: make(map[int]User), nextID: 1}
}

func (r *fakeUserRepo) Save(name, email string) (User, error) {
	u := User{ID: r.nextID, Name: name, Email: email}
	r.store[r.nextID] = u
	r.nextID++
	return u, nil
}

func (r *fakeUserRepo) FindByID(id int) (User, error) {
	u, ok := r.store[id]
	if !ok {
		return User{}, errors.New("user not found")
	}
	return u, nil
}

// ── Tests ─────────────────────────────────────────────────────────────────────

func newTestHandler() (*UserHandler, *fakeEmailSender, *fakeUserRepo) {
	emailSender := &fakeEmailSender{}
	repo        := newFakeUserRepo()
	handler := &UserHandler{
		Repo:          repo,
		Notifications: &NotificationService{Sender: emailSender},
	}
	return handler, emailSender, repo
}

func TestCreateUser_Returns201AndCorrectBody(t *testing.T) {
	handler, _, _ := newTestHandler()

	body := strings.NewReader(`{"name":"Alice","email":"alice@example.com"}`)
	req  := httptest.NewRequest(http.MethodPost, "/users", body)
	req.Header.Set("Content-Type", "application/json")
	rec  := httptest.NewRecorder()

	handler.ServeHTTP(rec, req)

	require.Equal(t, http.StatusCreated, rec.Code)

	var user User
	err := json.NewDecoder(rec.Body).Decode(&user)
	require.NoError(t, err)
	assert.Equal(t, 1, user.ID)
	assert.Equal(t, "Alice", user.Name)
	assert.Equal(t, "alice@example.com", user.Email)
}

func TestCreateUser_InvalidEmail_Returns422(t *testing.T) {
	handler, _, _ := newTestHandler()

	body := strings.NewReader(`{"name":"Alice","email":"not-an-email"}`)
	req  := httptest.NewRequest(http.MethodPost, "/users", body)
	rec  := httptest.NewRecorder()

	handler.ServeHTTP(rec, req)

	assert.Equal(t, http.StatusUnprocessableEntity, rec.Code)
}

func TestCreateUser_SendsWelcomeEmail(t *testing.T) {
	handler, emailSender, _ := newTestHandler()

	body := strings.NewReader(`{"name":"Alice","email":"alice@example.com"}`)
	req  := httptest.NewRequest(http.MethodPost, "/users", body)
	rec  := httptest.NewRecorder()

	handler.ServeHTTP(rec, req)

	require.Equal(t, http.StatusCreated, rec.Code)
	require.Len(t, emailSender.Calls, 1)
	assert.Equal(t, "alice@example.com", emailSender.Calls[0].To)
	assert.Equal(t, "Welcome!", emailSender.Calls[0].Subject)
}

func TestCreateUser_InvalidJSON_Returns400(t *testing.T) {
	handler, _, _ := newTestHandler()

	req := httptest.NewRequest(http.MethodPost, "/users", strings.NewReader("not-json"))
	rec := httptest.NewRecorder()

	handler.ServeHTTP(rec, req)

	assert.Equal(t, http.StatusBadRequest, rec.Code)
}

func TestUnknownRoute_Returns404(t *testing.T) {
	handler, _, _ := newTestHandler()

	req := httptest.NewRequest(http.MethodGet, "/nonexistent", nil)
	rec := httptest.NewRecorder()

	handler.ServeHTTP(rec, req)

	assert.Equal(t, http.StatusNotFound, rec.Code)
}

// ── NotificationService tests ─────────────────────────────────────────────────

func TestNotificationService_Welcome_SendsEmail(t *testing.T) {
	sender := &fakeEmailSender{}
	svc    := &NotificationService{Sender: sender}

	err := svc.Welcome("alice@example.com", "Alice")

	require.NoError(t, err)
	require.Len(t, sender.Calls, 1)
	assert.Equal(t, "alice@example.com", sender.Calls[0].To)
	assert.Contains(t, sender.Calls[0].Body, "Alice")
}
