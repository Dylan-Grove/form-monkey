#!/usr/bin/env python3

import random
import os
import json
import string
import time
from typing import Dict, Any, List, Union, Optional, Tuple

# Default paths
RANDOM_DATA_PATH = "random_data.json"

def load_random_data() -> Dict[str, Any]:
    """
    Load random data from random_data.json.
    
    Returns:
        Dictionary containing random data for name generation
    """
    try:
        with open(RANDOM_DATA_PATH, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading random data: {e}")
        # Return minimal fallback data
        return {
            "first_names": ["John", "Jane", "Alex", "Sam"],
            "last_names": ["Smith", "Doe", "Johnson", "Brown"],
            "email_domains": ["example.com", "test.com"],
            "area_codes": {
                "canadian": ["416", "647", "437"],
                "american": ["212", "312", "415"]
            }
        }

def generate_name(name_type: str = "first") -> str:
    """
    Generate a random name.
    
    Args:
        name_type: Type of name to generate ("first" or "last")
    
    Returns:
        Random name
    """
    random_data = load_random_data()
    if name_type.lower() == "first":
        return random.choice(random_data.get("first_names", ["John", "Jane"]))
    else:
        return random.choice(random_data.get("last_names", ["Smith", "Doe"]))

def generate_email() -> str:
    """
    Generate a random email address.
    
    Returns:
        Random email address
    """
    random_data = load_random_data()
    first_name = generate_name("first").lower()
    last_name = generate_name("last").lower()
    domain = random.choice(random_data.get("email_domains", ["example.com"]))
    
    # Add a random number for uniqueness
    random_num = random.randint(1, 9999)
    
    # Create email with different formats
    formats = [
        f"{first_name}.{last_name}{random_num}@{domain}",
        f"{first_name}{random_num}@{domain}",
        f"{first_name[0]}{last_name}@{domain}",
        f"{first_name}_{last_name}@{domain}"
    ]
    
    return random.choice(formats)

def get_area_code(area_code_type: Optional[Union[str, List[str]]]) -> str:
    """
    Get an area code based on the specified type.
    
    Args:
        area_code_type: Area code type (e.g., "canadian", "american") or list of types
    
    Returns:
        An area code string
    """
    random_data = load_random_data()
    area_codes = random_data.get("area_codes", {})
    
    # If area_code_type is a list, randomly choose one type
    if isinstance(area_code_type, list):
        if not area_code_type:  # Empty list
            area_code_type = "canadian"  # Default
        else:
            area_code_type = random.choice(area_code_type)
    
    # If no area code type specified or invalid type, default to canadian
    if not area_code_type or area_code_type not in area_codes:
        area_code_type = "canadian"
    
    return random.choice(area_codes.get(area_code_type, ["416"]))

def generate_phone(area_code_type: Optional[Union[str, List[str]]] = None) -> str:
    """
    Generate a random phone number in the specified format.
    
    Args:
        area_code_type: Type of area code to use or list of types
    
    Returns:
        Random phone number as a string
    """
    area_code = get_area_code(area_code_type)
    exchange = random.randint(100, 999)
    line = random.randint(1000, 9999)
    
    # Format based on area code type
    if isinstance(area_code_type, list):
        selected_type = random.choice(area_code_type) if area_code_type else "canadian"
    else:
        selected_type = area_code_type or "canadian"
    
    # Create phone number with different formats based on type
    if selected_type == "american":
        return f"({area_code}) {exchange}-{line}"
    elif selected_type == "canadian":
        return f"({area_code}) {exchange}-{line}"
    elif selected_type == "uk":
        return f"+44 {area_code} {exchange} {line}"
    elif selected_type == "australian":
        return f"+61 {area_code} {exchange} {line}"
    elif selected_type == "russian":
        return f"+7 ({area_code}) {exchange}-{line}"
    elif selected_type == "chinese":
        return f"+86 {area_code} {exchange} {line}"
    elif selected_type == "mexican":
        return f"+52 ({area_code}) {exchange}-{line}"
    else:
        return f"{area_code}-{exchange}-{line}"

def get_selector_type(field_config: Dict[str, Any]) -> str:
    """
    Get the selector type for a field (CSS or XPath).
    
    Args:
        field_config: Field configuration dictionary
    
    Returns:
        Selector type string ("css" or "xpath")
    """
    return field_config.get("type", "css").lower()

def get_element_wait_time(context: Dict[str, Any]) -> int:
    """
    Get the wait time for element presence/interaction.
    
    Args:
        context: Application context
    
    Returns:
        Wait time in seconds
    """
    config = context.get("config", {})
    timing = config.get("timing", {})
    return timing.get("element_wait_time", 10)

def get_submission_interval(context: Dict[str, Any]) -> int:
    """
    Calculate a random interval between form submissions.
    
    Args:
        context: Application context
    
    Returns:
        Interval in seconds
    """
    config = context.get("config", {})
    timing = config.get("timing", {})
    
    min_interval = timing.get("min_interval", 300)  # Default: 5 minutes
    max_interval = timing.get("max_interval", 2700)  # Default: 45 minutes
    
    # Override with environment variables if present
    try:
        env_min = os.environ.get("MIN_INTERVAL")
        if env_min is not None:
            min_interval = int(env_min)
        
        env_max = os.environ.get("MAX_INTERVAL")
        if env_max is not None:
            max_interval = int(env_max)
    except (ValueError, TypeError):
        pass
    
    # Ensure min <= max
    if min_interval > max_interval:
        min_interval, max_interval = max_interval, min_interval
    
    return random.randint(min_interval, max_interval) 