#!/usr/bin/env python3
import logging
import time
import json
import os
import re
import random
import string
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urlparse, urljoin

from selenium import webdriver
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
from bs4 import BeautifulSoup

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
        "name": "csrf_test_browser",
    }
    
    # Use the centralized setup_driver function from utils
    return utils.setup_driver(config, logger)

def extract_form_details(html_content: str) -> List[Dict[str, Any]]:
    """
    Extract details about forms on the page.
    
    Args:
        html_content: HTML content to parse
        
    Returns:
        List of dictionaries with form details
    """
    forms = []
    soup = BeautifulSoup(html_content, 'html.parser')
    
    for form in soup.find_all('form'):
        form_details = {
            'action': form.get('action', ''),
            'method': form.get('method', 'get').lower(),
            'id': form.get('id', ''),
            'name': form.get('name', ''),
            'inputs': [],
            'has_csrf_token': False
        }
        
        # Extract input fields
        for input_tag in form.find_all('input'):
            input_type = input_tag.get('type', 'text')
            input_name = input_tag.get('name', '')
            input_value = input_tag.get('value', '')
            
            form_details['inputs'].append({
                'type': input_type,
                'name': input_name,
                'value': input_value
            })
            
            # Check for potential CSRF tokens
            if input_type == 'hidden' and input_name and (
                'csrf' in input_name.lower() or 
                'token' in input_name.lower() or
                'nonce' in input_name.lower()
            ):
                form_details['has_csrf_token'] = True
                form_details['csrf_field'] = input_name
                form_details['csrf_value'] = input_value
        
        forms.append(form_details)
    
    return forms

def check_for_csrf_protection(form: Dict[str, Any], cookies: List[Dict[str, str]], 
                             referer_policy: str) -> Dict[str, Any]:
    """
    Check a form for various CSRF protections.
    
    Args:
        form: Form details dictionary
        cookies: List of cookies from the browser
        referer_policy: Referrer policy from the response headers
        
    Returns:
        Dictionary with protection details
    """
    protection = {
        'has_csrf_token': form.get('has_csrf_token', False),
        'has_samesite_cookie': False,
        'has_secure_cookie': False,
        'has_httponly_cookie': False,
        'has_referer_protection': False,
        'score': 0  # Higher score means better protection
    }
    
    # Check for secure cookies and SameSite attribute
    for cookie in cookies:
        if cookie.get('secure'):
            protection['has_secure_cookie'] = True
            protection['score'] += 1
        
        if cookie.get('httpOnly'):
            protection['has_httponly_cookie'] = True
            protection['score'] += 1
        
        if cookie.get('sameSite') in ['Strict', 'Lax']:
            protection['has_samesite_cookie'] = True
            protection['score'] += 2
    
    # Check referrer policy
    if referer_policy in ['same-origin', 'strict-origin', 'strict-origin-when-cross-origin']:
        protection['has_referer_protection'] = True
        protection['score'] += 1
    
    # CSRF token presence is a strong protection
    if protection['has_csrf_token']:
        protection['score'] += 3
    
    # Classify the protection level
    if protection['score'] >= 4:
        protection['level'] = 'strong'
    elif protection['score'] >= 2:
        protection['level'] = 'medium'
    else:
        protection['level'] = 'weak'
    
    return protection

def test_csrf_vulnerability(driver: webdriver.Chrome, url: str, 
                           form: Dict[str, Any], logger: logging.Logger) -> Dict[str, Any]:
    """
    Test a form for CSRF vulnerability.
    
    Args:
        driver: Selenium WebDriver instance
        url: URL of the page containing the form
        form: Form details dictionary
        logger: Logger instance
        
    Returns:
        Dictionary with test results
    """
    result = {
        'form_id': form.get('id', ''),
        'form_name': form.get('name', ''),
        'method': form.get('method', ''),
        'action': form.get('action', ''),
        'vulnerable': False,
        'severity': 'low',
        'details': ''
    }
    
    # Get the cookies and referrer policy
    cookies = driver.get_cookies()
    referrer_policy = ''
    
    try:
        # Get referrer policy if available
        script = "return document.referrerPolicy || '';"
        referrer_policy = driver.execute_script(script)
    except Exception:
        # Fallback if script execution fails
        pass
    
    # Analyze protection mechanisms
    protection = check_for_csrf_protection(form, cookies, referrer_policy)
    result['protection'] = protection
    
    # Determine vulnerability based on protection level
    if protection['level'] == 'weak':
        result['vulnerable'] = True
        result['severity'] = 'high'
        result['details'] = "Form has weak or no CSRF protection."
    elif protection['level'] == 'medium':
        result['vulnerable'] = True
        result['severity'] = 'medium'
        result['details'] = "Form has some CSRF protection, but it could be improved."
    else:
        result['vulnerable'] = False
        result['details'] = "Form has strong CSRF protection."
    
    # Log findings
    if result['vulnerable']:
        logger.warning(f"Potential CSRF vulnerability in form {result['form_id'] or result['form_name']}. "
                      f"Severity: {result['severity']}. {result['details']}")
    else:
        logger.info(f"No CSRF vulnerability detected in form {result['form_id'] or result['form_name']}.")
    
    return result

def run_csrf_mode(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run CSRF testing mode.
    
    Args:
        context: Application context containing config and logger
        
    Returns:
        Dict with testing results
    """
    config = context["config"]
    logger = context["logger"]
    
    logger.info("Starting CSRF testing mode")
    logger.info(f"Configuration: {config.get('name', 'default')}")
    
    # Get target URL
    url = config.get("url")
    if not url:
        logger.error("No URL specified in configuration")
        return {"success": False, "vulnerabilities": [], "error": "No URL specified"}
    
    # Initialize results
    results = {
        "target_url": url,
        "test_type": "csrf",
        "forms_tested": 0,
        "vulnerabilities": [],
        "start_time": time.time(),
        "success": True
    }
    
    try:
        # Setup WebDriver
        driver = utils.setup_driver(config, logger)
        logger.info(f"Navigating to {url}")
        driver.get(url)
        
        # Wait for the page to load
        time.sleep(3)
        
        # Get page HTML
        html_content = driver.page_source
        
        # Extract form details
        forms = extract_form_details(html_content)
        
        if not forms:
            logger.warning("No forms found on the page")
            results["forms_tested"] = 0
            results["success"] = True
            return results
        
        # Test each form for CSRF vulnerabilities
        for form in forms:
            results["forms_tested"] += 1
            
            # Skip GET forms as they are less susceptible to CSRF
            if form['method'] == 'get':
                logger.info(f"Skipping GET form (id={form.get('id', '')}, name={form.get('name', '')})")
                continue
            
            logger.info(f"Testing form (id={form.get('id', '')}, name={form.get('name', '')}) for CSRF vulnerabilities")
            
            # Test the form
            test_result = test_csrf_vulnerability(driver, url, form, logger)
            
            # Record vulnerability if found
            if test_result['vulnerable']:
                results["vulnerabilities"].append({
                    "form_id": test_result['form_id'],
                    "form_name": test_result['form_name'],
                    "type": "csrf",
                    "severity": test_result['severity'],
                    "details": test_result['details'],
                    "protection": test_result['protection']
                })
        
        # Calculate result summary
        results["duration"] = time.time() - results["start_time"]
        results["vulnerable"] = len(results["vulnerabilities"]) > 0
        
        # Close WebDriver
        driver.quit()
        
    except Exception as e:
        logger.error(f"Error during CSRF testing: {str(e)}")
        results["success"] = False
        results["error"] = str(e)
    
    # Log summary
    if results["vulnerable"]:
        logger.warning(f"CSRF testing completed. Found {len(results['vulnerabilities'])} potential vulnerabilities.")
    else:
        logger.info("CSRF testing completed. No vulnerabilities were detected.")
    
    return results 