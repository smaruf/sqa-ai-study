// Level 3 - Advanced: Cucumber BDD Step Definitions in Java
// ===========================================================
// This file contains JUnit 5 + Cucumber step definitions matching
// the login.feature Gherkin scenarios.
//
// Maven dependencies:
//   io.cucumber:cucumber-java:7.x
//   io.cucumber:cucumber-junit-platform-engine:7.x
//   org.junit.platform:junit-platform-suite:1.10.x
//
// Run:  mvn test

package sqa.level3;

import io.cucumber.java.en.*;
import io.cucumber.java.Before;
import static org.junit.jupiter.api.Assertions.*;

import java.util.HashMap;
import java.util.Map;

public class LoginSteps {

    // ── Simple AuthService (SUT) ───────────────────────────────────────────────

    static class AuthService {
        private final Map<String, Map<String, String>> users = new HashMap<>();

        void register(String email, String password, String name) {
            users.put(email, Map.of("password", password, "name", name));
        }

        Map<String, String> login(String email, String password) {
            var user = users.get(email);
            if (user == null || !user.get("password").equals(password)) {
                throw new SecurityException("Invalid credentials");
            }
            return Map.of("token", "tok_" + email, "name", user.get("name"));
        }
    }

    // ── Shared state between steps ─────────────────────────────────────────────

    private AuthService authService;
    private Map<String, String> loginResult;
    private String error;
    private String currentEmail;
    private String currentPassword;

    @Before
    public void setup() {
        authService = new AuthService();
        loginResult = null;
        error       = null;
    }

    // ── Step definitions ───────────────────────────────────────────────────────

    @Given("a registered user with email {string} and password {string}")
    public void a_registered_user(String email, String password) {
        authService.register(email, password, "Test User");
        currentEmail    = email;
        currentPassword = password;
    }

    @When("they log in with the correct password")
    public void login_with_correct_password() {
        try {
            loginResult = authService.login(currentEmail, currentPassword);
            error       = null;
        } catch (SecurityException e) {
            loginResult = null;
            error       = e.getMessage();
        }
    }

    @When("they log in with the wrong password {string}")
    public void login_with_wrong_password(String wrongPassword) {
        try {
            loginResult = authService.login(currentEmail, wrongPassword);
            error       = null;
        } catch (SecurityException e) {
            loginResult = null;
            error       = e.getMessage();
        }
    }

    @Then("they should receive a valid auth token")
    public void should_receive_token() {
        assertNotNull(loginResult, "Expected a login result but got null");
        assertTrue(loginResult.containsKey("token"));
        assertTrue(loginResult.get("token").startsWith("tok_"));
    }

    @Then("they should see an invalid credentials error")
    public void should_see_error() {
        assertNotNull(error, "Expected an error but got none");
        assertTrue(error.contains("Invalid credentials"));
    }

    @Then("they should not receive a token")
    public void should_not_receive_token() {
        assertNull(loginResult, "Expected no token but got one");
    }
}
