// Level 4 - Expert: Security Anti-Patterns in Java
// ==================================================
// Demonstrates Bandit/FindSecBugs-detectable vulnerabilities and their fixes.
//
// WARNING: The insecure examples are intentionally vulnerable.
//          NEVER use them in production.
//
// Run:  mvn test

package sqa.level4;

import org.junit.jupiter.api.*;
import java.security.*;
import java.security.spec.KeySpec;
import java.sql.*;
import java.util.Base64;
import javax.crypto.*;
import javax.crypto.spec.*;
import static org.junit.jupiter.api.Assertions.*;

@DisplayName("Security Anti-Patterns and Secure Alternatives")
class SecurityAntiPatternsTest {

    // ── A02: Cryptographic Failures ───────────────────────────────────────────

    /** INSECURE: MD5 is broken — do not use for passwords or integrity checks */
    static String hashInsecureMD5(String input) throws Exception {
        MessageDigest md = MessageDigest.getInstance("MD5");
        return Base64.getEncoder().encodeToString(md.digest(input.getBytes()));
    }

    /**
     * SECURE: PBKDF2-HMAC-SHA256 with a random salt.
     * In production, prefer BCrypt or Argon2 via the Spring Security or
     * Bouncy Castle library.
     */
    static byte[] hashSecure(String password) throws Exception {
        SecureRandom random = new SecureRandom();
        byte[] salt = new byte[16];
        random.nextBytes(salt);

        KeySpec spec = new PBEKeySpec(password.toCharArray(), salt, 310_000, 256);
        SecretKeyFactory f = SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256");
        byte[] hash = f.generateSecret(spec).getEncoded();

        // Prepend salt so it can be stored alongside the hash
        byte[] result = new byte[salt.length + hash.length];
        System.arraycopy(salt, 0, result, 0, salt.length);
        System.arraycopy(hash, 0, result, salt.length, hash.length);
        return result;
    }

    static boolean verifySecure(String password, byte[] stored) throws Exception {
        byte[] salt = new byte[16];
        System.arraycopy(stored, 0, salt, 0, 16);
        byte[] storedHash = new byte[stored.length - 16];
        System.arraycopy(stored, 16, storedHash, 0, storedHash.length);

        KeySpec spec = new PBEKeySpec(password.toCharArray(), salt, 310_000, 256);
        SecretKeyFactory f = SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256");
        byte[] hash = f.generateSecret(spec).getEncoded();
        return MessageDigest.isEqual(hash, storedHash);
    }

    @Test
    @DisplayName("secure hash verifies correctly with the right password")
    void secureHash_VerifiesCorrectPassword() throws Exception {
        byte[] stored = hashSecure("my_secret_password");
        assertTrue(verifySecure("my_secret_password", stored));
    }

    @Test
    @DisplayName("secure hash rejects the wrong password")
    void secureHash_RejectsWrongPassword() throws Exception {
        byte[] stored = hashSecure("correct_password");
        assertFalse(verifySecure("wrong_password", stored));
    }

    @Test
    @DisplayName("two hashes of the same password differ (random salt)")
    void secureHash_TwoHashesDiffer() throws Exception {
        byte[] h1 = hashSecure("password");
        byte[] h2 = hashSecure("password");
        assertFalse(MessageDigest.isEqual(h1, h2));
    }

    // ── A03: SQL Injection ────────────────────────────────────────────────────

    private Connection createInMemoryDb() throws SQLException {
        Connection conn = DriverManager.getConnection("jdbc:h2:mem:test;DB_CLOSE_DELAY=-1");
        conn.createStatement().execute(
                "CREATE TABLE IF NOT EXISTS users (id INT, name VARCHAR, email VARCHAR)");
        conn.createStatement().execute(
                "INSERT INTO users VALUES (1, 'Alice', 'alice@example.com')");
        return conn;
    }

    /** INSECURE: String concatenation allows SQL injection */
    java.util.List<String> findByEmailInsecure(Connection conn, String email) throws SQLException {
        // This is vulnerable: attacker can pass: ' OR '1'='1
        String sql = "SELECT name FROM users WHERE email = '" + email + "'";
        var rs = conn.createStatement().executeQuery(sql);
        java.util.List<String> names = new java.util.ArrayList<>();
        while (rs.next()) names.add(rs.getString("name"));
        return names;
    }

    /** SECURE: PreparedStatement with parameterised query */
    java.util.List<String> findByEmailSecure(Connection conn, String email) throws SQLException {
        var ps = conn.prepareStatement("SELECT name FROM users WHERE email = ?");
        ps.setString(1, email);
        var rs = ps.executeQuery();
        java.util.List<String> names = new java.util.ArrayList<>();
        while (rs.next()) names.add(rs.getString("name"));
        return names;
    }

    @Test
    @DisplayName("secure query finds the correct user")
    void secureQuery_FindsUser() throws Exception {
        var conn = createInMemoryDb();
        var names = findByEmailSecure(conn, "alice@example.com");
        assertEquals(java.util.List.of("Alice"), names);
    }

    @Test
    @DisplayName("secure query returns empty for SQL injection payload")
    void secureQuery_SqlInjectionReturnsEmpty() throws Exception {
        var conn = createInMemoryDb();
        var names = findByEmailSecure(conn, "' OR '1'='1");
        assertTrue(names.isEmpty(), "Parameterised query should not be injectable");
    }

    // ── A07: Weak Random Token ─────────────────────────────────────────────────

    /** INSECURE: java.util.Random is predictable */
    static String generateInsecureToken() {
        return String.valueOf(new java.util.Random().nextLong());
    }

    /** SECURE: SecureRandom is cryptographically strong */
    static String generateSecureToken() {
        byte[] bytes = new byte[32];
        new SecureRandom().nextBytes(bytes);
        return Base64.getUrlEncoder().withoutPadding().encodeToString(bytes);
    }

    @Test
    @DisplayName("secure tokens have expected length")
    void secureToken_HasExpectedLength() {
        String token = generateSecureToken();
        // Base64url without padding: ceil(32 * 4/3) = 43 chars
        assertTrue(token.length() >= 42);
    }

    @Test
    @DisplayName("secure tokens are unique")
    void secureToken_IsUnique() {
        var tokens = new java.util.HashSet<String>();
        for (int i = 0; i < 1000; i++) tokens.add(generateSecureToken());
        assertEquals(1000, tokens.size());
    }
}
