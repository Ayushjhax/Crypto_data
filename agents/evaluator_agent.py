"""
Evaluator Agent - Orchestrates evaluation workflow.

INTERVIEW EXPLANATION:
This agent coordinates the evaluation process, integrates with the database,
and manages the workflow of evaluating data from all pipeline stages.

Agent Pattern:
- Collector Agent: Collects data
- Cleaner Agent: Cleans data
- Labeler Agent: Labels data
- Evaluator Agent (this): Evaluates the quality of all the above
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from core.data_evaluator import DataEvaluator
from database.models import DatabaseManager, Evaluation
from config.settings import RAW_DATA_DIR, CLEANED_DATA_DIR, LABELED_DATA_DIR
from utils.logger import setup_logger

logger = setup_logger(__name__)


class EvaluatorAgent:
    """
    Agent responsible for orchestrating data quality evaluation.
    
    INTERVIEW EXPLANATION:
    This is the critic agent that evaluates the work of other agents.
    It coordinates evaluation, stores results in database, and provides
    analytics capabilities.
    
    Responsibilities:
    1. Evaluate data from collector, cleaner, and labeler agents
    2. Save evaluation results to database
    3. Track evaluation statistics
    4. Manage pipeline run tracking
    """
    
    def __init__(self, db_path: str = "data/evaluations.db"):
        """
        Initialize the evaluator agent.
        
        INTERVIEW EXPLANATION:
        Args:
            db_path: Path to SQLite database file for storing evaluations
        """
        # Create evaluator instance (contains the evaluation logic)
        self.evaluator = DataEvaluator()
        
        # Initialize database manager (handles database connection)
        self.db_manager = DatabaseManager(db_path)
        
        # Track evaluation statistics
        self.stats = {
            'evaluations_performed': 0,
            'evaluations_saved': 0,
            'evaluations_failed': 0
        }
        
        # Current pipeline run ID (groups evaluations from same pipeline execution)
        self.current_run_id = None
    
    def start_pipeline_run(self) -> str:
        """
        Start a new pipeline evaluation run.
        
        INTERVIEW EXPLANATION:
        Creates a unique ID for this pipeline execution.
        All evaluations from this run will share this ID.
        Useful for:
        - Tracking all evaluations from one pipeline execution
        - Comparing performance across runs
        - Debugging: Find all evaluations from a specific run
        
        Returns:
            Unique run ID string
        """
        # Generate unique run ID: run_YYYYMMDD_HHMMSS_randomhex
        self.current_run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        logger.info(f"Started pipeline evaluation run: {self.current_run_id}")
        return self.current_run_id
    
    def evaluate_collector_output(
        self, 
        data: Dict[str, Any], 
        file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate data from collector agent and save to database.
        
        INTERVIEW EXPLANATION:
        Process:
        1. Call evaluator to assess data quality
        2. Save evaluation result to database
        3. Update statistics
        4. Return evaluation result
        
        Args:
            data: Collected data dictionary (from collector agent)
            file_path: Optional path to data file (for tracking)
        
        Returns:
            Evaluation result dictionary with scores and issues
        """
        try:
            symbol = data.get('symbol', 'unknown')
            logger.info(f"Evaluating collector data for symbol: {symbol}")
            
            # Step 1: Perform evaluation using evaluator
            # This calls evaluate_collector_data() from DataEvaluator class
            evaluation_result = self.evaluator.evaluate_collector_data(data)
            
            # Step 2: Save evaluation to database
            self._save_evaluation(
                agent_type='collector',
                symbol=symbol,
                evaluation_result=evaluation_result,
                file_path=file_path
            )
            
            # Step 3: Update statistics
            self.stats['evaluations_performed'] += 1
            self.stats['evaluations_saved'] += 1
            
            return evaluation_result
            
        except Exception as e:
            # Error handling: Log error and update failure count
            logger.error(f"Error evaluating collector data: {e}", exc_info=True)
            self.stats['evaluations_failed'] += 1
            return {}  # Return empty dict on error
    
    def evaluate_cleaner_output(
        self, 
        data: Dict[str, Any], 
        file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate data from cleaner agent and save to database.
        
        INTERVIEW EXPLANATION:
        Same process as evaluate_collector_output, but for cleaned data.
        
        Args:
            data: Cleaned data dictionary (from cleaner agent)
            file_path: Optional path to cleaned data file
        
        Returns:
            Evaluation result dictionary
        """
        try:
            symbol = data.get('symbol', 'unknown')
            logger.info(f"Evaluating cleaner data for symbol: {symbol}")
            
            # Evaluate cleaned data
            evaluation_result = self.evaluator.evaluate_cleaner_data(data)
            
            # Save to database
            self._save_evaluation(
                agent_type='cleaner',
                symbol=symbol,
                evaluation_result=evaluation_result,
                file_path=file_path
            )
            
            self.stats['evaluations_performed'] += 1
            self.stats['evaluations_saved'] += 1
            
            return evaluation_result
            
        except Exception as e:
            logger.error(f"Error evaluating cleaner data: {e}", exc_info=True)
            self.stats['evaluations_failed'] += 1
            return {}
    
    def evaluate_labeler_output(
        self, 
        data: Dict[str, Any], 
        file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate data from labeler agent and save to database.
        
        INTERVIEW EXPLANATION:
        Same process as above, but for labeled data.
        
        Args:
            data: Labeled data dictionary (from labeler agent)
            file_path: Optional path to labeled data file
        
        Returns:
            Evaluation result dictionary
        """
        try:
            symbol = data.get('symbol', 'unknown')
            logger.info(f"Evaluating labeler data for symbol: {symbol}")
            
            # Evaluate labeled data
            evaluation_result = self.evaluator.evaluate_labeler_data(data)
            
            # Save to database
            self._save_evaluation(
                agent_type='labeler',
                symbol=symbol,
                evaluation_result=evaluation_result,
                file_path=file_path
            )
            
            self.stats['evaluations_performed'] += 1
            self.stats['evaluations_saved'] += 1
            
            return evaluation_result
            
        except Exception as e:
            logger.error(f"Error evaluating labeler data: {e}", exc_info=True)
            self.stats['evaluations_failed'] += 1
            return {}
    
    def evaluate_all_pipeline_outputs(self) -> Dict[str, Any]:
        """
        Evaluate all outputs from the pipeline.
        
        INTERVIEW EXPLANATION:
        This method processes all data files from raw, cleaned, and labeled
        directories and evaluates them. This is batch processing - processing
        many files in one operation.
        
        Process:
        1. Start a new pipeline run (get unique run ID)
        2. Find all data files in each directory
        3. For each file:
           - Load JSON data
           - Evaluate it
           - Save evaluation to database
        4. Return summary of all evaluations
        
        Returns:
            Dictionary with evaluation results for each agent type
        """
        logger.info("Starting evaluation of all pipeline outputs")
        
        # Step 1: Start new pipeline run
        run_id = self.start_pipeline_run()
        
        # Step 2: Initialize results dictionary
        results = {
            'run_id': run_id,
            'collector_evaluations': [],  # List to store collector eval results
            'cleaner_evaluations': [],    # List to store cleaner eval results
            'labeler_evaluations': []     # List to store labeler eval results
        }
        
        # ============================================================
        # Step 3: Evaluate raw/collected data files
        # ============================================================
        # Get all JSON files from raw data directory
        raw_files = list(RAW_DATA_DIR.glob("*.json"))
        # Filter out aggregated files (files starting with "all_coins")
        raw_files = [f for f in raw_files if not f.name.startswith("all_coins")]
        
        logger.info(f"Found {len(raw_files)} raw data files to evaluate")
        
        for file_path in raw_files:
            try:
                # Load JSON data from file
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                # Evaluate the data
                eval_result = self.evaluate_collector_output(data, str(file_path))
                
                # Add to results if evaluation was successful
                if eval_result:
                    results['collector_evaluations'].append(eval_result)
                    
            except Exception as e:
                # Log error but continue with other files (graceful degradation)
                logger.error(f"Error evaluating {file_path}: {e}")
        
        # ============================================================
        # Step 4: Evaluate cleaned data files
        # ============================================================
        cleaned_files = list(CLEANED_DATA_DIR.glob("*.json"))
        cleaned_files = [f for f in cleaned_files if not f.name.startswith("all_coins")]
        
        logger.info(f"Found {len(cleaned_files)} cleaned data files to evaluate")
        
        for file_path in cleaned_files:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                eval_result = self.evaluate_cleaner_output(data, str(file_path))
                
                if eval_result:
                    results['cleaner_evaluations'].append(eval_result)
                    
            except Exception as e:
                logger.error(f"Error evaluating {file_path}: {e}")
        
        # ============================================================
        # Step 5: Evaluate labeled data files
        # ============================================================
        labeled_files = list(LABELED_DATA_DIR.glob("*.json"))
        labeled_files = [f for f in labeled_files if not f.name.startswith("all_coins")]
        
        logger.info(f"Found {len(labeled_files)} labeled data files to evaluate")
        
        for file_path in labeled_files:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                eval_result = self.evaluate_labeler_output(data, str(file_path))
                
                if eval_result:
                    results['labeler_evaluations'].append(eval_result)
                    
            except Exception as e:
                logger.error(f"Error evaluating {file_path}: {e}")
        
        # Step 6: Log summary and return results
        logger.info("Completed evaluation of all pipeline outputs")
        self._log_summary()
        
        return results
    
    def _save_evaluation(
        self,
        agent_type: str,
        symbol: Optional[str],
        evaluation_result: Dict[str, Any],
        file_path: Optional[str] = None
    ):
        """
        Save evaluation to database.
        
        INTERVIEW EXPLANATION:
        This is a private method (underscore prefix) that handles database operations.
        
        Process:
        1. Get database session
        2. Create Evaluation model object with evaluation data
        3. Add to session (stage for insert)
        4. Commit to database (actually save)
        5. Handle errors with rollback
        
        Args:
            agent_type: Type of agent evaluated ('collector', 'cleaner', 'labeler')
            symbol: Crypto symbol (e.g., 'BTC', 'ETH')
            evaluation_result: Dictionary with evaluation scores and details
            file_path: Path to the data file that was evaluated
        """
        # Get database session
        session = self.db_manager.get_session()
        try:
            # Create Evaluation model object
            # This maps Python object to database row
            eval_record = Evaluation(
                agent_type=agent_type,
                symbol=symbol,
                # Scores from evaluation result
                completeness_score=evaluation_result.get('completeness_score'),
                accuracy_score=evaluation_result.get('accuracy_score'),
                consistency_score=evaluation_result.get('consistency_score'),
                overall_score=evaluation_result.get('overall_score'),
                # JSON fields: Store complex data as JSON strings
                metrics_json=evaluation_result.get('metrics_json', '{}'),
                evaluated_fields=json.dumps(evaluation_result.get('evaluated_fields', [])),
                issues_found=json.dumps(evaluation_result.get('issues_found', [])),
                recommendations=json.dumps(evaluation_result.get('recommendations', [])),
                # Metadata
                pipeline_run_id=self.current_run_id,
                data_file_path=file_path
            )
            
            # Add to session (stages the insert, doesn't execute yet)
            session.add(eval_record)
            
            # Commit: Actually execute the INSERT statement
            session.commit()
            
            logger.debug(f"Saved evaluation for {agent_type} - {symbol}")
            
        except Exception as e:
            # If error occurs, rollback (undo) the transaction
            logger.error(f"Error saving evaluation to database: {e}", exc_info=True)
            session.rollback()
        finally:
            # Always close session to free database connection
            session.close()
    
    def _log_summary(self):
        """
        Log evaluation summary statistics.
        
        INTERVIEW EXPLANATION:
        Private method that logs a summary of evaluation statistics.
        Useful for monitoring and debugging.
        """
        logger.info("=" * 50)
        logger.info("EVALUATION SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Evaluations performed: {self.stats['evaluations_performed']}")
        logger.info(f"Evaluations saved: {self.stats['evaluations_saved']}")
        logger.info(f"Evaluations failed: {self.stats['evaluations_failed']}")
        logger.info("=" * 50)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get evaluation statistics.
        
        INTERVIEW EXPLANATION:
        Returns combined statistics from both evaluator agent and core evaluator.
        
        Returns:
            Dictionary with all statistics
        """
        return {
            **self.stats,  # Spread operator: Include all stats from self.stats
            **self.evaluator.get_evaluation_stats()  # Include stats from evaluator
        }
    
    def close(self):
        """
        Close database connections.
        
        INTERVIEW EXPLANATION:
        Clean up resources. Important to call when done with evaluator agent
        to properly close database connections.
        """
        self.db_manager.close()

