"""
Level 3 - Advanced: Playwright E2E Tests in Python
===================================================
Playwright drives a real browser (Chromium/Firefox/WebKit) and lets
you test the full user experience of a web application.

Prerequisites:
    pip install playwright pytest-playwright
    playwright install chromium

Run:
    pytest 01_playwright_e2e.py -v --headed  # --headed shows the browser

NOTE: These tests target https://playwright.dev/python/docs/intro
      as a stable, public demonstration target. Adapt the URLs and
      selectors to your own application.
"""

import pytest
from playwright.sync_api import Page, expect


# ─── Page Object Model ────────────────────────────────────────────────────────
# The Page Object pattern encapsulates selectors and interactions,
# making tests more readable and maintainable.

class PlaywrightDocsPage:
    """Page object for https://playwright.dev."""

    URL = "https://playwright.dev"

    def __init__(self, page: Page):
        self._page = page

    def navigate(self):
        self._page.goto(self.URL)

    def search(self, query: str):
        self._page.get_by_role("button", name="Search").click()
        self._page.get_by_placeholder("Search docs").fill(query)

    @property
    def title(self) -> str:
        return self._page.title()

    @property
    def heading(self):
        return self._page.get_by_role("heading", name="Playwright enables reliable end-to-end testing")


# ─── Tests ────────────────────────────────────────────────────────────────────

@pytest.mark.skip(reason="Requires network access — enable for live E2E runs")
def test_playwright_docs_page_has_correct_title(page: Page):
    """Verify the page title contains 'Playwright'."""
    docs = PlaywrightDocsPage(page)
    docs.navigate()
    expect(page).to_have_title("Fast and reliable end-to-end testing for modern web apps | Playwright")


@pytest.mark.skip(reason="Requires network access — enable for live E2E runs")
def test_playwright_docs_main_heading_is_visible(page: Page):
    """Verify the main heading is visible."""
    docs = PlaywrightDocsPage(page)
    docs.navigate()
    expect(docs.heading).to_be_visible()


# ─── Local app E2E example ────────────────────────────────────────────────────
# The tests below show how you would test a local web app.
# Replace the URL and selectors with your own application.

class LoginPage:
    """Page object for a login form."""

    def __init__(self, page: Page, base_url: str):
        self._page = page
        self._base_url = base_url

    def navigate(self):
        self._page.goto(f"{self._base_url}/login")

    def fill_email(self, email: str):
        self._page.get_by_label("Email").fill(email)

    def fill_password(self, password: str):
        self._page.get_by_label("Password").fill(password)

    def submit(self):
        self._page.get_by_role("button", name="Sign in").click()

    def error_message(self):
        return self._page.get_by_role("alert")


@pytest.mark.skip(reason="Requires a running local app — remove skip to enable")
def test_login_with_valid_credentials_redirects_to_dashboard(page: Page):
    """
    Full login flow:
    1. Navigate to /login
    2. Fill in valid credentials
    3. Submit the form
    4. Assert redirect to /dashboard
    """
    login = LoginPage(page, "http://localhost:8000")
    login.navigate()
    login.fill_email("alice@example.com")
    login.fill_password("secret123")
    login.submit()

    expect(page).to_have_url("http://localhost:8000/dashboard")


@pytest.mark.skip(reason="Requires a running local app — remove skip to enable")
def test_login_with_wrong_password_shows_error(page: Page):
    login = LoginPage(page, "http://localhost:8000")
    login.navigate()
    login.fill_email("alice@example.com")
    login.fill_password("wrong-password")
    login.submit()

    expect(login.error_message()).to_be_visible()
    expect(login.error_message()).to_contain_text("Invalid credentials")
