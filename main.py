#!/usr/bin/env python3
import json
import logging
import argparse
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional

# Import mode handlers
from mode_submit import run_submit_mode
from mode_sql_inject import run_sql_injection_mode
from mode_xss import run_xss_mode
from mode_csrf import run_csrf_mode
from mode_headers import run_headers_mode
from mode_comprehensive import run_comprehensive_mode
import utils

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("form_monkey")

# Global configuration
FORM_CONFIG = None
FORM_CONFIG_NAME = None
FORM_CONFIG_DATA = None
RANDOM_DATA = None
VERBOSITY = "balanced"

# Default configuration file path
CONFIG_FILE_PATH = "config.json"
# Try to get alternative config file path from environment
CONFIG_FILE_PATH = os.environ.get("CONFIG", CONFIG_FILE_PATH)

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Form Monkey - Automated Form Submission Tool")
    
    parser.add_argument(
        "--config", "-c", 
        help="Form configuration to use (default from form_config.json)"
    )
    parser.add_argument(
        "--mode", "-m",
        choices=["submit", "sql_inject", "xss", "csrf", "headers", "comprehensive"],
        help="Operation mode (submit, sql_inject, xss, csrf, headers, or comprehensive)"
    )
    parser.add_argument(
        "--verbosity", "-v",
        choices=["minimal", "balanced", "verbose"],
        help="Set logging verbosity level"
    )
    parser.add_argument(
        "--min-interval",
        type=int,
        help="Override minimum time (in seconds) between submissions"
    )
    parser.add_argument(
        "--max-interval",
        type=int,
        help="Override maximum time (in seconds) between submissions"
    )
    parser.add_argument(
        "--url",
        help="Override the URL from the configuration"
    )
    parser.add_argument(
        "--report-format",
        choices=["html", "json", "both"],
        help="Report format for security tests (html, json, or both)"
    )
    parser.add_argument(
        "--report-dir",
        help="Directory to save security reports"
    )
    parser.add_argument(
        "--test",
        action="append",
        choices=["sql", "xss", "csrf", "headers"],
        help="Security tests to run in comprehensive mode (can be specified multiple times)"
    )
    
    return parser.parse_args()

def load_config(config_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from config.json.
    
    Args:
        config_name: Name of the configuration to load. If None, use environment
                    variable or default.
    
    Returns:
        Dict containing the configuration.
    """
    # Try to get config name from environment if not provided as argument
    if not config_name:
        config_name = os.environ.get("FORM", "default")
    
    # Get absolute path to the config file for better logging
    abs_config_path = os.path.abspath(CONFIG_FILE_PATH)
    logger.info(f"Loading configuration '{config_name}' from file: {abs_config_path}")
    
    try:
        with open(CONFIG_FILE_PATH, "r") as f:
            all_configs = json.load(f)
            
        if config_name not in all_configs:
            logger.error(f"Configuration '{config_name}' not found in {CONFIG_FILE_PATH}")
            logger.info(f"Available configurations: {', '.join(all_configs.keys())}")
            sys.exit(1)
            
        config = all_configs[config_name]
        logger.info(f"Loaded configuration: {config_name}")
        return config
    
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {CONFIG_FILE_PATH}")
        sys.exit(1)
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in configuration file: {CONFIG_FILE_PATH}")
        sys.exit(1)

def get_operation_mode(args: argparse.Namespace, config: Dict[str, Any]) -> str:
    """
    Determine the operation mode based on command-line args, environment vars, and config.
    
    Args:
        args: Command-line arguments
        config: Configuration dictionary
    
    Returns:
        Operation mode string
    """
    # Priority: CLI args > Environment variable > Config file > Default
    if args.mode:
        return args.mode
    
    env_mode = os.environ.get("MODE")
    if env_mode in ["submit", "sql_inject", "xss", "csrf", "headers", "comprehensive"]:
        return env_mode
    
    return config.get("mode", "submit")

def get_verbosity(args: argparse.Namespace, config: Dict[str, Any]) -> str:
    """
    Determine verbosity level based on command-line args, environment vars, and config.
    
    Args:
        args: Command-line arguments
        config: Configuration dictionary
    
    Returns:
        Verbosity level string
    """
    # Priority: CLI args > Environment variable > Config file > Default
    if args.verbosity:
        return args.verbosity
    
    env_verbosity = os.environ.get("VERBOSITY")
    if env_verbosity in ["minimal", "balanced", "verbose"]:
        return env_verbosity
    
    return config.get("verbosity", "balanced")

def configure_logging(verbosity: str) -> None:
    """
    Configure logging level based on verbosity setting.
    
    Args:
        verbosity: Verbosity level ("minimal", "balanced", or "verbose")
    """
    if verbosity == "minimal":
        logger.setLevel(logging.WARNING)
    elif verbosity == "balanced":
        logger.setLevel(logging.INFO)
    elif verbosity == "verbose":
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

def apply_command_line_overrides(args: argparse.Namespace, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply command-line argument overrides to the configuration.
    
    Args:
        args: Command-line arguments
        config: Configuration dictionary
    
    Returns:
        Updated configuration dictionary
    """
    # Override URL if provided
    if args.url:
        config["url"] = args.url
    elif os.environ.get("TARGET_URL"):
        config["url"] = os.environ.get("TARGET_URL")
    
    # Override timing settings if provided
    if "timing" not in config:
        config["timing"] = {}
    
    if args.min_interval is not None:
        config["timing"]["min_interval"] = args.min_interval
    elif os.environ.get("MIN_INTERVAL"):
        try:
            config["timing"]["min_interval"] = int(os.environ.get("MIN_INTERVAL", 300))
        except ValueError:
            logger.warning("Invalid MIN_INTERVAL environment variable, using default")
    
    if args.max_interval is not None:
        config["timing"]["max_interval"] = args.max_interval
    elif os.environ.get("MAX_INTERVAL"):
        try:
            config["timing"]["max_interval"] = int(os.environ.get("MAX_INTERVAL", 2700))
        except ValueError:
            logger.warning("Invalid MAX_INTERVAL environment variable, using default")
    
    # Override security testing settings if provided
    if args.report_format or args.report_dir or args.test:
        if "comprehensive_settings" not in config:
            config["comprehensive_settings"] = {}
        
        if args.report_format:
            config["comprehensive_settings"]["report_format"] = args.report_format
        elif os.environ.get("REPORT_FORMAT"):
            config["comprehensive_settings"]["report_format"] = os.environ.get("REPORT_FORMAT")
        
        if args.report_dir:
            config["comprehensive_settings"]["report_dir"] = args.report_dir
        elif os.environ.get("REPORT_DIR"):
            config["comprehensive_settings"]["report_dir"] = os.environ.get("REPORT_DIR")
        
        if args.test:
            config["comprehensive_settings"]["tests"] = args.test
        elif os.environ.get("SECURITY_TESTS"):
            tests = os.environ.get("SECURITY_TESTS", "").split(",")
            if all(test in ["sql", "xss", "csrf", "headers"] for test in tests):
                config["comprehensive_settings"]["tests"] = tests
    
    return config

def main() -> None:
    """Main entry point for the application."""
    # Parse command-line arguments
    args = parse_arguments()
    
    # Load configuration
    config = load_config(args.config)
    
    # Determine operation mode
    mode = get_operation_mode(args, config)
    
    # Set up verbosity
    verbosity = get_verbosity(args, config)
    configure_logging(verbosity)
    
    # Apply command-line overrides
    config = apply_command_line_overrides(args, config)
    
    # Create context object to pass to mode handlers
    context = {
        "config": config,
        "logger": logger,
        "verbosity": verbosity,
    }
    
    # Run appropriate mode
    logger.info(f"Starting Form Monkey in {mode} mode")
    if mode == "submit":
        run_submit_mode(context)
    elif mode == "sql_inject":
        run_sql_injection_mode(context)
    elif mode == "xss":
        run_xss_mode(context)
    elif mode == "csrf":
        run_csrf_mode(context)
    elif mode == "headers":
        run_headers_mode(context)
    elif mode == "comprehensive":
        run_comprehensive_mode(context)
    else:
        logger.error(f"Unknown mode: {mode}")
        sys.exit(1)

if __name__ == "__main__":
    main() 