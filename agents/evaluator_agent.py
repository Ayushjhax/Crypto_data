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
    
    def __init__(self, db_path: str = "data/evaluations.db"):
        self.evaluator = DataEvaluator()
        
        self.db_manager = DatabaseManager(db_path)
        
        self.stats = {
            'evaluations_performed': 0,
            'evaluations_saved': 0,
            'evaluations_failed': 0
        }
        
        self.current_run_id = None
    
    def start_pipeline_run(self) -> str:
        self.current_run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        logger.info(f"Started pipeline evaluation run: {self.current_run_id}")
        return self.current_run_id
    
    def evaluate_collector_output(
        self, 
        data: Dict[str, Any], 
        file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        try:
            symbol = data.get('symbol', 'unknown')
            logger.info(f"Evaluating collector data for symbol: {symbol}")
            
            evaluation_result = self.evaluator.evaluate_collector_data(data)
            
            self._save_evaluation(
                agent_type='collector',
                symbol=symbol,
                evaluation_result=evaluation_result,
                file_path=file_path
            )
            
            self.stats['evaluations_performed'] += 1
            self.stats['evaluations_saved'] += 1
            
            return evaluation_result
            
        except Exception as e:
            logger.error(f"Error evaluating collector data: {e}", exc_info=True)
            self.stats['evaluations_failed'] += 1
            return {}
    
    def evaluate_cleaner_output(
        self, 
        data: Dict[str, Any], 
        file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        try:
            symbol = data.get('symbol', 'unknown')
            logger.info(f"Evaluating cleaner data for symbol: {symbol}")
            
            evaluation_result = self.evaluator.evaluate_cleaner_data(data)
            
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
        try:
            symbol = data.get('symbol', 'unknown')
            logger.info(f"Evaluating labeler data for symbol: {symbol}")
            
            evaluation_result = self.evaluator.evaluate_labeler_data(data)
            
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
        logger.info("Starting evaluation of all pipeline outputs")
        
        run_id = self.start_pipeline_run()
        
        results = {
            'run_id': run_id,
            'collector_evaluations': [],
            'cleaner_evaluations': [],
            'labeler_evaluations': []
        }
        
        raw_files = list(RAW_DATA_DIR.glob("*.json"))
        raw_files = [f for f in raw_files if not f.name.startswith("all_coins")]
        
        logger.info(f"Found {len(raw_files)} raw data files to evaluate")
        
        for file_path in raw_files:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                eval_result = self.evaluate_collector_output(data, str(file_path))
                
                if eval_result:
                    results['collector_evaluations'].append(eval_result)
                    
            except Exception as e:
                logger.error(f"Error evaluating {file_path}: {e}")
        
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
        session = self.db_manager.get_session()
        try:
            eval_record = Evaluation(
                agent_type=agent_type,
                symbol=symbol,
                completeness_score=evaluation_result.get('completeness_score'),
                accuracy_score=evaluation_result.get('accuracy_score'),
                consistency_score=evaluation_result.get('consistency_score'),
                overall_score=evaluation_result.get('overall_score'),
                metrics_json=evaluation_result.get('metrics_json', '{}'),
                evaluated_fields=json.dumps(evaluation_result.get('evaluated_fields', [])),
                issues_found=json.dumps(evaluation_result.get('issues_found', [])),
                recommendations=json.dumps(evaluation_result.get('recommendations', [])),
                pipeline_run_id=self.current_run_id,
                data_file_path=file_path
            )
            
            session.add(eval_record)
            
            session.commit()
            
            logger.debug(f"Saved evaluation for {agent_type} - {symbol}")
            
        except Exception as e:
            logger.error(f"Error saving evaluation to database: {e}", exc_info=True)
            session.rollback()
        finally:
            session.close()
    
    def _log_summary(self):
        logger.info("=" * 50)
        logger.info("EVALUATION SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Evaluations performed: {self.stats['evaluations_performed']}")
        logger.info(f"Evaluations saved: {self.stats['evaluations_saved']}")
        logger.info(f"Evaluations failed: {self.stats['evaluations_failed']}")
        logger.info("=" * 50)
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            **self.stats,
            **self.evaluator.get_evaluation_stats()
        }
    
    def close(self):
        self.db_manager.close()
