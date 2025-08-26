#!/usr/bin/env python3
"""
Configuration for Free UPC Verification System
"""

import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data"
CACHE_DIR = DATA_DIR / "upc_cache"
LOGS_DIR = BASE_DIR / "logs"

# Ensure directories exist
CACHE_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Database configuration
UPC_CACHE_DB = CACHE_DIR / "upc_cache.db"

# Free API endpoints and limits
FREE_APIS = {
    'openfoodfacts': {
        'base_url': 'https://world.openfoodfacts.org',
        'rate_limit': 1.0,  # seconds between requests
        'timeout': 10,
        'max_retries': 3
    },
    'dabs_locator': {
        'base_url': 'https://webapps2.abc.utah.gov/ProdApps/ProductLocatorCore',
        'rate_limit': 2.0,
        'timeout': 15,
        'max_retries': 2
    },
    'upcitemdb_free': {
        'base_url': 'https://api.upcitemdb.com/prod/trial/lookup',
        'rate_limit': 3.0,  # Free tier is more restrictive
        'timeout': 10,
        'max_retries': 1,
        'daily_limit': 100  # Free tier daily limit
    }
}

# Web scraping configuration
WEB_SCRAPING = {
    'user_agents': [
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    ],
    'timeout': 15,
    'max_redirects': 5,
    'retry_delay': 2.0
}

# UPC validation rules
UPC_VALIDATION = {
    'valid_lengths': [12, 13],  # UPC-A (12) and EAN-13 (13)
    'check_digit_validation': True,
    'allow_leading_zeros': True
}

# Cache configuration
CACHE_CONFIG = {
    'expiry_days': 30,  # Cache entries expire after 30 days
    'max_entries': 10000,  # Maximum cache entries
    'cleanup_interval': 7  # Days between cache cleanup
}

# Logging configuration
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': LOGS_DIR / 'upc_verification.log',
    'max_size': 10 * 1024 * 1024,  # 10MB
    'backup_count': 5
}

# Batch processing limits
BATCH_LIMITS = {
    'max_concurrent': 3,  # Maximum concurrent API requests
    'batch_size': 50,     # Items per batch
    'progress_interval': 10  # Progress updates every N items
}

# Confidence scoring weights
CONFIDENCE_WEIGHTS = {
    'single_source': 0.3,
    'multiple_sources': 0.6,
    'verified_sources': 0.9,
    'dabs_official': 1.0
}

# DABS specific configuration
DABS_CONFIG = {
    'product_locator_url': 'https://webapps2.abc.utah.gov/ProdApps/ProductLocatorCore',
    'search_timeout': 20,
    'max_search_results': 10,
    'search_retry_delay': 3.0
}

# Verifone barcode format handling
VERIFONE_CONFIG = {
    'drop_check_digit': True,  # Drop last digit for 12-digit barcodes
    'format_12_to_11': True,   # Convert 12-digit to 11-digit for Verifone
    'validate_format': True
}

# Error handling
ERROR_CONFIG = {
    'max_retries': 3,
    'retry_delay': 2.0,
    'timeout_multiplier': 1.5,
    'circuit_breaker_threshold': 5  # Failures before circuit breaker opens
}

# Performance monitoring
PERFORMANCE_CONFIG = {
    'track_response_times': True,
    'track_success_rates': True,
    'alert_slow_responses': 10.0,  # Alert if response > 10 seconds
    'alert_low_success_rate': 0.7  # Alert if success rate < 70%
}

def get_config():
    """Get complete configuration dictionary"""
    return {
        'paths': {
            'base_dir': BASE_DIR,
            'data_dir': DATA_DIR,
            'cache_dir': CACHE_DIR,
            'logs_dir': LOGS_DIR,
            'cache_db': UPC_CACHE_DB
        },
        'apis': FREE_APIS,
        'scraping': WEB_SCRAPING,
        'validation': UPC_VALIDATION,
        'cache': CACHE_CONFIG,
        'logging': LOGGING_CONFIG,
        'batch': BATCH_LIMITS,
        'confidence': CONFIDENCE_WEIGHTS,
        'dabs': DABS_CONFIG,
        'verifone': VERIFONE_CONFIG,
        'errors': ERROR_CONFIG,
        'performance': PERFORMANCE_CONFIG
    }
