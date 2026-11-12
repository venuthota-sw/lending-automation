"""Step definitions for the underwriting UI feature."""

from pathlib import Path

from behave import given, then, when
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

RESOURCE_DIR = Path(__file__).resolve().parents[2] / "src" / "main" / "resources"
REPORT_TIMEOUT = 300  # SLM analysis can take several minutes


def _wait(driver, css, timeout=REPORT_TIMEOUT):
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, css))
    )


@given('I open the lending UI at "{url}"')
def step_open_ui(context, url):
    context.driver.get(url)
    # Wait for the upload form to render
    _wait(context.driver, "input[type='file']", timeout=15)


@when('I upload "{filename}" as the {role}')
def step_upload(context, filename, role):
    path = RESOURCE_DIR / filename
    assert path.exists(), f"Test document not found: {path}"

    inputs = context.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
    index = 0 if "application" in role else 1
    inputs[index].send_keys(str(path))


@when('I click "{button_text}"')
def step_click(context, button_text):
    btn = WebDriverWait(context.driver, 15).until(
        EC.element_to_be_clickable(
            (By.XPATH, f"//button[contains(., '{button_text}')]")
        )
    )
    btn.click()


@then("the underwriting report should appear")
def step_report_appears(context):
    _wait(context.driver, ".report-card")
    error = context.driver.find_elements(By.CSS_SELECTOR, ".error-banner")
    assert not error, f"UI showed an error: {error[0].text}"


def _badge_texts(context, css):
    badges = context.driver.find_elements(By.CSS_SELECTOR, css)
    return [b.text.strip() for b in badges]


@then('the underwriting action should be "{action}"')
def step_action(context, action):
    badge = _wait(context.driver, ".action-badge")
    assert badge.text.strip() == action, (
        f"Expected action {action}, got {badge.text.strip()}"
    )


@then('the underwriting action should be one of "{actions}"')
def step_action_one_of(context, actions):
    badge = _wait(context.driver, ".action-badge")
    allowed = [a.strip() for a in actions.split(",")]
    assert badge.text.strip() in allowed, (
        f"Expected one of {allowed}, got {badge.text.strip()}"
    )


@then('the applicant name status should be "{status}"')
def step_name_status(context, status):
    # First .status-badge inside the report belongs to Applicant Name card
    badges = _badge_texts(context, ".field-card .status-badge")
    assert badges and badges[0] == status, (
        f"Applicant name status expected {status}, badges: {badges}"
    )


@then('the employer status should be "{status}"')
def step_employer_status(context, status):
    # Second .status-badge inside .field-card belongs to Employer card
    badges = _badge_texts(context, ".field-card .status-badge")
    assert len(badges) >= 2 and badges[1] == status, (
        f"Employer status expected {status}, badges: {badges}"
    )


@then('the income status should be "{status}"')
def step_income_status(context, status):
    # Third .status-badge inside .field-card belongs to Income Validation card
    badges = _badge_texts(context, ".field-card .status-badge")
    assert len(badges) >= 3 and badges[2] == status, (
        f"Income status expected {status}, badges: {badges}"
    )


@then('the address status should be "{status}"')
def step_address_status(context, status):
    badges = _badge_texts(context, ".field-card .status-badge")
    assert len(badges) >= 4 and badges[3] == status, (
        f"Address status expected {status}, badges: {badges}"
    )


@then('the ssn status should be "{status}"')
def step_ssn_status(context, status):
    badges = _badge_texts(context, ".field-card .status-badge")
    assert len(badges) >= 5 and badges[4] == status, (
        f"SSN status expected {status}, badges: {badges}"
    )


@then('the affordability status should be "{status}"')
def step_affordability_status(context, status):
    badges = _badge_texts(context, ".field-card .status-badge")
    assert len(badges) >= 6 and badges[5] == status, (
        f"Affordability status expected {status}, badges: {badges}"
    )
