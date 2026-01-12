"""
Configuration module for DSS App
Supports both local development and cloud deployment via environment variables
"""

import os
from pathlib import Path

# Base paths - can be overridden via environment variables
# For local development, uses absolute paths
# For deployment, set these via environment variables

def get_base_path():
    """Get the base path for the application"""
    env_path = os.environ.get('DSS_BASE_PATH')
    if env_path:
        return Path(env_path)
    # Default: relative to this file's location
    return Path(__file__).parent.parent


def get_data_path():
    """Get the path to the data directory"""
    env_path = os.environ.get('DSS_DATA_PATH')
    if env_path:
        return Path(env_path)
    # Default: data folder in app directory
    return get_base_path() / "data"


def get_census_path():
    """Get the path to census/CBG shape data"""
    env_path = os.environ.get('DSS_CENSUS_PATH')
    if env_path:
        return Path(env_path)
    # Default: census folder in data directory
    return get_data_path() / "census"


def get_processed_data_path():
    """Get the path to processed data files"""
    env_path = os.environ.get('DSS_PROCESSED_PATH')
    if env_path:
        return Path(env_path)
    return get_data_path() / "processed"


# Export paths for easy importing
BASE_PATH = get_base_path()
DATA_PATH = get_data_path()
CENSUS_PATH = get_census_path()
PROCESSED_PATH = get_processed_data_path()

# Debug: print paths when running in debug mode
if os.environ.get('DSS_DEBUG'):
    print(f"DSS Config:")
    print(f"  BASE_PATH: {BASE_PATH}")
    print(f"  DATA_PATH: {DATA_PATH}")
    print(f"  CENSUS_PATH: {CENSUS_PATH}")
    print(f"  PROCESSED_PATH: {PROCESSED_PATH}")
