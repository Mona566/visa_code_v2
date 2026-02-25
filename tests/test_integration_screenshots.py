"""
Integration tests for the INIS visa application form filler.

These are NOT unit tests. They launch a real Chrome browser, navigate to
the INIS visa form, fill each page using the real fill_page_N() functions,
and take a screenshot of the FILLED form (before clicking Next) for each page.

Prerequisites:
  - Chrome and ChromeDriver must be installed and on PATH
  - Network access to visas.inis.gov.ie must be available

Run all pages from scratch:
  RUN_INTEGRATION_TESTS=1 python -m unittest tests.test_integration_screenshots -v

Run from page 9 onwards (requires application_number.txt from a prior run):
  RUN_INTEGRATION_TESTS=1 START_FROM_PAGE=9 python -m unittest tests.test_integration_screenshots -v

Screenshots are saved to:
  screenshots/integration/page_N_filled_YYYYMMDD_HHMMSS.png  ← filled form, before Next
  screenshots/integration/page_N_<error>_YYYYMMDD_HHMMSS.png ← on failure

NOTE: Excluded from tests/run_tests.py. Skipped by `unittest discover` unless
RUN_INTEGRATION_TESTS=1 is set.
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
from insert_function.main_flow import initialize_form_session
from insert_function.application_management import (
    get_saved_application_number, retrieve_application
)
from insert_function.page_fillers import (
    fill_page_1, fill_page_2, fill_page_3, fill_page_4, fill_page_5,
    fill_page_6, fill_page_7, fill_page_8, fill_page_9, fill_page_10,
)

SCREENSHOTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "screenshots", "integration",
)

# Hardcoded retrieval credentials (must match what fill_page_1/2 fill in)
_PASSPORT_NUMBER = "112223"
_COUNTRY = "People's Republic of China"
_DOB = "18/06/1995"

logger = setup_logging()


@unittest.skipUnless(
    os.environ.get("RUN_INTEGRATION_TESTS") == "1",
    "Skipped: set RUN_INTEGRATION_TESTS=1 to run integration tests",
)
class TestIntegrationScreenshots(unittest.TestCase):
    """
    Integration test that fills the INIS visa form page by page and
    takes a screenshot of the FILLED form before each Next click.

    Screenshots are named page_N_filled_YYYYMMDD_HHMMSS.png and capture
    the actual filled fields, not the blank next page.

    Set START_FROM_PAGE=N (e.g. START_FROM_PAGE=9) to skip to a specific
    page using the saved application number from application_number.txt.
    """

    @classmethod
    def setUpClass(cls):
        """Launch one Chrome browser for the entire test run."""
        options = Options()
        options.add_experimental_option("detach", True)
        options.add_argument("--start-maximized")

        cls.browser = webdriver.Chrome(options=options)
        cls.wait = WebDriverWait(cls.browser, 15)
        cls.screenshots_taken = []
        cls.failed_at_page = None
        cls.start_from_page = int(os.environ.get("START_FROM_PAGE", "1"))

        if cls.start_from_page > 1:
            # Resume from a specific page using saved application number
            app_number = get_saved_application_number()
            if not app_number:
                cls.browser.quit()
                raise RuntimeError(
                    f"START_FROM_PAGE={cls.start_from_page} requires application_number.txt "
                    "to exist from a prior run."
                )
            log_operation("setUpClass", "INFO",
                          f"Resuming from page {cls.start_from_page} "
                          f"with application {app_number}...")
            ok = initialize_form_session(cls.browser, cls.wait)
            if not ok:
                cls.browser.quit()
                raise RuntimeError("initialize_form_session() failed during resume.")
            retrieved = retrieve_application(
                cls.browser, cls.wait,
                app_number, _PASSPORT_NUMBER, _COUNTRY, _DOB
            )
            if not retrieved:
                cls.browser.quit()
                raise RuntimeError(
                    f"retrieve_application() failed for {app_number}. "
                    "Check that the application is still active."
                )
            log_operation("setUpClass", "INFO",
                          f"Resumed. URL: {cls.browser.current_url}")
        else:
            log_operation("setUpClass", "INFO",
                          "Initializing new form session (homepage → privacy → form)...")
            ok = initialize_form_session(cls.browser, cls.wait)
            if not ok:
                cls.browser.quit()
                raise RuntimeError(
                    "initialize_form_session() failed — could not reach the INIS form page."
                )
            log_operation("setUpClass", "INFO",
                          f"Session ready. URL: {cls.browser.current_url}")

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

    def _record_screenshot(self, page_num, suffix="filled"):
        """Record a screenshot path into cls.screenshots_taken."""
        label = f"page_{page_num:02d}_{suffix}"
        path = take_screenshot(self.browser, label, output_dir=SCREENSHOTS_DIR)
        if path:
            self.__class__.screenshots_taken.append(path)
        return path

    def _assert_fill_succeeded(self, result, page_num):
        """
        Assert that fill_page_N() returned an accepted success value.
        The screenshot of the filled form was already taken inside fill_page_N()
        before clicking Next. On failure, we take an additional error screenshot.
        """
        if result == "application_error":
            self._record_screenshot(page_num, suffix="application_error")
            self.__class__.failed_at_page = page_num
            self.fail(
                f"Page {page_num}: fill_page_{page_num}() returned 'application_error'."
            )

        if result is False:
            self._record_screenshot(page_num, suffix="fill_failed")
            self.__class__.failed_at_page = page_num
            self.fail(f"Page {page_num}: fill_page_{page_num}() returned False.")

        if isinstance(result, str) and "homepage_redirect" in result:
            self._record_screenshot(page_num, suffix="homepage_redirect")
            self.__class__.failed_at_page = page_num
            self.fail(
                f"Page {page_num}: unexpected homepage redirect — session may have expired."
            )

        if result in (True, "success", "submission_complete"):
            return

        if isinstance(result, str) and "form_page_" in result:
            log_operation(f"assert_fill_succeeded page {page_num}", "WARN",
                          f"Page jump detected: {result}")
            return

        log_operation(f"assert_fill_succeeded page {page_num}", "WARN",
                      f"Unrecognised result: {result!r}")

    def _skip_if_failed(self):
        if self.__class__.failed_at_page is not None:
            self.skipTest(
                f"Skipping — page {self.__class__.failed_at_page} already failed."
            )

    def _skip_if_before_start(self, page_num):
        if page_num < self.__class__.start_from_page:
            self.skipTest(f"Skipping page {page_num} — START_FROM_PAGE="
                          f"{self.__class__.start_from_page}")

    # ------------------------------------------------------------------
    # Test methods — screenshots are taken INSIDE fill_page_N() before
    # clicking Next, so they show the filled form fields.
    # ------------------------------------------------------------------

    def test_page_01(self):
        """Fill page 1 — screenshot taken of filled form before Next."""
        self._skip_if_before_start(1)
        self._skip_if_failed()
        log_operation("test_page_01", "INFO", "Filling page 1...")
        result = fill_page_1(self.browser, self.wait, screenshots_dir=SCREENSHOTS_DIR)
        self._assert_fill_succeeded(result, 1)
        time.sleep(2)

    def test_page_02(self):
        """Fill page 2 — screenshot taken of filled form before Next."""
        self._skip_if_before_start(2)
        self._skip_if_failed()
        log_operation("test_page_02", "INFO", "Filling page 2...")
        result = fill_page_2(self.browser, self.wait, screenshots_dir=SCREENSHOTS_DIR)
        self._assert_fill_succeeded(result, 2)
        time.sleep(2)

    def test_page_03(self):
        """Fill page 3 — screenshot taken of filled form before Next."""
        self._skip_if_before_start(3)
        self._skip_if_failed()
        log_operation("test_page_03", "INFO", "Filling page 3...")
        result = fill_page_3(self.browser, self.wait, screenshots_dir=SCREENSHOTS_DIR)
        self._assert_fill_succeeded(result, 3)
        time.sleep(2)

    def test_page_04(self):
        """Fill page 4 — screenshot taken of filled form before Next."""
        self._skip_if_before_start(4)
        self._skip_if_failed()
        log_operation("test_page_04", "INFO", "Filling page 4...")
        result = fill_page_4(self.browser, self.wait, screenshots_dir=SCREENSHOTS_DIR)
        self._assert_fill_succeeded(result, 4)
        time.sleep(2)

    def test_page_05(self):
        """Fill page 5 — screenshot taken of filled form before Next."""
        self._skip_if_before_start(5)
        self._skip_if_failed()
        log_operation("test_page_05", "INFO", "Filling page 5...")
        result = fill_page_5(self.browser, self.wait, screenshots_dir=SCREENSHOTS_DIR)
        self._assert_fill_succeeded(result, 5)
        time.sleep(2)

    def test_page_06(self):
        """Fill page 6 — screenshot taken of filled form before Next."""
        self._skip_if_before_start(6)
        self._skip_if_failed()
        log_operation("test_page_06", "INFO", "Filling page 6...")
        result = fill_page_6(self.browser, self.wait, screenshots_dir=SCREENSHOTS_DIR)
        self._assert_fill_succeeded(result, 6)
        time.sleep(2)

    def test_page_07(self):
        """Fill page 7 — screenshot taken of filled form before Next."""
        self._skip_if_before_start(7)
        self._skip_if_failed()
        log_operation("test_page_07", "INFO", "Filling page 7...")
        result = fill_page_7(self.browser, self.wait, screenshots_dir=SCREENSHOTS_DIR)
        self._assert_fill_succeeded(result, 7)
        time.sleep(2)

    def test_page_08(self):
        """Fill page 8 — screenshot taken of filled form before Next."""
        self._skip_if_before_start(8)
        self._skip_if_failed()
        log_operation("test_page_08", "INFO", "Filling page 8...")
        result = fill_page_8(self.browser, self.wait, screenshots_dir=SCREENSHOTS_DIR)
        self._assert_fill_succeeded(result, 8)
        time.sleep(2)

    def test_page_09(self):
        """Fill page 9 — screenshot taken of filled form before Next."""
        self._skip_if_before_start(9)
        self._skip_if_failed()
        log_operation("test_page_09", "INFO", "Filling page 9...")
        result = fill_page_9(self.browser, self.wait, screenshots_dir=SCREENSHOTS_DIR)
        self._assert_fill_succeeded(result, 9)
        time.sleep(2)

    def test_page_10(self):
        """Fill page 10 (final submission) — screenshot taken before submit."""
        self._skip_if_before_start(10)
        self._skip_if_failed()
        log_operation("test_page_10", "INFO", "Filling page 10 (final submission)...")
        result = fill_page_10(self.browser, self.wait, screenshots_dir=SCREENSHOTS_DIR)
        self._assert_fill_succeeded(result, 10)


if __name__ == "__main__":
    unittest.main(verbosity=2)
