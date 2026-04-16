# Feature: User Login
# (Java Cucumber version — same scenarios as the Python version)

Feature: User Login

  As a registered user
  I want to be able to log in with my credentials
  So that I can access my account

  Background:
    Given a registered user with email "alice@example.com" and password "secret123"

  Scenario: Successful login with valid credentials
    When they log in with the correct password
    Then they should receive a valid auth token

  Scenario: Failed login with wrong password
    When they log in with the wrong password "wrong-password"
    Then they should see an invalid credentials error
    And they should not receive a token
