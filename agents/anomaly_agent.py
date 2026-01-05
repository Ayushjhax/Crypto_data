"""
Anomaly Detection Agent - Monitors metrics for anomalies.

INTERVIEW EXPLANATION:
This agent orchestrates anomaly detection and alerting:
1. Checks all agents for quality score anomalies
2. Monitors collection metrics
3. Sends alerts when anomalies are detected
4. Stores anomaly records in database

This follows the same agent pattern as EvaluatorAgent, CollectorAgent, etc.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from core.anomaly_detector import AnomalyDetector
from utils.alerting import AlertManager
from database.models import DatabaseManager
from utils.logger import setup_logger

logger = setup_logger(__name__)


class AnomalyAgent:
    """
    Agent responsible for anomaly detection and alerting.
    
    INTERVIEW EXPLANATION:
    This agent monitors product metrics (quality scores, error rates, etc.)
    and alerts the engineering team when anomalies are detected.
    
    Responsibilities:
    1. Detect anomalies in data quality metrics
    2. Monitor collection metrics
    3. Send alerts through configured channels
    4. Track anomaly statistics
    """
    
    def __init__(
        self, 
        db_path: str = "data/evaluations.db",
        alert_channels: Optional[List[str]] = None
    ):
        """
        Initialize the anomaly agent.
        
        INTERVIEW EXPLANATION:
        Args:
            db_path: Path to evaluation database (to read quality scores)
            alert_channels: List of alert channels to use (default: ['console'])
        """
        # Initialize database manager (to read evaluation data)
        self.db_manager = DatabaseManager(db_path)
        
        # Initialize anomaly detector (contains detection logic)
        self.detector = AnomalyDetector(self.db_manager)
        
        # Initialize alert manager (handles alert delivery)
        self.alert_manager = AlertManager(alert_channels=alert_channels)
        
        # Track statistics
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
        """
        Check all agents for metric anomalies.
        
        INTERVIEW EXPLANATION:
        This is the main method that:
        1. Checks all agent types (collector, cleaner, labeler) for anomalies
        2. Sends alerts if anomalies detected
        3. Updates statistics
        4. Returns comprehensive results
        
        Args:
            threshold: Minimum acceptable quality score
            lookback_days: Number of days to analyze
            send_alerts: Whether to send alerts (default: True)
            
        Returns:
            Dictionary with anomaly check results
        """
        logger.info("Starting anomaly check for all metrics")
        
        # Update statistics
        self.stats['anomaly_checks_performed'] += 1
        
        # Check all agents for anomalies
        check_results = self.detector.check_all_agents(
            threshold=threshold,
            lookback_days=lookback_days
        )
        
        # Count anomalies
        anomalies_found = check_results.get('anomalies_found', 0)
        critical_anomalies = check_results.get('critical_anomalies', 0)
        
        if anomalies_found > 0:
            self.stats['anomalies_detected'] += anomalies_found
            self.stats['critical_anomalies'] += critical_anomalies
            
            # Send alerts if enabled
            if send_alerts:
                alert_sent = self.alert_manager.send_summary_alert(check_results)
                if alert_sent:
                    self.stats['alerts_sent'] += 1
                
                # Also send individual alerts for each agent with anomalies
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
        """
        Check a single agent for anomalies.
        
        INTERVIEW EXPLANATION:
        Useful for targeted monitoring of specific agents.
        
        Args:
            agent_type: Which agent to check ('collector', 'cleaner', 'labeler')
            threshold: Minimum acceptable quality score
            lookback_days: Number of days to analyze
            send_alert: Whether to send alert if anomaly detected
            
        Returns:
            Anomaly detection result for the agent
        """
        logger.info(f"Checking {agent_type} for anomalies")
        
        # Detect anomalies
        anomaly_result = self.detector.detect_quality_score_anomaly(
            agent_type=agent_type,
            threshold=threshold,
            lookback_days=lookback_days
        )
        
        # Send alert if anomaly detected
        if anomaly_result.get('anomaly_detected') and send_alert:
            self.alert_manager.send_anomaly_alert(anomaly_result)
            self.stats['alerts_sent'] += 1
            self.stats['anomalies_detected'] += 1
            
            if anomaly_result.get('overall_severity') == 'high':
                self.stats['critical_anomalies'] += 1
        
        self.stats['anomaly_checks_performed'] += 1
        
        return anomaly_result
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get anomaly detection statistics.
        
        INTERVIEW EXPLANATION:
        Returns statistics about anomaly checks performed and alerts sent.
        Useful for monitoring and reporting.
        
        Returns:
            Dictionary with statistics
        """
        return self.stats.copy()
    
    def close(self):
        """
        Close database connections.
        
        INTERVIEW EXPLANATION:
        Clean up resources. Important to call when done with agent.
        """
        self.db_manager.close()
        logger.info("AnomalyAgent closed")

