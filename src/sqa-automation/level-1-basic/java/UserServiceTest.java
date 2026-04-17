// Level 1 - Basic: JUnit 5 Lifecycle, Assertions, and Parameterised Tests
// =========================================================================
// Demonstrates @BeforeEach/@AfterEach, AssertJ assertions,
// and @ParameterizedTest with @CsvSource.
//
// Maven dependencies:
//   org.junit.jupiter:junit-jupiter:5.10.x
//   org.assertj:assertj-core:3.25.x
//
// Run:  mvn test

package sqa.level1;

import org.junit.jupiter.api.*;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;
import org.junit.jupiter.params.provider.ValueSource;

import java.util.ArrayList;
import java.util.List;

import static org.assertj.core.api.Assertions.*;
import static org.junit.jupiter.api.Assertions.*;

/**
 * User service with a basic in-memory repository.
 */
class UserService {

    record User(int id, String name, String email) {}

    private final List<User> store = new ArrayList<>();
    private int nextId = 1;

    User create(String name, String email) {
        if (name == null || name.isBlank())
            throw new IllegalArgumentException("Name must not be blank");
        if (email == null || !email.contains("@"))
            throw new IllegalArgumentException("Invalid email address");
        var user = new User(nextId++, name.trim(), email.trim());
        store.add(user);
        return user;
    }

    List<User> findAll() { return List.copyOf(store); }

    User findById(int id) {
        return store.stream().filter(u -> u.id() == id).findFirst()
                .orElseThrow(() -> new IllegalArgumentException("User not found: " + id));
    }

    boolean delete(int id) {
        return store.removeIf(u -> u.id() == id);
    }
}

// ── Lifecycle tests ───────────────────────────────────────────────────────────

@DisplayName("UserService")
class UserServiceTest {

    private UserService service;

    /** Runs before each @Test method. */
    @BeforeEach
    void setUp() {
        service = new UserService();
    }

    /** Runs after each @Test method — for cleanup (e.g. closing resources). */
    @AfterEach
    void tearDown() {
        // Nothing to clean up here; shown for completeness.
    }

    @Test
    @DisplayName("creates a user and assigns a sequential ID")
    void createUser_AssignsSequentialId() {
        var alice = service.create("Alice", "alice@example.com");
        var bob   = service.create("Bob",   "bob@example.com");

        // AssertJ fluent assertions
        assertThat(alice.id()).isEqualTo(1);
        assertThat(bob.id()).isEqualTo(2);
    }

    @Test
    @DisplayName("findById returns the correct user")
    void findById_ReturnsCorrectUser() {
        var created = service.create("Alice", "alice@example.com");
        var found   = service.findById(created.id());

        assertThat(found).isNotNull();
        assertThat(found.name()).isEqualTo("Alice");
        assertThat(found.email()).isEqualTo("alice@example.com");
    }

    @Test
    @DisplayName("findById throws for unknown ID")
    void findById_UnknownId_Throws() {
        assertThatThrownBy(() -> service.findById(999))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("User not found");
    }

    @Test
    @DisplayName("delete removes user from store")
    void delete_RemovesUser() {
        var user = service.create("Alice", "alice@example.com");
        boolean removed = service.delete(user.id());

        assertThat(removed).isTrue();
        assertThat(service.findAll()).isEmpty();
    }

    @Test
    @DisplayName("delete returns false for non-existent user")
    void delete_NonExistentUser_ReturnsFalse() {
        assertThat(service.delete(999)).isFalse();
    }

    // ── Validation tests ──────────────────────────────────────────────────────

    @ParameterizedTest(name = "blank name [{0}] should throw")
    @ValueSource(strings = {"", "  ", "\t"})
    @DisplayName("create with blank name throws")
    void create_BlankName_Throws(String blankName) {
        assertThatIllegalArgumentException()
                .isThrownBy(() -> service.create(blankName, "user@example.com"))
                .withMessageContaining("Name must not be blank");
    }

    @ParameterizedTest(name = "invalid email [{0}] should throw")
    @ValueSource(strings = {"not-an-email", "", "missing-at-sign.com"})
    @DisplayName("create with invalid email throws")
    void create_InvalidEmail_Throws(String badEmail) {
        assertThatIllegalArgumentException()
                .isThrownBy(() -> service.create("Alice", badEmail));
    }

    // ── Parameterised tests with CSV input ────────────────────────────────────

    @ParameterizedTest(name = "create({0}, {1}) → name={0}")
    @CsvSource({
        "Alice, alice@example.com",
        "Bob,   bob@example.com",
        "Carol, carol@example.com"
    })
    @DisplayName("created user has correct name and email")
    void create_ValidInput_StoresCorrectly(String name, String email) {
        var user = service.create(name.trim(), email.trim());

        assertThat(user.name()).isEqualTo(name.trim());
        assertThat(user.email()).isEqualTo(email.trim());
    }
}
