#!/usr/bin/env python3
import logging
import json
import time
import os
from typing import Dict, Any, List, Optional
from selenium.common.exceptions import WebDriverException
import datetime

# Import all mode modules
import mode_sql_inject
import mode_xss
import mode_csrf
import mode_headers
import security_report

def run_comprehensive_mode(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main function to run comprehensive security testing.
    This mode runs all security tests and generates a comprehensive report.
    
    Args:
        context: Application context containing configuration and other data
    
    Returns:
        Dictionary with all test results
    """
    config = context["config"]
    logger = context.get("logger", logging.getLogger())
    
    # Get the target URL
    url = config.get("url")
    if not url:
        logger.error("No URL defined in configuration")
        return {"error": "No URL defined"}
    
    logger.info(f"Starting comprehensive security testing on URL: {url}")
    
    # Store results from all tests
    comprehensive_results = {}
    
    # Get comprehensive testing settings
    comprehensive_settings = config.get("comprehensive_settings", {})
    tests_to_run = comprehensive_settings.get("tests", ["sql", "xss", "csrf", "headers"])
    report_format = comprehensive_settings.get("report_format", "html")
    report_dir = comprehensive_settings.get("report_dir", "reports")
    
    # Run SQL injection tests if requested
    if "sql" in tests_to_run:
        logger.info("=== Starting SQL Injection Testing ===")
        sql_context = context.copy()
        sql_context["config"] = config.copy()  # Make a copy to avoid modifying original
        
        # Override with specific SQL injection settings if available
        if "sql_injection_settings" in comprehensive_settings:
            sql_context["config"]["sql_injection_settings"] = comprehensive_settings["sql_injection_settings"]
        
        # Run the SQL injection tests
        try:
            start_time = time.time()
            sql_results = mode_sql_inject.run_sql_injection_mode(sql_context)
            execution_time = time.time() - start_time
            logger.info(f"SQL Injection Testing completed in {execution_time:.2f} seconds")
            comprehensive_results["sql_injection_results"] = sql_results
        except WebDriverException as e:
            logger.error(f"WebDriver error during SQL Injection Testing: {e}")
            logger.info("Continuing with other tests despite WebDriver error")
            comprehensive_results["sql_injection_results"] = {"error": f"WebDriver error: {str(e)}"}
        except Exception as e:
            logger.error(f"Error during SQL Injection Testing: {e}")
            comprehensive_results["sql_injection_results"] = {"error": str(e)}
    
    # Run XSS tests if requested
    if "xss" in tests_to_run:
        logger.info("=== Starting XSS Testing ===")
        xss_context = context.copy()
        xss_context["config"] = config.copy()
        
        # Override with specific XSS settings if available
        if "xss_settings" in comprehensive_settings:
            xss_context["config"]["xss_settings"] = comprehensive_settings["xss_settings"]
        
        # Run the XSS tests
        try:
            start_time = time.time()
            xss_results = mode_xss.run_xss_mode(xss_context)
            execution_time = time.time() - start_time
            logger.info(f"XSS Testing completed in {execution_time:.2f} seconds")
            comprehensive_results["xss_results"] = xss_results
        except WebDriverException as e:
            logger.error(f"WebDriver error during XSS Testing: {e}")
            logger.info("Continuing with other tests despite WebDriver error")
            comprehensive_results["xss_results"] = {"error": f"WebDriver error: {str(e)}"}
        except Exception as e:
            logger.error(f"Error during XSS Testing: {e}")
            comprehensive_results["xss_results"] = {"error": str(e)}
    
    # Run CSRF tests if requested
    if "csrf" in tests_to_run:
        logger.info("=== Starting CSRF Testing ===")
        csrf_context = context.copy()
        csrf_context["config"] = config.copy()
        
        # Override with specific CSRF settings if available
        if "csrf_settings" in comprehensive_settings:
            csrf_context["config"]["csrf_settings"] = comprehensive_settings["csrf_settings"]
        
        # Run the CSRF tests
        try:
            start_time = time.time()
            csrf_results = mode_csrf.run_csrf_mode(csrf_context)
            execution_time = time.time() - start_time
            logger.info(f"CSRF Testing completed in {execution_time:.2f} seconds")
            comprehensive_results["csrf_results"] = csrf_results
        except WebDriverException as e:
            logger.error(f"WebDriver error during CSRF Testing: {e}")
            logger.info("Continuing with other tests despite WebDriver error")
            comprehensive_results["csrf_results"] = {"error": f"WebDriver error: {str(e)}"}
        except Exception as e:
            logger.error(f"Error during CSRF Testing: {e}")
            comprehensive_results["csrf_results"] = {"error": str(e)}
    
    # Run header tests if requested
    if "headers" in tests_to_run:
        logger.info("=== Starting Security Headers Testing ===")
        headers_context = context.copy()
        headers_context["config"] = config.copy()
        
        # Run the header tests
        try:
            start_time = time.time()
            headers_results = mode_headers.run_headers_mode(headers_context)
            execution_time = time.time() - start_time
            logger.info(f"Security Headers Testing completed in {execution_time:.2f} seconds")
            comprehensive_results["headers_results"] = headers_results
        except WebDriverException as e:
            logger.error(f"WebDriver error during Headers Testing: {e}")
            logger.info("Continuing with other tests despite WebDriver error")
            comprehensive_results["headers_results"] = {"error": f"WebDriver error: {str(e)}"}
        except Exception as e:
            logger.error(f"Error during Security Headers Testing: {e}")
            comprehensive_results["headers_results"] = {"error": str(e)}
    
    # Generate comprehensive report
    logger.info("=== Generating Security Report ===")
    
    try:
        # Ensure all required fields are present in comprehensive_results
        # Check for necessary data structures before calling generate_report
        for test_type in ["sql_injection_results", "xss_results", "csrf_results", "headers_results"]:
            if test_type not in comprehensive_results:
                comprehensive_results[test_type] = {}
            
            # Ensure each test result has expected sub-fields to prevent NoneType errors
            if "error" not in comprehensive_results[test_type] and not isinstance(comprehensive_results[test_type], dict):
                comprehensive_results[test_type] = {"note": f"No results available for {test_type}"}
                
        # Create report directory if it doesn't exist
        if not os.path.exists(report_dir):
            os.makedirs(report_dir)
        
        # Ensure headers_results has security_issues
        if "headers_results" in comprehensive_results and comprehensive_results["headers_results"] is not None:
            if "security_issues" not in comprehensive_results["headers_results"] or comprehensive_results["headers_results"]["security_issues"] is None:
                comprehensive_results["headers_results"]["security_issues"] = []
        
        # Wrap the entire report generation in a try/except with detailed debug
        try:
            # Debug print the headers_results content
            headers_content = comprehensive_results.get("headers_results", {})
            logger.debug(f"Headers results debug: {str(headers_content)[:200]}...")
            logger.debug(f"Full headers_results keys: {list(headers_content.keys())}")
            logger.debug(f"Headers results structure: {json.dumps(headers_content, default=str)[:500]}...")
            
            # Debug print security_issues
            security_issues = headers_content.get("security_issues")
            logger.debug(f"Security issues type: {type(security_issues)}")
            
            if security_issues is None:
                logger.debug("Security issues is None - initializing empty list")
                # Initialize it to prevent TypeError
                comprehensive_results["headers_results"]["security_issues"] = []
            elif not isinstance(security_issues, list):
                logger.debug(f"Security issues is not a list, it's {type(security_issues)}")
                # Convert to list if possible
                try:
                    if hasattr(security_issues, '__iter__'):
                        comprehensive_results["headers_results"]["security_issues"] = list(security_issues)
                    else:
                        comprehensive_results["headers_results"]["security_issues"] = []
                except:
                    comprehensive_results["headers_results"]["security_issues"] = []
            
            report_path = security_report.generate_report(
                comprehensive_results,
                url,
                output_path=report_dir,
                format=report_format
            )
            logger.info(f"Security report generated at: {report_path}")
            comprehensive_results["report_path"] = report_path
        except Exception as e:
            logger.error(f"Error in report generation: {e}")
            # Provide detailed info about the error
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            logger.error(f"Error location: {e.__traceback__.tb_frame.f_code.co_filename}, line {e.__traceback__.tb_lineno}")
            
            # Try to handle specific issues with security report
            if isinstance(e, TypeError) and "'NoneType' object is not iterable" in str(e):
                logger.error("Found NoneType not iterable error - trying fallback report generation")
                try:
                    # Very basic report generation as fallback
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    simple_report_dir = os.path.join(report_dir, f"simple_report_{timestamp}")
                    os.makedirs(simple_report_dir, exist_ok=True)
                    
                    # Create a simple HTML report
                    with open(os.path.join(simple_report_dir, "security_report.html"), "w") as f:
                        f.write(f"""
                        <!DOCTYPE html>
                        <html>
                        <head>
                            <title>Security Assessment Report</title>
                            <style>
                                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 1000px; margin: 0 auto; padding: 20px; }}
                                h1, h2, h3 {{ color: #2c3e50; }}
                                h1 {{ border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
                                h2 {{ border-bottom: 1px solid #3498db; padding-bottom: 5px; margin-top: 30px; }}
                            </style>
                        </head>
                        <body>
                            <h1>Security Assessment Report</h1>
                            <p><strong>Target URL:</strong> {url}</p>
                            <p><strong>Scan Date:</strong> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                            <p><strong>Report Type:</strong> Form Security Assessment</p>
                            
                            <h2>Summary of Findings</h2>
                            <p>Due to an error in report generation, this is a simplified report.</p>
                            
                            <h2>Security Headers</h2>
                            <p>Found {headers_content.get('missing_headers', 0)} missing and {headers_content.get('weak_headers', 0)} weak security headers.</p>
                            <p>Security score: {headers_content.get('security_score', 'N/A')}/100 ({headers_content.get('security_rating', 'unknown')})</p>
                            
                            <h2>Security Score</h2>
                            <p>Overall security score: {comprehensive_results.get('security_score', 0)}/100</p>
                        </body>
                        </html>
                        """)
                    
                    # Create a simple JSON report
                    with open(os.path.join(simple_report_dir, "security_report.json"), "w") as f:
                        json.dump({
                            "meta": {
                                "target_url": url,
                                "scan_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "report_type": "Form Security Assessment (Fallback)"
                            },
                            "results": {
                                "headers": {
                                    "missing_headers": headers_content.get('missing_headers', 0),
                                    "weak_headers": headers_content.get('weak_headers', 0),
                                    "security_score": headers_content.get('security_score', 0)
                                },
                                "overall_score": comprehensive_results.get('security_score', 0)
                            },
                            "error": str(e)
                        }, f, indent=2)
                    
                    comprehensive_results["report_path"] = simple_report_dir
                    logger.info(f"Simple security report generated at: {simple_report_dir}")
                except Exception as fallback_e:
                    logger.error(f"Even fallback report generation failed: {fallback_e}")
            
            comprehensive_results["report_error"] = str(e)
            
    except Exception as e:
        logger.error(f"Error generating security report: {e}")
        logger.error(f"Report generation failed with error type: {type(e).__name__}")
        comprehensive_results["report_error"] = str(e)
        
    # Calculate security score with appropriate error handling
    try:
        security_score = calculate_security_score(comprehensive_results)
        logger.info(f"Overall security score: {security_score}/100")
        comprehensive_results["security_score"] = security_score
    except Exception as e:
        logger.error(f"Error calculating security score: {e}")
        comprehensive_results["security_score"] = 0
    
    return comprehensive_results

def calculate_security_score(results: Dict[str, Any]) -> int:
    """
    Calculate an overall security score based on findings.
    
    Args:
        results: Dictionary containing all test results
    
    Returns:
        Security score from 0-100
    """
    # Start with full score and deduct points for issues
    score = 100
    
    # Count issues by severity
    severity_counts = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0
    }
    
    # Initialize result dictionaries if they don't exist
    if not results:
        return score
    
    # SQL injection vulnerabilities (critical)
    sql_results = results.get("sql_injection_results", {})
    if sql_results is not None:
        sql_vulns = sql_results.get("sql_vulnerabilities", [])
        if sql_vulns is not None:
            severity_counts["critical"] += len(sql_vulns)
    
    # XSS vulnerabilities (critical)
    xss_results = results.get("xss_results", {})
    if xss_results is not None:
        xss_vulns = xss_results.get("xss_vulnerabilities", [])
        if xss_vulns is not None:
            severity_counts["critical"] += len(xss_vulns)
    
    # CSRF vulnerabilities (by severity)
    csrf_results = results.get("csrf_results", {})
    if csrf_results is not None:
        csrf_vulns = csrf_results.get("csrf_vulnerabilities", [])
        if csrf_vulns is not None:
            for vuln in csrf_vulns:
                severity = vuln.get("severity", "medium")
                if severity in severity_counts:
                    severity_counts[severity] += 1
    
    # Header issues (by severity)
    headers_results = results.get("headers_results", {})
    if headers_results is not None:
        security_issues = headers_results.get("security_issues", [])
        if security_issues is not None:
            for issue in security_issues:
                severity = issue.get("severity", "medium")
                if severity in severity_counts:
                    severity_counts[severity] += 1
    
    # Deduct points based on severity
    # Critical: -15 points each
    # High: -10 points each
    # Medium: -5 points each
    # Low: -1 point each
    score -= severity_counts["critical"] * 15
    score -= severity_counts["high"] * 10
    score -= severity_counts["medium"] * 5
    score -= severity_counts["low"] * 1
    
    # Ensure score doesn't go below 0
    return max(0, score) 