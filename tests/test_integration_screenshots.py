"""
Integration tests for the INIS visa application form filler.

These are NOT unit tests. They launch a real Chrome browser, navigate to
https://www.visas.inis.gov.ie/AVATS/VisaTypeDetails.aspx, fill each page
using the real fill_page_N() functions, and take a screenshot after each page.

Prerequisites:
  - Chrome and ChromeDriver must be installed and on PATH
  - Network access to visas.inis.gov.ie must be available

Run:
  RUN_INTEGRATION_TESTS=1 python -m unittest tests.test_integration_screenshots -v

Screenshots are saved to:
  screenshots/integration/page_N_after_fill_YYYYMMDD_HHMMSS.png

NOTE: This file is intentionally excluded from tests/run_tests.py. It is also
skipped automatically during `python -m unittest discover tests` unless the
RUN_INTEGRATION_TESTS=1 environment variable is set.
"""

import os
import sys
import time
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

from insert_function.utils import take_screenshot, log_operation, setup_logging
from insert_function.page_fillers import (
    fill_page_1, fill_page_2, fill_page_3, fill_page_4, fill_page_5,
    fill_page_6, fill_page_7, fill_page_8, fill_page_9, fill_page_10,
)

SCREENSHOTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "screenshots", "integration",
)

TARGET_URL = "https://www.visas.inis.gov.ie/AVATS/VisaTypeDetails.aspx"

logger = setup_logging()


@unittest.skipUnless(
    os.environ.get("RUN_INTEGRATION_TESTS") == "1",
    "Skipped: set RUN_INTEGRATION_TESTS=1 to run integration tests",
)
class TestIntegrationScreenshots(unittest.TestCase):
    """
    Integration test that fills the INIS visa form page by page and
    takes a screenshot after each page fill.

    All 10 test methods share one browser session (setUpClass) so the form
    session is preserved across pages. Methods are named test_page_01 …
    test_page_10 so unittest's alphabetical sort runs them in the correct order.

    If any page fails, all subsequent pages are skipped via the
    failed_at_page class variable.

    Screenshots capture the browser state AFTER fill_page_N() returns
    (i.e. after the Next button has been clicked). They show the page the
    browser transitioned to, which is useful for verifying that the form
    advanced correctly and that no errors appeared.
    """

    @classmethod
    def setUpClass(cls):
        """Launch one Chrome browser for the entire test run."""
        options = Options()
        options.add_experimental_option("detach", True)  # Keep browser open on failure
        options.add_argument("--start-maximized")

        cls.browser = webdriver.Chrome(options=options)
        cls.wait = WebDriverWait(cls.browser, 10)
        cls.screenshots_taken = []
        cls.failed_at_page = None

        log_operation("setUpClass", "INFO", f"Navigating to {TARGET_URL}")
        cls.browser.get(TARGET_URL)
        time.sleep(3)
        cls.wait.until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        log_operation("setUpClass", "INFO", f"Page title: {cls.browser.title}")

    @classmethod
    def tearDownClass(cls):
        """Print a summary of screenshots taken, then close the browser."""
        print("\n" + "=" * 60)
        print("Integration Test — Screenshot Summary")
        print("=" * 60)
        if cls.screenshots_taken:
            print(f"{len(cls.screenshots_taken)} screenshot(s) saved:")
            for path in cls.screenshots_taken:
                print(f"  {path}")
        else:
            print("No screenshots were saved.")
        if cls.failed_at_page:
            print(f"\nTest stopped at page {cls.failed_at_page}.")
        print("=" * 60)

        try:
            cls.browser.quit()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _screenshot(self, page_num, suffix="after_fill"):
        """Take a screenshot and record the path in cls.screenshots_taken."""
        label = f"page_{page_num:02d}_{suffix}"
        path = take_screenshot(self.browser, label, output_dir=SCREENSHOTS_DIR)
        if path:
            self.__class__.screenshots_taken.append(path)
        return path

    def _assert_fill_succeeded(self, result, page_num):
        """
        Assert that fill_page_N() returned an accepted success value.

        Accepted:  True, "success", "submission_complete", or "form_page_N"
                   (page jump — logged as a warning but not a failure)
        Failures:  False, "application_error", "homepage_redirect"
        """
        if result == "application_error":
            self._screenshot(page_num, suffix="application_error")
            self.__class__.failed_at_page = page_num
            self.fail(
                f"Page {page_num}: fill_page_{page_num}() returned 'application_error' — "
                "unrecoverable error state."
            )

        if result is False:
            self._screenshot(page_num, suffix="fill_failed")
            self.__class__.failed_at_page = page_num
            self.fail(f"Page {page_num}: fill_page_{page_num}() returned False.")

        if isinstance(result, str) and "homepage_redirect" in result:
            self._screenshot(page_num, suffix="homepage_redirect")
            self.__class__.failed_at_page = page_num
            self.fail(
                f"Page {page_num}: unexpected homepage redirect — session may have expired."
            )

        # Accepted outcomes
        if result in (True, "success", "submission_complete"):
            return

        if isinstance(result, str) and "form_page_" in result:
            log_operation(
                f"assert_fill_succeeded page {page_num}",
                "WARN",
                f"Page jump detected: {result}",
            )
            return

        log_operation(
            f"assert_fill_succeeded page {page_num}",
            "WARN",
            f"Unrecognised result: {result!r}",
        )

    def _skip_if_failed(self):
        if self.__class__.failed_at_page is not None:
            self.skipTest(
                f"Skipping — page {self.__class__.failed_at_page} already failed."
            )

    # ------------------------------------------------------------------
    # Test methods (zero-padded names guarantee alphabetical == numeric order)
    # ------------------------------------------------------------------

    def test_page_01(self):
        """Fill page 1 and screenshot the resulting state."""
        self._skip_if_failed()
        log_operation("test_page_01", "INFO", "Filling page 1...")
        result = fill_page_1(self.browser, self.wait)
        self._screenshot(1)
        self._assert_fill_succeeded(result, 1)
        time.sleep(2)

    def test_page_02(self):
        """Fill page 2 and screenshot the resulting state."""
        self._skip_if_failed()
        log_operation("test_page_02", "INFO", "Filling page 2...")
        result = fill_page_2(self.browser, self.wait)
        self._screenshot(2)
        self._assert_fill_succeeded(result, 2)
        time.sleep(2)

    def test_page_03(self):
        """Fill page 3 and screenshot the resulting state."""
        self._skip_if_failed()
        log_operation("test_page_03", "INFO", "Filling page 3...")
        result = fill_page_3(self.browser, self.wait)
        self._screenshot(3)
        self._assert_fill_succeeded(result, 3)
        time.sleep(2)

    def test_page_04(self):
        """Fill page 4 and screenshot the resulting state."""
        self._skip_if_failed()
        log_operation("test_page_04", "INFO", "Filling page 4...")
        result = fill_page_4(self.browser, self.wait)
        self._screenshot(4)
        self._assert_fill_succeeded(result, 4)
        time.sleep(2)

    def test_page_05(self):
        """Fill page 5 and screenshot the resulting state."""
        self._skip_if_failed()
        log_operation("test_page_05", "INFO", "Filling page 5...")
        result = fill_page_5(self.browser, self.wait)
        self._screenshot(5)
        self._assert_fill_succeeded(result, 5)
        time.sleep(2)

    def test_page_06(self):
        """Fill page 6 and screenshot the resulting state."""
        self._skip_if_failed()
        log_operation("test_page_06", "INFO", "Filling page 6...")
        result = fill_page_6(self.browser, self.wait)
        self._screenshot(6)
        self._assert_fill_succeeded(result, 6)
        time.sleep(2)

    def test_page_07(self):
        """Fill page 7 and screenshot the resulting state."""
        self._skip_if_failed()
        log_operation("test_page_07", "INFO", "Filling page 7...")
        result = fill_page_7(self.browser, self.wait)
        self._screenshot(7)
        self._assert_fill_succeeded(result, 7)
        time.sleep(2)

    def test_page_08(self):
        """Fill page 8 and screenshot the resulting state."""
        self._skip_if_failed()
        log_operation("test_page_08", "INFO", "Filling page 8...")
        result = fill_page_8(self.browser, self.wait)
        self._screenshot(8)
        self._assert_fill_succeeded(result, 8)
        time.sleep(2)

    def test_page_09(self):
        """Fill page 9 and screenshot the resulting state."""
        self._skip_if_failed()
        log_operation("test_page_09", "INFO", "Filling page 9...")
        result = fill_page_9(self.browser, self.wait)
        self._screenshot(9)
        self._assert_fill_succeeded(result, 9)
        time.sleep(2)

    def test_page_10(self):
        """Fill page 10 (final submission) and screenshot the resulting state."""
        self._skip_if_failed()
        log_operation("test_page_10", "INFO", "Filling page 10 (final submission)...")
        result = fill_page_10(self.browser, self.wait)
        self._screenshot(10)
        self._assert_fill_succeeded(result, 10)


if __name__ == "__main__":
    unittest.main(verbosity=2)
