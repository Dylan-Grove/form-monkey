#!/usr/bin/env python3
import os
import json
import logging
import datetime
from typing import Dict, Any, List, Optional
import markdown
import matplotlib.pyplot as plt
from matplotlib import colors
import numpy as np

def count_issues_by_severity(results: Dict[str, Any]) -> Dict[str, int]:
    """
    Count issues by severity across all test results.
    
    Args:
        results: Dictionary containing all test results
    
    Returns:
        Dictionary with counts by severity
    """
    severity_counts = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "info": 0
    }
    
    # Safety check for results
    if not results:
        return severity_counts
    
    try:
        # Get result dictionaries safely
        sql_results = results.get("sql_injection_results", {}) or {}
        xss_results = results.get("xss_results", {}) or {}
        csrf_results = results.get("csrf_results", {}) or {}
        headers_results = results.get("headers_results", {}) or {}
        
        # Count SQL injection vulnerabilities
        try:
            sql_vulns = sql_results.get("sql_vulnerabilities", []) or []
            for vuln in sql_vulns:
                severity_counts["critical"] += 1
        except Exception as e:
            print(f"Error counting SQL vulnerabilities: {e}")
        
        # Count XSS vulnerabilities
        try:
            xss_vulns = xss_results.get("xss_vulnerabilities", []) or []
            for vuln in xss_vulns:
                severity_counts["critical"] += 1
        except Exception as e:
            print(f"Error counting XSS vulnerabilities: {e}")
        
        # Count CSRF vulnerabilities
        try:
            csrf_vulns = csrf_results.get("csrf_vulnerabilities", []) or []
            for vuln in csrf_vulns:
                severity = vuln.get("severity", "medium")
                severity_counts[severity] += 1
        except Exception as e:
            print(f"Error counting CSRF vulnerabilities: {e}")
        
        # Count header issues
        try:
            security_issues = headers_results.get("security_issues", []) or []
            
            # Initialize to empty list if None
            if security_issues is None:
                security_issues = []
                
            # Convert to list if possible but not a list
            if not isinstance(security_issues, list):
                try:
                    if hasattr(security_issues, '__iter__'):
                        security_issues = list(security_issues)
                    else:
                        security_issues = []
                except:
                    security_issues = []
                    
            for issue in security_issues:
                severity = issue.get("severity", "medium")
                severity_counts[severity] += 1
        except Exception as e:
            print(f"Error counting security header issues: {e}")
            
    except Exception as e:
        print(f"Error in count_issues_by_severity: {e}")
        
    # Always return severity counts regardless of errors
    return severity_counts

def generate_severity_chart(severity_counts: Dict[str, int], output_path: str) -> str:
    """
    Generate pie chart of vulnerabilities by severity.
    
    Args:
        severity_counts: Dictionary with counts by severity
        output_path: Directory to save the chart
    
    Returns:
        Path to the generated image
    """
    # Filter out zero counts
    labels = []
    sizes = []
    
    for severity, count in severity_counts.items():
        if count > 0:
            labels.append(severity.capitalize())
            sizes.append(count)
    
    if not sizes:
        return ""
    
    # Define colors for each severity
    severity_colors = {
        "Critical": "darkred",
        "High": "red",
        "Medium": "orange",
        "Low": "yellow",
        "Info": "lightblue"
    }
    
    colors_list = [severity_colors.get(label, "gray") for label in labels]
    
    # Create pie chart
    plt.figure(figsize=(8, 6))
    plt.pie(sizes, labels=labels, colors=colors_list, autopct='%1.1f%%', shadow=True, startangle=140)
    plt.axis('equal')
    plt.title('Vulnerabilities by Severity')
    
    # Save the chart
    os.makedirs(output_path, exist_ok=True)
    chart_path = os.path.join(output_path, "severity_chart.png")
    plt.savefig(chart_path)
    plt.close()
    
    return chart_path

def generate_issue_type_chart(results: Dict[str, Any], output_path: str) -> str:
    """
    Generate bar chart of vulnerabilities by type.
    
    Args:
        results: Dictionary containing all test results
        output_path: Directory to save the chart
    
    Returns:
        Path to the generated image
    """
    # Safety check
    if not results:
        return ""
    
    try:
        # Get result dictionaries safely with extra careful handling
        sql_results = results.get("sql_injection_results", {}) or {}
        xss_results = results.get("xss_results", {}) or {}
        csrf_results = results.get("csrf_results", {}) or {}
        headers_results = results.get("headers_results", {}) or {}
        
        # Extra careful handling of potentially None values
        sql_vulns = []
        if sql_results.get("sql_vulnerabilities") is not None:
            sql_vulns = sql_results.get("sql_vulnerabilities")
            if not isinstance(sql_vulns, list):
                sql_vulns = list(sql_vulns) if hasattr(sql_vulns, '__iter__') else []
        
        xss_vulns = []
        if xss_results.get("xss_vulnerabilities") is not None:
            xss_vulns = xss_results.get("xss_vulnerabilities")
            if not isinstance(xss_vulns, list):
                xss_vulns = list(xss_vulns) if hasattr(xss_vulns, '__iter__') else []
        
        csrf_vulns = []
        if csrf_results.get("csrf_vulnerabilities") is not None:
            csrf_vulns = csrf_results.get("csrf_vulnerabilities")
            if not isinstance(csrf_vulns, list):
                csrf_vulns = list(csrf_vulns) if hasattr(csrf_vulns, '__iter__') else []
        
        security_issues = []
        if headers_results.get("security_issues") is not None:
            security_issues = headers_results.get("security_issues")
            if not isinstance(security_issues, list):
                security_issues = list(security_issues) if hasattr(security_issues, '__iter__') else []
        
        # Count issues using ultra-safe code
        missing_headers_count = 0
        weak_headers_count = 0
        insecure_cookies_count = 0
        
        for issue in security_issues:
            if not isinstance(issue, dict):
                continue
                
            issue_type = issue.get("type", "")
            if issue_type == "missing_header":
                missing_headers_count += 1
            elif issue_type == "weak_header":
                weak_headers_count += 1
            elif issue_type == "insecure_cookie":
                insecure_cookies_count += 1
        
        issue_counts = {
            "SQL Injection": len(sql_vulns),
            "XSS": len(xss_vulns),
            "CSRF": len(csrf_vulns),
            "Missing Headers": missing_headers_count,
            "Weak Headers": weak_headers_count,
            "Insecure Cookies": insecure_cookies_count
        }
        
        # Filter out zero counts
        types = []
        counts = []
        
        for issue_type, count in issue_counts.items():
            if count > 0:
                types.append(issue_type)
                counts.append(count)
        
        if not counts:
            return ""
        
        # Create bar chart
        plt.figure(figsize=(10, 6))
        bars = plt.bar(types, counts, color='skyblue')
        
        # Add count labels on top of bars
        for bar in bars:
            height = bar.get_height()
            plt.annotate(f'{height}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom')
        
        plt.xlabel('Vulnerability Type')
        plt.ylabel('Count')
        plt.title('Vulnerabilities by Type')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        # Save the chart
        os.makedirs(output_path, exist_ok=True)
        chart_path = os.path.join(output_path, "issue_type_chart.png")
        plt.savefig(chart_path)
        plt.close()
        
        return chart_path
    except Exception as e:
        # If anything goes wrong, return empty string but don't crash
        print(f"Error generating issue type chart: {str(e)}")
        return ""

def generate_html_report(results: Dict[str, Any], target_url: str, output_path: str) -> str:
    """
    Generate HTML security report with findings.
    
    Args:
        results: Dictionary containing all test results
        target_url: URL that was tested
        output_path: Directory to save the report
    
    Returns:
        Path to the generated report
    """
    # Safety check for results
    if not results:
        results = {}
    
    # Ensure all required fields exist
    if "sql_injection_results" not in results or results["sql_injection_results"] is None:
        results["sql_injection_results"] = {}
    if "xss_results" not in results or results["xss_results"] is None:
        results["xss_results"] = {}
    if "csrf_results" not in results or results["csrf_results"] is None:
        results["csrf_results"] = {}
    if "headers_results" not in results or results["headers_results"] is None:
        results["headers_results"] = {}
        
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Generate charts
    chart_dir = os.path.join(output_path, "charts")
    os.makedirs(chart_dir, exist_ok=True)
    severity_chart = generate_severity_chart(count_issues_by_severity(results), chart_dir)
    issue_chart = generate_issue_type_chart(results, chart_dir)
    
    # Start building markdown report
    markdown_content = f"""
# Security Assessment Report

## Overview

* **Target URL:** {target_url}
* **Scan Date:** {timestamp}
* **Report Type:** Form Security Assessment

## Summary of Findings

"""
    
    # Add severity summary
    severity_counts = count_issues_by_severity(results)
    total_issues = sum(severity_counts.values())
    
    if total_issues > 0:
        markdown_content += f"A total of **{total_issues} security issues** were identified:\n\n"
        
        for severity, count in severity_counts.items():
            if count > 0:
                markdown_content += f"* **{count} {severity.capitalize()}** severity issues\n"
        
        # Add chart references
        if severity_chart:
            markdown_content += "\n![Vulnerabilities by Severity](charts/severity_chart.png)\n"
        
        if issue_chart:
            markdown_content += "\n![Vulnerabilities by Type](charts/issue_type_chart.png)\n"
    else:
        markdown_content += "No security issues were identified during the assessment.\n"
    
    # Detailed findings
    markdown_content += "\n## Detailed Findings\n\n"
    
    # SQL Injection findings
    sql_injection_results = results.get("sql_injection_results", {}) or {}
    sql_vulnerabilities = sql_injection_results.get("sql_vulnerabilities", []) or []
    if sql_vulnerabilities:
        markdown_content += "### SQL Injection Vulnerabilities\n\n"
        
        for i, vuln in enumerate(sql_vulnerabilities, 1):
            markdown_content += f"#### {i}. SQL Injection in field '{vuln.get('field')}'\n\n"
            markdown_content += f"* **Payload:** `{vuln.get('payload')}`\n"
            markdown_content += f"* **Pattern Matched:** {vuln.get('pattern_matched')}\n"
            markdown_content += "* **Severity:** Critical\n"
            markdown_content += f"* **URL:** {vuln.get('url')}\n\n"
            markdown_content += """**Recommendation:** Implement parameterized queries or prepared statements. 
            Never use user input directly in SQL queries. Apply input validation and sanitization.\n\n"""
    
    # XSS findings
    xss_results = results.get("xss_results", {}) or {}
    xss_vulnerabilities = xss_results.get("xss_vulnerabilities", []) or []
    if xss_vulnerabilities:
        markdown_content += "### Cross-Site Scripting (XSS) Vulnerabilities\n\n"
        
        for i, vuln in enumerate(xss_vulnerabilities, 1):
            markdown_content += f"#### {i}. XSS in field '{vuln.get('field')}'\n\n"
            markdown_content += f"* **Payload:** `{vuln.get('payload')}`\n"
            markdown_content += f"* **Type:** {vuln.get('type')}\n"
            markdown_content += f"* **Details:** {vuln.get('details')}\n"
            markdown_content += "* **Severity:** Critical\n"
            markdown_content += f"* **URL:** {vuln.get('url')}\n\n"
            markdown_content += """**Recommendation:** Implement proper output encoding and input validation. 
            Consider using a Content Security Policy (CSP) and modern frameworks that automatically escape output.\n\n"""
    
    # CSRF findings
    csrf_results = results.get("csrf_results", {}) or {}
    csrf_vulnerabilities = csrf_results.get("csrf_vulnerabilities", []) or []
    if csrf_vulnerabilities:
        markdown_content += "### Cross-Site Request Forgery (CSRF) Vulnerabilities\n\n"
        
        for i, vuln in enumerate(csrf_vulnerabilities, 1):
            markdown_content += f"#### {i}. {vuln.get('type', '').replace('_', ' ').title()}\n\n"
            markdown_content += f"* **Details:** {vuln.get('details')}\n"
            markdown_content += f"* **Severity:** {vuln.get('severity', 'medium').capitalize()}\n"
            markdown_content += f"* **URL:** {vuln.get('url')}\n\n"
            markdown_content += """**Recommendation:** Implement anti-CSRF tokens for all state-changing operations. 
            Use SameSite cookie attribute and consider adding custom headers for AJAX requests.\n\n"""
    
    # Header security issues
    headers_results = results.get("headers_results", {}) or {}
    header_issues = headers_results.get("security_issues")
    if header_issues is None:
        header_issues = []
    # Add additional type safety for header_issues
    elif not isinstance(header_issues, list):
        try:
            if hasattr(header_issues, '__iter__'):
                header_issues = list(header_issues)
            else:
                header_issues = []
        except:
            header_issues = []
    
    if header_issues:
        markdown_content += "### Security Header Issues\n\n"
        
        for i, issue in enumerate(header_issues, 1):
            if not isinstance(issue, dict):
                continue
                
            issue_type = issue.get("type", "").replace("_", " ").title()
            
            if issue.get("type") == "missing_header":
                markdown_content += f"#### {i}. Missing Header: {issue.get('header')}\n\n"
                markdown_content += f"* **Description:** {issue.get('description')}\n"
                markdown_content += f"* **Recommendation:** {issue.get('recommendation')}\n"
                markdown_content += f"* **Severity:** {issue.get('severity', 'medium').capitalize()}\n"
                markdown_content += f"* **Reference:** [{issue.get('header')} Documentation]({issue.get('reference', '#')})\n\n"
            
            elif issue.get("type") == "weak_header":
                markdown_content += f"#### {i}. Weak Header: {issue.get('header')}\n\n"
                markdown_content += f"* **Current Value:** `{issue.get('value')}`\n"
                markdown_content += f"* **Issue:** {issue.get('issue')}\n"
                markdown_content += f"* **Recommendation:** {issue.get('recommendation')}\n"
                markdown_content += f"* **Severity:** {issue.get('severity', 'medium').capitalize()}\n\n"
            
            elif issue.get("type") == "insecure_cookie":
                cookie_issues = issue.get('issues', [])
                if not isinstance(cookie_issues, list):
                    cookie_issues = []
                    
                markdown_content += f"#### {i}. Insecure Cookie: {issue.get('cookie')}\n\n"
                markdown_content += f"* **Issues:** {', '.join(cookie_issues)}\n"
                markdown_content += f"* **Recommendation:** {issue.get('recommendation')}\n"
                markdown_content += f"* **Severity:** {issue.get('severity', 'medium').capitalize()}\n\n"
    
    # Recommendations section
    markdown_content += "## General Security Recommendations\n\n"
    
    markdown_content += """### Input Validation
* Implement server-side input validation for all form fields
* Validate data type, length, format, and range
* Use allowlist validation when possible
* Apply context-specific encoding and escaping

### Output Encoding
* Apply HTML encoding for HTML contexts
* Apply JavaScript encoding for JavaScript contexts
* Apply CSS encoding for CSS contexts
* Apply URL encoding for URL parameters

### Authentication & Session Management
* Implement secure password policies
* Use HTTPS for all authentication traffic
* Set secure, HttpOnly, and SameSite flags on sensitive cookies
* Implement account lockout after failed login attempts
* Consider multi-factor authentication for sensitive operations

### Security Headers
* Implement Content Security Policy (CSP)
* Add X-Content-Type-Options: nosniff
* Add X-Frame-Options: DENY or SAMEORIGIN
* Add Strict-Transport-Security with appropriate max-age
* Add X-XSS-Protection: 1; mode=block
* Add Referrer-Policy: strict-origin-when-cross-origin

### Error Handling
* Implement custom error pages
* Avoid exposing sensitive information in error messages
* Log errors securely without exposing sensitive data

### Database Security
* Use parameterized queries for all database interactions
* Apply the principle of least privilege to database users
* Consider using an ORM that handles SQL escaping
* Encrypt sensitive data stored in the database
"""
    
    # Generate HTML from markdown
    html_content = markdown.markdown(markdown_content, extensions=['tables'])
    
    # Add CSS styling
    styled_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Security Assessment Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1, h2, h3, h4 {{
            color: #2c3e50;
        }}
        h1 {{
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            border-bottom: 1px solid #3498db;
            padding-bottom: 5px;
            margin-top: 30px;
        }}
        h3 {{
            margin-top: 25px;
        }}
        h4 {{
            margin-top: 20px;
        }}
        img {{
            max-width: 100%;
            height: auto;
            margin: 20px 0;
        }}
        code {{
            background-color: #f8f8f8;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: monospace;
            color: #e74c3c;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 10px;
            text-align: left;
        }}
        th {{
            background-color: #f2f2f2;
        }}
        .severity-critical {{
            color: darkred;
            font-weight: bold;
        }}
        .severity-high {{
            color: red;
            font-weight: bold;
        }}
        .severity-medium {{
            color: orange;
        }}
        .severity-low {{
            color: #997300;
        }}
        .footer {{
            margin-top: 50px;
            border-top: 1px solid #ddd;
            padding-top: 20px;
            color: #777;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    {html_content}
    <div class="footer">
        <p>Generated by Form Monkey Security Scanner on {timestamp}</p>
    </div>
</body>
</html>
"""
    
    # Create output directory if it doesn't exist
    os.makedirs(output_path, exist_ok=True)
    
    # Save the HTML report
    report_path = os.path.join(output_path, "security_report.html")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(styled_html)
    
    return report_path

def generate_json_report(results: Dict[str, Any], target_url: str, output_path: str) -> str:
    """
    Generate JSON security report with findings.
    
    Args:
        results: Dictionary containing all test results
        target_url: URL that was tested
        output_path: Directory to save the report
    
    Returns:
        Path to the generated report
    """
    # Create report structure
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Ensure header_issues is properly initialized
    headers_results = results.get("headers_results", {}) or {}
    security_issues = headers_results.get("security_issues")
    if security_issues is None:
        security_issues = []
    elif not isinstance(security_issues, list):
        try:
            if hasattr(security_issues, '__iter__'):
                security_issues = list(security_issues)
            else:
                security_issues = []
        except:
            security_issues = []
    
    # Now use the safe security_issues in the report
    report = {
        "meta": {
            "target_url": target_url,
            "scan_date": timestamp,
            "report_type": "Form Security Assessment"
        },
        "summary": {
            "severity_counts": count_issues_by_severity(results),
            "total_issues": sum(count_issues_by_severity(results).values())
        },
        "findings": {
            "sql_injection": results.get("sql_injection_results", {}).get("sql_vulnerabilities", []),
            "xss": results.get("xss_results", {}).get("xss_vulnerabilities", []),
            "csrf": results.get("csrf_results", {}).get("csrf_vulnerabilities", []),
            "header_issues": security_issues
        },
        "raw_results": results
    }
    
    # Create output directory if it doesn't exist
    os.makedirs(output_path, exist_ok=True)
    
    # Save the JSON report
    report_path = os.path.join(output_path, "security_report.json")
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    return report_path

def generate_report(
    results: Dict[str, Any],
    target_url: str,
    output_path: str = "reports",
    format: str = "html"
) -> str:
    """
    Generate a security report in the specified format.
    
    Args:
        results: Dictionary containing all test results
        target_url: URL that was tested
        output_path: Directory to save the report
        format: Report format ("html", "json", or "both")
    
    Returns:
        Path to the generated report
    """
    # Safety check for results
    if not results:
        results = {}
    
    # Ensure all results objects exist
    if "sql_injection_results" not in results or results["sql_injection_results"] is None:
        results["sql_injection_results"] = {}
    if "xss_results" not in results or results["xss_results"] is None:
        results["xss_results"] = {}
    if "csrf_results" not in results or results["csrf_results"] is None:
        results["csrf_results"] = {}
    if "headers_results" not in results or results["headers_results"] is None:
        results["headers_results"] = {}
        
    # Create timestamp-based directory
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = os.path.join(output_path, f"report_{timestamp}")
    
    # Create output directory if it doesn't exist
    try:
        os.makedirs(report_dir, exist_ok=True)
    except Exception as e:
        print(f"Error creating report directory: {e}")
        # Fallback to a simple directory name if there's an issue
        report_dir = os.path.join(output_path, "security_report")
        os.makedirs(report_dir, exist_ok=True)
    
    html_path = ""
    json_path = ""
    
    # Additional sanity checks for headers_results
    if "headers_results" in results and results["headers_results"] is not None:
        if "security_issues" not in results["headers_results"] or results["headers_results"]["security_issues"] is None:
            results["headers_results"]["security_issues"] = []
    
    if format.lower() == "html" or format.lower() == "both":
        try:
            html_path = generate_html_report(results, target_url, report_dir)
            print(f"Generated HTML report at: {html_path}")
        except Exception as e:
            print(f"Error generating HTML report: {e}")
            # Generate a simple fallback HTML report
            try:
                fallback_html_path = os.path.join(report_dir, "security_report_fallback.html")
                with open(fallback_html_path, 'w') as f:
                    f.write(f"""
                    <!DOCTYPE html>
                    <html>
                    <head><title>Security Report</title></head>
                    <body>
                        <h1>Security Assessment Report</h1>
                        <p>Target URL: {target_url}</p>
                        <p>Scan Date: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                        <p>Error generating full report: {str(e)}</p>
                    </body>
                    </html>
                    """)
                html_path = fallback_html_path
            except:
                # If even fallback fails, just continue
                pass
        
    if format.lower() == "json" or format.lower() == "both":
        try:
            json_path = generate_json_report(results, target_url, report_dir)
            print(f"Generated JSON report at: {json_path}")
        except Exception as e:
            print(f"Error generating JSON report: {e}")
            # Generate a simple fallback JSON report
            try:
                fallback_json_path = os.path.join(report_dir, "security_report_fallback.json")
                with open(fallback_json_path, 'w') as f:
                    json.dump({
                        "error": str(e),
                        "target_url": target_url,
                        "scan_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }, f)
                json_path = fallback_json_path
            except:
                # If even fallback fails, just continue
                pass
    
    # Return the appropriate path
    if format.lower() == "both":
        return report_dir
    elif format.lower() == "html":
        return html_path
    else:  # json
        return json_path 