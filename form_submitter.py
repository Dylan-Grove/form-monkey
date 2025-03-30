from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from faker import Faker
import time
import random
import logging
import os
import json
from datetime import datetime, timedelta
import undetected_chromedriver as uc
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description='Form Monkey - A chaos engineering tool for automated form submissions')
    parser.add_argument('--help', action='help', help='Show this help message and exit')
    parser.add_argument('--config', '-c', help='Form configuration to use (default: from FORM_CONFIG env var or "default")')
    parser.add_argument('--verbosity', '-v', choices=['minimal', 'balanced', 'verbose'], 
                       help='Logging verbosity level (default: from VERBOSITY env var or "balanced")')
    parser.add_argument('--min-interval', type=int, help='Minimum time between submissions in seconds (overrides config)')
    parser.add_argument('--max-interval', type=int, help='Maximum time between submissions in seconds (overrides config)')
    return parser.parse_args()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Parse command line arguments
args = parse_args()

# Load form configuration
with open('form_config.json', 'r') as f:
    CONFIG = json.load(f)

# Load random data configuration
with open('random_data.json', 'r') as f:
    RANDOM_DATA = json.load(f)

# Get the form configuration to use
FORM_CONFIG = args.config or os.getenv('FORM_CONFIG', 'default')
FORM_CONFIG_DATA = CONFIG.get(FORM_CONFIG, CONFIG['default'])

# Get timing configuration from config file
timing_config = FORM_CONFIG_DATA.get('timing', {})
MIN_INTERVAL = args.min_interval or int(os.getenv('MIN_INTERVAL', timing_config.get('min_interval', 180)))  # Default 3 minutes
MAX_INTERVAL = args.max_interval or int(os.getenv('MAX_INTERVAL', timing_config.get('max_interval', 1800)))  # Default 30 minutes

# Get URL from environment or config
URL = os.getenv('TARGET_URL', FORM_CONFIG_DATA['url'])

# Get verbosity from environment or config
VERBOSITY = args.verbosity or os.getenv('VERBOSITY', FORM_CONFIG_DATA.get('verbosity', 'balanced'))
if VERBOSITY == 'minimal':
    logging.getLogger().setLevel(logging.WARNING)
elif VERBOSITY == 'verbose':
    logging.getLogger().setLevel(logging.DEBUG)

def generate_phone():
    area_code_type = FORM_CONFIG_DATA.get('area_code_type', 'canadian')
    area_codes = RANDOM_DATA['area_codes'][area_code_type]
    area_code = random.choice(area_codes)
    prefix = random.randint(200, 999)
    line_number = random.randint(1000, 9999)
    return f"{area_code}{prefix}{line_number}"

def generate_random_username():
    # Randomly choose a pattern for username generation
    pattern = random.choice([
        # Pattern 1: random word + random numbers + random word
        lambda: f"{random.choice(RANDOM_DATA['common_words'])}{random.randint(1, 999)}{random.choice(RANDOM_DATA['common_words'])}",
        
        # Pattern 2: random word + random special char + random word + random numbers
        lambda: f"{random.choice(RANDOM_DATA['common_words'])}{random.choice(RANDOM_DATA['random_values']['special_chars'])}{random.choice(RANDOM_DATA['common_words'])}{random.randint(1, 999)}",
        
        # Pattern 3: random word + year + random word
        lambda: f"{random.choice(RANDOM_DATA['common_words'])}{random.choice(RANDOM_DATA['random_values']['years'])}{random.choice(RANDOM_DATA['common_words'])}",
        
        # Pattern 4: random word + random word + random special char + random numbers
        lambda: f"{random.choice(RANDOM_DATA['common_words'])}{random.choice(RANDOM_DATA['common_words'])}{random.choice(RANDOM_DATA['random_values']['special_chars'])}{random.randint(1, 999)}",
        
        # Pattern 5: random word + date + random word
        lambda: f"{random.choice(RANDOM_DATA['common_words'])}{random.choice(RANDOM_DATA['random_values']['years'])}{random.choice(RANDOM_DATA['random_values']['months'])}{random.choice(RANDOM_DATA['random_values']['days'])}{random.choice(RANDOM_DATA['common_words'])}",
        
        # Pattern 6: random word + random chars + random numbers
        lambda: f"{random.choice(RANDOM_DATA['common_words'])}{''.join(random.choices(RANDOM_DATA['random_values']['chars'], k=random.randint(2, 4)))}{random.randint(1, 999)}",
        
        # Pattern 7: random word + random special char + random chars + random numbers
        lambda: f"{random.choice(RANDOM_DATA['common_words'])}{random.choice(RANDOM_DATA['random_values']['special_chars'])}{''.join(random.choices(RANDOM_DATA['random_values']['chars'], k=random.randint(2, 4)))}{random.randint(1, 999)}",
        
        # Pattern 8: random word + random word + random special char + random chars
        lambda: f"{random.choice(RANDOM_DATA['common_words'])}{random.choice(RANDOM_DATA['common_words'])}{random.choice(RANDOM_DATA['random_values']['special_chars'])}{''.join(random.choices(RANDOM_DATA['random_values']['chars'], k=random.randint(2, 4)))}",
        
        # Pattern 9: random word + random numbers + random special char + random word
        lambda: f"{random.choice(RANDOM_DATA['common_words'])}{random.randint(1, 999)}{random.choice(RANDOM_DATA['random_values']['special_chars'])}{random.choice(RANDOM_DATA['common_words'])}",
        
        # Pattern 10: random word + random chars + random special char + random numbers
        lambda: f"{random.choice(RANDOM_DATA['common_words'])}{''.join(random.choices(RANDOM_DATA['random_values']['chars'], k=random.randint(2, 4)))}{random.choice(RANDOM_DATA['random_values']['special_chars'])}{random.randint(1, 999)}",
        
        # Pattern 11: random word + random numbers + random word + random special char + random chars
        lambda: f"{random.choice(RANDOM_DATA['common_words'])}{random.randint(1, 999)}{random.choice(RANDOM_DATA['common_words'])}{random.choice(RANDOM_DATA['random_values']['special_chars'])}{''.join(random.choices(RANDOM_DATA['random_values']['chars'], k=random.randint(2, 4)))}",
        
        # Pattern 12: random word + random special char + random word + random special char + random numbers
        lambda: f"{random.choice(RANDOM_DATA['common_words'])}{random.choice(RANDOM_DATA['random_values']['special_chars'])}{random.choice(RANDOM_DATA['common_words'])}{random.choice(RANDOM_DATA['random_values']['special_chars'])}{random.randint(1, 999)}",
        
        # Pattern 13: very short username (3-6 chars)
        lambda: f"{random.randint(1, 999)}{random.choice(RANDOM_DATA['random_values']['special_chars'])}{random.choice(RANDOM_DATA['common_words'])[:3]}",
        
        # Pattern 14: very long username with multiple words
        lambda: f"{random.choice(RANDOM_DATA['common_words'])}{random.choice(RANDOM_DATA['random_values']['special_chars'])}{random.choice(RANDOM_DATA['common_words'])}{random.choice(RANDOM_DATA['random_values']['special_chars'])}{random.choice(RANDOM_DATA['common_words'])}{random.choice(RANDOM_DATA['random_values']['special_chars'])}{random.randint(1, 999)}",
        
        # Pattern 15: username with multiple special chars
        lambda: f"{random.choice(RANDOM_DATA['common_words'])}{random.choice(RANDOM_DATA['random_values']['special_chars'])}{random.choice(RANDOM_DATA['common_words'])}{random.choice(RANDOM_DATA['random_values']['special_chars'])}{random.choice(RANDOM_DATA['common_words'])}{random.randint(1, 999)}"
    ])
    
    return pattern()

def generate_email(first_name, last_name):
    # Randomly choose between name-based and completely random email
    if random.random() < 0.4:  # 40% chance of using name-based email
        # Create variations of the email username
        username_variations = [
            # Short variations
            f"{first_name.lower()[0]}{random.randint(1, 999)}",
            f"{first_name.lower()[:2]}{random.choice(RANDOM_DATA['random_values']['special_chars'])}{random.randint(1, 99)}",
            f"{last_name.lower()[:3]}{random.randint(1, 999)}",
            
            # Medium variations
            f"{first_name.lower()}{random.randint(1, 999)}{random.choice(RANDOM_DATA['random_values']['special_chars'])}{random.choice(RANDOM_DATA['common_words'])}",
            f"{first_name.lower()[0]}{last_name.lower()}{random.randint(1, 999)}{random.choice(RANDOM_DATA['random_values']['special_chars'])}{''.join(random.choices(RANDOM_DATA['random_values']['chars'], k=random.randint(2, 4)))}",
            f"{first_name.lower()}{random.choice(RANDOM_DATA['random_values']['special_chars'])}{last_name.lower()}{random.randint(1, 99)}{random.choice(RANDOM_DATA['random_values']['special_chars'])}{random.choice(RANDOM_DATA['common_words'])}",
            
            # Long variations
            f"{first_name.lower()}{random.choice(RANDOM_DATA['random_values']['special_chars'])}{random.choice(RANDOM_DATA['random_values']['years'])}{random.choice(RANDOM_DATA['random_values']['special_chars'])}{''.join(random.choices(RANDOM_DATA['random_values']['chars'], k=random.randint(2, 4)))}",
            f"{first_name.lower()}{random.choice(RANDOM_DATA['random_values']['special_chars'])}{random.choice(RANDOM_DATA['common_words'])}{random.randint(1, 999)}",
            f"{first_name.lower()}{random.choice(RANDOM_DATA['random_values']['special_chars'])}{last_name.lower()}{random.choice(RANDOM_DATA['random_values']['special_chars'])}{random.choice(RANDOM_DATA['common_words'])}{random.randint(1, 999)}",
            
            # Very long variations
            f"{first_name.lower()}{random.choice(RANDOM_DATA['random_values']['special_chars'])}{last_name.lower()}{random.choice(RANDOM_DATA['random_values']['special_chars'])}{random.choice(RANDOM_DATA['common_words'])}{random.choice(RANDOM_DATA['random_values']['special_chars'])}{random.choice(RANDOM_DATA['common_words'])}{random.randint(1, 999)}",
            f"{first_name.lower()}{random.choice(RANDOM_DATA['random_values']['special_chars'])}{random.choice(RANDOM_DATA['common_words'])}{random.choice(RANDOM_DATA['random_values']['special_chars'])}{random.choice(RANDOM_DATA['common_words'])}{random.choice(RANDOM_DATA['random_values']['special_chars'])}{random.randint(1, 999)}",
            
            # Date-based variations
            f"{first_name.lower()}{random.choice(RANDOM_DATA['random_values']['special_chars'])}{random.choice(RANDOM_DATA['random_values']['years'])}{random.choice(RANDOM_DATA['random_values']['months'])}{random.choice(RANDOM_DATA['random_values']['days'])}{random.choice(RANDOM_DATA['random_values']['special_chars'])}{random.choice(RANDOM_DATA['common_words'])}",
            f"{last_name.lower()}{random.choice(RANDOM_DATA['random_values']['special_chars'])}{random.choice(RANDOM_DATA['random_values']['years'])}{random.choice(RANDOM_DATA['random_values']['months'])}{random.choice(RANDOM_DATA['random_values']['days'])}{random.choice(RANDOM_DATA['random_values']['special_chars'])}{random.choice(RANDOM_DATA['common_words'])}"
        ]
        username = random.choice(username_variations)
    else:
        # 60% chance of using completely random username
        username = generate_random_username()
    
    domain = random.choice(RANDOM_DATA['email_domains'])
    return f"{username}@{domain}"

def setup_driver():
    logging.info("Setting up undetected Chrome WebDriver...")
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--start-maximized')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-popup-blocking')
    options.add_argument('--disable-notifications')
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    
    driver = uc.Chrome(options=options)
    driver.set_page_load_timeout(30)  # Set page load timeout to 30 seconds
    logging.info("Chrome WebDriver setup complete")
    return driver

def submit_form():
    fake = Faker()
    driver = setup_driver()
    
    try:
        logging.info(f"Navigating to {URL}")
        driver.get(URL)
        
        # Add a longer delay to let the page load completely
        time.sleep(30)  # Increased initial wait time
        
        # Log the current URL and page title
        logging.info(f"Current URL: {driver.current_url}")
        logging.info(f"Page title: {driver.title}")
        
        # Wait for page to be fully loaded
        wait = WebDriverWait(driver, 60)  # Increased timeout
        wait.until(lambda driver: driver.execute_script('return document.readyState') == 'complete')
        
        # Wait for any dynamic content to load
        time.sleep(10)
        
        # Check for dynamic form loading
        logging.info("Checking for dynamic form loading...")
        try:
            # Wait for any form elements to appear
            wait.until(lambda driver: len(driver.find_elements(By.TAG_NAME, "form")) > 0 or
                      len(driver.find_elements(By.TAG_NAME, "input")) > 0)
        except:
            logging.warning("No form elements found after waiting")
        
        # Log all input fields on the page
        logging.info("Scanning for all input fields on the page...")
        inputs = driver.find_elements(By.TAG_NAME, "input")
        logging.info(f"Found {len(inputs)} input fields")
        for i, input_field in enumerate(inputs):
            try:
                input_type = input_field.get_attribute('type')
                input_name = input_field.get_attribute('name')
                input_id = input_field.get_attribute('id')
                input_class = input_field.get_attribute('class')
                input_placeholder = input_field.get_attribute('placeholder')
                logging.info(f"Input {i+1}: type={input_type}, name={input_name}, id={input_id}, class={input_class}, placeholder={input_placeholder}")
            except:
                pass
        
        # Check for and handle iframes
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        logging.info(f"Found {len(iframes)} iframes on the page")
        
        for i, iframe in enumerate(iframes):
            try:
                iframe_src = iframe.get_attribute('src')
                logging.info(f"Iframe {i+1} src: {iframe_src}")
                if 'captcha' in iframe_src.lower() or 'challenge' in iframe_src.lower():
                    logging.warning(f"Found potential anti-bot iframe: {iframe_src}")
            except:
                pass
        
        # Check for shadow DOM elements
        shadow_hosts = driver.execute_script("""
            return Array.from(document.querySelectorAll('*')).filter(el => el.shadowRoot);
        """)
        if shadow_hosts:
            logging.info(f"Found {len(shadow_hosts)} shadow DOM elements")
            for host in shadow_hosts:
                try:
                    shadow_root = driver.execute_script("return arguments[0].shadowRoot", host)
                    shadow_inputs = driver.execute_script("return arguments[0].querySelectorAll('input')", shadow_root)
                    logging.info(f"Found {len(shadow_inputs)} inputs in shadow DOM")
                    for input_field in shadow_inputs:
                        try:
                            input_type = driver.execute_script("return arguments[0].type", input_field)
                            input_name = driver.execute_script("return arguments[0].name", input_field)
                            input_id = driver.execute_script("return arguments[0].id", input_field)
                            logging.info(f"Shadow DOM Input: type={input_type}, name={input_name}, id={input_id}")
                        except:
                            pass
                except:
                    pass
        
        # Check for common anti-bot elements
        anti_bot_elements = [
            "iframe[src*='captcha']",
            "iframe[src*='recaptcha']",
            "iframe[src*='challenge']",
            "div[class*='captcha']",
            "div[class*='challenge']",
            "div[id*='captcha']",
            "div[id*='challenge']",
            "div[class*='cloudflare']",
            "div[id*='cloudflare']"
        ]
        
        for element in anti_bot_elements:
            try:
                if driver.find_elements(By.CSS_SELECTOR, element):
                    logging.warning(f"Found potential anti-bot element: {element}")
            except:
                pass
        
        # Log the page source for debugging
        logging.info("Current page source:")
        logging.info(driver.page_source[:2000] + "...")  # Increased to 2000 chars
        
        # Check if we're on the correct page
        if "crzyunbelevableofer" not in driver.current_url:
            logging.error("URL changed unexpectedly. Current URL: " + driver.current_url)
            return
            
        # Wait for any dynamic content to load
        time.sleep(5)
        
        # First check if any form exists
        try:
            forms = driver.find_elements(By.TAG_NAME, "form")
            logging.info(f"Found {len(forms)} forms on the page")
            for i, form in enumerate(forms):
                logging.info(f"Form {i+1} HTML: {form.get_attribute('outerHTML')[:500]}...")
        except Exception as e:
            logging.warning(f"Could not find forms: {str(e)}")
        
        # Generate random data - ensure first and last names are at least 2 characters
        first_name = fake.first_name()
        while len(first_name) < FORM_CONFIG_DATA['fields']['first_name'].get('min_length', 2):
            first_name = fake.first_name()
            
        last_name = fake.last_name()
        while len(last_name) < FORM_CONFIG_DATA['fields']['last_name'].get('min_length', 2):
            last_name = fake.last_name()
            
        # Generate phone number based on configuration
        phone = generate_phone()
        
        # Generate email using common domains
        email = generate_email(first_name, last_name)
        
        logging.info("Generated random data for form submission:")
        logging.info(f"First Name: {first_name}")
        logging.info(f"Last Name: {last_name}")
        logging.info(f"Email: {email}")
        logging.info(f"Phone: {phone}")
        
        # Fill in the form using configuration
        logging.info("Attempting to fill form fields...")
        
        # First name field - try multiple methods to find it
        logging.info(f"Looking for first name field with selector: {FORM_CONFIG_DATA['fields']['first_name']['selector']}")
        first_name_input = None
        
        # Method 1: Try direct selector
        try:
            first_name_input = wait.until(EC.presence_of_element_located((
                By.XPATH if FORM_CONFIG_DATA['fields']['first_name']['type'] == 'xpath' else By.CSS_SELECTOR,
                FORM_CONFIG_DATA['fields']['first_name']['selector']
            )))
        except:
            logging.info("First name field not found with direct selector")
        
        # Method 2: Try finding by name attribute
        if not first_name_input:
            try:
                first_name_input = wait.until(EC.presence_of_element_located((
                    By.CSS_SELECTOR,
                    f"input[name*='first'][name*='name']"
                )))
            except:
                logging.info("First name field not found by name attribute")
        
        # Method 3: Try finding by placeholder
        if not first_name_input:
            try:
                first_name_input = wait.until(EC.presence_of_element_located((
                    By.CSS_SELECTOR,
                    f"input[placeholder*='first'][placeholder*='name']"
                )))
            except:
                logging.info("First name field not found by placeholder")
        
        # Method 4: Try finding in iframes
        if not first_name_input:
            logging.info("First name field not found in main document, checking iframes...")
            for iframe in iframes:
                try:
                    driver.switch_to.frame(iframe)
                    first_name_input = wait.until(EC.presence_of_element_located((
                        By.XPATH if FORM_CONFIG_DATA['fields']['first_name']['type'] == 'xpath' else By.CSS_SELECTOR,
                        FORM_CONFIG_DATA['fields']['first_name']['selector']
                    )))
                    logging.info("Found first name field in iframe")
                    break
                except:
                    driver.switch_to.default_content()
                    continue
        
        # Method 5: Try finding in shadow DOM
        if not first_name_input and shadow_hosts:
            logging.info("First name field not found in main document or iframes, checking shadow DOM...")
            for host in shadow_hosts:
                try:
                    shadow_root = driver.execute_script("return arguments[0].shadowRoot", host)
                    first_name_input = driver.execute_script("""
                        return arguments[0].querySelector(arguments[1])
                    """, shadow_root, FORM_CONFIG_DATA['fields']['first_name']['selector'])
                    if first_name_input:
                        logging.info("Found first name field in shadow DOM")
                        break
                except:
                    continue
        
        # Method 6: Try finding by JavaScript
        if not first_name_input:
            logging.info("First name field not found with previous methods, trying JavaScript...")
            try:
                first_name_input = driver.execute_script("""
                    return document.querySelector(arguments[0]) ||
                           document.querySelector('input[name*="first"][name*="name"]') ||
                           document.querySelector('input[placeholder*="first"][placeholder*="name"]');
                """, FORM_CONFIG_DATA['fields']['first_name']['selector'])
                if first_name_input:
                    logging.info("Found first name field using JavaScript")
            except:
                logging.info("First name field not found using JavaScript")
        
        if not first_name_input:
            raise Exception("Could not find first name field using any method")
        
        # Fill the first name field
        driver.execute_script("arguments[0].scrollIntoView(true);", first_name_input)
        time.sleep(1)  # Wait for scroll to complete
        first_name_input.clear()
        first_name_input.send_keys(first_name)
        logging.info(f"Filled first name: {first_name}")
        
        # Last name field
        logging.info(f"Looking for last name field with selector: {FORM_CONFIG_DATA['fields']['last_name']['selector']}")
        last_name_input = wait.until(EC.presence_of_element_located((
            By.XPATH if FORM_CONFIG_DATA['fields']['last_name']['type'] == 'xpath' else By.CSS_SELECTOR,
            FORM_CONFIG_DATA['fields']['last_name']['selector']
        )))
        last_name_input.clear()
        last_name_input.send_keys(last_name)
        logging.info(f"Filled last name: {last_name}")
        
        # Email field
        logging.info(f"Looking for email field with selector: {FORM_CONFIG_DATA['fields']['email']['selector']}")
        email_input = wait.until(EC.presence_of_element_located((
            By.XPATH if FORM_CONFIG_DATA['fields']['email']['type'] == 'xpath' else By.CSS_SELECTOR,
            FORM_CONFIG_DATA['fields']['email']['selector']
        )))
        email_input.clear()
        email_input.send_keys(email)
        logging.info(f"Filled email: {email}")
        
        # Phone field
        logging.info(f"Looking for phone field with selector: {FORM_CONFIG_DATA['fields']['phone']['selector']}")
        phone_input = wait.until(EC.presence_of_element_located((
            By.XPATH if FORM_CONFIG_DATA['fields']['phone']['type'] == 'xpath' else By.CSS_SELECTOR,
            FORM_CONFIG_DATA['fields']['phone']['selector']
        )))
        phone_input.clear()
        phone_input.send_keys(phone)
        logging.info(f"Filled phone: {phone}")
        
        # Click submit button
        logging.info(f"Looking for submit button with selector: {FORM_CONFIG_DATA['fields']['submit_button']['selector']}")
        submit_button = wait.until(EC.element_to_be_clickable((
            By.XPATH if FORM_CONFIG_DATA['fields']['submit_button']['type'] == 'xpath' else By.CSS_SELECTOR,
            FORM_CONFIG_DATA['fields']['submit_button']['selector']
        )))
        submit_button.click()
        logging.info("Clicked submit button")
        
        # Wait a moment to see if there's any response
        time.sleep(5)
        
        # Log the page source after submission for debugging
        logging.info("Page source after submission:")
        logging.info(driver.page_source[:500] + "...")  # Log first 500 chars
        
        # Check for error messages using the data-error-status attribute
        try:
            error_messages = driver.find_elements(By.CSS_SELECTOR, "[data-error-status='active']")
            if error_messages:
                for error in error_messages:
                    logging.warning(f"Form validation error: {error.text}")
            else:
                logging.info("No validation errors found")
        except Exception as e:
            logging.info(f"Could not check for validation errors: {str(e)}")
        
        logging.info("Form submission completed")
        
    except Exception as e:
        logging.error(f"An error occurred during form submission: {str(e)}", exc_info=True)
        # Log the current URL
        try:
            logging.error(f"Current URL: {driver.current_url}")
        except:
            logging.error("Could not get current URL")
        # Log the page source
        try:
            logging.error("Current page source:")
            logging.error(driver.page_source[:1000] + "...")  # Log first 1000 chars
        except:
            logging.error("Could not get page source")
    finally:
        logging.info("Closing WebDriver...")
        driver.quit()

def main():
    logging.info("Starting form submission automation")
    logging.info(f"Configuration:")
    logging.info(f"  Min interval: {MIN_INTERVAL} seconds")
    logging.info(f"  Max interval: {MAX_INTERVAL} seconds")
    logging.info(f"  Target URL: {URL}")
    logging.info(f"  Form configuration: {FORM_CONFIG}")
    
    submission_count = 0
    
    # Submit first form immediately
    submission_count += 1
    logging.info(f"\n{'='*50}")
    logging.info(f"Starting initial submission #{submission_count}")
    logging.info(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    submit_form()
    
    # Small random delay after first submission (5-15 seconds)
    initial_delay = random.uniform(5, 15)
    logging.info(f"Initial delay of {initial_delay:.2f} seconds before starting regular intervals")
    time.sleep(initial_delay)
    
    while True:
        try:
            # Calculate next interval (3-30 minutes)
            next_interval = random.uniform(MIN_INTERVAL, MAX_INTERVAL)
            minutes = next_interval / 60
            next_submission_time = datetime.now() + timedelta(seconds=next_interval)
            logging.info(f"Waiting {minutes:.1f} minutes before next submission")
            logging.info(f"Next submission will be at: {next_submission_time.strftime('%Y-%m-%d %H:%M:%S')}")
            logging.info(f"{'='*50}\n")
            
            # Wait for the calculated interval
            time.sleep(next_interval)
            
            # After waiting, proceed with submission
            submission_count += 1
            logging.info(f"\n{'='*50}")
            logging.info(f"Starting submission #{submission_count}")
            logging.info(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            submit_form()
            
        except KeyboardInterrupt:
            logging.info("\nReceived keyboard interrupt. Shutting down...")
            break
        except Exception as e:
            logging.error(f"Unexpected error in main loop: {str(e)}", exc_info=True)
            logging.info("Continuing with next submission...")
            time.sleep(5)  # Wait a bit before retrying

if __name__ == "__main__":
    main() 