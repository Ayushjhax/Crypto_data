"""
Cleaner Agent - Orchestrates data cleaning workflow.

INTERVIEW EXPLANATION:
This agent coordinates the data cleaning process:
1. Loads raw data
2. Applies cleaning operations
3. Saves cleaned data
4. Tracks cleaning statistics

The agent pattern allows us to:
- Coordinate multiple cleaning steps
- Handle errors gracefully
- Track progress and statistics
- Make the workflow reusable
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from core.data_cleaner import DataCleaner
from config.settings import RAW_DATA_DIR, CLEANED_DATA_DIR
from utils.logger import setup_logger

logger = setup_logger(__name__)


class CleanerAgent:
    """
    Agent responsible for orchestrating crypto data cleaning.
    
    INTERVIEW EXPLANATION:
    This agent handles the workflow of cleaning data.
    It doesn't do the actual cleaning - it orchestrates the process.
    """
    
    def __init__(self):
        """Initialize the cleaner agent."""
        self.cleaner = DataCleaner()
        self.stats = {
            "files_processed": 0,
            "files_cleaned": 0,
            "files_failed": 0,
            "records_processed": 0,
            "records_cleaned": 0
        }
    
    def clean_file(self, filepath: Path) -> Optional[Dict[str, Any]]:
        """
        Clean data from a single file.
        
        Args:
            filepath: Path to raw data file
        
        Returns:
            Cleaned data dictionary, or None if cleaning failed
        """
        try:
            logger.info(f"Cleaning data from {filepath.name}")
            
            # Load raw data
            with open(filepath, "r") as f:
                raw_data = json.load(f)
            
            # Clean the data
            cleaned_data = self.cleaner.clean_data(raw_data)
            
            if cleaned_data:
                self.stats["files_cleaned"] += 1
                self.stats["records_cleaned"] += 1
                return cleaned_data
            else:
                self.stats["files_failed"] += 1
                logger.warning(f"Failed to clean data from {filepath.name}")
                return None
                
        except Exception as e:
            logger.error(f"Error cleaning file {filepath}: {e}")
            self.stats["files_failed"] += 1
            return None
        finally:
            self.stats["files_processed"] += 1
    
    def clean_all_raw_files(self, save_to_file: bool = True) -> List[Dict[str, Any]]:
        """
        Clean all raw data files.
        
        INTERVIEW EXPLANATION:
        This method demonstrates batch processing.
        It processes all files in the raw data directory.
        
        Args:
            save_to_file: Whether to save cleaned data to files
        
        Returns:
            List of cleaned data dictionaries
        """
        logger.info("Starting data cleaning for all raw files")
        
        # Get all JSON files from raw directory (excluding aggregated files)
        raw_files = [
            f for f in RAW_DATA_DIR.glob("*.json")
            if not f.name.startswith("all_coins")
        ]
        
        if not raw_files:
            logger.warning("No raw data files found to clean")
            return []
        
        logger.info(f"Found {len(raw_files)} files to clean")
        
        cleaned_data_list = []
        
        for filepath in raw_files:
            try:
                cleaned_data = self.clean_file(filepath)
                
                if cleaned_data:
                    cleaned_data_list.append(cleaned_data)
                    
                    # Save cleaned data
                    if save_to_file:
                        self.cleaner.save_cleaned_data(cleaned_data, format="json")
                
            except Exception as e:
                logger.error(f"Error processing {filepath.name}: {e}")
                continue
        
        # Save aggregated cleaned data
        if save_to_file and cleaned_data_list:
            self._save_aggregated_cleaned_data(cleaned_data_list)
        
        # Log summary
        self._log_summary()
        
        return cleaned_data_list
    
    def _save_aggregated_cleaned_data(self, data: List[Dict[str, Any]]):
        """Save all cleaned data in a single aggregated file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"all_coins_cleaned_{timestamp}.json"
        filepath = CLEANED_DATA_DIR / filename
        
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Saved aggregated cleaned data to {filepath}")
    
    def _log_summary(self):
        """Log cleaning summary statistics."""
        cleaning_stats = self.cleaner.get_cleaning_stats()
        
        logger.info("=" * 50)
        logger.info("CLEANING SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Files processed: {self.stats['files_processed']}")
        logger.info(f"Files cleaned: {self.stats['files_cleaned']}")
        logger.info(f"Files failed: {self.stats['files_failed']}")
        logger.info(f"Records processed: {cleaning_stats['records_processed']}")
        logger.info(f"Records cleaned: {cleaning_stats['records_cleaned']}")
        logger.info(f"Missing values handled: {cleaning_stats['missing_values_removed']}")
        logger.info(f"Outliers removed: {cleaning_stats['outliers_removed']}")
        logger.info(f"Duplicates removed: {cleaning_stats['duplicates_removed']}")
        logger.info("=" * 50)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cleaning statistics."""
        return {
            **self.stats,
            **self.cleaner.get_cleaning_stats()
        }

