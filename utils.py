#!/usr/bin/env python3

import logging
import random
import os
import json
import string
import time
import re
import datetime
from typing import Dict, Any, List, Optional, Union, Tuple
from pathlib import Path

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementNotInteractableException,
    StaleElementReferenceException,
    WebDriverException,
    SessionNotCreatedException,
    InvalidArgumentException,
    JavascriptException,
    NoSuchWindowException,
    ElementClickInterceptedException,
    ElementNotVisibleException,
    InvalidSelectorException
)

# Default paths
RANDOM_DATA_PATH = "random_data.json"

def load_random_data() -> Dict[str, Any]:
    """
    Load random data from random_data.json.
    
    Returns:
        Dictionary containing random data for name generation
    """
    try:
        with open(RANDOM_DATA_PATH, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"Error loading random data: {e}")
        # Return minimal fallback data
        return {
            "first_names": ["John", "Jane", "Alex", "Sam"],
            "last_names": ["Smith", "Doe", "Johnson", "Brown"],
            "email_domains": ["example.com", "test.com"],
            "area_codes": {
                "canadian": ["416", "647", "437"],
                "american": ["212", "312", "415"]
            }
        }

def generate_name(name_type: str = "first") -> str:
    """
    Generate a random name.
    
    Args:
        name_type: Type of name to generate ("first" or "last")
    
    Returns:
        Random name
    """
    random_data = load_random_data()
    if name_type.lower() == "first":
        return random.choice(random_data.get("first_names", ["John", "Jane"]))
    else:
        return random.choice(random_data.get("last_names", ["Smith", "Doe"]))

def generate_email() -> str:
    """
    Generate a random email address.
    
    Returns:
        Random email address
    """
    random_data = load_random_data()
    first_name = generate_name("first").lower()
    last_name = generate_name("last").lower()
    domain = random.choice(random_data.get("email_domains", ["example.com"]))
    
    # Add a random number for uniqueness
    random_num = random.randint(1, 9999)
    
    # Create email with different formats
    formats = [
        f"{first_name}.{last_name}{random_num}@{domain}",
        f"{first_name}{random_num}@{domain}",
        f"{first_name[0]}{last_name}@{domain}",
        f"{first_name}_{last_name}@{domain}"
    ]
    
    return random.choice(formats)

def get_area_code(area_code_type: Optional[Union[str, List[str]]]) -> str:
    """
    Get an area code based on the specified type.
    
    Args:
        area_code_type: Area code type (e.g., "canadian", "american") or list of types
    
    Returns:
        An area code string
    """
    random_data = load_random_data()
    area_codes = random_data.get("area_codes", {})
    
    # If area_code_type is a list, randomly choose one type
    if isinstance(area_code_type, list):
        if not area_code_type:  # Empty list
            area_code_type = "canadian"  # Default
        else:
            area_code_type = random.choice(area_code_type)
    
    # If no area code type specified or invalid type, default to canadian
    if not area_code_type or area_code_type not in area_codes:
        area_code_type = "canadian"
    
    return random.choice(area_codes.get(area_code_type, ["416"]))

def generate_phone(area_code_type: Optional[Union[str, List[str]]] = None) -> str:
    """
    Generate a random phone number in the specified format.
    
    Args:
        area_code_type: Type of area code to use or list of types
    
    Returns:
        Random phone number as a string
    """
    area_code = get_area_code(area_code_type)
    exchange = random.randint(100, 999)
    line = random.randint(1000, 9999)
    
    # Format based on area code type
    if isinstance(area_code_type, list):
        selected_type = random.choice(area_code_type) if area_code_type else "canadian"
    else:
        selected_type = area_code_type or "canadian"
    
    # Create phone number with different formats based on type
    if selected_type == "american":
        return f"({area_code}) {exchange}-{line}"
    elif selected_type == "canadian":
        return f"({area_code}) {exchange}-{line}"
    elif selected_type == "uk":
        return f"+44 {area_code} {exchange} {line}"
    elif selected_type == "australian":
        return f"+61 {area_code} {exchange} {line}"
    elif selected_type == "russian":
        return f"+7 ({area_code}) {exchange}-{line}"
    elif selected_type == "chinese":
        return f"+86 {area_code} {exchange} {line}"
    elif selected_type == "mexican":
        return f"+52 ({area_code}) {exchange}-{line}"
    else:
        return f"{area_code}-{exchange}-{line}"

def get_selector_type(field_config: Dict[str, Any]) -> str:
    """
    Get the selector type for a field (CSS or XPath).
    
    Args:
        field_config: Field configuration dictionary
    
    Returns:
        Selector type string ("css" or "xpath")
    """
    return field_config.get("type", "css").lower()

def get_element_wait_time(context: Dict[str, Any]) -> int:
    """
    Get the wait time for element presence/interaction.
    
    Args:
        context: Application context
    
    Returns:
        Wait time in seconds
    """
    config = context.get("config", {})
    timing = config.get("timing", {})
    return timing.get("element_wait_time", 10)

def get_submission_interval(context: Dict[str, Any]) -> int:
    """
    Calculate a random interval between form submissions.
    
    Args:
        context: Application context
    
    Returns:
        Interval in seconds
    """
    config = context.get("config", {})
    timing = config.get("timing", {})
    
    min_interval = timing.get("min_interval", 300)  # Default: 5 minutes
    max_interval = timing.get("max_interval", 2700)  # Default: 45 minutes
    
    # Override with environment variables if present
    try:
        env_min = os.environ.get("MIN_INTERVAL")
        if env_min is not None:
            min_interval = int(env_min)
        
        env_max = os.environ.get("MAX_INTERVAL")
        if env_max is not None:
            max_interval = int(env_max)
    except (ValueError, TypeError):
        pass
    
    # Ensure min <= max
    if min_interval > max_interval:
        min_interval, max_interval = max_interval, min_interval
    
    return random.randint(min_interval, max_interval)

def generate_random_string(length: int = 8) -> str:
    """Generate a random alphanumeric string."""
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(length))

def generate_address() -> str:
    """Generate a random street address."""
    number = str(random.randint(1, 9999))
    street = random.choice(load_random_data().get("streets", ["Main St"]))
    
    return f"{number} {street}"

def generate_city() -> str:
    """Generate a random city name."""
    return random.choice(load_random_data().get("cities", ["New York"]))

def generate_state() -> str:
    """Generate a random state/province code."""
    return random.choice(load_random_data().get("states", ["NY"]))

def generate_zip() -> str:
    """Generate a random ZIP/postal code."""
    # US format
    if random.random() < 0.5:
        return str(random.randint(10000, 99999))
    # Canadian format
    else:
        letters = string.ascii_uppercase
        return f"{random.choice(letters)}{random.randint(0, 9)}{random.choice(letters)} {random.randint(0, 9)}{random.choice(letters)}{random.randint(0, 9)}"

def setup_driver(config: Dict[str, Any], logger: logging.Logger) -> uc.Chrome:
    """
    Set up the Selenium WebDriver with undetected_chromedriver.
    
    Args:
        config: Configuration dictionary
        logger: Logger instance
        
    Returns:
        Configured Chrome WebDriver instance
    """
    logger.info("Setting up WebDriver...")
    
    try:
        # Docker container detection (more robust)
        in_docker = any([
            os.environ.get("DOCKER_CONTAINER") == "true",
            os.path.exists("/.dockerenv"),
            os.path.exists("/proc/1/cgroup") and "docker" in open("/proc/1/cgroup", "r").read()
        ])
        
        # In Docker, use standard Selenium directly to avoid version issues
        if in_docker:
            logger.info("Running in Docker container, using standard Selenium WebDriver")
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            # Try to find chromedriver in common Docker locations
            chromedriver_paths = [
                "/usr/local/bin/chromedriver",
                "/usr/bin/chromedriver",
                "/opt/chromedriver"
            ]
            
            for path in chromedriver_paths:
                if os.path.exists(path):
                    logger.info(f"Found chromedriver at {path}")
                    service = Service(executable_path=path)
                    driver = webdriver.Chrome(service=service, options=chrome_options)
                    driver.implicitly_wait(10)
                    driver.set_page_load_timeout(30)
                    return driver
            
            # If no specific path found, let Selenium find chromedriver
            driver = webdriver.Chrome(options=chrome_options)
            driver.implicitly_wait(10)
            driver.set_page_load_timeout(30)
            return driver
            
        # Setup Chrome options for undetected_chromedriver (non-Docker)
        chrome_options = uc.ChromeOptions()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Custom user agent if provided
        user_agent = config.get("user_agent")
        if user_agent:
            chrome_options.add_argument(f"--user-agent={user_agent}")
            
        # For Windows environments
        if os.name == "nt":  # Windows
            chrome_options.add_argument("--disable-features=HeadlessMode")
        
        # Initialize Chrome driver with retry logic
        max_attempts = 3
        last_error = None
        
        for attempt in range(max_attempts):
            try:
                logger.info(f"WebDriver creation attempt {attempt+1}/{max_attempts}")
                driver = uc.Chrome(options=chrome_options)
                
                # Configure timeouts
                driver.implicitly_wait(10)
                driver.set_page_load_timeout(30)
                driver.set_script_timeout(30)
                
                # Test the driver with a simple command
                driver.execute_script("return navigator.userAgent")
                logger.info("WebDriver created successfully")
                
                return driver
            except Exception as e:
                last_error = e
                logger.warning(f"WebDriver creation failed, attempt {attempt+1}/{max_attempts}: {e}")
                if attempt < max_attempts - 1:
                    time.sleep(2)  # Short delay before retry
        
        # If all attempts failed, raise the last error
        raise last_error
                
    except Exception as e:
        logger.error(f"Failed to set up WebDriver: {str(e)}")
        raise

def find_form_field(driver: uc.Chrome, field_id: Optional[str] = None, 
                   field_name: Optional[str] = None, selector: Optional[str] = None,
                   timeout: int = 10, logger: Optional[logging.Logger] = None) -> Optional[Any]:
    """
    Find a form field using multiple strategies.
    
    Args:
        driver: Selenium WebDriver instance
        field_id: ID of the field
        field_name: Name attribute of the field
        selector: Custom CSS selector
        timeout: Maximum time to wait for the element
        logger: Optional logger to use for logging
        
    Returns:
        WebElement if found, None otherwise
    """
    # Use a default logger if none provided
    if logger is None:
        logger = logging.getLogger(__name__)
    
    # Log which field we're looking for
    if logger.isEnabledFor(logging.DEBUG):
        search_params = []
        if selector:
            search_params.append(f"selector='{selector}'")
        if field_id:
            search_params.append(f"id='{field_id}'")
        if field_name:
            search_params.append(f"name='{field_name}'")
        logger.debug(f"Searching for form field with {', '.join(search_params)}")
    
    # Step 1: Try finding by selector first if provided
    if selector:
        try:
            logger.debug(f"Trying to find element by CSS selector: {selector}")
            return WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
        except (TimeoutException, NoSuchElementException):
            logger.debug("Element not found by CSS selector")
    
    # Step 2: Try finding by name (prioritized over ID since it's more reliable in this app)
    if field_name:
        try:
            logger.debug(f"Trying to find element by name: {field_name}")
            return WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.NAME, field_name)))
        except (TimeoutException, NoSuchElementException):
            logger.debug("Element not found by name")
    
    # Step 3: Try finding by ID with a very short timeout to avoid long waits for non-existent IDs
    if field_id:
        try:
            logger.debug(f"Trying to find element by ID: {field_id}")
            # Using a shorter timeout (1 second) for ID lookups to avoid long waits
            return WebDriverWait(driver, 1).until(EC.element_to_be_clickable((By.ID, field_id)))
        except (TimeoutException, NoSuchElementException):
            logger.debug("Element not found by ID")
    
    # Step 4: Try more relaxed XPath lookups
    selectors_to_try = []
    
    # First prioritize name-based XPath queries
    if field_name:
        selectors_to_try.append(f"//input[contains(@name, '{field_name}')]")
        selectors_to_try.append(f"//select[contains(@name, '{field_name}')]")
        selectors_to_try.append(f"//textarea[contains(@name, '{field_name}')]")
    
    # Then try ID-based XPath queries
    if field_id:
        selectors_to_try.append(f"//input[contains(@id, '{field_id}')]")
        selectors_to_try.append(f"//select[contains(@id, '{field_id}')]")
        selectors_to_try.append(f"//textarea[contains(@id, '{field_id}')]")
    
    for xpath in selectors_to_try:
        try:
            logger.debug(f"Trying to find element by XPath: {xpath}")
            element = driver.find_element(By.XPATH, xpath)
            if element:
                return element
        except NoSuchElementException:
            pass
    
    logger.debug("Failed to find element with any strategy")
    return None

def find_submit_button(driver: uc.Chrome, config: Dict[str, Any]) -> Optional[Any]:
    """
    Find the submit button in a form.
    
    Args:
        driver: Selenium WebDriver instance
        config: Configuration dictionary
        
    Returns:
        WebElement if found, None otherwise
    """
    # Check if there's a specific submit button configuration
    submit_config = config.get("submit_button", {})
    
    if submit_config.get("selector"):
        try:
            return driver.find_element(By.CSS_SELECTOR, submit_config["selector"])
        except NoSuchElementException:
            pass
    
    if submit_config.get("id"):
        try:
            return driver.find_element(By.ID, submit_config["id"])
        except NoSuchElementException:
            pass
    
    if submit_config.get("name"):
        try:
            return driver.find_element(By.NAME, submit_config["name"])
        except NoSuchElementException:
            pass
    
    # Try common submit button selectors
    selectors = [
        "//button[@type='submit']",
        "//input[@type='submit']",
        "//button[contains(@class, 'submit')]",
        "//button[contains(text(), 'Submit')]",
        "//button[contains(text(), 'Send')]",
        "//input[contains(@class, 'submit')]"
    ]
    
    for selector in selectors:
        try:
            return driver.find_element(By.XPATH, selector)
        except NoSuchElementException:
            continue
    
    return None

def fill_field_with_random_data(driver: uc.Chrome, field_name: str, 
                               field_info: Dict[str, Any], logger: logging.Logger) -> bool:
    """
    Fill a form field with random data based on field type.
    
    Args:
        driver: Selenium WebDriver instance
        field_name: Name of the field (for logging)
        field_info: Field configuration dictionary
        logger: Logger instance
        
    Returns:
        True if successful, False otherwise
    """
    # Skip if the field info doesn't contain at least one selector method
    has_selector_method = any([
        field_info.get("id"),
        field_info.get("name"),
        field_info.get("selector")
    ])
    
    if not has_selector_method:
        logger.warning(f"Field '{field_name}' has no selector information (id, name, or CSS selector)")
        return False
    
    field_id = field_info.get("id")
    field_type = field_info.get("type", "text")
    field_name_attr = field_info.get("name")
    field_selector = field_info.get("selector")
    
    try:
        field_element = find_form_field(driver, field_id, field_name_attr, field_selector, logger=logger)
        
        if not field_element:
            logger.warning(f"Could not find field '{field_name}'")
            return False
        
        # Skip hidden fields
        if field_type == "hidden":
            return True
        
        # For select fields
        if field_type == "select" or field_element.tag_name.lower() == "select":
            select = Select(field_element)
            options = select.options
            if options:
                # Skip the first option if it looks like a placeholder
                start_index = 1 if len(options) > 1 else 0
                select.select_by_index(random.randint(start_index, len(options) - 1))
            else:
                logger.warning(f"No options found for select field '{field_name}'")
                return False
            
        # For checkbox or radio buttons
        elif field_type in ["checkbox", "radio"]:
            if not field_element.is_selected() and random.random() < 0.7:  # 70% chance to select
                field_element.click()
                
        # For text input fields
        else:
            # Clear existing value
            field_element.clear()
            
            # Generate value based on field name hints
            field_name_lower = field_name.lower()
            value = ""
            
            if "first" in field_name_lower and "name" in field_name_lower:
                value = generate_name("first")
            elif "last" in field_name_lower and "name" in field_name_lower:
                value = generate_name("last")
            elif "name" in field_name_lower:
                value = f"{generate_name('first')} {generate_name('last')}"
            elif "email" in field_name_lower:
                value = generate_email()
            elif "phone" in field_name_lower:
                # Get area code type from field config, defaulting to "canadian"
                area_code_type = field_info.get('area_code_type', 'canadian')
                value = generate_phone(area_code_type)
            elif "address" in field_name_lower:
                value = generate_address()
            elif "city" in field_name_lower:
                value = generate_city()
            elif "state" in field_name_lower or "province" in field_name_lower:
                value = generate_state()
            elif "zip" in field_name_lower or "postal" in field_name_lower:
                value = generate_zip()
            else:
                # Generic text input
                value = generate_random_string(12)
            
            # Send the value to the field
            field_element.send_keys(value)
            logger.debug(f"Filled field '{field_name}' with value: {value}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error filling field '{field_name}': {str(e)}")
        return False

def sleep_with_jitter(min_seconds: int, max_seconds: int) -> None:
    """
    Sleep for a random amount of time within a range.
    
    Args:
        min_seconds: Minimum sleep time in seconds
        max_seconds: Maximum sleep time in seconds
    """
    sleep_time = random.uniform(min_seconds, max_seconds)
    time.sleep(sleep_time)

def create_report_directory(report_dir: Optional[str] = None) -> str:
    """
    Create a directory for storing security reports.
    
    Args:
        report_dir: Optional directory path, defaults to 'security_reports'
        
    Returns:
        Path to the created directory
    """
    if not report_dir:
        report_dir = "security_reports"
    
    # Create the base directory if it doesn't exist
    Path(report_dir).mkdir(exist_ok=True)
    
    # Create a timestamped subdirectory for this report
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    report_subdir = os.path.join(report_dir, f"report_{timestamp}")
    Path(report_subdir).mkdir(exist_ok=True)
    
    return report_subdir

def generate_json_report(results: Dict[str, Any], output_path: str) -> str:
    """
    Generate a JSON report from test results.
    
    Args:
        results: Dictionary containing test results
        output_path: Directory to save the report
        
    Returns:
        Path to the generated report file
    """
    # Add report metadata
    report_data = {
        "report_generated": datetime.datetime.now().isoformat(),
        "results": results
    }
    
    # Determine filename
    test_type = results.get("test_type", "security")
    filename = f"{test_type}_report.json"
    filepath = os.path.join(output_path, filename)
    
    # Write report to file
    with open(filepath, 'w') as f:
        json.dump(report_data, f, indent=2)
    
    return filepath

def generate_html_report(results: Dict[str, Any], output_path: str) -> str:
    """
    Generate an HTML report from test results.
    
    Args:
        results: Dictionary containing test results
        output_path: Directory to save the report
        
    Returns:
        Path to the generated report file
    """
    # Determine filename
    test_type = results.get("test_type", "security")
    filename = f"{test_type}_report.html"
    filepath = os.path.join(output_path, filename)
    
    # Get current timestamp
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Start building HTML content
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Security Test Report - {test_type.upper()}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                color: #333;
                line-height: 1.6;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
            }}
            h1, h2, h3 {{
                color: #2c3e50;
            }}
            .summary {{
                background-color: #f8f9fa;
                border-left: 4px solid #5bc0de;
                padding: 15px;
                margin-bottom: 20px;
            }}
            .vulnerability {{
                background-color: #fff;
                border: 1px solid #ddd;
                border-left: 4px solid #d9534f;
                padding: 15px;
                margin-bottom: 15px;
            }}
            .vulnerability.medium {{
                border-left: 4px solid #f0ad4e;
            }}
            .vulnerability.low {{
                border-left: 4px solid #5bc0de;
            }}
            .table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
            }}
            .table th, .table td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}
            .table th {{
                background-color: #f2f2f2;
            }}
            .badge {{
                display: inline-block;
                padding: 3px 7px;
                font-size: 12px;
                font-weight: bold;
                line-height: 1;
                color: #fff;
                text-align: center;
                white-space: nowrap;
                vertical-align: middle;
                border-radius: 10px;
            }}
            .badge-danger {{ background-color: #d9534f; }}
            .badge-warning {{ background-color: #f0ad4e; }}
            .badge-info {{ background-color: #5bc0de; }}
            .badge-success {{ background-color: #5cb85c; }}
            .footer {{
                margin-top: 30px;
                font-size: 12px;
                color: #777;
                text-align: center;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Security Test Report</h1>
            <p>Generated on: {timestamp}</p>
    """
    
    # Add summary section
    html_content += f"""
            <div class="summary">
                <h2>Test Summary</h2>
                <p><strong>Target URL:</strong> {results.get('target_url', 'N/A')}</p>
                <p><strong>Test Type:</strong> {test_type.upper()}</p>
                <p><strong>Duration:</strong> {results.get('duration', 0):.2f} seconds</p>
    """
    
    # Add security score if available (for headers test)
    if "security_score" in results:
        score_color = ""
        if results["security_score"] >= 90:
            score_color = "badge-success"
        elif results["security_score"] >= 75:
            score_color = "badge-info"
        elif results["security_score"] >= 50:
            score_color = "badge-warning"
        else:
            score_color = "badge-danger"
            
        html_content += f"""
                <p><strong>Security Score:</strong> <span class="badge {score_color}">{results.get('security_score', 0)}/100</span></p>
                <p><strong>Rating:</strong> {results.get('security_rating', 'N/A').upper()}</p>
        """
    
    # Add vulnerability summary
    vuln_count = len(results.get('vulnerabilities', []))
    html_content += f"""
                <p><strong>Vulnerabilities Found:</strong> {vuln_count}</p>
            </div>
    """
    
    # Add vulnerabilities section if any found
    if vuln_count > 0:
        html_content += """
            <h2>Detected Vulnerabilities</h2>
        """
        
        # Group vulnerabilities by severity
        high_vulns = [v for v in results.get('vulnerabilities', []) if v.get('severity') == 'high']
        medium_vulns = [v for v in results.get('vulnerabilities', []) if v.get('severity') == 'medium']
        low_vulns = [v for v in results.get('vulnerabilities', []) if v.get('severity') == 'low']
        
        # Add high vulnerabilities
        if high_vulns:
            html_content += """
                <h3>High Severity Issues</h3>
            """
            
            for i, vuln in enumerate(high_vulns):
                html_content += f"""
                <div class="vulnerability">
                    <h4>#{i+1}. {vuln.get('type', 'Issue').replace('_', ' ').title()}</h4>
                    <p><strong>Severity:</strong> <span class="badge badge-danger">High</span></p>
                """
                
                if "field" in vuln:
                    html_content += f"""<p><strong>Field:</strong> {vuln.get('field', 'N/A')}</p>"""
                    
                if "header" in vuln:
                    html_content += f"""<p><strong>Header:</strong> {vuln.get('header', 'N/A')}</p>"""
                    
                html_content += f"""
                    <p><strong>Details:</strong> {vuln.get('details', 'No details provided')}</p>
                """
                
                if "payload" in vuln:
                    html_content += f"""<p><strong>Payload:</strong> <code>{vuln.get('payload', '')}</code></p>"""
                    
                if "recommendation" in vuln:
                    html_content += f"""<p><strong>Recommendation:</strong> {vuln.get('recommendation', 'No recommendation provided')}</p>"""
                    
                html_content += """
                </div>
                """
        
        # Add medium vulnerabilities
        if medium_vulns:
            html_content += """
                <h3>Medium Severity Issues</h3>
            """
            
            for i, vuln in enumerate(medium_vulns):
                html_content += f"""
                <div class="vulnerability medium">
                    <h4>#{i+1}. {vuln.get('type', 'Issue').replace('_', ' ').title()}</h4>
                    <p><strong>Severity:</strong> <span class="badge badge-warning">Medium</span></p>
                """
                
                if "field" in vuln:
                    html_content += f"""<p><strong>Field:</strong> {vuln.get('field', 'N/A')}</p>"""
                    
                if "header" in vuln:
                    html_content += f"""<p><strong>Header:</strong> {vuln.get('header', 'N/A')}</p>"""
                    
                html_content += f"""
                    <p><strong>Details:</strong> {vuln.get('details', 'No details provided')}</p>
                """
                
                if "payload" in vuln:
                    html_content += f"""<p><strong>Payload:</strong> <code>{vuln.get('payload', '')}</code></p>"""
                    
                if "recommendation" in vuln:
                    html_content += f"""<p><strong>Recommendation:</strong> {vuln.get('recommendation', 'No recommendation provided')}</p>"""
                    
                html_content += """
                </div>
                """
        
        # Add low vulnerabilities
        if low_vulns:
            html_content += """
                <h3>Low Severity Issues</h3>
            """
            
            for i, vuln in enumerate(low_vulns):
                html_content += f"""
                <div class="vulnerability low">
                    <h4>#{i+1}. {vuln.get('type', 'Issue').replace('_', ' ').title()}</h4>
                    <p><strong>Severity:</strong> <span class="badge badge-info">Low</span></p>
                """
                
                if "field" in vuln:
                    html_content += f"""<p><strong>Field:</strong> {vuln.get('field', 'N/A')}</p>"""
                    
                if "header" in vuln:
                    html_content += f"""<p><strong>Header:</strong> {vuln.get('header', 'N/A')}</p>"""
                    
                html_content += f"""
                    <p><strong>Details:</strong> {vuln.get('details', 'No details provided')}</p>
                """
                
                if "payload" in vuln:
                    html_content += f"""<p><strong>Payload:</strong> <code>{vuln.get('payload', '')}</code></p>"""
                    
                if "recommendation" in vuln:
                    html_content += f"""<p><strong>Recommendation:</strong> {vuln.get('recommendation', 'No recommendation provided')}</p>"""
                    
                html_content += """
                </div>
                """
    else:
        html_content += """
            <div class="summary">
                <h2>No Vulnerabilities Detected</h2>
                <p>No security issues were found during this test. This does not guarantee that the application is secure,
                but no common vulnerabilities were detected with the current tests.</p>
            </div>
        """
    
    # Add test-specific content
    if test_type == "security_headers":
        html_content += """
            <h2>Security Headers Analysis</h2>
            <table class="table">
                <thead>
                    <tr>
                        <th>Header</th>
                        <th>Status</th>
                        <th>Value</th>
                        <th>Recommendation</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for header in results.get('header_results', []):
            status_class = ""
            if header.get('status') == 'missing':
                status_class = "badge-danger"
                status_text = "Missing"
            elif header.get('status') == 'weak' or header.get('status') == 'invalid':
                status_class = "badge-warning"
                status_text = "Weak"
            else:
                status_class = "badge-success"
                status_text = "Present"
                
            html_content += f"""
                <tr>
                    <td>{header.get('name', 'Unknown')}</td>
                    <td><span class="badge {status_class}">{status_text}</span></td>
                    <td><code>{header.get('value', 'N/A')}</code></td>
                    <td>{header.get('recommendation', 'No recommendation')}</td>
                </tr>
            """
            
        html_content += """
                </tbody>
            </table>
        """
        
        # Add HTTPS redirect info
        https_redirect = results.get('https_redirect', {})
        redirect_status = https_redirect.get('status', 'not_tested')
        
        if redirect_status != 'skipped':
            status_class = ""
            if redirect_status == 'passed':
                status_class = "badge-success"
                status_text = "Passed"
            elif redirect_status == 'failed':
                status_class = "badge-danger"
                status_text = "Failed"
            else:
                status_class = "badge-warning"
                status_text = "Error"
                
            html_content += f"""
                <h3>HTTP to HTTPS Redirection</h3>
                <p><strong>Status:</strong> <span class="badge {status_class}">{status_text}</span></p>
                <p><strong>Details:</strong> {https_redirect.get('details', 'No details provided')}</p>
            """
    
    # Close the HTML document
    html_content += """
            <div class="footer">
                <p>This report was automatically generated. The results should be reviewed by a security professional.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Write the HTML content to the file
    with open(filepath, 'w') as f:
        f.write(html_content)
    
    return filepath

def generate_security_report(results: Dict[str, Any], report_format: str = "html", 
                            report_dir: Optional[str] = None) -> Dict[str, str]:
    """
    Generate a security report from test results.
    
    Args:
        results: Dictionary containing test results
        report_format: Format of the report ("html", "json", or "both")
        report_dir: Directory to save the report
        
    Returns:
        Dictionary with paths to generated reports
    """
    output_paths = {}
    
    # Create report directory
    output_dir = create_report_directory(report_dir)
    
    # Generate reports based on format
    if report_format in ["json", "both"]:
        json_path = generate_json_report(results, output_dir)
        output_paths["json"] = json_path
    
    if report_format in ["html", "both"]:
        html_path = generate_html_report(results, output_dir)
        output_paths["html"] = html_path
    
    return output_paths 