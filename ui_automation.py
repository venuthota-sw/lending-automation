"""
Selenium UI automation for the Lending Automation POC.

Opens the Angular UI, uploads the loan application + verification document
from src/main/resources, clicks "Run Underwriting", waits for the report,
and prints the extracted report text.

Prereqs:
    pip install selenium
    - Spring Boot backend on :8081, OCR server on :8000, Ollama on :11434
    - UI dev server on :4200 (ng serve)
"""

import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
UI_URL = "http://localhost:4200"
RESOURCE_DIR = Path(__file__).parent / "src" / "main" / "resources"

APPLICATION_FORM = RESOURCE_DIR / "loan_application3.png"
VERIFICATION_DOC = RESOURCE_DIR / "paystub_good3.png"

REPORT_TIMEOUT_SECONDS = 300  # SLM analysis can take a while


def main() -> None:
    for path in (APPLICATION_FORM, VERIFICATION_DOC):
        if not path.exists():
            raise FileNotFoundError(f"Missing input file: {path}")

    options = Options()
    options.add_argument("--start-maximized")
    # options.add_argument("--headless=new")  # uncomment for headless runs

    driver = webdriver.Chrome(options=options)
    try:
        driver.get(UI_URL)

        # Two file inputs in DOM order: application form, then verification doc
        file_inputs = WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "input[type='file']"))
        )
        assert len(file_inputs) >= 2, f"Expected 2 file inputs, found {len(file_inputs)}"

        file_inputs[0].send_keys(str(APPLICATION_FORM))
        file_inputs[1].send_keys(str(VERIFICATION_DOC))
        print(f"Uploaded: {APPLICATION_FORM.name}, {VERIFICATION_DOC.name}")

        submit_btn = driver.find_element(By.CSS_SELECTOR, "button.submit-btn")
        submit_btn.click()
        print("Clicked 'Run Underwriting' — waiting for report...")

        # Wait for either the report card or the error banner
        wait = WebDriverWait(driver, REPORT_TIMEOUT_SECONDS)
        wait.until(
            EC.any_of(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".report-card")),
                EC.presence_of_element_located((By.CSS_SELECTOR, ".error-banner")),
            )
        )

        error_banner = driver.find_elements(By.CSS_SELECTOR, ".error-banner")
        if error_banner:
            print(f"ERROR: {error_banner[0].text}")
            return

        report_card = driver.find_element(By.CSS_SELECTOR, ".report-card")
        report_text = report_card.text
        print("\n" + "=" * 60)
        print("UNDERWRITING REPORT")
        print("=" * 60)
        print(report_text)
        print("=" * 60)

        screenshot_path = Path(__file__).parent / "underwriting_report.png"
        driver.save_screenshot(str(screenshot_path))
        print(f"\nScreenshot saved to: {screenshot_path}")

    finally:
        # Keep browser open briefly so the report stays visible, then close
        time.sleep(5)
        driver.quit()


if __name__ == "__main__":
    main()
