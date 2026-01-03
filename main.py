"""
Main entry point for the crypto data collection pipeline.

INTERVIEW EXPLANATION:
This is the entry point of the application. It:
1. Initializes the agent
2. Runs the collection workflow
3. Handles top-level errors
4. Provides a simple interface to run the pipeline

In production, this might be:
- A CLI tool with arguments
- A scheduled job (cron, Airflow, etc.)
- A web service endpoint
- Part of a larger orchestration system
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agents.collector_agent import CollectorAgent
from agents.cleaner_agent import CleanerAgent
from agents.labeler_agent import LabelerAgent
from utils.logger import setup_logger

logger = setup_logger(__name__)


def main():
    """
    Main function to run the complete data pipeline.
    
    INTERVIEW EXPLANATION:
    This function orchestrates the complete pipeline:
    1. Data Collection (Phase 1)
    2. Data Cleaning (Phase 2)
    3. Data Labeling (Phase 3)
    
    This demonstrates a complete ETL (Extract, Transform, Load) pipeline.
    """
    logger.info("=" * 60)
    logger.info("DonutAI - Complete Crypto Data Pipeline")
    logger.info("Phase 1: Collection → Phase 2: Cleaning → Phase 3: Labeling")
    logger.info("=" * 60)
    
    try:
        # ============================================================
        # PHASE 1: DATA COLLECTION
        # ============================================================
        logger.info("\n" + "=" * 60)
        logger.info("PHASE 1: DATA COLLECTION")
        logger.info("=" * 60)
        
        collector_agent = CollectorAgent()
        collected_data = collector_agent.collect_all(save_to_file=True)
        
        if not collected_data:
            logger.error("No data collected. Cannot proceed with cleaning and labeling.")
            return 1
        
        print(f"\n✅ Phase 1 Complete: Collected {len(collected_data)} coins")
        
        # ============================================================
        # PHASE 2: DATA CLEANING
        # ============================================================
        logger.info("\n" + "=" * 60)
        logger.info("PHASE 2: DATA CLEANING")
        logger.info("=" * 60)
        
        cleaner_agent = CleanerAgent()
        cleaned_data = cleaner_agent.clean_all_raw_files(save_to_file=True)
        
        if not cleaned_data:
            logger.warning("No data cleaned. Proceeding with available data.")
        
        print(f"✅ Phase 2 Complete: Cleaned {len(cleaned_data)} records")
        
        # ============================================================
        # PHASE 3: DATA LABELING
        # ============================================================
        logger.info("\n" + "=" * 60)
        logger.info("PHASE 3: DATA LABELING")
        logger.info("=" * 60)
        
        labeler_agent = LabelerAgent()
        labeled_data = labeler_agent.label_all_cleaned_files(save_to_file=True)
        
        if not labeled_data:
            logger.warning("No data labeled.")
        
        print(f"✅ Phase 3 Complete: Labeled {len(labeled_data)} records")
        
        # ============================================================
        # FINAL SUMMARY
        # ============================================================
        print("\n" + "=" * 60)
        print("PIPELINE COMPLETE")
        print("=" * 60)
        print(f"\nPhase 1 - Collection:")
        collector_stats = collector_agent.get_stats()
        print(f"  - Collected: {collector_stats['successful']} coins")
        print(f"  - Data saved to: data/raw/")
        
        print(f"\nPhase 2 - Cleaning:")
        cleaner_stats = cleaner_agent.get_stats()
        print(f"  - Cleaned: {cleaner_stats['files_cleaned']} files")
        print(f"  - Data saved to: data/cleaned/")
        
        print(f"\nPhase 3 - Labeling:")
        labeler_stats = labeler_agent.get_stats()
        print(f"  - Labeled: {labeler_stats['records_labeled']} records")
        print(f"  - Data saved to: data/labeled/")
        
        print("\n" + "=" * 60)
        
        return 0  # Success exit code
        
    except KeyboardInterrupt:
        logger.info("Collection interrupted by user")
        return 130  # Standard exit code for Ctrl+C
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1  # Error exit code


if __name__ == "__main__":
    """
    INTERVIEW EXPLANATION:
    The `if __name__ == "__main__"` guard ensures:
    1. Code only runs when script is executed directly
    2. Can import this module without running main()
    3. Standard Python pattern for executable scripts
    """
    exit_code = main()
    sys.exit(exit_code)

