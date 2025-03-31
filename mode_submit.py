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
    # Create a simple logger for this function
    logger = logging.getLogger(__name__)
    
    # Create minimal config
    config = {
        "name": "submit_test_browser",
    }
    
    # Use the centralized setup_driver function from utils
    return utils.setup_driver(config, logger)

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
    Run form submission mode.
    
    Args:
        context: Application context containing config and logger
    """
    config = context["config"]
    logger = context["logger"]
    
    logger.info("Starting form submission mode")
    logger.info(f"Configuration: {config.get('name', 'default')}")
    
    # Get timing settings
    timing_config = config.get("timing", {})
    min_interval = timing_config.get("min_interval", 300)  # 5 minutes default
    max_interval = timing_config.get("max_interval", 2700)  # 45 minutes default
    
    # Get target URL
    url = config.get("url")
    if not url:
        logger.error("No URL specified in configuration")
        return
    
    # Initialize counters
    submission_count = 0
    success_count = 0
    failure_count = 0
    consecutive_failures = 0  # Track consecutive failures to avoid endless loops
    max_consecutive_failures = 3
    
    try:
        while True:
            submission_count += 1
            logger.info(f"Starting submission #{submission_count}")
            
            driver = None
            try:
                # Setup WebDriver with retry mechanism already built into utils.setup_driver
                logger.info("Setting up WebDriver for submission")
                driver = utils.setup_driver(config, logger)
                
                # Navigate to the form URL
                logger.info(f"Navigating to {url}")
                driver.get(url)
                
                # Wait for the page to load
                time.sleep(3)
                
                # Get form fields from the configuration
                fields = config.get("fields", {})
                if not fields:
                    logger.error("No form fields defined in the configuration")
                    failure_count += 1
                    consecutive_failures += 1
                    continue
                
                # Log fields that will be filled
                field_names = [name for name in fields.keys() if name != "submit_button"]
                logger.info(f"Configuration defines {len(field_names)} fields to fill: {', '.join(field_names)}")
                
                # Fill form fields with random data (only those explicitly defined in config)
                field_fill_count = 0
                for field_name, field_info in fields.items():
                    if field_name == "submit_button":
                        continue
                        
                    logger.info(f"Filling field: {field_name}")
                    success = utils.fill_field_with_random_data(driver, field_name, field_info, logger)
                    if success:
                        field_fill_count += 1
                        logger.info(f"Successfully filled field: {field_name}")
                    else:
                        # Don't treat this as a critical error if the field is marked as not required
                        if field_info.get("required", True):
                            logger.warning(f"Failed to fill required field: {field_name}")
                        else:
                            logger.info(f"Skipped optional field: {field_name}")
                
                # Check if enough fields were filled
                required_fields = sum(1 for f, info in fields.items() 
                                     if f != "submit_button" and info.get("required", True))
                
                if field_fill_count == 0:
                    logger.error("Failed to fill any fields, possible configuration issue")
                    failure_count += 1
                    consecutive_failures += 1
                    continue
                elif field_fill_count < required_fields:
                    logger.warning(f"Filled only {field_fill_count} of {required_fields} required fields")
                else:
                    logger.info(f"Filled all {required_fields} required fields")
                
                # Find and click the submit button
                submit_button = utils.find_submit_button(driver, config)
                
                if submit_button:
                    logger.info("Found submit button, clicking...")
                    submit_button.click()
                    
                    # Wait for submission to complete
                    time.sleep(5)
                    
                    # Success!
                    logger.info("Form submitted successfully")
                    success_count += 1
                    consecutive_failures = 0  # Reset consecutive failures on success
                else:
                    logger.error("Submit button not found")
                    failure_count += 1
                    consecutive_failures += 1
                
            except (TimeoutException, NoSuchElementException, 
                    ElementNotInteractableException, StaleElementReferenceException) as e:
                logger.error(f"Selenium error during submission: {str(e)}")
                failure_count += 1
                consecutive_failures += 1
                
            except Exception as e:
                logger.error(f"Unexpected error during submission: {str(e)}")
                failure_count += 1
                consecutive_failures += 1
            
            finally:
                # Close the browser
                if driver:
                    try:
                        driver.quit()
                        logger.info("Browser closed successfully")
                    except Exception as e:
                        logger.warning(f"Error closing browser: {str(e)}")
                
                # Log submission stats
                logger.info(f"Submission stats - Total: {submission_count}, "
                           f"Success: {success_count}, Failures: {failure_count}")
                
                # Check for too many consecutive failures
                if consecutive_failures >= max_consecutive_failures:
                    logger.error(f"Too many consecutive failures ({consecutive_failures}). Pausing for recovery.")
                    # Longer pause for recovery
                    time.sleep(60)
                    consecutive_failures = 0
                
                # Sleep before next submission
                sleep_time = random.randint(min_interval, max_interval)
                next_time = time.strftime("%H:%M:%S", time.localtime(time.time() + sleep_time))
                logger.info(f"Sleeping for {sleep_time} seconds. Next submission at {next_time}")
                time.sleep(sleep_time)
    
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt detected, stopping submissions")
    except Exception as e:
        logger.error(f"Fatal error in submission loop: {str(e)}")
    finally:
        logger.info(f"Form submission completed. Total submissions: {submission_count}, "
                   f"Successful: {success_count}, Failed: {failure_count}") 