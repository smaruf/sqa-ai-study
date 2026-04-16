// Level 4 - Expert: Security Anti-Patterns in Go
// ================================================
// Demonstrates gosec-detectable vulnerabilities and their secure alternatives.
//
// WARNING: The insecure examples are intentionally vulnerable.
//          NEVER use them in production.
//
// Run security scan: gosec ./...
// Run tests:         go test -v ./...

package level4

import (
	"crypto/rand"
	"crypto/sha256"
	"crypto/subtle"
	"database/sql"
	"encoding/hex"
	"fmt"
	"os"
	"path/filepath"
	"testing"

	"golang.org/x/crypto/bcrypt"
	_ "github.com/mattn/go-sqlite3"
)

// ── A01: Path Traversal ───────────────────────────────────────────────────────

// ReadFileInsecure does NOT validate that the path stays within baseDir.
// Attacker can pass "../../etc/passwd".
func ReadFileInsecure(baseDir, filename string) ([]byte, error) {
	return os.ReadFile(filepath.Join(baseDir, filename))
}

// ReadFileSecure validates that the resolved path stays within baseDir.
func ReadFileSecure(baseDir, filename string) ([]byte, error) {
	base, err := filepath.Abs(baseDir)
	if err != nil {
		return nil, err
	}
	target, err := filepath.Abs(filepath.Join(baseDir, filename))
	if err != nil {
		return nil, err
	}
	// Ensure target is within base
	rel, err := filepath.Rel(base, target)
	if err != nil || len(rel) > 2 && rel[:3] == "../" || rel == ".." {
		return nil, fmt.Errorf("path traversal detected: %q is outside base dir", filename)
	}
	return os.ReadFile(target)
}

func TestReadFileSecure_WithinBase(t *testing.T) {
	dir := t.TempDir()
	if err := os.WriteFile(filepath.Join(dir, "safe.txt"), []byte("safe"), 0o600); err != nil {
		t.Fatal(err)
	}
	data, err := ReadFileSecure(dir, "safe.txt")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if string(data) != "safe" {
		t.Errorf("got %q; want %q", data, "safe")
	}
}

func TestReadFileSecure_PathTraversalRejected(t *testing.T) {
	dir := t.TempDir()
	_, err := ReadFileSecure(dir, "../../etc/passwd")
	if err == nil {
		t.Error("expected error for path traversal, got nil")
	}
}

// ── A02: Cryptographic Failures ───────────────────────────────────────────────

// HashPasswordInsecure uses plain SHA-256 — fast but not suitable for passwords.
func HashPasswordInsecure(password string) string {
	h := sha256.Sum256([]byte(password))
	return hex.EncodeToString(h[:])
}

// HashPasswordSecure uses bcrypt (adaptive cost, built-in salt).
func HashPasswordSecure(password string) (string, error) {
	hash, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	return string(hash), err
}

// VerifyPasswordSecure uses constant-time comparison via bcrypt.
func VerifyPasswordSecure(password, hash string) bool {
	return bcrypt.CompareHashAndPassword([]byte(hash), []byte(password)) == nil
}

func TestHashPasswordSecure_VerifiesCorrectPassword(t *testing.T) {
	hash, err := HashPasswordSecure("my_secret")
	if err != nil {
		t.Fatalf("hashing error: %v", err)
	}
	if !VerifyPasswordSecure("my_secret", hash) {
		t.Error("expected password to verify successfully")
	}
}

func TestHashPasswordSecure_RejectsWrongPassword(t *testing.T) {
	hash, _ := HashPasswordSecure("correct")
	if VerifyPasswordSecure("wrong", hash) {
		t.Error("expected wrong password to fail verification")
	}
}

func TestHashPasswordSecure_TwoHashesDiffer(t *testing.T) {
	h1, _ := HashPasswordSecure("password")
	h2, _ := HashPasswordSecure("password")
	if h1 == h2 {
		t.Error("expected different hashes due to random salt")
	}
}

// ── A03: SQL Injection ────────────────────────────────────────────────────────

func setupTestDB(t *testing.T) *sql.DB {
	t.Helper()
	db, err := sql.Open("sqlite3", ":memory:")
	if err != nil {
		t.Fatal(err)
	}
	_, err = db.Exec("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT)")
	if err != nil {
		t.Fatal(err)
	}
	_, err = db.Exec("INSERT INTO users VALUES (1, 'Alice', 'alice@example.com')")
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = db.Close() })
	return db
}

// FindByEmailInsecure: vulnerable to SQL injection.
func FindByEmailInsecure(db *sql.DB, email string) ([]string, error) {
	query := fmt.Sprintf("SELECT name FROM users WHERE email = '%s'", email) //nolint:gosec
	rows, err := db.Query(query)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var names []string
	for rows.Next() {
		var name string
		if err := rows.Scan(&name); err != nil {
			return nil, err
		}
		names = append(names, name)
	}
	return names, rows.Err()
}

// FindByEmailSecure: uses parameterised query.
func FindByEmailSecure(db *sql.DB, email string) ([]string, error) {
	rows, err := db.Query("SELECT name FROM users WHERE email = ?", email)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var names []string
	for rows.Next() {
		var name string
		if err := rows.Scan(&name); err != nil {
			return nil, err
		}
		names = append(names, name)
	}
	return names, rows.Err()
}

func TestFindByEmailSecure_FindsUser(t *testing.T) {
	db := setupTestDB(t)
	names, err := FindByEmailSecure(db, "alice@example.com")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(names) != 1 || names[0] != "Alice" {
		t.Errorf("got %v; want [Alice]", names)
	}
}

func TestFindByEmailSecure_InjectionReturnsEmpty(t *testing.T) {
	db := setupTestDB(t)
	names, err := FindByEmailSecure(db, "' OR '1'='1")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(names) != 0 {
		t.Errorf("expected empty result for injection payload, got %v", names)
	}
}

// ── A07: Weak Token Generation ────────────────────────────────────────────────

// GenerateTokenSecure uses crypto/rand for a cryptographically secure token.
func GenerateTokenSecure(nbytes int) (string, error) {
	b := make([]byte, nbytes)
	if _, err := rand.Read(b); err != nil {
		return "", err
	}
	return hex.EncodeToString(b), nil
}

// ConstantTimeEqual uses subtle.ConstantTimeCompare to prevent timing attacks.
func ConstantTimeEqual(a, b string) bool {
	return subtle.ConstantTimeCompare([]byte(a), []byte(b)) == 1
}

func TestGenerateTokenSecure_HasExpectedLength(t *testing.T) {
	token, err := GenerateTokenSecure(32)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(token) != 64 { // hex: 2 chars per byte
		t.Errorf("token length = %d; want 64", len(token))
	}
}

func TestGenerateTokenSecure_TokensAreUnique(t *testing.T) {
	seen := make(map[string]bool, 1000)
	for i := 0; i < 1000; i++ {
		tok, _ := GenerateTokenSecure(32)
		if seen[tok] {
			t.Fatal("duplicate token generated")
		}
		seen[tok] = true
	}
}
