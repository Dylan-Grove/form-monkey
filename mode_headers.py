#!/usr/bin/env python3
import logging
import time
import json
import os
import re
import requests
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urlparse

import undetected_chromedriver as uc
import utils

# Security headers to check
SECURITY_HEADERS = {
    'Strict-Transport-Security': {
        'description': 'HTTP Strict Transport Security (HSTS)',
        'recommendation': 'max-age=31536000; includeSubDomains; preload',
        'severity': 'high',
        'info': 'Ensures the browser always uses HTTPS for your domain'
    },
    'Content-Security-Policy': {
        'description': 'Content Security Policy (CSP)',
        'recommendation': "default-src 'self'; script-src 'self'; object-src 'none'",
        'severity': 'high',
        'info': 'Prevents XSS attacks by specifying which content sources are approved'
    },
    'X-Content-Type-Options': {
        'description': 'X-Content-Type-Options',
        'recommendation': 'nosniff',
        'severity': 'medium',
        'info': 'Prevents MIME type sniffing which can lead to security vulnerabilities'
    },
    'X-Frame-Options': {
        'description': 'X-Frame-Options',
        'recommendation': 'DENY or SAMEORIGIN',
        'severity': 'medium',
        'info': 'Prevents clickjacking attacks by specifying if a browser should be allowed to render a page in a frame'
    },
    'X-XSS-Protection': {
        'description': 'X-XSS-Protection',
        'recommendation': '1; mode=block',
        'severity': 'medium',
        'info': 'Enables cross-site scripting (XSS) filtering in browsers'
    },
    'Referrer-Policy': {
        'description': 'Referrer Policy',
        'recommendation': 'no-referrer or same-origin',
        'severity': 'medium',
        'info': 'Controls what information is sent in the Referer header'
    },
    'Permissions-Policy': {
        'description': 'Permissions Policy',
        'recommendation': 'camera=(), microphone=(), geolocation=()',
        'severity': 'low',
        'info': 'Controls which browser features can be used on the page'
    },
    'Cache-Control': {
        'description': 'Cache-Control',
        'recommendation': 'no-store, max-age=0',
        'severity': 'low',
        'info': 'Controls how pages are cached by browsers and proxies'
    },
    'Clear-Site-Data': {
        'description': 'Clear-Site-Data',
        'recommendation': '"cache", "cookies", "storage"',
        'severity': 'low',
        'info': 'Clears browsing data (cookies, storage, cache) associated with the requesting website'
    }
}

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
        "name": "headers_test_browser",
    }
    
    # Use the centralized setup_driver function from utils
    return utils.setup_driver(config, logger)

def analyze_header(header_name: str, header_value: str) -> Dict[str, Any]:
    """
    Analyze a security header and evaluate its implementation.
    
    Args:
        header_name: Name of the header
        header_value: Value of the header
        
    Returns:
        Dictionary with analysis results
    """
    header_info = SECURITY_HEADERS.get(header_name, {
        'description': header_name,
        'recommendation': 'N/A',
        'severity': 'low',
        'info': 'Custom security header'
    })
    
    result = {
        'name': header_name,
        'value': header_value,
        'description': header_info['description'],
        'status': 'present',
        'severity': header_info['severity'],
        'recommendation': header_info['recommendation'],
        'info': header_info['info']
    }
    
    # Perform header-specific analysis
    if header_name == 'Strict-Transport-Security':
        if 'max-age=' in header_value:
            try:
                max_age = int(header_value.split('max-age=')[1].split(';')[0].strip())
                if max_age < 31536000:  # Less than 1 year
                    result['status'] = 'weak'
                    result['info'] += '. The max-age is less than recommended (1 year)'
            except:
                result['status'] = 'invalid'
        else:
            result['status'] = 'weak'
            
    elif header_name == 'Content-Security-Policy':
        if "default-src 'none'" in header_value or "default-src 'self'" in header_value:
            result['status'] = 'strong'
        elif "default-src" in header_value:
            result['status'] = 'moderate'
        else:
            result['status'] = 'weak'
            
    elif header_name == 'X-Content-Type-Options':
        if header_value.lower() != 'nosniff':
            result['status'] = 'weak'
            
    elif header_name == 'X-Frame-Options':
        if header_value.upper() not in ['DENY', 'SAMEORIGIN']:
            result['status'] = 'weak'
            
    elif header_name == 'X-XSS-Protection':
        if header_value != '1; mode=block':
            result['status'] = 'weak'
            
    elif header_name == 'Referrer-Policy':
        strong_policies = ['no-referrer', 'same-origin', 'strict-origin', 'strict-origin-when-cross-origin']
        weak_policies = ['origin', 'origin-when-cross-origin', 'no-referrer-when-downgrade']
        if any(policy in header_value for policy in strong_policies):
            result['status'] = 'strong'
        elif any(policy in header_value for policy in weak_policies):
            result['status'] = 'moderate'
        else:
            result['status'] = 'weak'
    
    return result

def evaluate_security_headers(headers: Dict[str, str], logger: logging.Logger) -> List[Dict[str, Any]]:
    """
    Evaluate security headers in a response.
    
    Args:
        headers: HTTP headers from the response
        logger: Logger instance
        
    Returns:
        List of dictionaries with header analysis results
    """
    results = []
    headers_lower = {k.lower(): (k, v) for k, v in headers.items()}
    
    for header_name in SECURITY_HEADERS:
        # Find the header (case-insensitive)
        header_key_lower = header_name.lower()
        if header_key_lower in headers_lower:
            original_key, value = headers_lower[header_key_lower]
            result = analyze_header(header_name, value)
            
            if result['status'] == 'weak' or result['status'] == 'invalid':
                logger.warning(f"Security header '{header_name}' has a weak implementation: {value}")
            
            results.append(result)
        else:
            # Header is missing
            header_info = SECURITY_HEADERS[header_name]
            results.append({
                'name': header_name,
                'value': None,
                'description': header_info['description'],
                'status': 'missing',
                'severity': header_info['severity'],
                'recommendation': header_info['recommendation'],
                'info': header_info['info']
            })
            
            if header_info['severity'] == 'high':
                logger.warning(f"Important security header '{header_name}' is missing")
            else:
                logger.info(f"Security header '{header_name}' is missing")
    
    return results

def check_https_redirection(url: str, logger: logging.Logger) -> Dict[str, Any]:
    """
    Check if HTTP requests are redirected to HTTPS.
    
    Args:
        url: URL to check
        logger: Logger instance
        
    Returns:
        Dictionary with redirect check results
    """
    result = {
        'test': 'https_redirect',
        'status': 'failed',
        'details': 'Unable to test HTTPS redirection'
    }
    
    parsed_url = urlparse(url)
    
    # Only test if the URL is HTTPS
    if parsed_url.scheme != 'https':
        result['status'] = 'skipped'
        result['details'] = 'URL is not using HTTPS'
        return result
    
    try:
        # Try to access the site via HTTP
        http_url = f"http://{parsed_url.netloc}{parsed_url.path}"
        response = requests.get(http_url, allow_redirects=True, timeout=10)
        
        # Check if we were redirected to HTTPS
        final_url = response.url
        
        if final_url.startswith('https://'):
            result['status'] = 'passed'
            result['details'] = f"HTTP correctly redirects to HTTPS: {final_url}"
            logger.info("HTTP to HTTPS redirection is properly configured")
        else:
            result['status'] = 'failed'
            result['details'] = f"HTTP does not redirect to HTTPS. Final URL: {final_url}"
            logger.warning("Site does not redirect HTTP to HTTPS - this is a security issue")
            
    except Exception as e:
        result['status'] = 'error'
        result['details'] = f"Error testing HTTP to HTTPS redirection: {str(e)}"
        logger.error(f"Error checking HTTPS redirection: {str(e)}")
    
    return result

def run_headers_mode(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run security headers testing mode.
    
    Args:
        context: Application context containing config and logger
        
    Returns:
        Dict with testing results
    """
    config = context["config"]
    logger = context["logger"]
    
    logger.info("Starting security headers testing mode")
    logger.info(f"Configuration: {config.get('name', 'default')}")
    
    # Get target URL
    url = config.get("url")
    if not url:
        logger.error("No URL specified in configuration")
        return {"success": False, "error": "No URL specified"}
    
    # Initialize results
    results = {
        "target_url": url,
        "test_type": "security_headers",
        "headers_tested": 0,
        "missing_headers": 0,
        "weak_headers": 0,
        "header_results": [],
        "https_redirect": {},
        "start_time": time.time(),
        "success": True
    }
    
    try:
        logger.info(f"Testing security headers for {url}")
        
        # Make a request to the target URL
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()  # Raise exception for 4XX/5XX status codes
        except requests.exceptions.RequestException as e:
            logger.error(f"Error connecting to {url}: {str(e)}")
            results["success"] = False
            results["error"] = f"Failed to connect to {url}: {str(e)}"
            return results
        
        # Extract and analyze headers
        headers = response.headers
        header_results = evaluate_security_headers(headers, logger)
        results["header_results"] = header_results
        results["headers_tested"] = len(header_results)
        
        # Count missing and weak headers
        for header in header_results:
            if header['status'] == 'missing':
                results["missing_headers"] += 1
            elif header['status'] in ['weak', 'invalid']:
                results["weak_headers"] += 1
        
        # Check HTTP to HTTPS redirection
        https_redirect = check_https_redirection(url, logger)
        results["https_redirect"] = https_redirect
        
        # Calculate overall security score (0-100)
        total_weight = sum(3 if SECURITY_HEADERS[h['name']]['severity'] == 'high' else
                           2 if SECURITY_HEADERS[h['name']]['severity'] == 'medium' else
                           1 for h in header_results if h['name'] in SECURITY_HEADERS)
        
        earned_weight = sum(3 if SECURITY_HEADERS[h['name']]['severity'] == 'high' and h['status'] in ['present', 'strong', 'moderate'] else
                           2 if SECURITY_HEADERS[h['name']]['severity'] == 'medium' and h['status'] in ['present', 'strong', 'moderate'] else
                           1 if h['status'] in ['present', 'strong', 'moderate'] else
                           0 for h in header_results if h['name'] in SECURITY_HEADERS)
        
        # Add bonus for HTTPS redirect
        if https_redirect['status'] == 'passed':
            earned_weight += 2
            total_weight += 2
        
        security_score = int((earned_weight / total_weight) * 100) if total_weight > 0 else 0
        results["security_score"] = security_score
        
        # Assess security rating
        if security_score >= 90:
            results["security_rating"] = "excellent"
        elif security_score >= 75:
            results["security_rating"] = "good"
        elif security_score >= 50:
            results["security_rating"] = "fair"
        else:
            results["security_rating"] = "poor"
        
        # Calculate result summary
        results["duration"] = time.time() - results["start_time"]
        
        # Add findings for missing critical headers
        results["vulnerabilities"] = []
        results["security_issues"] = []  # Initialize the security_issues list
        
        for header in header_results:
            if header['status'] == 'missing' and header['severity'] == 'high':
                issue = {
                    "type": "missing_header",
                    "header": header['name'],
                    "severity": "high",
                    "details": f"Missing {header['description']} header: {header['info']}",
                    "recommendation": f"Add the header with value: {header['recommendation']}",
                    "description": header['description'],
                    "reference": f"https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/{header['name']}"
                }
                results["vulnerabilities"].append(issue)
                results["security_issues"].append(issue)
            elif header['status'] in ['weak', 'invalid'] and header['severity'] == 'high':
                issue = {
                    "type": "weak_header",
                    "header": header['name'],
                    "severity": "medium",
                    "details": f"Weak implementation of {header['description']} header: {header['value']}",
                    "recommendation": f"Improve the header value to: {header['recommendation']}",
                    "issue": f"Current value does not meet security best practices",
                    "value": header['value']
                }
                results["vulnerabilities"].append(issue)
                results["security_issues"].append(issue)
        
        # Add HTTPS redirect issue if applicable
        if https_redirect['status'] == 'failed':
            issue = {
                "type": "http_not_redirected",
                "severity": "high",
                "details": "HTTP requests are not redirected to HTTPS",
                "recommendation": "Configure the server to redirect all HTTP requests to HTTPS"
            }
            results["vulnerabilities"].append(issue)
            results["security_issues"].append(issue)
        
        results["vulnerable"] = len(results["vulnerabilities"]) > 0
        
    except Exception as e:
        logger.error(f"Error during security headers testing: {str(e)}")
        results["success"] = False
        results["error"] = str(e)
    
    # Log summary
    if results.get("security_score"):
        logger.info(f"Security headers score: {results['security_score']}/100 ({results['security_rating']})")
        logger.info(f"Found {results['missing_headers']} missing and {results['weak_headers']} weak security headers")
    
    return results 