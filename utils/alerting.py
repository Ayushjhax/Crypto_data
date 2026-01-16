
import json
from typing import Dict, Any, Optional
from utils.logger import setup_logger

logger = setup_logger(__name__)


class AlertManager:
    
    def __init__(self, alert_channels: Optional[list] = None):
        self.alert_channels = alert_channels or ['console']
        logger.info(f"AlertManager initialized with channels: {self.alert_channels}")
    
    def send_anomaly_alert(
        self, 
        anomaly_result: Dict[str, Any], 
        channel: Optional[str] = None
    ) -> bool:
        if not anomaly_result.get('anomaly_detected'):
            return False
        
        message = self._format_alert_message(anomaly_result)
        
        channels = [channel] if channel else self.alert_channels
        
        success = True
        for ch in channels:
            try:
                if ch == 'console':
                    self._send_console_alert(message, anomaly_result)
                elif ch == 'email':
                    self._send_email(message, anomaly_result)
                elif ch == 'slack':
                    self._send_slack(message, anomaly_result)
                elif ch == 'webhook':
                    self._send_webhook(message, anomaly_result)
                else:
                    logger.warning(f"Unknown alert channel: {ch}")
                    success = False
            except Exception as e:
                logger.error(f"Error sending alert via {ch}: {e}", exc_info=True)
                success = False
        
        return success
    
    def _format_alert_message(self, anomaly_result: Dict[str, Any]) -> str:
        agent_type = anomaly_result.get('agent_type', 'unknown')
        anomalies = anomaly_result.get('anomalies', [])
        severity = anomaly_result.get('overall_severity', 'medium')
        
        severity_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(severity, '⚪')
        msg = f"{severity_emoji} ANOMALY ALERT: {agent_type.upper()} Metrics\n"
        msg += "=" * 60 + "\n\n"
        
        latest_score = anomaly_result.get('latest_score')
        historical_avg = anomaly_result.get('historical_avg')
        msg += f"Current Quality Score: {latest_score:.3f}\n"
        msg += f"Historical Average: {historical_avg:.3f}\n"
        msg += f"Severity: {severity.upper()}\n\n"
        
        msg += "Anomalies Detected:\n"
        msg += "-" * 60 + "\n"
        for i, anomaly in enumerate(anomalies, 1):
            msg += f"{i}. [{anomaly['type'].upper()}] {anomaly['severity'].upper()}\n"
            msg += f"   {anomaly['message']}\n"
            if 'current_value' in anomaly and 'threshold' in anomaly:
                msg += f"   Value: {anomaly['current_value']:.3f} | Threshold: {anomaly['threshold']:.3f}\n"
            msg += "\n"
        
        msg += "=" * 60 + "\n"
        msg += "ACTION REQUIRED:\n"
        msg += "- Please investigate the quality score drop\n"
        msg += "- Check logs for errors in data collection/cleaning/labeling\n"
        msg += "- Verify data sources are functioning correctly\n"
        msg += f"- Timestamp: {anomaly_result.get('timestamp', 'N/A')}\n"
        msg += "=" * 60
        
        return msg
    
    def _send_console_alert(self, message: str, anomaly_result: Dict[str, Any]):
        severity = anomaly_result.get('overall_severity', 'medium')
        
        if severity == 'high':
            logger.error(f"\n{message}\n")
        elif severity == 'medium':
            logger.warning(f"\n{message}\n")
        else:
            logger.info(f"\n{message}\n")
    
    def _send_email(self, message: str, anomaly_result: Dict[str, Any]):
        logger.info(f"Email alert (not implemented): {message[:100]}...")
    
    def _send_slack(self, message: str, anomaly_result: Dict[str, Any]):
        logger.info(f"Slack alert (not implemented): {message[:100]}...")
    
    def _send_webhook(self, message: str, anomaly_result: Dict[str, Any]):
        logger.info(f"Webhook alert (not implemented): {message[:100]}...")
    
    def send_summary_alert(self, check_results: Dict[str, Any]) -> bool:
        anomalies_found = check_results.get('anomalies_found', 0)
        critical_anomalies = check_results.get('critical_anomalies', 0)
        
        if anomalies_found == 0:
            logger.info("✅ No anomalies detected - all metrics are healthy")
            return True
        
        msg = f"🔍 ANOMALY CHECK SUMMARY\n"
        msg += "=" * 60 + "\n\n"
        msg += f"Total Anomalies Found: {anomalies_found}\n"
        msg += f"Critical Anomalies: {critical_anomalies}\n\n"
        
        for agent_check in check_results.get('agents_checked', []):
            agent_type = agent_check.get('agent_type')
            if agent_check.get('anomaly_detected'):
                severity = agent_check.get('severity', 'medium')
                count = agent_check.get('anomaly_count', 0)
                score = agent_check.get('latest_score', 'N/A')
                msg += f"  🔴 {agent_type}: {count} anomaly(ies) - Severity: {severity} - Score: {score}\n"
            else:
                score = agent_check.get('latest_score', 'N/A')
                msg += f"  ✅ {agent_type}: No anomalies - Score: {score}\n"
        
        msg += f"\nTimestamp: {check_results.get('timestamp')}\n"
        msg += "=" * 60
        
        if critical_anomalies > 0:
            logger.error(f"\n{msg}\n")
        elif anomalies_found > 0:
            logger.warning(f"\n{msg}\n")
        else:
            logger.info(f"\n{msg}\n")
        
        return True

