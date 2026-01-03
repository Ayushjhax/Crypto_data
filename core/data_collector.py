"""
Core data collection logic.

INTERVIEW EXPLANATION:
This module contains the core business logic for data collection.
It's separated from the agent layer because:

1. SINGLE RESPONSIBILITY: This class only handles API communication
2. TESTABILITY: Can test collection logic without agent complexity
3. REUSABILITY: Can be used by different agents or scripts
4. MAINTAINABILITY: Changes to API logic are isolated here

Key concepts demonstrated:
- HTTP requests with error handling
- Rate limiting
- Retry logic with exponential backoff
- Data transformation
- File I/O operations
"""

import time
import requests
from typing import Dict, List, Optional, Any
from pathlib import Path
import json
from datetime import datetime
import pandas as pd

from config.settings import (
    FREECRYPTO_API_KEY,
    FREECRYPTO_API_BASE_URL,
    MAX_RETRIES,
    REQUEST_TIMEOUT,
    RAW_DATA_DIR
)
from utils.logger import setup_logger
from utils.validators import validate_api_response, validate_crypto_data

logger = setup_logger(__name__)


class DataCollector:
    """
    Core data collector for crypto data from FreeCryptoAPI.
    
    INTERVIEW EXPLANATION:
    This is a class-based design. Why use a class?
    1. State Management: Can store API key, session, rate limit state
    2. Encapsulation: Groups related methods together
    3. Reusability: Can create multiple instances with different configs
    4. Testability: Can mock the class in tests
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: str = FREECRYPTO_API_BASE_URL,
        max_retries: int = MAX_RETRIES,
        timeout: int = REQUEST_TIMEOUT
    ):
        """
        Initialize the data collector.
        
        INTERVIEW EXPLANATION:
        Constructor (__init__) sets up the object's initial state.
        We use dependency injection (passing api_key as parameter) so:
        1. Can use different API keys for different instances
        2. Easy to test with mock API keys
        3. Follows dependency inversion principle
        """
        self.api_key = api_key
        self.base_url = base_url
        self.max_retries = max_retries
        self.timeout = timeout
        
        # Session object for connection pooling
        # INTERVIEW EXPLANATION: requests.Session() reuses TCP connections
        # This is more efficient than requests.get() which creates new connections
        self.session = requests.Session()
        # FreeCryptoAPI uses Bearer token authentication
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })
        
        # Rate limiting state
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Minimum seconds between requests
    
    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        retry_count: int = 0
    ) -> Optional[Dict[str, Any]]:
        """
        Make HTTP request with retry logic and error handling.
        
        INTERVIEW EXPLANATION:
        The underscore prefix (_make_request) indicates this is a private method.
        It's an internal implementation detail, not part of the public API.
        
        Key concepts:
        1. RETRY LOGIC: Handles transient failures (network issues)
        2. EXPONENTIAL BACKOFF: Wait longer between retries
        3. ERROR HANDLING: Catches and logs specific error types
        4. RATE LIMITING: Prevents overwhelming the API
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            retry_count: Current retry attempt
        
        Returns:
            JSON response as dictionary, or None if failed
        """
        # Rate limiting: ensure minimum time between requests
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            logger.debug(f"Making request to {url} (attempt {retry_count + 1})")
            response = self.session.get(
                url,
                params=params,
                timeout=self.timeout
            )
            self.last_request_time = time.time()
            
            # Check HTTP status code
            # INTERVIEW EXPLANATION: Status codes indicate request outcome
            # 200: Success
            # 400: Bad request (client error)
            # 401: Unauthorized (authentication failed)
            # 429: Too many requests (rate limit exceeded)
            # 500: Server error
            response.raise_for_status()  # Raises exception for 4xx/5xx codes
            
            data = response.json()
            
            # Validate response structure
            if not validate_api_response(data):
                logger.warning(f"Invalid API response structure from {url}")
                return None
            
            return data
            
        except requests.exceptions.Timeout:
            logger.error(f"Request timeout for {url}")
            if retry_count < self.max_retries:
                return self._make_request(endpoint, params, retry_count + 1)
            return None
            
        except requests.exceptions.HTTPError as e:
            # INTERVIEW EXPLANATION: Different error codes need different handling
            if e.response.status_code == 429:  # Rate limited
                wait_time = 2 ** retry_count  # Exponential backoff
                logger.warning(f"Rate limited. Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
                if retry_count < self.max_retries:
                    return self._make_request(endpoint, params, retry_count + 1)
            
            logger.error(f"HTTP error {e.response.status_code} for {url}: {e}")
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {url}: {e}")
            if retry_count < self.max_retries:
                wait_time = 2 ** retry_count  # Exponential backoff
                time.sleep(wait_time)
                return self._make_request(endpoint, params, retry_count + 1)
            return None
            
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON response from {url}")
            return None
    
    def collect_coin_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Collect current data for a specific cryptocurrency.
        
        INTERVIEW EXPLANATION:
        This is a public method - part of the class's API.
        It's the main method callers will use.
        
        Args:
            symbol: Cryptocurrency symbol (e.g., "BTC", "ETH")
        
        Returns:
            Dictionary with coin data, or None if collection failed
        """
        logger.info(f"Collecting data for {symbol}")
        
        # FreeCryptoAPI endpoint format: /getData?symbol={symbol}
        endpoint = "getData"
        params = {"symbol": symbol}
        
        data = self._make_request(endpoint, params=params)
        
        if not data:
            logger.warning(f"Failed to collect data for {symbol}")
            return None
        
        # Transform data to standard format
        # INTERVIEW EXPLANATION: Data transformation ensures consistent structure
        # regardless of API response format
        transformed_data = self._transform_coin_data(data, symbol)
        
        # Validate transformed data
        is_valid, error_msg = validate_crypto_data(transformed_data)
        if not is_valid:
            logger.error(f"Validation failed for {symbol}: {error_msg}")
            return None
        
        return transformed_data
    
    def _transform_coin_data(self, raw_data: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """
        Transform API response to standard format.
        
        INTERVIEW EXPLANATION:
        Data transformation is crucial because:
        1. APIs have different response formats
        2. We want consistent data structure internally
        3. Makes downstream processing easier
        
        This method adapts to the actual API response structure.
        FreeCryptoAPI format: {"status": "success", "symbols": [{"symbol": "BTC", "last": "89870.03", ...}]}
        """
        # Add timestamp for when data was collected
        timestamp = datetime.now().isoformat()
        
        # FreeCryptoAPI format: {"status": "success", "symbols": [...]}
        coin_data = None
        if raw_data.get("status") == "success" and "symbols" in raw_data:
            symbols_list = raw_data["symbols"]
            if isinstance(symbols_list, list) and len(symbols_list) > 0:
                # Find the matching symbol in the list
                for coin in symbols_list:
                    if coin.get("symbol") == symbol:
                        coin_data = coin
                        break
                # If not found, use first item
                if not coin_data and len(symbols_list) > 0:
                    coin_data = symbols_list[0]
        elif "data" in raw_data:
            coin_data = raw_data["data"]
        elif "result" in raw_data:
            coin_data = raw_data["result"]
        else:
            coin_data = raw_data
        
        if not coin_data:
            raise ValueError(f"No coin data found in API response for {symbol}")
        
        # Extract and convert fields from FreeCryptoAPI format
        # Prices come as strings, need to convert to float
        price_str = coin_data.get("last") or coin_data.get("price") or "0"
        try:
            price = float(price_str)
        except (ValueError, TypeError):
            price = 0.0
        
        # Extract other fields
        lowest_str = coin_data.get("lowest") or "0"
        highest_str = coin_data.get("highest") or "0"
        change_str = coin_data.get("daily_change_percentage") or coin_data.get("price_change_24h") or "0"
        
        try:
            lowest = float(lowest_str)
        except (ValueError, TypeError):
            lowest = None
        
        try:
            highest = float(highest_str)
        except (ValueError, TypeError):
            highest = None
        
        try:
            price_change_24h = float(change_str)
        except (ValueError, TypeError):
            price_change_24h = None
        
        # Standard format
        transformed = {
            "symbol": coin_data.get("symbol") or symbol,
            "timestamp": timestamp,
            "price": price,
            "lowest_24h": lowest,
            "highest_24h": highest,
            "price_change_24h": price_change_24h,
            "source_exchange": coin_data.get("source_exchange"),
            "date": coin_data.get("date"),
            "raw_data": raw_data  # Keep raw data for debugging
        }
        
        return transformed
    
    def save_data(
        self,
        data: Dict[str, Any],
        filename: Optional[str] = None,
        format: str = "json"
    ) -> Path:
        """
        Save collected data to file.
        
        INTERVIEW EXPLANATION:
        Why save raw data?
        1. Audit trail: Can see what was collected
        2. Reproducibility: Can replay data collection
        3. Debugging: Can inspect raw API responses
        4. Backup: Don't lose data if processing fails
        
        Args:
            data: Data dictionary to save
            filename: Optional custom filename
            format: File format ("json" or "csv")
        
        Returns:
            Path to saved file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        symbol = data.get("symbol", "unknown")
        
        if not filename:
            filename = f"{symbol}_{timestamp}.{format}"
        
        filepath = RAW_DATA_DIR / filename
        
        if format == "json":
            with open(filepath, "w") as f:
                json.dump(data, f, indent=2)
        elif format == "csv":
            # Convert single record to DataFrame
            df = pd.DataFrame([data])
            df.to_csv(filepath, index=False)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        logger.info(f"Saved data to {filepath}")
        return filepath
    
    def collect_multiple_coins(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """
        Collect data for multiple cryptocurrencies.
        
        INTERVIEW EXPLANATION:
        This method demonstrates batch processing.
        It collects data for multiple coins sequentially.
        
        For production, you might want to:
        1. Use threading/async for parallel requests
        2. Add progress tracking
        3. Handle partial failures gracefully
        
        Args:
            symbols: List of cryptocurrency symbols
        
        Returns:
            List of collected data dictionaries
        """
        results = []
        
        for symbol in symbols:
            data = self.collect_coin_data(symbol)
            if data:
                results.append(data)
            else:
                logger.warning(f"Skipping {symbol} due to collection failure")
            
            # Small delay between requests to be respectful
            time.sleep(0.5)
        
        logger.info(f"Collected data for {len(results)}/{len(symbols)} coins")
        return results
    
    def close(self):
        """
        Clean up resources.
        
        INTERVIEW EXPLANATION:
        Always clean up resources (close connections, files, etc.)
        This is good practice, especially for long-running processes.
        """
        self.session.close()
        logger.debug("DataCollector session closed")

