from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from faker import Faker
import time
import random
import logging
import os
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Configuration
MIN_INTERVAL = int(os.getenv('MIN_INTERVAL', 60))  # Default 1 minute
MAX_INTERVAL = int(os.getenv('MAX_INTERVAL', 300))  # Default 5 minutes
URL = os.getenv('TARGET_URL', 'https://crzyunbelevableofer.club/')

def setup_driver():
    logging.info("Setting up Chrome WebDriver...")
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    logging.info("Chrome WebDriver setup complete")
    return driver

def submit_form():
    fake = Faker()
    driver = setup_driver()
    
    try:
        logging.info(f"Navigating to {URL}")
        driver.get(URL)
        
        # Wait for the form to be present
        wait = WebDriverWait(driver, 10)
        logging.info("Waiting for form elements to be present...")
        
        # Generate random data
        first_name = fake.first_name()
        last_name = fake.last_name()
        email = fake.email()
        phone = fake.phone_number()
        
        logging.info("Generated random data for form submission")
        
        # Fill in the form
        logging.info("Attempting to fill form fields...")
        
        first_name_input = wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/section[3]/div/div/div[1]/div[2]/form/div[2]/input')))
        first_name_input.send_keys(first_name)
        logging.info(f"Filled first name: {first_name}")
        
        last_name_input = driver.find_element(By.XPATH, '/html/body/section[3]/div/div/div[1]/div[2]/form/div[3]/input')
        last_name_input.send_keys(last_name)
        logging.info(f"Filled last name: {last_name}")
        
        email_input = driver.find_element(By.XPATH, '/html/body/section[3]/div/div/div[1]/div[2]/form/div[4]/input')
        email_input.send_keys(email)
        logging.info(f"Filled email: {email}")
        
        phone_input = driver.find_element(By.XPATH, '/html/body/section[3]/div/div/div[1]/div[2]/form/div[5]')
        phone_input.send_keys(phone)
        logging.info(f"Filled phone: {phone}")
        
        # Click submit button
        logging.info("Attempting to submit form...")
        submit_button = driver.find_element(By.XPATH, '/html/body/section[3]/div/div/div[1]/div[2]/form/div[6]/button')
        submit_button.click()
        
        # Wait a moment to see if there's any response
        time.sleep(2)
        
        logging.info("Form submission completed successfully")
        logging.info("Form submission data:")
        logging.info(f"  First Name: {first_name}")
        logging.info(f"  Last Name: {last_name}")
        logging.info(f"  Email: {email}")
        logging.info(f"  Phone: {phone}")
        
    except Exception as e:
        logging.error(f"An error occurred during form submission: {str(e)}", exc_info=True)
    finally:
        logging.info("Closing WebDriver...")
        driver.quit()

def main():
    logging.info("Starting form submission automation")
    logging.info(f"Configuration:")
    logging.info(f"  Min interval: {MIN_INTERVAL} seconds")
    logging.info(f"  Max interval: {MAX_INTERVAL} seconds")
    logging.info(f"  Target URL: {URL}")
    
    submission_count = 0
    while True:
        try:
            submission_count += 1
            logging.info(f"\n{'='*50}")
            logging.info(f"Starting submission #{submission_count}")
            logging.info(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            submit_form()
            
            # Calculate next interval
            next_interval = random.uniform(MIN_INTERVAL, MAX_INTERVAL)
            logging.info(f"Waiting {next_interval:.2f} seconds before next submission")
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