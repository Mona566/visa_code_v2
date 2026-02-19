"""
Hybrid Browser Automation Layer

Provides human-like browser interaction using Playwright with accessibility tree support.
Replaces Selenium's CSS ID/XPath based approach with semantic locators.
"""

from playwright.sync_api import sync_playwright, Page, Browser, Playwright
from typing import Optional, Union
import logging

logger = logging.getLogger(__name__)


class HybridBrowser:
    """
    Human-like browser automation using Playwright + Accessibility tree.

    Instead of using CSS IDs or XPath, this provides semantic locators
    that match how humans read and interact with forms.
    """

    def __init__(self, headless: bool = False, timeout: int = 30000, ignore_ssl_errors: bool = True):
        """
        Initialize the hybrid browser.

        Args:
            headless: Run browser in headless mode
            timeout: Default timeout in milliseconds
            ignore_ssl_errors: Ignore SSL certificate errors
        """
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.context = None
        self.headless = headless
        self.timeout = timeout
        self.ignore_ssl_errors = ignore_ssl_errors

    def start(self):
        """Start the browser"""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            args=['--disable-blink-features=AutomationControlled',
                  '--ignore-certificate-errors'] if self.ignore_ssl_errors else []
        )
        self.context = self.browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        self.page = self.context.new_page()
        self.page.set_default_timeout(self.timeout)
        logger.info("HybridBrowser started")
        return self

    def close(self):
        """Close the browser"""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        logger.info("HybridBrowser closed")

    def __enter__(self):
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # ─────────────────────────────────────────────────────────
    # Smart Locators (like humans read the page)
    # ─────────────────────────────────────────────────────────

    def get_by_label(self, label: str, exact: bool = False):
        """
        Find input by its label text - primary human-like method.

        Example: get_by_label("Course Title").fill("Computer Science")
        """
        if exact:
            return self.page.get_by_label(label, exact=True)
        return self.page.get_by_label(label)

    def get_by_role(self, role: str, **kwargs):
        """
        Find element by ARIA role.

        Example: get_by_role("button", name="Submit")
                 get_by_role("textbox", name="Email")
                 get_by_role("combobox", name="Country")
        """
        return self.page.get_by_role(role, **kwargs)

    def get_by_text(self, text: str, exact: bool = False):
        """Find element containing or matching text."""
        if exact:
            return self.page.get_by_text(text, exact=True)
        return self.page.get_by_text(text)

    def get_by_placeholder(self, placeholder: str, exact: bool = False):
        """Find input by placeholder text."""
        if exact:
            return self.page.get_by_placeholder(placeholder, exact=True)
        return self.page.get_by_placeholder(placeholder)

    # ─────────────────────────────────────────────────────────
    # Convenience Methods
    # ─────────────────────────────────────────────────────────

    def fill(self, label: str, value: str):
        """Fill a field by its label."""
        self.get_by_label(label, exact=False).fill(value)

    def fill_by_id(self, selector: str, value: str):
        """Fill a field by CSS ID (fallback for known IDs)."""
        self.page.fill(f"#{selector}", value)

    def select_option(self, label: str, value: str):
        """Select an option from a dropdown by label."""
        self.get_by_label(label).select_option(value)

    def select_option_by_value(self, label: str, value: str):
        """Select an option by value attribute."""
        self.get_by_label(label).select_option(value=value)

    def click(self, label: str = None, role: str = None, text: str = None, selector: str = None):
        """
        Click an element. Provide one of: label, role, text, or selector.

        Examples:
            click(label="Submit")
            click(role="button", name="Continue")
            click(text="Next")
            click(selector="#submit-btn")
        """
        if label:
            self.get_by_label(label).click()
        elif role:
            self.get_by_role(role, name=text).click()
        elif text:
            self.get_by_text(text).click()
        elif selector:
            self.page.click(selector)
        else:
            raise ValueError("Must provide label, role, text, or selector")

    def check(self, label: str):
        """Check a checkbox by its label."""
        self.get_by_label(label).check()

    def uncheck(self, label: str):
        """Uncheck a checkbox by its label."""
        self.get_by_label(label).uncheck()

    def is_checked(self, label: str) -> bool:
        """Check if a checkbox is checked."""
        return self.get_by_label(label).is_checked()

    # ─────────────────────────────────────────────────────────
    # Navigation
    # ─────────────────────────────────────────────────────────

    def goto(self, url: str):
        """Navigate to URL."""
        self.page.goto(url)
        self.page.wait_for_load_state("domcontentloaded")

    def wait_for_url(self, url_pattern: str):
        """Wait for URL to match pattern."""
        self.page.wait_for_url(url_pattern)

    @property
    def current_url(self) -> str:
        """Get current URL."""
        return self.page.url

    # ─────────────────────────────────────────────────────────
    # Debugging
    # ─────────────────────────────────────────────────────────

    def take_screenshot(self, path: str = None):
        """Take a screenshot."""
        return self.page.screenshot(path=path)

    def get_accessibility_tree(self):
        """Get accessibility tree for debugging."""
        return self.page.accessibility.snapshot()

    def print_accessibility_tree(self):
        """Print accessibility tree for debugging."""
        tree = self.get_accessibility_tree()
        print(tree)

    def highlight(self, selector: str):
        """Highlight an element for debugging."""
        self.page.evaluate(f"""
            const el = document.querySelector('{selector}');
            if (el) {{
                el.style.outline = '3px solid red';
                el.style.backgroundColor = 'yellow';
            }}
        """)


# Convenience function for backward compatibility
def create_browser(headless: bool = False) -> HybridBrowser:
    """Create and start a HybridBrowser instance."""
    browser = HybridBrowser(headless=headless)
    browser.start()
    return browser
