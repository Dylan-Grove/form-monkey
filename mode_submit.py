#!/usr/bin/env python3
import logging
import time
import random
import os
import json
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementNotInteractableException,
    StaleElementReferenceException,
)
import utils
import undetected_chromedriver as uc

# Load random data
RANDOM_DATA = utils.load_random_data()

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

def fill_form_field(
    driver: uc.Chrome,
    field_name: str,
    field_config: Dict[str, Any],
    context: Dict[str, Any],
    logger: logging.Logger
) -> bool:
    """
    Fill a form field with random or generated data.
    
    Args:
        driver: Selenium WebDriver instance
        field_name: Name of the field to fill
        field_config: Configuration for the field
        context: Application context
        logger: Logger instance
    
    Returns:
        True if field was filled successfully, False otherwise
    """
    if field_name == "submit_button":
        return True
        
    selector = field_config.get("selector")
    selector_type = utils.get_selector_type(field_config)
    wait_time = utils.get_element_wait_time(context)
    
    if not selector:
        logger.warning(f"No selector defined for field '{field_name}', skipping")
        return False
    
    try:
        # Wait for the element to be present
        by_type = By.CSS_SELECTOR if selector_type == "css" else By.XPATH
        wait = WebDriverWait(driver, wait_time)
        element = wait.until(EC.presence_of_element_located((by_type, selector)))
        
        # Generate a value for the field
        config = context["config"]
        value = ""
        
        if field_name.lower() in ["first_name", "firstname", "first", "fname"]:
            value = utils.generate_name("first")
        elif field_name.lower() in ["last_name", "lastname", "last", "lname"]:
            value = utils.generate_name("last")
        elif field_name.lower() in ["email", "email_address", "emailaddress"]:
            value = utils.generate_email()
        elif field_name.lower() in ["phone", "phone_number", "phonenumber"]:
            # Get area code type from field config
            area_code_type = None
            if "area_code_type" in field_config:
                area_code_type = field_config["area_code_type"]
            value = utils.generate_phone(area_code_type)
        else:
            # For other fields, try to find a matching random value
            if "values" in field_config:
                value = random.choice(field_config["values"])
            else:
                # Default to a short random string
                value = f"test_{random.randint(1000, 9999)}"
        
        # Clear the field and fill it
        element.clear()
        element.send_keys(value)
        
        logger.info(f"Filled {field_name}: {value}")
        return True
        
    except (TimeoutException, NoSuchElementException) as e:
        logger.warning(f"Could not find element for field '{field_name}': {e}")
        return False
    except (ElementNotInteractableException, StaleElementReferenceException) as e:
        logger.warning(f"Could not interact with element for field '{field_name}': {e}")
        return False
    except Exception as e:
        logger.warning(f"Unexpected error filling field '{field_name}': {e}")
        return False

def submit_form(
    driver: uc.Chrome,
    config: Dict[str, Any],
    context: Dict[str, Any],
    logger: logging.Logger
) -> bool:
    """
    Submit the form by clicking the submit button.
    
    Args:
        driver: Selenium WebDriver instance
        config: Form configuration
        context: Application context
        logger: Logger instance
    
    Returns:
        True if form was submitted successfully, False otherwise
    """
    fields = config.get("fields", {})
    submit_button = fields.get("submit_button", {})
    
    if not submit_button:
        logger.warning("No submit button defined in configuration")
        return False
    
    selector = submit_button.get("selector")
    selector_type = utils.get_selector_type(submit_button)
    wait_time = utils.get_element_wait_time(context)
    
    try:
        # Wait for the submit button to be clickable
        by_type = By.CSS_SELECTOR if selector_type == "css" else By.XPATH
        wait = WebDriverWait(driver, wait_time)
        button = wait.until(EC.element_to_be_clickable((by_type, selector)))
        
        # Click the button
        button.click()
        logger.info("Form submitted successfully")
        return True
        
    except (TimeoutException, NoSuchElementException) as e:
        logger.warning(f"Could not find submit button: {e}")
        return False
    except (ElementNotInteractableException, StaleElementReferenceException) as e:
        logger.warning(f"Could not interact with submit button: {e}")
        return False
    except Exception as e:
        logger.warning(f"Unexpected error clicking submit button: {e}")
        return False

def run_submit_mode(context: Dict[str, Any]) -> None:
    """
    Main function to run the form submission mode.
    
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
    
    logger.info(f"Starting form submission to URL: {url}")
    logger.info(f"Using configuration: {json.dumps(config, indent=2)}")
    
    # Set up the browser
    driver = setup_browser()
    
    try:
        # Navigate to the form
        driver.get(url)
        logger.info("Page loaded successfully")
        
        # Wait for page to fully load
        time.sleep(3)
        
        # Fill each field in the form
        fields = config.get("fields", {})
        
        for field_name, field_config in fields.items():
            if field_config.get("required", False):
                fill_form_field(driver, field_name, field_config, context, logger)
            elif random.random() < 0.8:  # 80% chance to fill non-required fields
                fill_form_field(driver, field_name, field_config, context, logger)
        
        # Submit the form
        submit_form(driver, config, context, logger)
        
        # Wait for submission to complete
        time.sleep(5)
        
        # Calculate next submission interval
        interval = utils.get_submission_interval(context)
        
        logger.info(f"Form submission completed. Next submission in {interval} seconds")
        
        # Wait for the specified interval before next submission
        time.sleep(interval)
        
    except Exception as e:
        logger.error(f"Error during form submission: {e}")
    finally:
        # Close the browser
        driver.quit()
        logger.info("Browser closed") 