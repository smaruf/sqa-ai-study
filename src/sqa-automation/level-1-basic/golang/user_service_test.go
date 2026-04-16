// Level 1 - Basic: Table-Driven Tests and testify in Go
// ======================================================
// Idiomatic Go uses table-driven tests extensively.
// testify/assert provides richer failure messages than the stdlib.
//
// Install:  go get github.com/stretchr/testify/assert
// Run:      go test -v ./...

package level1

import (
	"errors"
	"fmt"
	"strings"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// ── System Under Test ─────────────────────────────────────────────────────────

// UserService manages a simple in-memory user store.
type UserService struct {
	store  map[int]User
	nextID int
}

// User represents a registered user.
type User struct {
	ID    int
	Name  string
	Email string
}

// NewUserService creates an initialised UserService.
func NewUserService() *UserService {
	return &UserService{store: make(map[int]User), nextID: 1}
}

// Create validates and stores a new user.
func (s *UserService) Create(name, email string) (User, error) {
	if strings.TrimSpace(name) == "" {
		return User{}, errors.New("name must not be blank")
	}
	if !strings.Contains(email, "@") {
		return User{}, fmt.Errorf("invalid email address: %q", email)
	}
	u := User{ID: s.nextID, Name: strings.TrimSpace(name), Email: strings.TrimSpace(email)}
	s.store[s.nextID] = u
	s.nextID++
	return u, nil
}

// FindByID returns the user with the given ID, or an error if not found.
func (s *UserService) FindByID(id int) (User, error) {
	u, ok := s.store[id]
	if !ok {
		return User{}, fmt.Errorf("user not found: %d", id)
	}
	return u, nil
}

// Delete removes a user; returns true if the user existed.
func (s *UserService) Delete(id int) bool {
	_, ok := s.store[id]
	delete(s.store, id)
	return ok
}

// Count returns the number of stored users.
func (s *UserService) Count() int { return len(s.store) }

// ── Tests ─────────────────────────────────────────────────────────────────────

func TestUserService_Create(t *testing.T) {
	svc := NewUserService()

	user, err := svc.Create("Alice", "alice@example.com")

	// require stops the test immediately on failure (unlike assert which continues)
	require.NoError(t, err)
	assert.Equal(t, 1, user.ID)
	assert.Equal(t, "Alice", user.Name)
	assert.Equal(t, "alice@example.com", user.Email)
}

func TestUserService_Create_AssignsSequentialIDs(t *testing.T) {
	svc := NewUserService()
	alice, _ := svc.Create("Alice", "alice@example.com")
	bob, _   := svc.Create("Bob",   "bob@example.com")
	assert.Equal(t, bob.ID, alice.ID+1)
}

func TestUserService_FindByID(t *testing.T) {
	svc := NewUserService()
	created, _ := svc.Create("Alice", "alice@example.com")

	found, err := svc.FindByID(created.ID)

	require.NoError(t, err)
	assert.Equal(t, created, found)
}

func TestUserService_FindByID_NotFound_ReturnsError(t *testing.T) {
	svc := NewUserService()
	_, err := svc.FindByID(999)
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "user not found")
}

func TestUserService_Delete(t *testing.T) {
	svc := NewUserService()
	user, _ := svc.Create("Alice", "alice@example.com")

	removed := svc.Delete(user.ID)

	assert.True(t, removed)
	assert.Equal(t, 0, svc.Count())
}

func TestUserService_Delete_NonExistent_ReturnsFalse(t *testing.T) {
	svc := NewUserService()
	assert.False(t, svc.Delete(999))
}

// ── Table-driven validation tests ─────────────────────────────────────────────

func TestUserService_Create_BlankName_ReturnsError(t *testing.T) {
	blankNames := []string{"", "  ", "\t", "\n"}
	svc := NewUserService()

	for _, name := range blankNames {
		t.Run(fmt.Sprintf("name=%q", name), func(t *testing.T) {
			_, err := svc.Create(name, "user@example.com")
			assert.Error(t, err)
			assert.Contains(t, err.Error(), "name must not be blank")
		})
	}
}

func TestUserService_Create_InvalidEmail_ReturnsError(t *testing.T) {
	tests := []struct {
		email string
	}{
		{"not-an-email"},
		{"missing-at-sign.com"},
		{""},
	}

	svc := NewUserService()
	for _, tc := range tests {
		t.Run(tc.email, func(t *testing.T) {
			_, err := svc.Create("Alice", tc.email)
			assert.Error(t, err)
		})
	}
}

// ── Parameterised (table-driven) success cases ────────────────────────────────

func TestUserService_Create_ValidInputs(t *testing.T) {
	tests := []struct {
		name  string
		email string
	}{
		{"Alice",   "alice@example.com"},
		{"Bob",     "bob@example.com"},
		{"Carol",   "carol@corp.org"},
		{"  Dave ", "dave@example.com"},   // leading/trailing space is trimmed
	}

	svc := NewUserService()
	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			user, err := svc.Create(tc.name, tc.email)
			require.NoError(t, err)
			assert.Equal(t, strings.TrimSpace(tc.name), user.Name)
		})
	}
}
