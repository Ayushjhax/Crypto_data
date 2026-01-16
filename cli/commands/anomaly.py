
import click

from agents.anomaly_agent import AnomalyAgent
from cli.utils import print_success, print_error, print_info, print_warning, format_output
from utils.logger import setup_logger

logger = setup_logger(__name__)


@click.group()
def anomaly():
    pass


@anomaly.command()
@click.option('--threshold', default=0.7, type=float, help='Quality score threshold (0-1)')
@click.option('--lookback-days', default=7, type=int, help='Number of days to look back')
@click.option('--send-alerts/--no-alerts', default=True, help='Send alerts when anomalies detected')
@click.option('--db-path', default='data/evaluations.db', help='Path to evaluation database')
@click.option('--output-format', type=click.Choice(['table', 'json']), default='table', help='Output format')
def check_all(threshold, lookback_days, send_alerts, db_path, output_format):
    try:
        print_info("Checking all metrics for anomalies...")
        agent = AnomalyAgent(db_path=db_path)
        
        results = agent.check_all_metrics(
            threshold=threshold,
            lookback_days=lookback_days,
            send_alerts=send_alerts
        )
        
        anomalies_found = results.get('anomalies_found', 0)
        critical_anomalies = results.get('critical_anomalies', 0)
        
        if anomalies_found > 0:
            print_warning(f"Found {anomalies_found} anomaly(ies), {critical_anomalies} critical")
        else:
            print_success("No anomalies detected - all metrics are healthy")
        
        if output_format == 'json':
            print(format_output(results, format=output_format))
        else:
            print("\n" + "="*60)
            print("ANOMALY DETECTION RESULTS")
            print("="*60)
            print(f"\nAnomalies Found: {anomalies_found}")
            print(f"Critical Anomalies: {critical_anomalies}")
            
            if results.get('agents_checked'):
                print("\nAgent Checks:")
                for agent_check in results['agents_checked']:
                    agent_type = agent_check.get('agent_type', 'unknown')
                    detected = agent_check.get('anomaly_detected', False)
                    status = "⚠️  ANOMALY DETECTED" if detected else "✅ Normal"
                    print(f"  {agent_type}: {status}")
                    
                    if detected:
                        details = agent_check.get('details', {})
                        print(f"    Severity: {details.get('overall_severity', 'unknown')}")
                        print(f"    Current Score: {details.get('current_score', 'N/A')}")
                        print(f"    Historical Avg: {details.get('historical_avg', 'N/A')}")
        
        stats = agent.get_stats()
        print(f"\nStatistics:")
        print(format_output(stats, format=output_format))
        
        agent.close()
        
    except Exception as e:
        print_error(f"Anomaly check failed: {e}")
        logger.error(f"Anomaly check failed: {e}", exc_info=True)
        raise click.Abort()


@anomaly.command()
@click.argument('agent_type', type=click.Choice(['collector', 'cleaner', 'labeler']))
@click.option('--threshold', default=0.7, type=float, help='Quality score threshold (0-1)')
@click.option('--lookback-days', default=7, type=int, help='Number of days to look back')
@click.option('--send-alert/--no-alert', default=True, help='Send alert if anomaly detected')
@click.option('--db-path', default='data/evaluations.db', help='Path to evaluation database')
@click.option('--output-format', type=click.Choice(['table', 'json']), default='table', help='Output format')
def check_agent(agent_type, threshold, lookback_days, send_alert, db_path, output_format):
    try:
        print_info(f"Checking {agent_type} for anomalies...")
        agent = AnomalyAgent(db_path=db_path)
        
        result = agent.check_single_agent(
            agent_type=agent_type,
            threshold=threshold,
            lookback_days=lookback_days,
            send_alert=send_alert
        )
        
        if result.get('anomaly_detected'):
            print_warning(f"Anomaly detected in {agent_type}!")
            print(f"Severity: {result.get('overall_severity', 'unknown')}")
        else:
            print_success(f"No anomalies detected in {agent_type}")
        
        print("\n" + format_output(result, format=output_format))
        
        agent.close()
        
    except Exception as e:
        print_error(f"Anomaly check failed: {e}")
        logger.error(f"Anomaly check failed: {e}", exc_info=True)
        raise click.Abort()


@anomaly.command()
@click.option('--db-path', default='data/evaluations.db', help='Path to evaluation database')
@click.option('--output-format', type=click.Choice(['table', 'json']), default='table', help='Output format')
def stats(db_path, output_format):
    try:
        agent = AnomalyAgent(db_path=db_path)
        stats = agent.get_stats()
        
        print("Anomaly Detection Statistics:")
        print(format_output(stats, format=output_format))
        
        agent.close()
        
    except Exception as e:
        print_error(f"Error getting stats: {e}")
        logger.error(f"Error getting stats: {e}", exc_info=True)
        raise click.Abort()

