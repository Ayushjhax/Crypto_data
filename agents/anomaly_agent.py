from typing import Dict, Any, Optional, List
from datetime import datetime

from core.anomaly_detector import AnomalyDetector
from utils.alerting import AlertManager
from database.models import DatabaseManager
from utils.logger import setup_logger

logger = setup_logger(__name__)


class AnomalyAgent:
    
    def __init__(
        self, 
        db_path: str = "data/evaluations.db",
        alert_channels: Optional[List[str]] = None
    ):
        self.db_manager = DatabaseManager(db_path)
        
        self.detector = AnomalyDetector(self.db_manager)
        
        self.alert_manager = AlertManager(alert_channels=alert_channels)
        
        self.stats = {
            'anomaly_checks_performed': 0,
            'anomalies_detected': 0,
            'alerts_sent': 0,
            'critical_anomalies': 0
        }
        
        logger.info("AnomalyAgent initialized")
    
    def check_all_metrics(
        self,
        threshold: float = 0.7,
        lookback_days: int = 7,
        send_alerts: bool = True
    ) -> Dict[str, Any]:
        logger.info("Starting anomaly check for all metrics")
        
        self.stats['anomaly_checks_performed'] += 1
        
        check_results = self.detector.check_all_agents(
            threshold=threshold,
            lookback_days=lookback_days
        )
        
        anomalies_found = check_results.get('anomalies_found', 0)
        critical_anomalies = check_results.get('critical_anomalies', 0)
        
        if anomalies_found > 0:
            self.stats['anomalies_detected'] += anomalies_found
            self.stats['critical_anomalies'] += critical_anomalies
            
            if send_alerts:
                alert_sent = self.alert_manager.send_summary_alert(check_results)
                if alert_sent:
                    self.stats['alerts_sent'] += 1
                
                for agent_check in check_results.get('agents_checked', []):
                    if agent_check.get('anomaly_detected'):
                        details = agent_check.get('details', {})
                        self.alert_manager.send_anomaly_alert(details)
        else:
            logger.info("✅ No anomalies detected - all metrics are healthy")
        
        logger.info(f"Anomaly check complete: {anomalies_found} anomaly(ies) found")
        
        return check_results
    
    def check_single_agent(
        self,
        agent_type: str,
        threshold: float = 0.7,
        lookback_days: int = 7,
        send_alert: bool = True
    ) -> Dict[str, Any]:
        logger.info(f"Checking {agent_type} for anomalies")
        
        anomaly_result = self.detector.detect_quality_score_anomaly(
            agent_type=agent_type,
            threshold=threshold,
            lookback_days=lookback_days
        )
        
        if anomaly_result.get('anomaly_detected') and send_alert:
            self.alert_manager.send_anomaly_alert(anomaly_result)
            self.stats['alerts_sent'] += 1
            self.stats['anomalies_detected'] += 1
            
            if anomaly_result.get('overall_severity') == 'high':
                self.stats['critical_anomalies'] += 1
        
        self.stats['anomaly_checks_performed'] += 1
        
        return anomaly_result
    
    def get_stats(self) -> Dict[str, Any]:
        return self.stats.copy()
    
    def close(self):
        self.db_manager.close()
        logger.info("AnomalyAgent closed")
