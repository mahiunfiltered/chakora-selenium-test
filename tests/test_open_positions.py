import os
import pytest
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

from selenium.webdriver.chrome.service import Service
import shutil

# Configuration
BASE_URL = os.getenv("CHAKORA_BASE_URL", "https://chakorahub.com").rstrip("/")
LOCAL_TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "chakora-website" / "templates"
HEADLESS = os.getenv("HEADLESS", "true").lower() in ("true", "1", "yes")


def get_chromedriver_service():
    """Finds cached or local chromedriver binary to prevent network blocking."""
    # 1. Check local selenium cache directory
    cache_base = Path.home() / ".cache" / "selenium" / "chromedriver"
    if cache_base.exists():
        found = list(cache_base.rglob("chromedriver.exe")) or list(cache_base.rglob("chromedriver"))
        if found:
            return Service(executable_path=str(found[0]))

    # 2. Check system PATH
    path_driver = shutil.which("chromedriver") or shutil.which("chromedriver.exe")
    if path_driver:
        return Service(executable_path=path_driver)

    # 3. Fallback to Selenium Manager default
    return Service()


@pytest.fixture(scope="module")
def driver():
    """Provisions a clean, configured Chrome WebDriver instance."""
    options = Options()
    if HEADLESS:
        options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--ignore-certificate-errors")
    options.page_load_strategy = "eager"

    service = get_chromedriver_service()
    web_driver = webdriver.Chrome(service=service, options=options)
    web_driver.set_window_size(1920, 1080)
    web_driver.implicitly_wait(5)
    yield web_driver
    web_driver.quit()


def scroll_and_click(driver, element):
    """Safely scrolls to an element and clicks it, handling sticky headers."""
    driver.execute_script("arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});", element)
    driver.execute_script("arguments[0].click();", element)


# ============================================================================
# USER SECTION TESTS: Candidate Application Flow (/apply & /track-application)
# ============================================================================

def test_user_apply_page_rendering_and_elements(driver):
    """
    User Section Test 1:
    Verifies that the candidate resume application page loads properly
    with all layout elements, headers, input fields, dropdowns, and buttons.
    """
    wait = WebDriverWait(driver, 15)
    apply_url = f"{BASE_URL}/apply"

    try:
        driver.get(apply_url)
        wait.until(EC.presence_of_element_located((By.ID, "resumeForm")))
    except Exception:
        # Fallback to local template if network is unavailable
        local_file = (LOCAL_TEMPLATES_DIR / "resume-upload.html").as_uri()
        driver.get(local_file)
        wait.until(EC.presence_of_element_located((By.ID, "resumeForm")))

    # Verify Page Title or Heading
    assert "Resume Upload" in driver.title or "Resume" in driver.page_source

    # Verify Required Form Inputs
    name_field = wait.until(EC.visibility_of_element_located((By.ID, "name")))
    email_field = driver.find_element(By.ID, "email")
    phone_field = driver.find_element(By.ID, "phone")
    exp_field = driver.find_element(By.ID, "experience_years")
    resume_input = driver.find_element(By.ID, "resume")

    assert name_field.is_displayed(), "Candidate Name input must be visible"
    assert email_field.is_displayed(), "Candidate Email input must be visible"
    assert phone_field.is_displayed(), "Candidate Phone input must be visible"
    assert exp_field.is_displayed(), "Experience (years) input must be visible"
    assert resume_input.get_attribute("type") == "file", "Resume field must be an upload input"

    # Verify Dropdowns
    qual_dropdown = Select(driver.find_element(By.ID, "qualification"))
    source_dropdown = Select(driver.find_element(By.ID, "source"))

    # Ensure dropdown options exist
    qual_options = [opt.text.strip() for opt in qual_dropdown.options]
    source_options = [opt.text.strip() for opt in source_dropdown.options]

    assert any("B.Tech" in opt or "Select" in opt for opt in qual_options)
    assert any("LinkedIn" in opt or "Select" in opt for opt in source_options)

    # Verify Submit Button
    submit_btn = driver.find_element(By.ID, "submitBtn")
    assert submit_btn.is_displayed(), "Submit button must be displayed"
    assert "Submit" in submit_btn.text


def test_user_apply_page_validation_and_interaction(driver):
    """
    User Section Test 2:
    Tests candidate form input population and validation behavior.
    """
    wait = WebDriverWait(driver, 10)
    apply_url = f"{BASE_URL}/apply"

    try:
        driver.get(apply_url)
        wait.until(EC.presence_of_element_located((By.ID, "resumeForm")))
    except Exception:
        local_file = (LOCAL_TEMPLATES_DIR / "resume-upload.html").as_uri()
        driver.get(local_file)
        wait.until(EC.presence_of_element_located((By.ID, "resumeForm")))

    # Populate Form fields
    name_field = driver.find_element(By.ID, "name")
    email_field = driver.find_element(By.ID, "email")
    phone_field = driver.find_element(By.ID, "phone")
    exp_field = driver.find_element(By.ID, "experience_years")
    qual_select = Select(driver.find_element(By.ID, "qualification"))
    source_select = Select(driver.find_element(By.ID, "source"))

    name_field.clear()
    name_field.send_keys("Test Candidate")
    email_field.clear()
    email_field.send_keys("candidate.test@example.com")
    phone_field.clear()
    phone_field.send_keys("9876543210")
    exp_field.clear()
    exp_field.send_keys("3.5")

    # Select dropdown values
    qual_select.select_by_index(1)
    source_select.select_by_index(1)

    # Verify values are correctly retained in DOM
    assert name_field.get_attribute("value") == "Test Candidate"
    assert email_field.get_attribute("value") == "candidate.test@example.com"
    assert phone_field.get_attribute("value") == "9876543210"
    assert exp_field.get_attribute("value") == "3.5"


def test_user_track_application_page_rendering(driver):
    """
    User Section Test 3:
    Verifies that candidate application tracking page (/track-application) loads properly
    with title, input field, and track button.
    """
    wait = WebDriverWait(driver, 15)
    track_url = f"{BASE_URL}/track-application"

    try:
        driver.get(track_url)
        wait.until(EC.presence_of_element_located((By.ID, "applicationId")))
    except Exception:
        local_file = (LOCAL_TEMPLATES_DIR / "track-application.html").as_uri()
        driver.get(local_file)
        wait.until(EC.presence_of_element_located((By.ID, "applicationId")))

    # Verify Page Title
    assert "Track" in driver.title

    # Verify Application ID Input and Track Button
    app_id_input = wait.until(EC.visibility_of_element_located((By.ID, "applicationId")))
    track_btn = driver.find_element(By.XPATH, "//button[contains(normalize-space(), 'Track Status')]")

    assert app_id_input.is_displayed()
    assert track_btn.is_displayed()
    assert track_btn.is_enabled()


def test_user_track_application_validation(driver):
    """
    User Section Test 4:
    Verifies tracking form validation when submitted with empty or sample tracking ID.
    """
    wait = WebDriverWait(driver, 10)
    track_url = f"{BASE_URL}/track-application"

    try:
        driver.get(track_url)
        wait.until(EC.presence_of_element_located((By.ID, "applicationId")))
    except Exception:
        local_file = (LOCAL_TEMPLATES_DIR / "track-application.html").as_uri()
        driver.get(local_file)
        wait.until(EC.presence_of_element_located((By.ID, "applicationId")))

    app_id_input = driver.find_element(By.ID, "applicationId")
    track_btn = driver.find_element(By.XPATH, "//button[contains(normalize-space(), 'Track Status')]")

    # Test Empty submission triggers error
    app_id_input.clear()
    scroll_and_click(driver, track_btn)

    error_box = wait.until(EC.visibility_of_element_located((By.ID, "error")))
    assert error_box.is_displayed(), "Error container must be displayed on empty submission"
    assert "Please enter an Application ID" in error_box.text

    # Test Sample ID input entry
    app_id_input.send_keys("APP_2026_TEST_12345")
    assert app_id_input.get_attribute("value") == "APP_2026_TEST_12345"


# ============================================================================
# ADMIN SECTION TESTS: Open Positions Management (CRUD, Table, and Modal)
# ============================================================================

def test_admin_open_positions_management_dashboard(driver):
    """
    Admin Section Test 5:
    Verifies the Open Positions Management dashboard layout, action buttons,
    pipeline lists, and candidate counters.
    """
    wait = WebDriverWait(driver, 15)
    local_file = (LOCAL_TEMPLATES_DIR / "OpenPositionsManagement.html").as_uri()

    driver.get(local_file)

    # Verify Action Controls
    add_btn = wait.until(EC.element_to_be_clickable((By.ID, "addPositionBtn")))
    refresh_btn = driver.find_element(By.ID, "refreshBtn")

    assert add_btn.is_displayed(), "Add Position button must be visible"
    assert refresh_btn.is_displayed(), "Refresh button must be visible"

    # Verify Pipeline Counters & Column Containers
    pending_list = driver.find_element(By.ID, "pendingList")
    processed_list = driver.find_element(By.ID, "processedList")
    mail_sent_list = driver.find_element(By.ID, "mailSentList")
    resume_list = driver.find_element(By.ID, "resumeList")

    assert pending_list.is_displayed()
    assert processed_list.is_displayed()
    assert mail_sent_list.is_displayed()
    assert resume_list.is_displayed()

    pending_count = driver.find_element(By.ID, "pendingCount")
    mail_sent_count = driver.find_element(By.ID, "mailSentCount")
    resume_count = driver.find_element(By.ID, "resumeCount")

    assert pending_count.is_displayed()
    assert mail_sent_count.is_displayed()
    assert resume_count.is_displayed()


def test_admin_add_position_modal_workflow(driver):
    """
    Admin Section Test 6:
    Verifies the complete Add Position modal dialog workflow:
    - Opens modal on Add Position click
    - Populates all form fields (Title, Location, Department, Employment Type, Salary Range)
    - Verifies cancel/close action cleanly dismisses modal
    """
    wait = WebDriverWait(driver, 15)
    local_file = (LOCAL_TEMPLATES_DIR / "OpenPositionsManagement.html").as_uri()

    driver.get(local_file)

    add_btn = wait.until(EC.element_to_be_clickable((By.ID, "addPositionBtn")))
    scroll_and_click(driver, add_btn)

    modal = wait.until(EC.visibility_of_element_located((By.ID, "positionModal")))
    assert modal.is_displayed(), "Position modal must open"

    # Verify and populate modal inputs
    pos_title = driver.find_element(By.ID, "positionTitle")
    pos_location = driver.find_element(By.ID, "positionLocation")
    pos_dept = Select(driver.find_element(By.ID, "positionDepartment"))
    pos_type = Select(driver.find_element(By.ID, "positionEmploymentType"))
    pos_salary = driver.find_element(By.ID, "positionSalaryRange")
    pos_manager = driver.find_element(By.ID, "positionHiringManager")

    pos_title.send_keys("Senior Python Automation Engineer")
    pos_location.send_keys("Hyderabad")
    pos_dept.select_by_visible_text("Engineering")
    pos_type.select_by_visible_text("Full-time")
    pos_salary.send_keys("12-16 LPA")
    pos_manager.send_keys("Subhash Chandra")

    # Assert entered data
    assert pos_title.get_attribute("value") == "Senior Python Automation Engineer"
    assert pos_location.get_attribute("value") == "Hyderabad"
    assert pos_salary.get_attribute("value") == "12-16 LPA"

    # Test Cancel button dismisses modal
    cancel_btn = driver.find_element(By.ID, "cancelBtn")
    scroll_and_click(driver, cancel_btn)

    wait.until(EC.invisibility_of_element_located((By.ID, "positionModal")))
    assert not modal.is_displayed(), "Modal should be closed after clicking Cancel"

    # Re-open and verify close 'X' button also works
    scroll_and_click(driver, add_btn)
    wait.until(EC.visibility_of_element_located((By.ID, "positionModal")))
    close_x = driver.find_element(By.CSS_SELECTOR, ".close-modal")
    scroll_and_click(driver, close_x)
    wait.until(EC.invisibility_of_element_located((By.ID, "positionModal")))
    assert not modal.is_displayed(), "Modal should be closed after clicking close 'X'"


def test_admin_application_tracking_dashboard(driver):
    """
    Admin Section Test 7:
    Verifies the Admin Application Tracking Dashboard (admin-dashboard.html):
    - Metrics overview cards (Total Apps, Pending Apps, Interview, Selected)
    - Applications table structure
    - Status update and Delete confirmation modal containers
    """
    wait = WebDriverWait(driver, 15)
    local_file = (LOCAL_TEMPLATES_DIR / "admin-dashboard.html").as_uri()

    driver.get(local_file)

    # 1. Verify Page Title and Metrics Cards
    assert "Admin Dashboard" in driver.title or "Application Tracking" in driver.page_source

    total_apps = wait.until(EC.presence_of_element_located((By.ID, "totalApps")))
    pending_apps = driver.find_element(By.ID, "pendingApps")
    interview_apps = driver.find_element(By.ID, "interviewApps")
    selected_apps = driver.find_element(By.ID, "selectedApps")

    assert total_apps.is_displayed(), "Total Applications card should be visible"
    assert pending_apps.is_displayed(), "Pending Applications card should be visible"
    assert interview_apps.is_displayed(), "Interview card should be visible"
    assert selected_apps.is_displayed(), "Selected card should be visible"

    # 2. Verify Applications Table container exists in DOM
    app_table = driver.find_element(By.ID, "applicationsTable")
    assert app_table is not None, "Applications table must exist in DOM"
    assert app_table.get_attribute("id") == "applicationsTable"

    # Verify table headers via textContent (handles hidden table state prior to API data load)
    th_elements = app_table.find_elements(By.TAG_NAME, "th")
    assert len(th_elements) >= 5, "Applications table should define at least 5 column headers"
    headers = [th.get_attribute("textContent").strip() for th in th_elements]
    assert any("Application ID" in h for h in headers)
    assert any("Name" in h for h in headers)
    assert any("Status" in h for h in headers)

    # 3. Verify Modal Containers exist in DOM
    update_modal = driver.find_element(By.ID, "updateModal")
    delete_modal = driver.find_element(By.ID, "deleteConfirmModal")

    assert update_modal is not None, "Update Status modal must exist in DOM"
    assert delete_modal is not None, "Delete Confirmation modal must exist in DOM"
