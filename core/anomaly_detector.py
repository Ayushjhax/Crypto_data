
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from database.queries import EvaluationQueries
from database.models import DatabaseManager
from utils.logger import setup_logger

logger = setup_logger(__name__)


class AnomalyDetector:
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.queries = EvaluationQueries(db_manager)
    
    def detect_quality_score_anomaly(
        self, 
        agent_type: str, 
        threshold: float = 0.7,
        lookback_days: int = 7,
        z_score_threshold: float = -2.0
    ) -> Dict[str, Any]:
        logger.info(f"Checking for anomalies in {agent_type} quality scores")
        
        recent_scores_data = self.queries.get_trend_over_time(
            agent_type=agent_type,
            days=lookback_days
        )
        
        if not recent_scores_data:
            return {
                'anomaly_detected': False,
                'agent_type': agent_type,
                'reason': 'No historical data available',
                'timestamp': datetime.now().isoformat()
            }
        
        recent_scores = [
            s['avg_score'] for s in recent_scores_data 
            if s['avg_score'] is not None
        ]
        
        if len(recent_scores) < 2:
            return {
                'anomaly_detected': False,
                'agent_type': agent_type,
                'reason': 'Insufficient data for anomaly detection (need at least 2 data points)',
                'timestamp': datetime.now().isoformat()
            }
        
        latest_score = recent_scores[-1]
        
        historical_scores = recent_scores[:-1]
        historical_avg = np.mean(historical_scores)
        historical_std = np.std(historical_scores) if len(historical_scores) > 1 else 0
        
        anomalies = []
        severity_levels = []
        
        if latest_score < threshold:
            anomalies.append({
                'type': 'threshold',
                'severity': 'high',
                'message': f'{agent_type} quality score {latest_score:.3f} below threshold {threshold}',
                'current_value': latest_score,
                'threshold': threshold,
                'deviation': latest_score - threshold
            })
            severity_levels.append('high')
        
        if historical_std > 0:  # Avoid division by zero
            z_score = (latest_score - historical_avg) / historical_std
            
            if z_score < z_score_threshold:
                anomalies.append({
                    'type': 'statistical',
                    'severity': 'medium' if abs(z_score) < 3.0 else 'high',
                    'message': f'{agent_type} score {latest_score:.3f} is {abs(z_score):.2f} std dev below average {historical_avg:.3f}',
                    'z_score': round(z_score, 3),
                    'historical_avg': round(historical_avg, 3),
                    'historical_std': round(historical_std, 3),
                    'current_value': latest_score
                })
                severity_levels.append('high' if abs(z_score) >= 3.0 else 'medium')
        
        if len(historical_scores) >= 2:
            previous_score = historical_scores[-1]
            if previous_score > 0:  # Avoid division by zero
                change_rate = (latest_score - previous_score) / previous_score
                
                if change_rate < -0.2:
                    anomalies.append({
                        'type': 'rate_of_change',
                        'severity': 'high',
                        'message': f'{agent_type} score dropped by {abs(change_rate)*100:.1f}% (from {previous_score:.3f} to {latest_score:.3f})',
                        'previous_score': previous_score,
                        'current_score': latest_score,
                        'change_percent': round(change_rate * 100, 2)
                    })
                    severity_levels.append('high')
        
        overall_severity = 'high' if 'high' in severity_levels else ('medium' if severity_levels else 'low')
        
        return {
            'anomaly_detected': len(anomalies) > 0,
            'agent_type': agent_type,
            'latest_score': latest_score,
            'historical_avg': round(historical_avg, 3),
            'historical_std': round(historical_std, 3) if historical_std > 0 else 0,
            'anomalies': anomalies,
            'overall_severity': overall_severity,
            'anomaly_count': len(anomalies),
            'lookback_days': lookback_days,
            'timestamp': datetime.now().isoformat()
        }
    
    def detect_error_rate_spike(
        self,
        error_counts: List[int],
        threshold_multiplier: float = 2.0
    ) -> Dict[str, Any]:
        if len(error_counts) < 2:
            return {
                'anomaly_detected': False,
                'reason': 'Insufficient data for error rate detection'
            }
        
        recent_errors = error_counts[-1]
        historical_errors = error_counts[:-1]
        historical_avg = np.mean(historical_errors)
        
        if historical_avg == 0:
            historical_avg = 1  # Avoid division by zero
        
        multiplier = recent_errors / historical_avg
        
        is_anomaly = multiplier >= threshold_multiplier
        
        severity = 'high' if multiplier >= 3.0 else ('medium' if is_anomaly else 'low')
        
        return {
            'anomaly_detected': is_anomaly,
            'recent_errors': recent_errors,
            'historical_avg': round(historical_avg, 2),
            'multiplier': round(multiplier, 2),
            'severity': severity,
            'message': f'Error count {recent_errors} is {multiplier:.1f}x the historical average {historical_avg:.1f}' if is_anomaly else 'Error rate is normal',
            'timestamp': datetime.now().isoformat()
        }
    
    def detect_collection_metrics_anomaly(
        self,
        collection_stats: Dict[str, Any],
        historical_avg: Dict[str, Any]
    ) -> Dict[str, Any]:
        anomalies = []
        
        current_success_rate = collection_stats.get('success_rate', 1.0)
        historical_success_rate = historical_avg.get('success_rate', 0.95)
        
        if current_success_rate < (historical_success_rate - 0.1):  # 10% drop
            anomalies.append({
                'type': 'success_rate',
                'severity': 'high',
                'message': f'Collection success rate dropped to {current_success_rate:.1%} from {historical_success_rate:.1%}',
                'current_value': current_success_rate,
                'historical_value': historical_success_rate
            })
        
        current_count = collection_stats.get('successful', 0)
        historical_count = historical_avg.get('successful', 8)
        
        if current_count < (historical_count * 0.5):  # Less than 50% of historical
            anomalies.append({
                'type': 'collection_count',
                'severity': 'medium',
                'message': f'Only {current_count} coins collected (expected ~{historical_count})',
                'current_value': current_count,
                'historical_value': historical_count
            })
        
        return {
            'anomaly_detected': len(anomalies) > 0,
            'anomalies': anomalies,
            'timestamp': datetime.now().isoformat()
        }
    
    def check_all_agents(self, threshold: float = 0.7, lookback_days: int = 7) -> Dict[str, Any]:
        results = {
            'timestamp': datetime.now().isoformat(),
            'agents_checked': [],
            'anomalies_found': 0,
            'critical_anomalies': 0
        }
        
        agent_types = ['collector', 'cleaner', 'labeler']
        
        for agent_type in agent_types:
            try:
                anomaly_result = self.detect_quality_score_anomaly(
                    agent_type=agent_type,
                    threshold=threshold,
                    lookback_days=lookback_days
                )
                
                results['agents_checked'].append({
                    'agent_type': agent_type,
                    'anomaly_detected': anomaly_result.get('anomaly_detected', False),
                    'severity': anomaly_result.get('overall_severity', 'low'),
                    'anomaly_count': anomaly_result.get('anomaly_count', 0),
                    'latest_score': anomaly_result.get('latest_score'),
                    'details': anomaly_result
                })
                
                if anomaly_result.get('anomaly_detected'):
                    results['anomalies_found'] += 1
                    if anomaly_result.get('overall_severity') == 'high':
                        results['critical_anomalies'] += 1
                        
            except Exception as e:
                logger.error(f"Error checking {agent_type} for anomalies: {e}", exc_info=True)
                results['agents_checked'].append({
                    'agent_type': agent_type,
                    'error': str(e)
                })
        
        return results

