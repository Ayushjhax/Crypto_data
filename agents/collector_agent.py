"""
Collector Agent - Orchestrates data collection workflow.

INTERVIEW EXPLANATION:
This agent demonstrates the "Agent Pattern" or "Orchestrator Pattern":

1. COORDINATION: The agent coordinates multiple steps:
   - Loading configuration
   - Initializing collectors
   - Collecting data
   - Saving data
   - Error handling

2. WORKFLOW MANAGEMENT: Handles the "how" of data collection
   - When to collect
   - What to collect
   - How to handle failures
   - How to report progress

3. SEPARATION OF CONCERNS:
   - Agent: Workflow and orchestration
   - Core: Business logic (DataCollector)
   - Config: Settings and parameters

This pattern is common in:
- Data pipelines
- Microservices orchestration
- Workflow engines
- ETL processes
"""

import yaml
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from core.data_collector import DataCollector
from config.settings import RAW_DATA_DIR
from utils.logger import setup_logger

logger = setup_logger(__name__)


class CollectorAgent:
    """
    Agent responsible for orchestrating crypto data collection.
    
    INTERVIEW EXPLANATION:
    This class is an "Agent" because it:
    1. Makes decisions about what to collect
    2. Coordinates multiple operations
    3. Handles errors and retries at a high level
    4. Reports on progress and results
    
    It's different from DataCollector because:
    - DataCollector: Low-level API communication
    - CollectorAgent: High-level workflow management
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the collector agent.
        
        INTERVIEW EXPLANATION:
        The agent loads configuration and initializes the core collector.
        This is dependency injection - the agent depends on DataCollector.
        """
        # Load configuration
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "data_sources.yaml"
        
        self.config = self._load_config(config_path)
        
        # Initialize core collector
        from config.settings import FREECRYPTO_API_KEY, FREECRYPTO_API_BASE_URL
        self.collector = DataCollector(
            api_key=FREECRYPTO_API_KEY,
            base_url=FREECRYPTO_API_BASE_URL
        )
        
        # Track collection statistics
        self.stats = {
            "total_collections": 0,
            "successful": 0,
            "failed": 0,
            "coins_collected": []
        }
    
    def _load_config(self, config_path: Path) -> Dict[str, Any]:
        """
        Load configuration from YAML file.
        
        INTERVIEW EXPLANATION:
        Configuration files (YAML, JSON) are better than hardcoding because:
        1. No code changes needed to modify behavior
        2. Version control friendly
        3. Can have different configs for different environments
        4. Non-technical users can modify settings
        """
        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded configuration from {config_path}")
            return config
        except FileNotFoundError:
            logger.error(f"Config file not found: {config_path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML: {e}")
            raise
    
    def get_coins_to_collect(self) -> List[str]:
        """
        Extract list of coin symbols from configuration.
        
        INTERVIEW EXPLANATION:
        This method demonstrates data extraction from configuration.
        It makes the agent flexible - can change coins without code changes.
        """
        coins = []
        try:
            data_sources = self.config.get("data_sources", {})
            freecrypto = data_sources.get("freecryptoapi", {})
            endpoints = freecrypto.get("endpoints", {})
            coin_list = endpoints.get("coins", [])

            for coin in coin_list:
                if isinstance(coin, dict):
                    coins.append(coin.get("symbol"))
                elif isinstance(coin, str):
                    coins.append(coin)
            
            logger.info(f"Found {len(coins)} coins to collect: {coins}")
            return coins
        except Exception as e:
            logger.error(f"Error extracting coins from config: {e}")
            # Fallback to default coins
            return ["BTC", "ETH", "BNB"]
    
    def collect_all(self, save_to_file: bool = True) -> List[Dict[str, Any]]:
        """
        Main method: Collect data for all configured coins.
        
        INTERVIEW EXPLANATION:
        This is the main orchestration method. It:
        1. Gets the list of coins to collect
        2. Collects data for each
        3. Saves data if requested
        4. Tracks statistics
        5. Handles errors gracefully
        
        This method demonstrates:
        - Error handling (try/except)
        - Resource management (finally block)
        - Progress tracking
        - Result aggregation
        """
        logger.info("Starting data collection for all coins")
        
        coins = self.get_coins_to_collect()
        collected_data = []
        
        try:
            # Collect data for each coin
            for symbol in coins:
                try:
                    logger.info(f"Collecting data for {symbol}...")
                    data = self.collector.collect_coin_data(symbol)
                    
                    if data:
                        collected_data.append(data)
                        self.stats["successful"] += 1
                        self.stats["coins_collected"].append(symbol)
                        
                        # Save individual coin data
                        if save_to_file:
                            self.collector.save_data(data, format="json")
                    else:
                        self.stats["failed"] += 1
                        logger.warning(f"Failed to collect data for {symbol}")
                    
                    self.stats["total_collections"] += 1
                    
                except Exception as e:
                    logger.error(f"Error collecting {symbol}: {e}")
                    self.stats["failed"] += 1
                    continue  # Continue with next coin even if one fails
            
            # Save aggregated data
            if save_to_file and collected_data:
                self._save_aggregated_data(collected_data)
            
            # Log summary
            self._log_summary()
            
        except Exception as e:
            logger.error(f"Fatal error during collection: {e}")
            raise
        finally:
            # Clean up resources
            self.collector.close()
        
        return collected_data
    
    def _save_aggregated_data(self, data: List[Dict[str, Any]]):
        """
        Save all collected data in a single aggregated file.
        
        INTERVIEW EXPLANATION:
        Aggregated files are useful for:
        1. Batch processing
        2. Analysis
        3. Creating datasets
        4. Backup
        
        We save both individual files (for granularity) and aggregated
        (for convenience).
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"all_coins_{timestamp}.json"
        filepath = RAW_DATA_DIR / filename
        
        import json
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Saved aggregated data to {filepath}")
    
    def _log_summary(self):
        """
        Log collection summary statistics.
        
        INTERVIEW EXPLANATION:
        Logging summaries is important for:
        1. Monitoring: Know if collection is working
        2. Debugging: Identify patterns in failures
        3. Reporting: Track success rates over time
        """
        logger.info("=" * 50)
        logger.info("COLLECTION SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Total collections attempted: {self.stats['total_collections']}")
        logger.info(f"Successful: {self.stats['successful']}")
        logger.info(f"Failed: {self.stats['failed']}")
        logger.info(f"Success rate: {self.stats['successful'] / max(self.stats['total_collections'], 1) * 100:.1f}%")
        logger.info(f"Coins collected: {', '.join(self.stats['coins_collected'])}")
        logger.info("=" * 50)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        return self.stats.copy()

