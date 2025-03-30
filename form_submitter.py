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
from datetime import datetime
import undetected_chromedriver as uc

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Configuration
MIN_INTERVAL = int(os.getenv('MIN_INTERVAL', 60))  # Default 1 minute
MAX_INTERVAL = int(os.getenv('MAX_INTERVAL', 1800))  # Default 30 minutes
FORM_CONFIG = os.getenv('FORM_CONFIG', 'default')  # Default form configuration to use

# Load form configuration
with open('form_config.json', 'r') as f:
    CONFIG = json.load(f)

# Get the form configuration to use
FORM_CONFIG_DATA = CONFIG.get(FORM_CONFIG, CONFIG['default'])
URL = os.getenv('TARGET_URL', FORM_CONFIG_DATA['url'])

# Common Canadian area codes
CANADIAN_AREA_CODES = [
    '226', '249', '289', '343', '365', '416', '437', '438', '450', '506',
    '514', '548', '579', '581', '587', '604', '613', '639', '647', '672',
    '705', '709', '742', '778', '780', '782', '807', '819', '825', '873',
    '902', '905'
]

# Common American area codes
AMERICAN_AREA_CODES = [
    '201', '202', '203', '205', '206', '207', '208', '209', '210', '212',
    '213', '214', '215', '216', '217', '218', '219', '220', '223', '224',
    '225', '228', '229', '231', '234', '239', '240', '248', '251', '252',
    '253', '254', '256', '260', '262', '267', '269', '270', '272', '276',
    '281', '301', '302', '303', '304', '305', '307', '308', '309', '310',
    '312', '313', '314', '315', '316', '317', '318', '319', '320', '321',
    '323', '325', '330', '331', '334', '336', '337', '339', '340', '341',
    '347', '351', '352', '360', '361', '364', '380', '385', '386', '401',
    '402', '404', '405', '406', '407', '408', '409', '410', '412', '413',
    '414', '415', '417', '419', '423', '424', '425', '430', '432', '434',
    '435', '440', '442', '443', '447', '458', '463', '469', '470', '475',
    '478', '479', '480', '484', '501', '502', '503', '504', '505', '507',
    '508', '509', '510', '512', '513', '515', '516', '517', '518', '520',
    '530', '531', '534', '539', '540', '541', '551', '559', '561', '562',
    '563', '564', '567', '570', '571', '573', '574', '575', '580', '585',
    '586', '601', '602', '603', '605', '606', '607', '608', '609', '610',
    '612', '614', '615', '616', '617', '618', '619', '620', '623', '626',
    '628', '629', '630', '631', '636', '641', '646', '650', '651', '657',
    '660', '661', '662', '667', '669', '678', '681', '701', '702', '703',
    '704', '706', '707', '708', '712', '713', '714', '715', '716', '717',
    '718', '719', '720', '724', '725', '727', '731', '732', '734', '737',
    '740', '743', '747', '754', '757', '760', '762', '763', '765', '769',
    '770', '772', '773', '774', '775', '779', '781', '785', '786', '801',
    '802', '803', '804', '805', '806', '808', '810', '812', '813', '814',
    '815', '816', '817', '818', '828', '830', '831', '832', '843', '845',
    '847', '848', '850', '856', '857', '858', '859', '860', '862', '863',
    '864', '865', '870', '872', '878', '901', '903', '904', '906', '907',
    '908', '909', '910', '912', '913', '914', '915', '916', '917', '918',
    '919', '920', '925', '928', '929', '930', '931', '934', '936', '937',
    '938', '940', '941', '947', '949', '951', '952', '954', '956', '959',
    '970', '971', '972', '973', '975', '978', '979', '980', '984', '985',
    '989'
]

# Common email domains
EMAIL_DOMAINS = ['gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com']

# Common words for random email generation
COMMON_WORDS = [
    # Cool/awesome words
    'cool', 'awesome', 'super', 'mega', 'ultra', 'pro', 'star', 'king', 'queen', 'master',
    'ninja', 'guru', 'wizard', 'hero', 'champ', 'boss', 'chief', 'lord', 'sir', 'madam',
    
    # Nature elements
    'rock', 'fire', 'ice', 'storm', 'thunder', 'lightning', 'dragon', 'eagle', 'lion', 'tiger',
    'bear', 'wolf', 'fox', 'cat', 'dog', 'bird', 'fish', 'snake', 'monkey', 'panda',
    
    # Tech terms
    'hack', 'code', 'byte', 'data', 'cyber', 'tech', 'geek', 'nerd', 'bot', 'dev',
    'cloud', 'web', 'net', 'bit', 'digi', 'info', 'app', 'api', 'dev', 'sys',
    
    # Gaming terms
    'game', 'play', 'win', 'beat', 'score', 'rank', 'level', 'raid', 'quest', 'guild',
    'team', 'clan', 'crew', 'squad', 'unit', 'force', 'army', 'navy', 'air', 'space',
    
    # Sports terms
    'sport', 'ball', 'team', 'play', 'win', 'beat', 'score', 'rank', 'race', 'run',
    'jump', 'swim', 'dive', 'ride', 'fly', 'surf', 'ski', 'skate', 'board', 'park',
    
    # Music terms
    'band', 'rock', 'jazz', 'blues', 'punk', 'metal', 'rap', 'hip', 'hop', 'beat',
    'tune', 'song', 'band', 'crew', 'gang', 'posse', 'squad', 'team', 'unit', 'force',
    
    # Food terms
    'food', 'eat', 'bite', 'chef', 'cook', 'dish', 'meal', 'feast', 'dine', 'taste',
    'sweet', 'spice', 'sauce', 'juice', 'brew', 'wine', 'beer', 'cafe', 'pub', 'bar',
    
    # Travel terms
    'trip', 'tour', 'ride', 'fly', 'sail', 'cruise', 'hike', 'walk', 'run', 'jump',
    'swim', 'dive', 'surf', 'ski', 'skate', 'board', 'park', 'camp', 'site', 'spot',
    
    # Art terms
    'art', 'draw', 'paint', 'ink', 'pen', 'pencil', 'brush', 'color', 'shade', 'tone',
    'line', 'form', 'shape', 'space', 'light', 'dark', 'bold', 'fine', 'soft', 'hard',
    
    # Science terms
    'atom', 'star', 'moon', 'sun', 'sky', 'air', 'wind', 'rain', 'snow', 'ice',
    'fire', 'earth', 'water', 'land', 'sea', 'ocean', 'lake', 'river', 'stream', 'wave',
    
    # Time terms
    'time', 'day', 'night', 'morn', 'noon', 'eve', 'week', 'month', 'year', 'age',
    'era', 'age', 'life', 'live', 'born', 'grow', 'rise', 'fall', 'flow', 'move',
    
    # Action words
    'run', 'jump', 'walk', 'talk', 'sing', 'dance', 'play', 'work', 'rest', 'stop',
    'go', 'come', 'give', 'take', 'make', 'do', 'be', 'see', 'hear', 'feel',
    
    # Color words
    'red', 'blue', 'green', 'yellow', 'black', 'white', 'gray', 'brown', 'pink', 'purple',
    'gold', 'silver', 'bronze', 'copper', 'steel', 'iron', 'lead', 'tin', 'zinc', 'brass',
    
    # Size words
    'big', 'small', 'tiny', 'huge', 'vast', 'wide', 'narrow', 'long', 'short', 'tall',
    'high', 'low', 'deep', 'shallow', 'thick', 'thin', 'heavy', 'light', 'fast', 'slow',
    
    # Mood words
    'happy', 'sad', 'mad', 'glad', 'bad', 'good', 'fine', 'nice', 'cool', 'hot',
    'warm', 'cold', 'soft', 'hard', 'sweet', 'sour', 'fresh', 'stale', 'new', 'old',
    
    # Number words
    'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten',
    'first', 'last', 'next', 'last', 'best', 'worst', 'most', 'least', 'more', 'less'
]

# Additional random elements for email generation
RANDOM_NUMBERS = [str(i) for i in range(10)]
RANDOM_CHARS = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
RANDOM_SPECIAL_CHARS = ['.', '_', '-', '']
RANDOM_YEARS = [str(i) for i in range(1980, 2024)]
RANDOM_MONTHS = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']
RANDOM_DAYS = [f"{i:02d}" for i in range(1, 32)]

def generate_phone():
    area_code_type = FORM_CONFIG_DATA.get('area_code_type', 'canadian')
    if area_code_type == 'american':
        area_codes = AMERICAN_AREA_CODES
    else:
        area_codes = CANADIAN_AREA_CODES
    
    area_code = random.choice(area_codes)
    prefix = random.randint(200, 999)
    line_number = random.randint(1000, 9999)
    return f"{area_code}{prefix}{line_number}"

def generate_random_username():
    # Randomly choose a pattern for username generation
    pattern = random.choice([
        # Pattern 1: random word + random numbers + random word
        lambda: f"{random.choice(COMMON_WORDS)}{random.randint(1, 999)}{random.choice(COMMON_WORDS)}",
        
        # Pattern 2: random word + random special char + random word + random numbers
        lambda: f"{random.choice(COMMON_WORDS)}{random.choice(RANDOM_SPECIAL_CHARS)}{random.choice(COMMON_WORDS)}{random.randint(1, 999)}",
        
        # Pattern 3: random word + year + random word
        lambda: f"{random.choice(COMMON_WORDS)}{random.choice(RANDOM_YEARS)}{random.choice(COMMON_WORDS)}",
        
        # Pattern 4: random word + random word + random special char + random numbers
        lambda: f"{random.choice(COMMON_WORDS)}{random.choice(COMMON_WORDS)}{random.choice(RANDOM_SPECIAL_CHARS)}{random.randint(1, 999)}",
        
        # Pattern 5: random word + date + random word
        lambda: f"{random.choice(COMMON_WORDS)}{random.choice(RANDOM_YEARS)}{random.choice(RANDOM_MONTHS)}{random.choice(RANDOM_DAYS)}{random.choice(COMMON_WORDS)}",
        
        # Pattern 6: random word + random chars + random numbers
        lambda: f"{random.choice(COMMON_WORDS)}{''.join(random.choices(RANDOM_CHARS, k=random.randint(2, 4)))}{random.randint(1, 999)}",
        
        # Pattern 7: random word + random special char + random chars + random numbers
        lambda: f"{random.choice(COMMON_WORDS)}{random.choice(RANDOM_SPECIAL_CHARS)}{''.join(random.choices(RANDOM_CHARS, k=random.randint(2, 4)))}{random.randint(1, 999)}",
        
        # Pattern 8: random word + random word + random special char + random chars
        lambda: f"{random.choice(COMMON_WORDS)}{random.choice(COMMON_WORDS)}{random.choice(RANDOM_SPECIAL_CHARS)}{''.join(random.choices(RANDOM_CHARS, k=random.randint(2, 4)))}",
        
        # Pattern 9: random word + random numbers + random special char + random word
        lambda: f"{random.choice(COMMON_WORDS)}{random.randint(1, 999)}{random.choice(RANDOM_SPECIAL_CHARS)}{random.choice(COMMON_WORDS)}",
        
        # Pattern 10: random word + random chars + random special char + random numbers
        lambda: f"{random.choice(COMMON_WORDS)}{''.join(random.choices(RANDOM_CHARS, k=random.randint(2, 4)))}{random.choice(RANDOM_SPECIAL_CHARS)}{random.randint(1, 999)}",
        
        # Pattern 11: random word + random numbers + random word + random special char + random chars
        lambda: f"{random.choice(COMMON_WORDS)}{random.randint(1, 999)}{random.choice(COMMON_WORDS)}{random.choice(RANDOM_SPECIAL_CHARS)}{''.join(random.choices(RANDOM_CHARS, k=random.randint(2, 4)))}",
        
        # Pattern 12: random word + random special char + random word + random special char + random numbers
        lambda: f"{random.choice(COMMON_WORDS)}{random.choice(RANDOM_SPECIAL_CHARS)}{random.choice(COMMON_WORDS)}{random.choice(RANDOM_SPECIAL_CHARS)}{random.randint(1, 999)}",
        
        # Pattern 13: very short username (3-6 chars)
        lambda: f"{random.randint(1, 999)}{random.choice(RANDOM_SPECIAL_CHARS)}{random.choice(COMMON_WORDS)[:3]}",
        
        # Pattern 14: very long username with multiple words
        lambda: f"{random.choice(COMMON_WORDS)}{random.choice(RANDOM_SPECIAL_CHARS)}{random.choice(COMMON_WORDS)}{random.choice(RANDOM_SPECIAL_CHARS)}{random.choice(COMMON_WORDS)}{random.choice(RANDOM_SPECIAL_CHARS)}{random.randint(1, 999)}",
        
        # Pattern 15: username with multiple special chars
        lambda: f"{random.choice(COMMON_WORDS)}{random.choice(RANDOM_SPECIAL_CHARS)}{random.choice(COMMON_WORDS)}{random.choice(RANDOM_SPECIAL_CHARS)}{random.choice(COMMON_WORDS)}{random.randint(1, 999)}"
    ])
    
    return pattern()

def generate_email(first_name, last_name):
    # Randomly choose between name-based and completely random email
    if random.random() < 0.4:  # 40% chance of using name-based email
        # Create variations of the email username
        username_variations = [
            # Short variations
            f"{first_name.lower()[0]}{random.randint(1, 999)}",
            f"{first_name.lower()[:2]}{random.choice(RANDOM_SPECIAL_CHARS)}{random.randint(1, 99)}",
            f"{last_name.lower()[:3]}{random.randint(1, 999)}",
            
            # Medium variations
            f"{first_name.lower()}{random.randint(1, 999)}{random.choice(RANDOM_SPECIAL_CHARS)}{random.choice(COMMON_WORDS)}",
            f"{first_name.lower()[0]}{last_name.lower()}{random.randint(1, 999)}{random.choice(RANDOM_SPECIAL_CHARS)}{''.join(random.choices(RANDOM_CHARS, k=random.randint(2, 4)))}",
            f"{first_name.lower()}{random.choice(RANDOM_SPECIAL_CHARS)}{last_name.lower()}{random.randint(1, 99)}{random.choice(RANDOM_SPECIAL_CHARS)}{random.choice(COMMON_WORDS)}",
            
            # Long variations
            f"{first_name.lower()}{random.choice(RANDOM_SPECIAL_CHARS)}{random.choice(RANDOM_YEARS)}{random.choice(RANDOM_SPECIAL_CHARS)}{''.join(random.choices(RANDOM_CHARS, k=random.randint(2, 4)))}",
            f"{first_name.lower()}{random.choice(RANDOM_SPECIAL_CHARS)}{random.choice(COMMON_WORDS)}{random.randint(1, 999)}",
            f"{first_name.lower()}{random.choice(RANDOM_SPECIAL_CHARS)}{last_name.lower()}{random.choice(RANDOM_SPECIAL_CHARS)}{random.choice(COMMON_WORDS)}{random.randint(1, 999)}",
            
            # Very long variations
            f"{first_name.lower()}{random.choice(RANDOM_SPECIAL_CHARS)}{last_name.lower()}{random.choice(RANDOM_SPECIAL_CHARS)}{random.choice(COMMON_WORDS)}{random.choice(RANDOM_SPECIAL_CHARS)}{random.choice(COMMON_WORDS)}{random.randint(1, 999)}",
            f"{first_name.lower()}{random.choice(RANDOM_SPECIAL_CHARS)}{random.choice(COMMON_WORDS)}{random.choice(RANDOM_SPECIAL_CHARS)}{random.choice(COMMON_WORDS)}{random.choice(RANDOM_SPECIAL_CHARS)}{random.randint(1, 999)}",
            
            # Date-based variations
            f"{first_name.lower()}{random.choice(RANDOM_SPECIAL_CHARS)}{random.choice(RANDOM_YEARS)}{random.choice(RANDOM_MONTHS)}{random.choice(RANDOM_DAYS)}{random.choice(RANDOM_SPECIAL_CHARS)}{random.choice(COMMON_WORDS)}",
            f"{last_name.lower()}{random.choice(RANDOM_SPECIAL_CHARS)}{random.choice(RANDOM_YEARS)}{random.choice(RANDOM_MONTHS)}{random.choice(RANDOM_DAYS)}{random.choice(RANDOM_SPECIAL_CHARS)}{random.choice(COMMON_WORDS)}"
        ]
        username = random.choice(username_variations)
    else:
        # 60% chance of using completely random username
        username = generate_random_username()
    
    domain = random.choice(EMAIL_DOMAINS)
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
            submission_count += 1
            logging.info(f"\n{'='*50}")
            logging.info(f"Starting submission #{submission_count}")
            logging.info(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            submit_form()
            
            # Calculate next interval (1-30 minutes)
            next_interval = random.uniform(MIN_INTERVAL, MAX_INTERVAL)
            minutes = next_interval / 60
            logging.info(f"Waiting {minutes:.1f} minutes before next submission")
            logging.info(f"{'='*50}\n")
            
            time.sleep(next_interval)
            
        except KeyboardInterrupt:
            logging.info("\nReceived keyboard interrupt. Shutting down...")
            break
        except Exception as e:
            logging.error(f"Unexpected error in main loop: {str(e)}", exc_info=True)
            logging.info("Continuing with next submission...")
            time.sleep(5)  # Wait a bit before retrying

if __name__ == "__main__":
    main() 