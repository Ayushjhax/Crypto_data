"""
Labeler Agent - Orchestrates data labeling workflow.

INTERVIEW EXPLANATION:
This agent coordinates the data labeling process:
1. Loads cleaned data
2. Applies labeling rules
3. Saves labeled data
4. Tracks labeling statistics
"""

import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from core.data_labeler import DataLabeler
from config.settings import CLEANED_DATA_DIR, LABELED_DATA_DIR
from utils.logger import setup_logger

logger = setup_logger(__name__)


class LabelerAgent:
    """
    Agent responsible for orchestrating crypto data labeling.
    
    INTERVIEW EXPLANATION:
    This agent handles the workflow of labeling data.
    It orchestrates the labeling process without doing the actual labeling.
    """
    
    def __init__(self):
        """Initialize the labeler agent."""
        self.labeler = DataLabeler()
        self.stats = {
            "files_processed": 0,
            "files_labeled": 0,
            "files_failed": 0,
            "records_labeled": 0
        }
    
    def label_file(self, filepath: Path) -> Dict[str, Any]:
        """
        Label data from a single cleaned file.
        
        Args:
            filepath: Path to cleaned data file
        
        Returns:
            Labeled data dictionary
        """
        try:
            logger.info(f"Labeling data from {filepath.name}")
            
            # Load cleaned data
            with open(filepath, "r") as f:
                cleaned_data = json.load(f)
            
            # Label the data
            labeled_data = self.labeler.label_data(cleaned_data)
            
            self.stats["files_labeled"] += 1
            self.stats["records_labeled"] += 1
            
            return labeled_data
                
        except Exception as e:
            logger.error(f"Error labeling file {filepath}: {e}")
            self.stats["files_failed"] += 1
            return {}
        finally:
            self.stats["files_processed"] += 1
    
    def label_all_cleaned_files(self, save_to_file: bool = True) -> List[Dict[str, Any]]:
        """
        Label all cleaned data files.
        
        INTERVIEW EXPLANATION:
        This method processes all cleaned files and adds labels.
        
        Args:
            save_to_file: Whether to save labeled data to files
        
        Returns:
            List of labeled data dictionaries
        """
        logger.info("Starting data labeling for all cleaned files")
        
        # Get all JSON files from cleaned directory (excluding aggregated files)
        cleaned_files = [
            f for f in CLEANED_DATA_DIR.glob("*.json")
            if not f.name.startswith("all_coins")
        ]
        
        if not cleaned_files:
            logger.warning("No cleaned data files found to label")
            return []
        
        logger.info(f"Found {len(cleaned_files)} files to label")
        
        labeled_data_list = []
        
        for filepath in cleaned_files:
            try:
                labeled_data = self.label_file(filepath)
                
                if labeled_data:
                    labeled_data_list.append(labeled_data)
                    
                    # Save labeled data
                    if save_to_file:
                        self.labeler.save_labeled_data(labeled_data, format="json")
                
            except Exception as e:
                logger.error(f"Error processing {filepath.name}: {e}")
                continue
        
        # Save aggregated labeled data
        if save_to_file and labeled_data_list:
            self._save_aggregated_labeled_data(labeled_data_list)
        
        # Log summary
        self._log_summary()
        
        return labeled_data_list
    
    def _save_aggregated_labeled_data(self, data: List[Dict[str, Any]]):
        """Save all labeled data in a single aggregated file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"all_coins_labeled_{timestamp}.json"
        filepath = LABELED_DATA_DIR / filename
        
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Saved aggregated labeled data to {filepath}")
    
    def _log_summary(self):
        """Log labeling summary statistics."""
        labeling_stats = self.labeler.get_labeling_stats()
        
        logger.info("=" * 50)
        logger.info("LABELING SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Files processed: {self.stats['files_processed']}")
        logger.info(f"Files labeled: {self.stats['files_labeled']}")
        logger.info(f"Files failed: {self.stats['files_failed']}")
        logger.info(f"Records labeled: {labeling_stats['records_labeled']}")
        logger.info(f"Labels created: {labeling_stats['labels_created']}")
        logger.info("=" * 50)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get labeling statistics."""
        return {
            **self.stats,
            **self.labeler.get_labeling_stats()
        }

