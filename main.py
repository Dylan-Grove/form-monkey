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
CONFIG_FILE_PATH = "form_config.json"

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Form Monkey - Automated Form Submission Tool")
    
    parser.add_argument(
        "--config", "-c", 
        help="Form configuration to use (default from form_config.json)"
    )
    parser.add_argument(
        "--mode", "-m",
        choices=["submit", "sql_inject"],
        help="Operation mode (submit or sql_inject)"
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
    
    return parser.parse_args()

def load_config(config_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from form_config.json.
    
    Args:
        config_name: Name of the configuration to load. If None, use environment
                    variable or default.
    
    Returns:
        Dict containing the configuration.
    """
    # Try to get config name from environment if not provided as argument
    if not config_name:
        config_name = os.environ.get("FORM_CONFIG", "default")
    
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
        Operation mode string ("submit" or "sql_inject")
    """
    # Priority: CLI args > Environment variable > Config file > Default
    if args.mode:
        return args.mode
    
    env_mode = os.environ.get("MODE")
    if env_mode in ["submit", "sql_inject"]:
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
    else:
        logger.error(f"Unknown mode: {mode}")
        sys.exit(1)

if __name__ == "__main__":
    main() 